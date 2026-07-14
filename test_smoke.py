"""smoke test：验证引擎逻辑正确性 + 无显示渲染不崩。"""

import os

# 必须在 import pygame 之前设置 dummy 驱动
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
from game_engine import GameEngine, Card
from ui_manager import UIManager
from move_handler import DragHandler, ClickHandler


def test_engine_logic():
    e = GameEngine()
    e.new_game()
    # 标准发牌：stock 24，tableau 28，分布 1..7
    assert len(e.stock) == 24, f"stock={len(e.stock)}"
    assert [len(s) for s in e.tableau] == [1, 2, 3, 4, 5, 6, 7]
    assert all(s[-1].face_up for s in e.tableau)
    assert all(not c.face_up for s in e.tableau for c in s[:-1])
    assert all(len(f) == 0 for f in e.foundation)
    # 抽牌
    e.draw_from_stock()
    assert len(e.waste) == 1 and e.waste[-1].face_up
    # stock 空时把 waste 倒回 stock（标准 reset）
    e.stock = []
    e.draw_from_stock()  # waste(1张) 倒回 stock
    assert len(e.waste) == 0 and len(e.stock) == 1
    # 都空时安全无操作
    e.stock = []
    e.waste = []
    e.draw_from_stock()
    assert len(e.stock) == 0 and len(e.waste) == 0
    # 规则：空 tableau 只收 K
    empty = []
    assert e.can_place_tableau(Card("K", "spades", True), empty) is True
    assert e.can_place_tableau(Card("Q", "spades", True), empty) is False
    # 规则：颜色相反 + 点数递减一级（J 可放 Q 上）
    red_q = [Card("Q", "hearts", True)]
    assert e.can_place_tableau(Card("J", "spades", True), red_q) is True   # J黑 放 Q红，递减一级
    assert e.can_place_tableau(Card("J", "hearts", True), red_q) is False  # 同色
    assert e.can_place_tableau(Card("10", "spades", True), red_q) is False  # 差2级
    assert e.can_place_tableau(Card("K", "spades", True), red_q) is False   # 比顶大
    # foundation：空只收 A，之后同花色递增
    f = []
    assert e.can_place_foundation(Card("A", "clubs", True), f) is True
    assert e.can_place_foundation(Card("2", "clubs", True), f) is False
    f.append(Card("A", "clubs", True))
    assert e.can_place_foundation(Card("2", "clubs", True), f) is True
    assert e.can_place_foundation(Card("2", "spades", True), f) is False  # 花色不同
    # 合法序列判定
    seq = [Card("9", "hearts", True), Card("8", "spades", True), Card("7", "diamonds", True)]
    assert e.is_valid_sequence(seq) is True
    bad = [Card("9", "hearts", True), Card("8", "hearts", True)]  # 同色
    assert e.is_valid_sequence(bad) is False
    print("[ok] engine logic")


def test_render_dummy():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    e = GameEngine()
    e.new_game()
    ui = UIManager(screen, e)
    for _ in range(5):
        ui.draw_all()
        pygame.display.flip()
    # 抽几张牌再渲染
    for _ in range(3):
        e.draw_from_stock()
    ui.draw_all()
    pygame.display.flip()
    print("[ok] render (dummy driver)")


def test_drag_flow():
    pygame.init()
    screen = pygame.display.set_mode((1024, 768))
    e = GameEngine()
    e.new_game()
    # 构造可移动局面：col0 顶牌红Q，col1 顶牌黑K（Q可放K上）
    e.tableau[0] = [Card("K", "spades", True), Card("Q", "hearts", True)]
    e.tableau[1] = [Card("K", "clubs", True)]
    ui = UIManager(screen, e)
    drag = DragHandler(e, ui)
    rect = ui.tableau_card_rect(0, 1)  # Q 的位置
    ok = drag.start((rect.centerx, rect.centery))
    assert ok and drag.dragging
    target = ui.tableau_card_rect(1, 0)  # col1 的 K 位置
    drag.end((target.centerx, target.centery))
    assert e.tableau[1][-1].rank == "Q"
    assert e.tableau[0][-1].rank == "K"
    assert len(e.tableau[0]) == 1 and len(e.tableau[1]) == 2
    print("[ok] drag flow")


if __name__ == "__main__":
    test_engine_logic()
    test_render_dummy()
    test_drag_flow()
    print("ALL SMOKE TESTS PASSED")
