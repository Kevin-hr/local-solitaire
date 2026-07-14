"""移动处理器 - v3.0 重写版（交互层）

修复要点（相对原 v3.0）：
- 不再引用未导入的 UIManager / 未定义的 CARD_WIDTH（NameError）
- DragHandler 持有 engine 与 ui 引用，坐标委托 ui.hit_test
- 拖拽采用「取出暂存 → 放置或回退」模型，杜绝重复绘制与状态不一致
- 单击 stock 抽牌；右键单击自动归位 foundation（替代易冲突的双击）
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from game_engine import Card


class MoveValidator:
    """规则校验 facade，委托给 GameEngine。"""

    def __init__(self, engine) -> None:
        self.engine = engine

    def can_move_to_tableau(self, card: Card, col: int) -> bool:
        return self.engine.can_place_tableau(card, self.engine.tableau[col])

    def can_move_to_foundation(self, card: Card, f: int) -> bool:
        return self.engine.can_place_foundation(card, self.engine.foundation[f])


class DragHandler:
    """拖拽处理器：取出牌序列暂存，松手时放置或回退。"""

    def __init__(self, engine, ui) -> None:
        self.engine = engine
        self.ui = ui
        self.dragging: bool = False
        self.drag_cards: List[Card] = []
        # drag_from: ("waste",0) / ("foundation",f) / ("tableau",col,from_idx)
        self.drag_from: Optional[Tuple] = None

    def start(self, pos: Tuple[int, int]) -> bool:
        hit = self.ui.hit_test(pos)
        if hit is None:
            return False
        zone, col, idx = hit
        if zone == "stock":
            return False  # stock 由 ClickHandler 处理
        if zone == "waste":
            if not self.engine.waste:
                return False
            card = self.engine.waste.pop()
            self.drag_cards = [card]
            self.drag_from = ("waste", 0)
        elif zone == "foundation":
            if not self.engine.foundation[col]:
                return False
            card = self.engine.foundation[col].pop()
            self.drag_cards = [card]
            self.drag_from = ("foundation", col)
        elif zone == "tableau":
            stack = self.engine.tableau[col]
            if idx < 0 or idx >= len(stack):
                return False
            seq = stack[idx:]
            if not all(c.face_up for c in seq):
                return False
            if not self.engine.is_valid_sequence(seq):
                return False
            del stack[idx:]
            self.drag_cards = seq
            self.drag_from = ("tableau", col, idx)
        else:
            return False
        self.dragging = True
        self.ui.set_drag(self.drag_cards, pos)
        return True

    def end(self, pos: Tuple[int, int]) -> None:
        if not self.dragging:
            return
        self.dragging = False
        cards = self.drag_cards
        frm = self.drag_from
        placed = False
        hit = self.ui.hit_test(pos)
        if hit is not None:
            zone, col, idx = hit
            if zone == "tableau":
                if self.engine.can_place_tableau(cards[0], self.engine.tableau[col]):
                    self.engine.tableau[col].extend(cards)
                    self.engine.moves += 1
                    if frm[0] == "tableau":
                        self.engine._flip_top(frm[1])
                    self.engine.check_win()
                    placed = True
                    if hasattr(self.ui, "trigger_placement_glow"):
                        self.ui.trigger_placement_glow(self.ui.tableau_base_rect(col))
                else:
                    if hasattr(self.ui, "flash_invalid"):
                        self.ui.flash_invalid(self.ui.tableau_base_rect(col))
            elif zone == "foundation":
                if (len(cards) == 1
                        and self.engine.can_place_foundation(cards[0], self.engine.foundation[col])):
                    self.engine.foundation[col].append(cards[0])
                    self.engine.moves += 1
                    if frm[0] == "tableau":
                        self.engine._flip_top(frm[1])
                    self.engine.check_win()
                    placed = True
                    if hasattr(self.ui, "trigger_placement_glow"):
                        self.ui.trigger_placement_glow(self.ui.foundation_rect(col))
                else:
                    if hasattr(self.ui, "flash_invalid"):
                        self.ui.flash_invalid(self.ui.foundation_rect(col))
        if not placed:
            self._return(frm, cards)
        self.drag_cards = []
        self.drag_from = None
        self.ui.clear_drag()

    def cancel(self) -> None:
        """放弃当前拖拽，把牌放回来源。"""
        if not self.dragging:
            return
        self._return(self.drag_from, self.drag_cards)
        self.dragging = False
        self.drag_cards = []
        self.drag_from = None
        self.ui.clear_drag()

    def _return(self, frm: Optional[Tuple], cards: List[Card]) -> None:
        if frm is None:
            return
        zone = frm[0]
        if zone == "waste":
            self.engine.waste.append(cards[0])
        elif zone == "foundation":
            self.engine.foundation[frm[1]].append(cards[0])
        elif zone == "tableau":
            self.engine.tableau[frm[1]].extend(cards)


class ClickHandler:
    """单击/右键处理器。"""

    def __init__(self, engine, ui, drag: DragHandler) -> None:
        self.engine = engine
        self.ui = ui
        self.drag = drag

    def handle_click(self, pos: Tuple[int, int]) -> None:
        hit = self.ui.hit_test(pos)
        if hit is None:
            return
        zone, col, idx = hit
        if zone == "stock":
            self.engine.draw_from_stock()
            return
        # 其余区域：交给拖拽
        self.drag.start(pos)

    def handle_right(self, pos: Tuple[int, int]) -> None:
        """右键：把顶牌自动归位 foundation。"""
        hit = self.ui.hit_test(pos)
        if hit is None:
            return
        zone, col, idx = hit
        if zone in ("waste", "tableau"):
            self.engine.auto_to_foundation(zone, col)
