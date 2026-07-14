"""UI 管理器 — Emerald Velour 重构版

视觉风格：深翠绿绒面赌桌 + 金色装饰边框 + 象牙白卡牌（衬线体）+ 酒红色 Art Deco 卡背
渲染优化：卡牌面/背预渲染至 Surface 缓存，避免每帧重复绘制
接口完全兼容 main.py 与 move_handler.py，无需修改调用方。

重构要点（相对上一版）：
- 背景从简单渐变升级为多层：垂直渐变 + 中心柔光 + 绒面噪点 + 径向暗角 + 金色装饰边框
- 卡牌正面：暖象牙渐变 + 圆角阴影 + 衬线字体（Georgia）+ 分层边框
- 卡牌背面：酒红渐变 + 金色菱形格纹（Art Deco）+ 中心金钻徽章
- 占位槽：凹陷效果 + 金色描边 + 花色水印
- 拖拽视觉：金色辉光 + 增强阴影
- HUD：金色文字 + 装饰分隔线 + 计时器
- 胜利画面：脉冲金光 + 火花粒子动画
- 帮助/规则面板：深色半透明 + 金色边框 + 优雅排版
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

import pygame

from game_engine import Card, SUIT_GLYPH, SUITS

# ════════════════════════════════════════════════════════
# 屏幕与布局常量（保持不变，确保兼容）
# ════════════════════════════════════════════════════════
SCREEN_W, SCREEN_H = 1920, 1080

CARD_W, CARD_H = 110, 160
COL_GAP = 20
COL_STRIDE = CARD_W + COL_GAP
N_COLS = 7
LEFT_MARGIN = max(16, (SCREEN_W - (N_COLS * CARD_W + (N_COLS - 1) * COL_GAP)) // 2)
TOP_Y = 28
TABLEAU_Y = 220
FAN_DOWN = 16
FAN_UP = 36
CARD_RADIUS = 12

# ════════════════════════════════════════════════════════
# 色彩系统 — Emerald Velour
# ════════════════════════════════════════════════════════
# 背景
BG_TOP = (14, 62, 40)        # 深翠绿（顶部）
BG_BOTTOM = (3, 16, 10)      # 近黑绿（底部）
BG_CENTER_GLOW = (40, 120, 80)  # 中心柔光

# 金色系
GOLD = (212, 175, 55)
GOLD_BRIGHT = (245, 215, 110)
GOLD_DIM = (130, 100, 30)
GOLD_FAINT = (80, 62, 20)

# 卡牌正面
CARD_FACE_TOP = (255, 252, 240)     # 暖象牙（顶部高光）
CARD_FACE_BOTTOM = (228, 220, 198)  # 暖象牙（底部阴影）
CARD_BORDER = (190, 178, 150)       # 暖边框
CARD_INNER_HIGHLIGHT = (255, 255, 255)  # 顶部高光线

# 卡牌背面
CARD_BACK_BG = (58, 20, 26)         # 深酒红
CARD_BACK_DARK = (38, 12, 18)       # 更深酒红
CARD_BACK_PATTERN = (90, 50, 55)    # 菱形格纹色（微亮于底色）

# 花色
RED = (176, 34, 43)       # 深绛红
BLACK = (26, 26, 38)      # 浓墨黑

# 文本
TEXT = (235, 230, 215)    # 暖白
TEXT_GOLD = (212, 175, 55)
TEXT_MUTED = (150, 145, 125)

# 效果
SHADOW_ALPHA = 70
HIGHLIGHT = (245, 215, 110)
PLACEHOLDER_FILL = (5, 28, 16)
PLACEHOLDER_BORDER = (50, 90, 65)
PLACEHOLDER_GLYPH = (35, 70, 50)


class UIManager:
    """渲染层管理器 — Emerald Velour 风格。

    所有布局/碰撞/拖拽接口与上一版完全一致。
    视觉层全面重构：缓存卡牌表面、多层背景、动画胜利画面。
    """

    # ──────────────────────────────────────────────
    #  初始化
    # ──────────────────────────────────────────────
    def __init__(self, screen: pygame.Surface, engine) -> None:
        self.screen = screen
        self.engine = engine
        pygame.font.init()

        # 字体：Georgia 衬线体用于卡牌与标题，Calibri 用于界面文本
        serif = "georgia,palatino,bookantiqua,serif"
        sans = "calibri,cambria,segoeui,microsoftyahei,arial,sans"

        self.font_card_rank = pygame.font.SysFont(serif, 24, bold=True)
        self.font_card_suit_s = pygame.font.SysFont(serif, 20)
        self.font_card_suit_l = pygame.font.SysFont(serif, 56)
        self.font_hud = pygame.font.SysFont(sans, 20)
        self.font_hud_small = pygame.font.SysFont(sans, 15)
        self.font_title = pygame.font.SysFont(serif, 72, bold=True)
        self.font_panel_title = pygame.font.SysFont(serif, 32, bold=True)
        self.font_panel_header = pygame.font.SysFont(serif, 24, bold=True)
        self.font_panel_body = pygame.font.SysFont(sans, 21)
        self.font_placeholder = pygame.font.SysFont(serif, 64)

        # 拖拽视觉状态
        self._drag_cards: List[Card] = []
        self._drag_pos: Tuple[int, int] = (0, 0)

        # 卡牌表面缓存
        self._face_cache: Dict[str, pygame.Surface] = {}
        self._back_cache: Optional[pygame.Surface] = None
        self._shadow_cache: Optional[pygame.Surface] = None

        # 计时器
        self._prev_moves = 0
        self._start_ticks = pygame.time.get_ticks()

        # 背景缓存
        self._bg = self._make_background()

    # ──────────────────────────────────────────────
    #  背景生成（多层合成）
    # ──────────────────────────────────────────────
    def _make_background(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_W, SCREEN_H))

        # 1. 垂直渐变
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
            g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
            b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))

        # 2. 中心柔光（径向）
        light_r = 480
        light = pygame.Surface((light_r * 2, light_r * 2), pygame.SRCALPHA)
        for r in range(light_r, 0, -3):
            t = r / light_r
            alpha = int((1 - t) ** 2 * 30)
            pygame.draw.circle(light, (*BG_CENTER_GLOW, alpha), (light_r, light_r), r)
        surf.blit(light, (SCREEN_W // 2 - light_r, SCREEN_H // 2 - light_r))

        # 3. 绒面噪点纹理（平铺小贴图）
        random.seed(42)
        tile_s = 128
        noise_tile = pygame.Surface((tile_s, tile_s), pygame.SRCALPHA)
        for _ in range(500):
            nx = random.randint(0, tile_s - 1)
            ny = random.randint(0, tile_s - 1)
            noise_tile.set_at((nx, ny), (255, 255, 255, random.randint(8, 28)))
        for _ in range(350):
            nx = random.randint(0, tile_s - 1)
            ny = random.randint(0, tile_s - 1)
            noise_tile.set_at((nx, ny), (0, 0, 0, random.randint(6, 22)))
        for x in range(0, SCREEN_W, tile_s):
            for y in range(0, SCREEN_H, tile_s):
                surf.blit(noise_tile, (x, y))
        random.seed()

        # 4. 径向暗角
        self._apply_vignette(surf)

        # 5. 金色装饰边框
        self._draw_gold_frame(surf)

        return surf

    def _apply_vignette(self, surf: pygame.Surface) -> None:
        """在小尺寸 Surface 上逐像素计算暗角 alpha，再平滑放大贴回。"""
        vs = 200
        vig = pygame.Surface((vs, vs), pygame.SRCALPHA)
        vcx, vcy = vs // 2, vs // 2
        vmax = math.hypot(vcx, vcy)
        for vy in range(vs):
            for vx in range(vs):
                dist = math.hypot(vx - vcx, vy - vcy)
                t = min(1, dist / vmax)
                alpha = int(t ** 2.2 * 110)
                vig.set_at((vx, vy), (0, 0, 0, alpha))
        vig = pygame.transform.smoothscale(vig, (SCREEN_W, SCREEN_H))
        surf.blit(vig, (0, 0))

    def _draw_gold_frame(self, surf: pygame.Surface) -> None:
        """绘制双层金色装饰边框。"""
        m = 6
        # 外框
        pygame.draw.rect(surf, GOLD_DIM,
                         (m, m, SCREEN_W - 2 * m, SCREEN_H - 2 * m), 2, border_radius=4)
        # 内框（更细更暗）
        m2 = m + 5
        pygame.draw.rect(surf, (50, 90, 65),
                         (m2, m2, SCREEN_W - 2 * m2, SCREEN_H - 2 * m2), 1, border_radius=2)
        # 四角装饰小钻
        for cx, cy in [(m + 2, m + 2), (SCREEN_W - m - 2, m + 2),
                       (m + 2, SCREEN_H - m - 2), (SCREEN_W - m - 2, SCREEN_H - m - 2)]:
            pygame.draw.polygon(surf, GOLD, [
                (cx, cy - 5), (cx + 4, cy), (cx, cy + 5), (cx - 4, cy)
            ])

    # ──────────────────────────────────────────────
    #  布局方法（接口不变）
    # ──────────────────────────────────────────────
    def stock_rect(self) -> pygame.Rect:
        return pygame.Rect(LEFT_MARGIN, TOP_Y, CARD_W, CARD_H)

    def waste_rect(self) -> pygame.Rect:
        return pygame.Rect(LEFT_MARGIN + COL_STRIDE, TOP_Y, CARD_W, CARD_H)

    def foundation_rect(self, f: int) -> pygame.Rect:
        return pygame.Rect(LEFT_MARGIN + (4 + f) * COL_STRIDE, TOP_Y, CARD_W, CARD_H)

    def tableau_base_rect(self, col: int) -> pygame.Rect:
        return pygame.Rect(LEFT_MARGIN + col * COL_STRIDE, TABLEAU_Y, CARD_W, CARD_H)

    def tableau_card_rect(self, col: int, idx: int) -> pygame.Rect:
        stack = self.engine.tableau[col]
        y = TABLEAU_Y
        for i in range(idx):
            y += FAN_DOWN if not stack[i].face_up else FAN_UP
        return pygame.Rect(LEFT_MARGIN + col * COL_STRIDE, y, CARD_W, CARD_H)

    def hit_test(self, pos: Tuple[int, int]) -> Optional[Tuple[str, int, int]]:
        """返回 (zone, col, idx)。col 对 foundation 是 0-3，tableau 0-6，waste/stock 0。"""
        x, y = pos
        if self.stock_rect().collidepoint(x, y):
            return ("stock", 0, 0)
        if self.waste_rect().collidepoint(x, y):
            return ("waste", 0, 0)
        for f in range(4):
            if self.foundation_rect(f).collidepoint(x, y):
                return ("foundation", f, 0)
        for col in range(7):
            cx = LEFT_MARGIN + col * COL_STRIDE
            if not (cx <= x <= cx + CARD_W):
                continue
            if y < TABLEAU_Y:
                continue
            stack = self.engine.tableau[col]
            if not stack:
                if y <= TABLEAU_Y + CARD_H:
                    return ("tableau", col, -1)
                continue
            for idx in range(len(stack) - 1, -1, -1):
                if self.tableau_card_rect(col, idx).collidepoint(x, y):
                    return ("tableau", col, idx)
            return ("tableau", col, len(stack) - 1)
        return None

    # ──────────────────────────────────────────────
    #  拖拽视觉（接口不变）
    # ──────────────────────────────────────────────
    def set_drag(self, cards: List[Card], pos: Tuple[int, int]) -> None:
        self._drag_cards = cards
        self._drag_pos = pos

    def clear_drag(self) -> None:
        self._drag_cards = []
        self._drag_pos = (0, 0)

    # ──────────────────────────────────────────────
    #  卡牌表面缓存
    # ──────────────────────────────────────────────
    def _get_card_face(self, card: Card) -> pygame.Surface:
        key = f"{card.rank}{card.suit}"
        if key not in self._face_cache:
            self._face_cache[key] = self._render_card_face(card)
        return self._face_cache[key]

    def _get_card_back(self) -> pygame.Surface:
        if self._back_cache is None:
            self._back_cache = self._render_card_back()
        return self._back_cache

    def _get_shadow(self) -> pygame.Surface:
        if self._shadow_cache is None:
            pad = 8
            sw, sh = CARD_W + pad * 2, CARD_H + pad * 2
            surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for i in range(pad, 0, -1):
                alpha = int(SHADOW_ALPHA * (pad - i + 1) / (pad * 2.5))
                rect = pygame.Rect(pad - i, pad - i + 3, CARD_W + i * 2, CARD_H + i * 2)
                pygame.draw.rect(surf, (0, 0, 0, alpha), rect, border_radius=CARD_RADIUS + i)
            self._shadow_cache = surf
        return self._shadow_cache

    def _render_card_face(self, card: Card) -> pygame.Surface:
        """渲染卡牌正面到独立 Surface（带圆角遮罩）。"""
        # 渐变底色
        gradient = pygame.Surface((CARD_W, CARD_H))
        for y in range(CARD_H):
            t = y / CARD_H
            r = int(CARD_FACE_TOP[0] * (1 - t) + CARD_FACE_BOTTOM[0] * t)
            g = int(CARD_FACE_TOP[1] * (1 - t) + CARD_FACE_BOTTOM[1] * t)
            b = int(CARD_FACE_TOP[2] * (1 - t) + CARD_FACE_BOTTOM[2] * t)
            pygame.draw.line(gradient, (r, g, b), (0, y), (CARD_W, y))

        # 圆角遮罩
        mask = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=CARD_RADIUS)

        surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        surf.blit(gradient, (0, 0))
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # 外边框
        pygame.draw.rect(surf, CARD_BORDER, surf.get_rect(), 2, border_radius=CARD_RADIUS)
        # 顶部高光线
        pygame.draw.line(surf, (255, 255, 255), (6, 2), (CARD_W - 6, 2), 1)

        col = RED if card.color == "red" else BLACK

        # 左上角：点数 + 小花色
        rank_t = self.font_card_rank.render(card.rank, True, col)
        suit_t = self.font_card_suit_s.render(card.glyph, True, col)
        surf.blit(rank_t, (8, 5))
        surf.blit(suit_t, (8, 5 + rank_t.get_height() - 4))

        # 中心大花色
        big = self.font_card_suit_l.render(card.glyph, True, col)
        surf.blit(big, ((CARD_W - big.get_width()) // 2,
                        (CARD_H - big.get_height()) // 2 + 4))

        # 右下角：倒置点数 + 小花色
        rank_r = pygame.transform.rotate(rank_t, 180)
        suit_r = pygame.transform.rotate(suit_t, 180)
        surf.blit(rank_r, (CARD_W - rank_r.get_width() - 8,
                           CARD_H - rank_r.get_height() - 5))
        surf.blit(suit_r, (CARD_W - suit_r.get_width() - 8,
                           CARD_H - rank_r.get_height() - suit_r.get_height() - 1))

        return surf

    def _render_card_back(self) -> pygame.Surface:
        """渲染卡牌背面：酒红渐变 + 金色 Art Deco 菱形格纹 + 中心金钻。"""
        # 渐变底色
        gradient = pygame.Surface((CARD_W, CARD_H))
        for y in range(CARD_H):
            t = y / CARD_H
            r = int(CARD_BACK_BG[0] * (1 - t * 0.4) + CARD_BACK_DARK[0] * t * 0.4)
            g = int(CARD_BACK_BG[1] * (1 - t * 0.4) + CARD_BACK_DARK[1] * t * 0.4)
            b = int(CARD_BACK_BG[2] * (1 - t * 0.4) + CARD_BACK_DARK[2] * t * 0.4)
            pygame.draw.line(gradient, (r, g, b), (0, y), (CARD_W, y))

        mask = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=CARD_RADIUS)

        surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        surf.blit(gradient, (0, 0))
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # 菱形格纹（Art Deco）
        spacing = 16
        for row in range(-1, CARD_H // spacing + 2):
            for col_idx in range(-1, CARD_W // spacing + 2):
                ox = spacing // 2 if row % 2 else 0
                px = col_idx * spacing + ox
                py = row * spacing
                s = 4
                pygame.draw.polygon(surf, CARD_BACK_PATTERN, [
                    (px, py - s), (px + s, py), (px, py + s), (px - s, py)
                ], 1)

        # 重新应用圆角遮罩（裁掉超出圆角的格纹）
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # 金色边框（双层）
        pygame.draw.rect(surf, GOLD_DIM, surf.get_rect(), 2, border_radius=CARD_RADIUS)
        inner = pygame.Rect(5, 5, CARD_W - 10, CARD_H - 10)
        pygame.draw.rect(surf, GOLD_FAINT, inner, 1, border_radius=8)

        # 中心金钻徽章
        cx, cy = CARD_W // 2, CARD_H // 2
        ds = 18
        pygame.draw.polygon(surf, GOLD, [
            (cx, cy - ds), (cx + ds // 2, cy), (cx, cy + ds), (cx - ds // 2, cy)
        ])
        pygame.draw.polygon(surf, GOLD_BRIGHT, [
            (cx, cy - ds + 3), (cx + ds // 2 - 3, cy),
            (cx, cy + ds - 3), (cx - ds // 2 + 3, cy)
        ], 1)
        # 徽章中心小钻
        ds2 = 6
        pygame.draw.polygon(surf, CARD_BACK_DARK, [
            (cx, cy - ds2), (cx + ds2, cy), (cx, cy + ds2), (cx - ds2, cy)
        ])

        return surf

    # ──────────────────────────────────────────────
    #  辅助绘制
    # ──────────────────────────────────────────────
    def _blit_shadow(self, x: int, y: int) -> None:
        sh = self._get_shadow()
        self.screen.blit(sh, (x - 8, y - 8))

    def _blit_card_face(self, card: Card, x: int, y: int) -> None:
        self._blit_shadow(x, y)
        self.screen.blit(self._get_card_face(card), (x, y))

    def _blit_card_back(self, x: int, y: int) -> None:
        self._blit_shadow(x, y)
        self.screen.blit(self._get_card_back(), (x, y))

    def _draw_placeholder(self, rect: pygame.Rect, glyph: str) -> None:
        """凹陷占位槽：深色填充 + 金色细边 + 花色水印。"""
        # 填充
        pygame.draw.rect(self.screen, PLACEHOLDER_FILL, rect, border_radius=CARD_RADIUS)
        # 顶部内阴影（凹陷感）
        top_shadow = pygame.Surface((rect.w, 6), pygame.SRCALPHA)
        for i in range(6):
            alpha = int(40 * (1 - i / 6))
            pygame.draw.line(top_shadow, (0, 0, 0, alpha), (0, i), (rect.w, i))
        self.screen.blit(top_shadow, rect.topleft)
        # 边框
        pygame.draw.rect(self.screen, PLACEHOLDER_BORDER, rect, 1, border_radius=CARD_RADIUS)
        # 顶部高光
        pygame.draw.line(self.screen, (60, 110, 80),
                         (rect.x + 5, rect.y + 1), (rect.right - 5, rect.y + 1), 1)
        # 花色水印
        if glyph:
            t = self.font_placeholder.render(glyph, True, PLACEHOLDER_GLYPH)
            self.screen.blit(t, (rect.x + (rect.w - t.get_width()) // 2,
                                 rect.y + (rect.h - t.get_height()) // 2))

    # ──────────────────────────────────────────────
    #  主绘制
    # ──────────────────────────────────────────────
    def draw_all(self) -> None:
        self.screen.blit(self._bg, (0, 0))

        # 计时器：检测新局
        if self.engine.moves == 0 and self._prev_moves > 0:
            self._start_ticks = pygame.time.get_ticks()
        self._prev_moves = self.engine.moves

        # foundation
        for f in range(4):
            r = self.foundation_rect(f)
            self._draw_placeholder(r, SUIT_GLYPH[SUITS[f]])
            st = self.engine.foundation[f]
            if st:
                self._blit_card_face(st[-1], r.x, r.y)

        # stock
        sr = self.stock_rect()
        if self.engine.stock:
            self._blit_card_back(sr.x, sr.y)
        else:
            self._draw_placeholder(sr, "\u21bb")

        # waste
        wr = self.waste_rect()
        if self.engine.waste:
            self._blit_card_face(self.engine.waste[-1], wr.x, wr.y)
        else:
            self._draw_placeholder(wr, "")

        # 装饰分隔线（顶行与 tableau 之间）
        self._draw_separator()

        # tableau
        for col in range(7):
            stack = self.engine.tableau[col]
            if not stack:
                self._draw_placeholder(self.tableau_base_rect(col), "")
                continue
            for idx, card in enumerate(stack):
                r = self.tableau_card_rect(col, idx)
                if card.face_up:
                    self._blit_card_face(card, r.x, r.y)
                else:
                    self._blit_card_back(r.x, r.y)

        # 拖拽中的牌
        self._draw_drag()

        # 悬停高亮
        self._draw_hover()

        # HUD
        self._draw_hud()

        # 胜利画面
        if self.engine.game_over:
            self._draw_victory()

    def _draw_separator(self) -> None:
        """顶行与 tableau 之间的金色装饰分隔线。"""
        sep_y = (TOP_Y + CARD_H + TABLEAU_Y) // 2
        left_end = SCREEN_W // 2 - 30
        right_start = SCREEN_W // 2 + 30
        pygame.draw.line(self.screen, GOLD_DIM, (LEFT_MARGIN, sep_y), (left_end, sep_y), 1)
        pygame.draw.line(self.screen, GOLD_DIM, (right_start, sep_y),
                         (SCREEN_W - LEFT_MARGIN, sep_y), 1)
        # 中心小钻
        cx = SCREEN_W // 2
        pygame.draw.polygon(self.screen, GOLD, [
            (cx, sep_y - 4), (cx + 5, sep_y), (cx, sep_y + 4), (cx - 5, sep_y)
        ])

    def _draw_drag(self) -> None:
        """拖拽中的牌：金色辉光 + 增强阴影。"""
        if not self._drag_cards:
            return
        ox, oy = self._drag_pos
        n = len(self._drag_cards)
        total_h = CARD_H + (n - 1) * FAN_UP

        # 金色辉光
        for i in range(6, 0, -1):
            alpha = max(0, 14 - i * 2)
            gr = pygame.Rect(ox - CARD_W // 2 - i, oy - CARD_H // 2 - i,
                             CARD_W + i * 2, total_h + i * 2)
            gs = pygame.Surface((gr.w, gr.h), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*GOLD_BRIGHT, alpha), gs.get_rect(),
                             border_radius=CARD_RADIUS + i)
            self.screen.blit(gs, gr.topleft)

        # 增强阴影
        sh = self._get_shadow()
        for i, card in enumerate(self._drag_cards):
            cy = oy - CARD_H // 2 + i * FAN_UP
            self.screen.blit(sh, (ox - CARD_W // 2 - 8, cy - 8))

        # 卡牌
        for i, card in enumerate(self._drag_cards):
            self.screen.blit(self._get_card_face(card),
                             (ox - CARD_W // 2, oy - CARD_H // 2 + i * FAN_UP))

    def _draw_hover(self) -> None:
        """鼠标悬停时在可交互卡牌上绘制金色描边。"""
        if self._drag_cards:
            return
        pos = pygame.mouse.get_pos()
        hit = self.hit_test(pos)
        if hit is None:
            return
        zone, col, idx = hit
        r: Optional[pygame.Rect] = None
        if zone == "tableau" and idx >= 0:
            stack = self.engine.tableau[col]
            if idx < len(stack) and stack[idx].face_up:
                r = self.tableau_card_rect(col, idx)
        elif zone == "waste" and self.engine.waste:
            r = self.waste_rect()
        elif zone == "stock" and self.engine.stock:
            r = self.stock_rect()
        if r:
            pygame.draw.rect(self.screen, GOLD_BRIGHT, r, 2, border_radius=CARD_RADIUS + 1)

    def _draw_hud(self) -> None:
        """底部 HUD：步数 + 计时 + 快捷键提示。"""
        bar_y = SCREEN_H - 44
        # 分隔线
        pygame.draw.line(self.screen, GOLD_DIM, (20, bar_y), (SCREEN_W - 20, bar_y), 1)
        # 装饰小钻
        for cx in (20, SCREEN_W - 20):
            pygame.draw.polygon(self.screen, GOLD, [
                (cx, bar_y - 3), (cx + 4, bar_y), (cx, bar_y + 3), (cx - 4, bar_y)
            ])

        # 步数
        moves_t = self.font_hud.render(f"\u6b65\u6570  {self.engine.moves}", True, TEXT_GOLD)
        self.screen.blit(moves_t, (24, SCREEN_H - 36))

        # 计时器
        elapsed = (pygame.time.get_ticks() - self._start_ticks) / 1000
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        time_t = self.font_hud.render(f"\u8ba1\u65f6  {mins:02d}:{secs:02d}", True, TEXT_GOLD)
        self.screen.blit(time_t, (24 + moves_t.get_width() + 30, SCREEN_H - 36))

        # foundation 进度
        total_f = sum(len(f) for f in self.engine.foundation)
        prog_t = self.font_hud.render(f"Foundation  {total_f}/52", True, TEXT_MUTED)
        self.screen.blit(prog_t, (24 + moves_t.get_width() + 30 + time_t.get_width() + 30,
                                  SCREEN_H - 36))

        # 快捷键
        hints = "ESC \u9000\u51fa  \u2502  R \u91cd\u5f00  \u2502  H \u5e2e\u52a9  \u2502  F1 \u89c4\u5219  \u2502  TAB \u5168\u5c4f"
        hint_t = self.font_hud.render(hints, True, TEXT_MUTED)
        self.screen.blit(hint_t, (SCREEN_W - hint_t.get_width() - 24, SCREEN_H - 36))

    # ──────────────────────────────────────────────
    #  胜利画面（动画）
    # ──────────────────────────────────────────────
    def _draw_victory(self) -> None:
        t = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(t * 2.5) + 1) / 2  # 0..1

        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        # 脉冲金色光晕
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        glow_r = int(260 + pulse * 40)
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for r in range(glow_r, 0, -4):
            tt = r / glow_r
            alpha = int((1 - tt) ** 2 * (40 + pulse * 30))
            pygame.draw.circle(glow, (*GOLD_BRIGHT, alpha), (glow_r, glow_r), r)
        self.screen.blit(glow, (cx - glow_r, cy - glow_r))

        # 火花粒子
        random.seed(int(t * 2))
        for _ in range(40):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(80, 300 + pulse * 50)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            ps = random.randint(2, 5)
            pa = random.randint(80, 200)
            pygame.draw.circle(self.screen, (*GOLD_BRIGHT, pa), (int(px), int(py)), ps)
        random.seed()

        # 标题
        title = self.font_title.render("VICTORY", True, GOLD_BRIGHT)
        self.screen.blit(title, (cx - title.get_width() // 2, cy - title.get_height() // 2 - 20))

        # 副标题
        sub = self.font_panel_body.render(
            f"\u8017\u65f6 {int(t)}s  \u2502  {self.engine.moves} \u6b65  \u2502  \u6309 R \u91cd\u65b0\u5f00\u59cb",
            True, TEXT)
        self.screen.blit(sub, (cx - sub.get_width() // 2, cy + 50))

    # ──────────────────────────────────────────────
    #  帮助面板
    # ──────────────────────────────────────────────
    def show_help(self) -> None:
        lines = [
            "\u2500\u2500 Klondike \u63a5\u9f99 \u2500\u2500",
            "",
            "\u3010\u76ee\u6807\u3011",
            "  \u5c06\u5168\u90e8 52 \u5f20\u724c\u6309 A\u2192K \u987a\u5e8f\u79fb\u81f3 4 \u4e2a\u57fa\u7840\u5806\u3002",
            "",
            "\u3010\u89c4\u5219\u3011",
            "  \u00b7 Tableau\uff08\u4e0b\u65b9 7 \u5217\uff09\uff1a\u7ea2\u9ed1\u4ea4\u66ff\u3001\u70b9\u6570\u9012\u51cf\u6392\u5217",
            "  \u00b7 \u7a7a\u5217\u53ea\u5141\u8bb8\u653e\u7f6e K",
            "  \u00b7 Foundation\uff08\u4e0a\u65b9 4 \u683c\uff09\uff1a\u540c\u82b1\u8272\uff0cA \u8d77\u59cb\u5230 K \u7ed3\u675f",
            "  \u00b7 Stock\uff08\u5de6\u4e0a\uff09\uff1a\u70b9\u51fb\u62bd 1 \u5f20\u5230 Waste",
            "  \u00b7 \u53ef\u6574\u6bb5\u79fb\u52a8\u8fde\u7eed\u7684\u5408\u6cd5\u5e8f\u5217",
            "",
            "\u3010\u64cd\u4f5c\u3011",
            "  \u00b7 \u5de6\u952e\u62d6\u62fd\uff1a\u79fb\u52a8\u9009\u4e2d\u724c\u5230\u76ee\u6807\u4f4d\u7f6e",
            "  \u00b7 \u5de6\u952e\u5355\u51fb Stock\uff1a\u62bd\u724c",
            "  \u00b7 \u53f3\u952e\u5355\u51fb\u724c\uff1a\u81ea\u52a8\u9001\u5165 Foundation",
            "  \u00b7 R\uff1a\u91cd\u65b0\u5f00\u59cb    H\uff1a\u5173\u95ed\u672c\u5e2e\u52a9    ESC\uff1a\u9000\u51fa\u6e38\u620f",
        ]
        self._draw_overlay_panel(lines, 660)

    # ──────────────────────────────────────────────
    #  规则面板
    # ──────────────────────────────────────────────
    def show_rules(self) -> None:
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        boxes = [
            ("\u3010\u6e38\u620f\u76ee\u6807\u3011", [
                "Klondike \u63a5\u9f99\u7684\u552f\u4e00\u76ee\u6807\u662f\uff1a\u5c06 52 \u5f20\u724c\u5168\u90e8\u79fb\u52a8\u5230",
                "\u53f3\u4e0a\u89d2\u7684 4 \u4e2a Foundation \u5806\u4e2d\u3002\u6bcf\u4e2a Foundation",
                "\u5fc5\u987b\u6309\u540c\u4e00\u82b1\u8272\u4ece A \u5230 K \u5347\u5e8f\u6392\u5217\u3002",
            ]),
            ("\u3010Tableau \u89c4\u5219\u3011\uff08\u4e0b\u65b9 7 \u5217\uff09", [
                "\u00b7 \u521d\u59cb\u53d1\u724c\uff1a\u7b2c i \u5217\u6709 i+1 \u5f20\u724c\uff0c\u4ec5\u672b\u5f20\u9762\u671d\u4e0a\u3002",
                "\u00b7 \u79fb\u52a8\uff1a\u989c\u8272\u5fc5\u987b\u76f8\u53cd\uff0c\u70b9\u6570\u9012\u51cf\u4e00\u7ea7\u3002",
                "\u00b7 \u7a7a\u5217\uff1a\u53ea\u80fd\u653e K\u3002K \u653e\u5165\u540e\u53ef\u7ee7\u7eed\u52a0\u724c\u3002",
                "\u00b7 \u7ffb\u724c\uff1a\u79fb\u8d70\u9876\u724c\u540e\uff0c\u4e0b\u4e00\u5f20\u81ea\u52a8\u7ffb\u5f00\u3002",
                "\u00b7 \u6574\u6bb5\u79fb\u52a8\uff1a\u5e95\u90e8\u8fde\u7eed\u591a\u5f20\u53ef\u4e00\u8d77\u62bd\u52a8\u3002",
            ]),
            ("\u3010Foundation \u89c4\u5219\u3011\uff08\u4e0a\u65b9 4 \u683c\uff09", [
                "\u00b7 \u6bcf\u683c\u4e00\u4e2a\u82b1\u8272\u3002\u8d77\u59cb\u5fc5\u987b\u653e A\u3002",
                "\u00b7 \u4e4b\u540e\u4f9d\u6b21\u653e 2, 3, ..., K\uff08\u540c\u82b1\u8272\u5347\u5e8f\uff09\u3002",
                "\u00b7 \u53ea\u6709\u6bcf\u5217\u6700\u4e0a\u65b9\u7684\u724c\u53ef\u4ee5\u9001\u5165 Foundation\u3002",
                "\u00b7 \u53f3\u952e\u5355\u51fb\u724c\u53ef\u81ea\u52a8\u9001\u5165\u5408\u9002\u7684 Foundation\u3002",
            ]),
            ("\u3010Stock / Waste \u89c4\u5219\u3011\uff08\u5de6\u4e0a / \u53f3\u4e0a\uff09", [
                "\u00b7 \u70b9\u51fb Stock \u724c\u5806\uff1a\u5c06\u6700\u4e0a\u65b9\u4e00\u5f20\u7ffb\u5f00\u653e\u5165 Waste\u3002",
                "\u00b7 Stock \u8017\u5c3d\u540e\uff0cWaste \u4f1a\u91cd\u65b0\u6d17\u56de Stock\u3002",
                "\u00b7 \u9ed8\u8ba4 Draw-1 \u6a21\u5f0f\uff1a\u6bcf\u6b21\u53ea\u62bd 1 \u5f20\u3002",
            ]),
        ]
        for i, (label, lines) in enumerate(boxes):
            x_off = 720 if i >= 2 else 0
            self._draw_rule_box(label, lines, x_offset=x_off)
        hint = self.font_hud_small.render(
            "\u6309 F1 \u5173\u95ed  \u2502  \u5b8c\u6574\u89c4\u5219\u89c1 README.md", True, TEXT_MUTED)
        self.screen.blit(hint, ((SCREEN_W - hint.get_width()) // 2, SCREEN_H - 50))

    # ──────────────────────────────────────────────
    #  面板渲染辅助
    # ──────────────────────────────────────────────
    def _draw_overlay_panel(self, lines: List[str], width: int) -> None:
        """居中半透明面板：金色边框 + 标题装饰线 + 正文。"""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        line_h = 30
        box_h = len(lines) * line_h + 60
        box = pygame.Rect((SCREEN_W - width) // 2, (SCREEN_H - box_h) // 2, width, box_h)

        # 面板背景
        panel = pygame.Surface((width, box_h), pygame.SRCALPHA)
        panel.fill((16, 16, 24, 210))
        self.screen.blit(panel, box.topleft)
        # 金色边框（双层）
        pygame.draw.rect(self.screen, GOLD, box, 2, border_radius=12)
        inner = box.inflate(-8, -8)
        pygame.draw.rect(self.screen, GOLD_FAINT, inner, 1, border_radius=8)
        # 四角小钻
        for cx, cy in [(box.x + 3, box.y + 3), (box.right - 3, box.y + 3),
                       (box.x + 3, box.bottom - 3), (box.right - 3, box.bottom - 3)]:
            pygame.draw.polygon(self.screen, GOLD_BRIGHT, [
                (cx, cy - 4), (cx + 3, cy), (cx, cy + 4), (cx - 3, cy)
            ])

        for i, ln in enumerate(lines):
            y = box.y + 30 + i * line_h
            if ln.startswith("\u2500"):
                # 标题行：装饰线 + 金色文字
                t = self.font_panel_title.render(ln, True, GOLD_BRIGHT)
                tx = box.x + (width - t.get_width()) // 2
                self.screen.blit(t, (tx, y - 2))
            elif ln.endswith("\u3011"):
                # 段落标题
                t = self.font_panel_header.render(ln, True, GOLD)
                self.screen.blit(t, (box.x + 30, y))
            elif ln == "":
                continue
            else:
                t = self.font_panel_body.render(ln, True, TEXT)
                self.screen.blit(t, (box.x + 30, y + 2))

    def _draw_rule_box(self, title: str, lines: List[str], x_offset: int = 0) -> None:
        """规则面板中的单个文本框。"""
        box_w = 680
        line_h = 28
        box_h = len(lines) * line_h + 64
        box_x = LEFT_MARGIN + x_offset
        box_y = (SCREEN_H - box_h) // 2 - 20
        box = pygame.Rect(box_x, box_y, box_w, box_h)

        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((14, 14, 22, 210))
        self.screen.blit(panel, box.topleft)
        pygame.draw.rect(self.screen, GOLD_DIM, box, 2, border_radius=10)
        inner = box.inflate(-6, -6)
        pygame.draw.rect(self.screen, GOLD_FAINT, inner, 1, border_radius=6)

        # 标题
        t = self.font_panel_header.render(title, True, GOLD)
        self.screen.blit(t, (box.x + 24, box.y + 18))
        # 标题下装饰线
        pygame.draw.line(self.screen, GOLD_DIM,
                         (box.x + 24, box.y + 50), (box.right - 24, box.y + 50), 1)

        for i, ln in enumerate(lines):
            text = self.font_panel_body.render(ln, True, TEXT)
            self.screen.blit(text, (box.x + 24, box.y + 60 + i * line_h))
