"""Klondike Solitaire - v3.0 完整版（全屏 / 美化 / 游戏规则文档）

运行：
  python main.py

操作：
  左键单击 stock：抽牌到 waste
  左键拖拽：移动牌（颜色相反、点数递减；空列收 K）
  右键单击：自动归位 foundation
  TAB / F：切换全屏
  F1：打开游戏规则
  R / N：重开    H：简短帮助    ESC：退出
"""

import sys

import pygame

from game_engine import GameEngine
from ui_manager import UIManager, SCREEN_W, SCREEN_H
from move_handler import DragHandler, ClickHandler
from tutorial import TutorialSystem

FPS = 60


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Klondike Solitaire v3.0 — 全屏版")
    clock = pygame.time.Clock()

    engine = GameEngine()
    engine.new_game()

    ui = UIManager(screen, engine)
    drag = DragHandler(engine, ui)
    click = ClickHandler(engine, ui, drag)
    tutorial = TutorialSystem(ui, engine)

    running = True
    show_help_short = False
    show_rules = False
    fullscreen = False
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if drag.dragging:
                        drag.cancel()
                    else:
                        running = False
                elif event.key == pygame.K_TAB:
                    fullscreen = not fullscreen
                    try:
                        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN if fullscreen else 0)
                        ui.screen = screen
                        ui._bg = ui._make_background()
                    except pygame.error:
                        pass  # 切换失败保持原状
                elif event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    try:
                        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.FULLSCREEN if fullscreen else 0)
                        ui.screen = screen
                        ui._bg = ui._make_background()
                    except pygame.error:
                        pass
                elif event.key in (pygame.K_r, pygame.K_n):
                    engine.new_game()
                    ui.clear_drag()
                elif event.key == pygame.K_h:
                    show_help_short = not show_help_short
                elif event.key == pygame.K_F1:
                    show_rules = not show_rules
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click.handle_click(event.pos)
                elif event.button == 3:
                    click.handle_right(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                if drag.dragging:
                    ui.set_drag(drag.drag_cards, event.pos)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                drag.end(event.pos)

        ui.draw_all()
        if show_help_short:
            ui.show_help()
        if show_rules:
            ui.show_rules()
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
