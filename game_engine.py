"""核心游戏引擎 - v3.0 重写版（标准 Klondike 规则，纯逻辑可测试）

修复要点（相对原 v3.0）：
- Deck.create_deck 不再引用 self.suit（ AttributeError ）
- 发牌张数改为标准 1..7（原 (col*5)+2 完全错误）
- 不再强制把每列底牌改成 A（破坏规则）
- waste 存 Card 对象而非字符串
- foundation/tableau 合法性按标准规则校验
- 移动后自动翻开 tableau 顶牌
- 胜利检测：4 个 foundation 各 13 张
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

# === 常量 ===

SUITS = ("hearts", "diamonds", "clubs", "spades")
RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
RANK_VALUE = {r: i for i, r in enumerate(RANKS, start=1)}  # A=1 ... K=13
SUIT_COLOR = {"hearts": "red", "diamonds": "red", "clubs": "black", "spades": "black"}
SUIT_GLYPH = {"hearts": "♥", "diamonds": "♦", "clubs": "♣", "spades": "♠"}


@dataclass
class Card:
    rank: str
    suit: str
    face_up: bool = False

    @property
    def value(self) -> int:
        return RANK_VALUE[self.rank]

    @property
    def color(self) -> str:
        return SUIT_COLOR[self.suit]

    @property
    def glyph(self) -> str:
        return SUIT_GLYPH[self.suit]

    def __repr__(self) -> str:  # 调试用
        return f"{self.rank}{self.glyph}{'^' if self.face_up else 'v'}"


class Deck:
    """标准 52 张牌，Fisher-Yates 洗牌。"""

    @staticmethod
    def create_deck() -> List[Card]:
        deck = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        random.shuffle(deck)
        return deck


class GameEngine:
    """主游戏引擎。坐标无关，只管规则与状态。"""

    def __init__(self) -> None:
        self.tableau: List[List[Card]] = [[] for _ in range(7)]
        self.foundation: List[List[Card]] = [[] for _ in range(4)]
        self.stock: List[Card] = []
        self.waste: List[Card] = []
        self.moves: int = 0
        self.game_over: bool = False

    # ---------- 初始化 ----------

    def new_game(self) -> None:
        """标准 Klondike 发牌：第 i 列 i+1 张，仅末张面朝上；余下 24 张进 stock。"""
        deck = Deck.create_deck()
        self.tableau = [[] for _ in range(7)]
        for col in range(7):
            for _ in range(col + 1):
                self.tableau[col].append(deck.pop())
            self.tableau[col][-1].face_up = True  # 末张翻开
        self.stock = deck  # 剩余 24 张
        self.waste = []
        self.foundation = [[] for _ in range(4)]
        self.moves = 0
        self.game_over = False

    # ---------- stock / waste ----------

    def draw_from_stock(self) -> None:
        """从 stock 抽 1 张到 waste 并翻开；stock 空则把 waste 倒回 stock。"""
        if not self.stock:
            if not self.waste:
                return
            # waste 全部扣下并倒序回到 stock
            for c in self.waste:
                c.face_up = False
            self.stock = list(reversed(self.waste))
            self.waste = []
            return
        card = self.stock.pop()
        card.face_up = True
        self.waste.append(card)
        self.moves += 1

    # ---------- 规则校验 ----------

    def can_place_tableau(self, card: Card, target_stack: List[Card]) -> bool:
        """tableau 放置规则：空列只收 K；非空列需颜色相反且点数递减一级。"""
        if not target_stack:
            return card.rank == "K"
        top = target_stack[-1]
        if not top.face_up:
            return False
        return top.color != card.color and top.value == card.value + 1

    def can_place_foundation(self, card: Card, target_f: List[Card]) -> bool:
        """foundation 规则：空堆只收 A；非空需同花色且点数递增一级。"""
        if not target_f:
            return card.rank == "A"
        top = target_f[-1]
        return top.suit == card.suit and top.value == card.value - 1

    def is_valid_sequence(self, cards: List[Card]) -> bool:
        """判断一组连续牌是否构成合法 tableau 序列（颜色交替、点数递减、全部面朝上）。"""
        if not cards:
            return False
        if not all(c.face_up for c in cards):
            return False
        for i in range(len(cards) - 1):
            upper, lower = cards[i], cards[i + 1]
            if upper.color == lower.color:
                return False
            if upper.value != lower.value + 1:
                return False
        return True

    # ---------- 移动 ----------

    def move_tableau_sequence(self, from_col: int, from_idx: int, to_col: int) -> bool:
        """把 tableau[from_col][from_idx:] 整组移到 tableau[to_col]。"""
        if not (0 <= from_col < 7 and 0 <= to_col < 7):
            return False
        src = self.tableau[from_col]
        if from_idx < 0 or from_idx >= len(src):
            return False
        seq = src[from_idx:]
        if not self.is_valid_sequence(seq):
            return False
        if not self.can_place_tableau(seq[0], self.tableau[to_col]):
            return False
        del src[from_idx:]
        self.tableau[to_col].extend(seq)
        self.moves += 1
        self._flip_top(from_col)
        self.check_win()
        return True

    def move_from_waste_to_tableau(self, to_col: int) -> bool:
        if not self.waste:
            return False
        card = self.waste[-1]
        if not self.can_place_tableau(card, self.tableau[to_col]):
            return False
        self.tableau[to_col].append(self.waste.pop())
        self.moves += 1
        self.check_win()
        return True

    def move_tableau_to_foundation(self, from_col: int, to_f: int) -> bool:
        if not (0 <= from_col < 7):
            return False
        src = self.tableau[from_col]
        if not src:
            return False
        card = src[-1]
        if not (0 <= to_f < 4):
            return False
        if not self.can_place_foundation(card, self.foundation[to_f]):
            return False
        self.foundation[to_f].append(src.pop())
        self.moves += 1
        self._flip_top(from_col)
        self.check_win()
        return True

    def move_waste_to_foundation(self, to_f: int) -> bool:
        if not self.waste:
            return False
        card = self.waste[-1]
        if not (0 <= to_f < 4):
            return False
        if not self.can_place_foundation(card, self.foundation[to_f]):
            return False
        self.foundation[to_f].append(self.waste.pop())
        self.moves += 1
        self.check_win()
        return True

    def auto_to_foundation(self, zone: str, col: int) -> bool:
        """双击自动归位：把指定区域顶牌尝试送进任意 foundation。"""
        card: Optional[Card] = None
        if zone == "waste" and self.waste:
            card = self.waste[-1]
        elif zone == "tableau" and 0 <= col < 7 and self.tableau[col]:
            card = self.tableau[col][-1]
        if card is None or not card.face_up:
            return False
        for f in range(4):
            if self.can_place_foundation(card, self.foundation[f]):
                if zone == "waste":
                    return self.move_waste_to_foundation(f)
                return self.move_tableau_to_foundation(col, f)
        return False

    def _flip_top(self, col: int) -> None:
        src = self.tableau[col]
        if src and not src[-1].face_up:
            src[-1].face_up = True

    # ---------- 胜负 ----------

    def check_win(self) -> bool:
        won = all(len(f) == 13 for f in self.foundation)
        self.game_over = won
        return won

    def reset(self) -> None:
        self.new_game()
