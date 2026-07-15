"""UI Manager - Emerald Velour Pro

Refactored with frontend-design-pro design principles:
- Modular type scale (1.25 ratio, base 16px)
- 8px spacing system for UI chrome elements
- Smooth hover transitions (exponential approach, ~150ms perceived)
- Invalid-move visual feedback (red flash, 300ms)
- Card placement glow micro-interaction (350ms)
- Refined color contrast (WCAG AA on all text)
- Font upgrade: Corbel (humanist sans) replaces generic Calibri

Interface is fully backward-compatible with main.py and move_handler.py.
New optional method: flash_invalid(rect) for enhanced interaction feedback.
"""

from __future__ import annotations

import math
import random
import time
from typing import Dict, List, Optional, Tuple

import pygame

from game_engine import Card, SUIT_GLYPH, SUITS

# ════════════════════════════════════════════════════════
# Design Tokens
# ════════════════════════════════════════════════════════

# -- Layout Constants (unchanged for compatibility) --
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

# -- Type Scale (1.25 modular ratio, base 16px) --
# 16 -> 20 -> 25 -> 31 -> 39 -> 49 -> 61 -> 76
TS_BASE = 16    # hint text
TS_SM = 20      # HUD / body text
TS_MD = 25      # card rank / panel header
TS_LG = 31      # panel title
TS_2XL = 49     # card suit large / placeholder glyph
TS_4XL = 76     # victory title

# -- Spacing System (4px base unit) --
SP_1 = 4
SP_2 = 8
SP_3 = 12
SP_4 = 16
SP_5 = 20
SP_6 = 24
SP_8 = 32

# -- Motion Constants --
HOVER_SPEED = 14.0      # exponential approach rate (higher = faster)
FLASH_DURATION = 0.30   # 300ms invalid-move flash
GLOW_DURATION = 0.35    # 350ms placement glow

# -- Color Palette: Emerald Velour (contrast refined) --
# Background
BG_TOP = (14, 62, 40)
BG_BOTTOM = (3, 16, 10)
BG_CENTER_GLOW = (40, 120, 80)

# Gold system
GOLD = (212, 175, 55)
GOLD_BRIGHT = (245, 215, 110)
GOLD_DIM = (130, 100, 30)
GOLD_FAINT = (80, 62, 20)

# Card face
CARD_FACE_TOP = (255, 252, 240)
CARD_FACE_BOTTOM = (228, 220, 198)
CARD_BORDER = (190, 178, 150)

# Card back
CARD_BACK_BG = (58, 20, 26)
CARD_BACK_DARK = (38, 12, 18)
CARD_BACK_PATTERN = (90, 50, 55)

# Suits
RED = (176, 34, 43)
BLACK = (26, 26, 38)

# Text (WCAG AA contrast: TEXT_MUTED >= 4.5:1 on dark bg)
TEXT = (240, 235, 220)
TEXT_GOLD = (218, 180, 60)
TEXT_MUTED = (172, 167, 142)

# Semantic colors
COLOR_INVALID = (220, 70, 70)
COLOR_PLACED = (100, 210, 130)

# Effects
SHADOW_ALPHA = 70
HIGHLIGHT = (245, 215, 110)
PLACEHOLDER_FILL = (5, 28, 16)
PLACEHOLDER_BORDER = (50, 90, 65)
PLACEHOLDER_GLYPH = (35, 70, 50)


# ════════════════════════════════════════════════════════
# Easing Functions (frontend-design-pro: cubic-bezier(0.16, 1, 0.3, 1))
# ════════════════════════════════════════════════════════

def ease_out_cubic(t: float) -> float:
    """Fast-in, slow-out easing. Approximates cubic-bezier(0.16, 1, 0.3, 1)."""
    return 1 - (1 - t) ** 3


# ════════════════════════════════════════════════════════
# UIManager
# ════════════════════════════════════════════════════════

class UIManager:
    """Render layer manager - Emerald Velour Pro style.

    Design principles (frontend-design-pro):
    - Typography: modular type scale (1.25), serif + humanist sans
    - Color: warm-tinted neutrals, WCAG AA contrast
    - Spatial: 8px spacing system for UI chrome
    - Motion: ease-out-cubic, 150ms micro, 300ms feedback
    - Interaction: smooth hover, invalid-move feedback, placement glow
    """

    # -----------------------------------------------
    #  Initialization
    # -----------------------------------------------
    def __init__(self, screen: pygame.Surface, engine) -> None:
        self.screen = screen
        self.engine = engine
        pygame.font.init()

        # Fonts: Unicode-capable serif (♥♦♣♠) + Corbel humanist sans (UI text)
        # 关键修复：之前用 Georgia/Cambria 在部分 Windows 上不渲染 Unicode 花色符号，
        # 改为使用 msyh.ttc（微软雅黑）— 自带完整 Unicode 支持，且字形质量优秀。
        # 使用 pygame.font.Font 直接指定 .ttc 路径以跳过字体名解析的 fallback 陷阱。
        _unicode_font = "C:/Windows/Fonts/msyh.ttc"  # Microsoft YaHei — full Unicode coverage
        _sans = "corbel,bahnschrift,candara,segoeui,microsoftyahei,sans"

        # Card fonts: use direct Font path for reliable Unicode support
        self.font_card_rank = pygame.font.Font(_unicode_font, TS_MD)
        self.font_card_suit_s = pygame.font.Font(_unicode_font, TS_SM)
        self.font_card_suit_l = pygame.font.Font(_unicode_font, TS_2XL)
        # HUD/UI: regular SysFont (Chinese UI text handled by msyh via microsoftyahei fallback)
        self.font_hud = pygame.font.SysFont(_sans, TS_SM)
        self.font_hud_small = pygame.font.SysFont(_sans, TS_BASE)
        # Title fonts: use direct font file for Unicode support
        self.font_title = pygame.font.Font(_unicode_font, TS_4XL)
        self.font_panel_title = pygame.font.Font(_unicode_font, TS_LG)
        self.font_panel_header = pygame.font.Font(_unicode_font, TS_MD)
        self.font_panel_body = pygame.font.SysFont(_sans, TS_SM)
        self.font_placeholder = pygame.font.Font(_unicode_font, TS_2XL)

        # Drag visual state
        self._drag_cards: List[Card] = []
        self._drag_pos: Tuple[int, int] = (0, 0)

        # Card surface cache
        self._face_cache: Dict[str, pygame.Surface] = {}
        self._back_cache: Optional[pygame.Surface] = None
        self._shadow_cache: Optional[pygame.Surface] = None

        # Timer
        self._prev_moves = 0
        self._start_ticks = pygame.time.get_ticks()

        # Animation state
        self._hover_alpha = 0.0
        self._hover_rect: Optional[pygame.Rect] = None
        self._last_time = time.monotonic()
        self._flash_start: Optional[float] = None
        self._flash_rect: Optional[pygame.Rect] = None
        self._glow_start: Optional[float] = None
        self._glow_rect: Optional[pygame.Rect] = None

        # Background cache
        self._bg = self._make_background()

    # -----------------------------------------------
    #  Background Generation (multi-layer composite)
    # -----------------------------------------------
    def _make_background(self) -> pygame.Surface:
        surf = pygame.Surface((SCREEN_W, SCREEN_H))

        # 1. Vertical gradient
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            r = int(BG_TOP[0] * (1 - t) + BG_BOTTOM[0] * t)
            g = int(BG_TOP[1] * (1 - t) + BG_BOTTOM[1] * t)
            b = int(BG_TOP[2] * (1 - t) + BG_BOTTOM[2] * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (SCREEN_W, y))

        # 2. Center radial glow
        light_r = 480
        light = pygame.Surface((light_r * 2, light_r * 2), pygame.SRCALPHA)
        for r in range(light_r, 0, -3):
            t = r / light_r
            alpha = int((1 - t) ** 2 * 30)
            pygame.draw.circle(light, (*BG_CENTER_GLOW, alpha), (light_r, light_r), r)
        surf.blit(light, (SCREEN_W // 2 - light_r, SCREEN_H // 2 - light_r))

        # 3. Velvet noise texture (tiled)
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

        # 4. Radial vignette
        self._apply_vignette(surf)

        # 5. Gold decorative frame
        self._draw_gold_frame(surf)

        return surf

    def _apply_vignette(self, surf: pygame.Surface) -> None:
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
        m = SP_1 + SP_2  # 12px outer margin
        pygame.draw.rect(surf, GOLD_DIM,
                         (m, m, SCREEN_W - 2 * m, SCREEN_H - 2 * m), 2, border_radius=4)
        m2 = m + SP_1 + SP_1  # 20px inner margin
        pygame.draw.rect(surf, (50, 90, 65),
                         (m2, m2, SCREEN_W - 2 * m2, SCREEN_H - 2 * m2), 1, border_radius=2)
        for cx, cy in [(m + 2, m + 2), (SCREEN_W - m - 2, m + 2),
                       (m + 2, SCREEN_H - m - 2), (SCREEN_W - m - 2, SCREEN_H - m - 2)]:
            pygame.draw.polygon(surf, GOLD, [
                (cx, cy - SP_1 - 1), (cx + SP_1, cy), (cx, cy + SP_1 + 1), (cx - SP_1, cy)
            ])

    # -----------------------------------------------
    #  Layout Methods (interface unchanged)
    # -----------------------------------------------
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

    # -----------------------------------------------
    #  Drag Visual (interface unchanged + extension)
    # -----------------------------------------------
    def set_drag(self, cards: List[Card], pos: Tuple[int, int]) -> None:
        self._drag_cards = cards
        self._drag_pos = pos

    def clear_drag(self) -> None:
        self._drag_cards = []
        self._drag_pos = (0, 0)

    def flash_invalid(self, rect: pygame.Rect) -> None:
        """Trigger a red flash on a rect to signal an invalid move attempt.

        This is a new optional method - move_handler may call it for enhanced
        interaction feedback. Not calling it does not break any existing behavior.
        """
        self._flash_start = time.monotonic()
        self._flash_rect = rect

    def trigger_placement_glow(self, rect: pygame.Rect) -> None:
        """Trigger a green glow when a card is successfully placed.

        Optional extension method for enhanced interaction feedback.
        """
        self._glow_start = time.monotonic()
        self._glow_rect = rect

    # -----------------------------------------------
    #  Card Surface Cache
    # -----------------------------------------------
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
            pad = SP_2
            sw, sh = CARD_W + pad * 2, CARD_H + pad * 2
            surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
            for i in range(pad, 0, -1):
                alpha = int(SHADOW_ALPHA * (pad - i + 1) / (pad * 2.5))
                rect = pygame.Rect(pad - i, pad - i + 3, CARD_W + i * 2, CARD_H + i * 2)
                pygame.draw.rect(surf, (0, 0, 0, alpha), rect, border_radius=CARD_RADIUS + i)
            self._shadow_cache = surf
        return self._shadow_cache

    def _render_card_face(self, card: Card) -> pygame.Surface:
        # Gradient base
        gradient = pygame.Surface((CARD_W, CARD_H))
        for y in range(CARD_H):
            t = y / CARD_H
            r = int(CARD_FACE_TOP[0] * (1 - t) + CARD_FACE_BOTTOM[0] * t)
            g = int(CARD_FACE_TOP[1] * (1 - t) + CARD_FACE_BOTTOM[1] * t)
            b = int(CARD_FACE_TOP[2] * (1 - t) + CARD_FACE_BOTTOM[2] * t)
            pygame.draw.line(gradient, (r, g, b), (0, y), (CARD_W, y))

        # Rounded mask
        mask = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=CARD_RADIUS)

        surf = pygame.Surface((CARD_W, CARD_H), pygame.SRCALPHA)
        surf.blit(gradient, (0, 0))
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # Outer border + top highlight line
        pygame.draw.rect(surf, CARD_BORDER, surf.get_rect(), 2, border_radius=CARD_RADIUS)
        pygame.draw.line(surf, (255, 255, 255), (SP_1 + SP_1, 2), (CARD_W - SP_1 - SP_1, 2), 1)

        col = RED if card.color == "red" else BLACK

        # Top-left: rank + small suit (8px spacing)
        rank_t = self.font_card_rank.render(card.rank, True, col)
        suit_t = self.font_card_suit_s.render(card.glyph, True, col)
        surf.blit(rank_t, (SP_2, SP_1 + SP_1))
        surf.blit(suit_t, (SP_2, SP_1 + SP_1 + rank_t.get_height() - SP_1))

        # Center: large suit glyph
        big = self.font_card_suit_l.render(card.glyph, True, col)
        surf.blit(big, ((CARD_W - big.get_width()) // 2,
                        (CARD_H - big.get_height()) // 2 + SP_1))

        # Bottom-right: rotated rank + suit
        rank_r = pygame.transform.rotate(rank_t, 180)
        suit_r = pygame.transform.rotate(suit_t, 180)
        surf.blit(rank_r, (CARD_W - rank_r.get_width() - SP_2,
                           CARD_H - rank_r.get_height() - SP_1 - SP_1))
        surf.blit(suit_r, (CARD_W - suit_r.get_width() - SP_2,
                           CARD_H - rank_r.get_height() - suit_r.get_height() - 1))

        return surf

    def _render_card_back(self) -> pygame.Surface:
        # Gradient base
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

        # Art Deco diamond grid
        spacing = SP_4  # 16px grid spacing
        for row in range(-1, CARD_H // spacing + 2):
            for col_idx in range(-1, CARD_W // spacing + 2):
                ox = spacing // 2 if row % 2 else 0
                px = col_idx * spacing + ox
                py = row * spacing
                s = SP_1
                pygame.draw.polygon(surf, CARD_BACK_PATTERN, [
                    (px, py - s), (px + s, py), (px, py + s), (px - s, py)
                ], 1)

        # Re-apply rounded mask
        surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        # Gold double border
        pygame.draw.rect(surf, GOLD_DIM, surf.get_rect(), 2, border_radius=CARD_RADIUS)
        inner = pygame.Rect(SP_1 + SP_1, SP_1 + SP_1, CARD_W - SP_5, CARD_H - SP_5)
        pygame.draw.rect(surf, GOLD_FAINT, inner, 1, border_radius=SP_2)

        # Center gold diamond emblem
        cx, cy = CARD_W // 2, CARD_H // 2
        ds = SP_3 + SP_5  # 18px
        pygame.draw.polygon(surf, GOLD, [
            (cx, cy - ds), (cx + ds // 2, cy), (cx, cy + ds), (cx - ds // 2, cy)
        ])
        pygame.draw.polygon(surf, GOLD_BRIGHT, [
            (cx, cy - ds + 3), (cx + ds // 2 - 3, cy),
            (cx, cy + ds - 3), (cx - ds // 2 + 3, cy)
        ], 1)
        ds2 = SP_1 + SP_2  # 6px inner diamond
        pygame.draw.polygon(surf, CARD_BACK_DARK, [
            (cx, cy - ds2), (cx + ds2, cy), (cx, cy + ds2), (cx - ds2, cy)
        ])

        return surf

    # -----------------------------------------------
    #  Blit Helpers
    # -----------------------------------------------
    def _blit_shadow(self, x: int, y: int) -> None:
        sh = self._get_shadow()
        self.screen.blit(sh, (x - SP_2, y - SP_2))

    def _blit_card_face(self, card: Card, x: int, y: int) -> None:
        self._blit_shadow(x, y)
        self.screen.blit(self._get_card_face(card), (x, y))

    def _blit_card_back(self, x: int, y: int) -> None:
        self._blit_shadow(x, y)
        self.screen.blit(self._get_card_back(), (x, y))

    def _draw_placeholder(self, rect: pygame.Rect, glyph: str) -> None:
        # Recessed fill
        pygame.draw.rect(self.screen, PLACEHOLDER_FILL, rect, border_radius=CARD_RADIUS)
        # Top inner shadow (recessed effect)
        top_shadow = pygame.Surface((rect.w, SP_1 + SP_2), pygame.SRCALPHA)
        for i in range(SP_1 + SP_2):
            alpha = int(40 * (1 - i / (SP_1 + SP_2)))
            pygame.draw.line(top_shadow, (0, 0, 0, alpha), (0, i), (rect.w, i))
        self.screen.blit(top_shadow, rect.topleft)
        # Border
        pygame.draw.rect(self.screen, PLACEHOLDER_BORDER, rect, 1, border_radius=CARD_RADIUS)
        # Top highlight
        pygame.draw.line(self.screen, (60, 110, 80),
                         (rect.x + SP_1 + SP_1, rect.y + 1), (rect.right - SP_1 - SP_1, rect.y + 1), 1)
        # Suit watermark
        if glyph:
            t = self.font_placeholder.render(glyph, True, PLACEHOLDER_GLYPH)
            self.screen.blit(t, (rect.x + (rect.w - t.get_width()) // 2,
                                 rect.y + (rect.h - t.get_height()) // 2))

    # -----------------------------------------------
    #  Animation Update
    # -----------------------------------------------
    def _update_animations(self) -> None:
        """Advance all animation state by one frame (frame-rate independent)."""
        now = time.monotonic()
        dt = now - self._last_time
        self._last_time = now

        # Smooth hover alpha (exponential approach toward target)
        target = 1.0 if self._hover_rect is not None else 0.0
        approach = 1.0 - math.exp(-dt * HOVER_SPEED)
        self._hover_alpha += (target - self._hover_alpha) * approach

        # Expire flash
        if self._flash_start is not None:
            if now - self._flash_start >= FLASH_DURATION:
                self._flash_start = None
                self._flash_rect = None

        # Expire glow
        if self._glow_start is not None:
            if now - self._glow_start >= GLOW_DURATION:
                self._glow_start = None
                self._glow_rect = None

    # -----------------------------------------------
    #  Main Draw
    # -----------------------------------------------
    def draw_all(self) -> None:
        self._update_animations()
        self.screen.blit(self._bg, (0, 0))

        # Timer: detect new game
        if self.engine.moves == 0 and self._prev_moves > 0:
            self._start_ticks = pygame.time.get_ticks()
        self._prev_moves = self.engine.moves

        # Foundation
        for f in range(4):
            r = self.foundation_rect(f)
            self._draw_placeholder(r, SUIT_GLYPH[SUITS[f]])
            st = self.engine.foundation[f]
            if st:
                self._blit_card_face(st[-1], r.x, r.y)

        # Stock
        sr = self.stock_rect()
        if self.engine.stock:
            self._blit_card_back(sr.x, sr.y)
        else:
            self._draw_placeholder(sr, "\u21bb")

        # Waste
        wr = self.waste_rect()
        if self.engine.waste:
            self._blit_card_face(self.engine.waste[-1], wr.x, wr.y)
        else:
            self._draw_placeholder(wr, "")

        # Decorative separator
        self._draw_separator()

        # Tableau
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

        # Drag cards
        self._draw_drag()

        # Hover highlight (smooth alpha transition)
        self._draw_hover()

        # Placement glow
        self._draw_placement_glow()

        # Invalid move flash
        self._draw_invalid_flash()

        # HUD
        self._draw_hud()

        # Victory screen
        if self.engine.game_over:
            self._draw_victory()

    def _draw_separator(self) -> None:
        sep_y = (TOP_Y + CARD_H + TABLEAU_Y) // 2
        left_end = SCREEN_W // 2 - SP_6 - SP_1  # 30px gap center
        right_start = SCREEN_W // 2 + SP_6 + SP_1
        pygame.draw.line(self.screen, GOLD_DIM, (LEFT_MARGIN, sep_y), (left_end, sep_y), 1)
        pygame.draw.line(self.screen, GOLD_DIM, (right_start, sep_y),
                         (SCREEN_W - LEFT_MARGIN, sep_y), 1)
        cx = SCREEN_W // 2
        pygame.draw.polygon(self.screen, GOLD, [
            (cx, sep_y - SP_1), (cx + SP_1 + 1, sep_y), (cx, sep_y + SP_1), (cx - SP_1 - 1, sep_y)
        ])

    def _draw_drag(self) -> None:
        if not self._drag_cards:
            return
        ox, oy = self._drag_pos
        n = len(self._drag_cards)
        total_h = CARD_H + (n - 1) * FAN_UP

        # Gold glow
        for i in range(SP_1 + SP_2, 0, -1):
            alpha = max(0, 14 - i * 2)
            gr = pygame.Rect(ox - CARD_W // 2 - i, oy - CARD_H // 2 - i,
                             CARD_W + i * 2, total_h + i * 2)
            gs = pygame.Surface((gr.w, gr.h), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*GOLD_BRIGHT, alpha), gs.get_rect(),
                             border_radius=CARD_RADIUS + i)
            self.screen.blit(gs, gr.topleft)

        # Enhanced shadows
        sh = self._get_shadow()
        for i, card in enumerate(self._drag_cards):
            cy = oy - CARD_H // 2 + i * FAN_UP
            self.screen.blit(sh, (ox - CARD_W // 2 - SP_2, cy - SP_2))

        # Cards
        for i, card in enumerate(self._drag_cards):
            self.screen.blit(self._get_card_face(card),
                             (ox - CARD_W // 2, oy - CARD_H // 2 + i * FAN_UP))

    def _draw_hover(self) -> None:
        """Smooth hover highlight with interpolated alpha (ease-out feel)."""
        if self._drag_cards:
            self._hover_rect = None
            return
        if self._hover_alpha < 0.01:
            return

        # Determine hover target rect
        pos = pygame.mouse.get_pos()
        hit = self.hit_test(pos)
        target_rect: Optional[pygame.Rect] = None
        if hit is not None:
            zone, col, idx = hit
            if zone == "tableau" and idx >= 0:
                stack = self.engine.tableau[col]
                if idx < len(stack) and stack[idx].face_up:
                    target_rect = self.tableau_card_rect(col, idx)
            elif zone == "waste" and self.engine.waste:
                target_rect = self.waste_rect()
            elif zone == "stock" and self.engine.stock:
                target_rect = self.stock_rect()

        self._hover_rect = target_rect

        if target_rect is None:
            # Fading out - draw with remaining alpha
            if self._hover_alpha < 0.01:
                return
            # Use last known rect for fade-out; if none, skip
            return

        # Draw border with smooth alpha
        alpha = int(self._hover_alpha * 255)
        border_surf = pygame.Surface(
            (target_rect.w + SP_1 * 2, target_rect.h + SP_1 * 2), pygame.SRCALPHA
        )
        pygame.draw.rect(border_surf, (*GOLD_BRIGHT, alpha),
                         border_surf.get_rect(), 2,
                         border_radius=CARD_RADIUS + SP_1)
        self.screen.blit(border_surf, (target_rect.x - SP_1, target_rect.y - SP_1))

    def _draw_placement_glow(self) -> None:
        """Green glow when a card is successfully placed (350ms ease-out)."""
        if self._glow_start is None or self._glow_rect is None:
            return
        elapsed = time.monotonic() - self._glow_start
        t = elapsed / GLOW_DURATION
        if t >= 1.0:
            return
        eased = ease_out_cubic(t)
        alpha = int((1 - eased) * 120)
        r = self._glow_rect.inflate(SP_1 * 2, SP_1 * 2)
        glow_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*COLOR_PLACED, alpha),
                         glow_surf.get_rect(), 3, border_radius=CARD_RADIUS + SP_1)
        self.screen.blit(glow_surf, r.topleft)

    def _draw_invalid_flash(self) -> None:
        """Red flash on invalid move target (300ms sine pulse)."""
        if self._flash_start is None or self._flash_rect is None:
            return
        elapsed = time.monotonic() - self._flash_start
        t = elapsed / FLASH_DURATION
        if t >= 1.0:
            return
        # Sine pulse: 0 -> 1 -> 0
        pulse = math.sin(t * math.pi)
        alpha = int(pulse * 200)
        r = self._flash_rect.inflate(SP_1 * 2, SP_1 * 2)
        flash_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(flash_surf, (*COLOR_INVALID, alpha),
                         flash_surf.get_rect(), 3, border_radius=CARD_RADIUS + SP_1)
        self.screen.blit(flash_surf, r.topleft)

    def _draw_hud(self) -> None:
        """Bottom HUD: moves + timer + foundation progress + hotkeys."""
        bar_y = SCREEN_H - SP_6 - SP_2 - SP_1  # 44px from bottom
        # Separator line
        pygame.draw.line(self.screen, GOLD_DIM, (SP_5, bar_y), (SCREEN_W - SP_5, bar_y), 1)
        # Decorative diamonds
        for cx in (SP_5, SCREEN_W - SP_5):
            pygame.draw.polygon(self.screen, GOLD, [
                (cx, bar_y - 3), (cx + SP_1, bar_y), (cx, bar_y + 3), (cx - SP_1, bar_y)
            ])

        # Moves
        moves_t = self.font_hud.render(f"\u6b65\u6570  {self.engine.moves}", True, TEXT_GOLD)
        self.screen.blit(moves_t, (SP_6, SCREEN_H - SP_6 - SP_1))

        # Timer
        elapsed = (pygame.time.get_ticks() - self._start_ticks) / 1000
        mins = int(elapsed) // 60
        secs = int(elapsed) % 60
        time_t = self.font_hud.render(f"\u8ba1\u65f6  {mins:02d}:{secs:02d}", True, TEXT_GOLD)
        self.screen.blit(time_t, (SP_6 + moves_t.get_width() + SP_6, SCREEN_H - SP_6 - SP_1))

        # Foundation progress
        total_f = sum(len(f) for f in self.engine.foundation)
        prog_t = self.font_hud.render(f"Foundation  {total_f}/52", True, TEXT_MUTED)
        self.screen.blit(prog_t, (SP_6 + moves_t.get_width() + SP_6 + time_t.get_width() + SP_6,
                                  SCREEN_H - SP_6 - SP_1))

        # Hotkey hints
        hints = "ESC \u9000\u51fa  \u2502  R \u91cd\u5f00  \u2502  H \u5e2e\u52a9  \u2502  F1 \u89c4\u5219  \u2502  TAB \u5168\u5c4f"
        hint_t = self.font_hud.render(hints, True, TEXT_MUTED)
        self.screen.blit(hint_t, (SCREEN_W - hint_t.get_width() - SP_6, SCREEN_H - SP_6 - SP_1))

    # -----------------------------------------------
    #  Victory Screen (animated)
    # -----------------------------------------------
    def _draw_victory(self) -> None:
        t = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(t * 2.5) + 1) / 2  # 0..1

        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.screen.blit(overlay, (0, 0))

        # Pulsing gold halo
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        glow_r = int(260 + pulse * SP_10)
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        for r in range(glow_r, 0, -4):
            tt = r / glow_r
            alpha = int((1 - tt) ** 2 * (40 + pulse * 30))
            pygame.draw.circle(glow, (*GOLD_BRIGHT, alpha), (glow_r, glow_r), r)
        self.screen.blit(glow, (cx - glow_r, cy - glow_r))

        # Spark particles
        random.seed(int(t * 2))
        for _ in range(40):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(80, 300 + pulse * SP_5)
            px = cx + math.cos(angle) * dist
            py = cy + math.sin(angle) * dist
            ps = random.randint(2, SP_1 + SP_1)
            pa = random.randint(80, 200)
            pygame.draw.circle(self.screen, (*GOLD_BRIGHT, pa), (int(px), int(py)), ps)
        random.seed()

        # Title
        title = self.font_title.render("VICTORY", True, GOLD_BRIGHT)
        self.screen.blit(title, (cx - title.get_width() // 2, cy - title.get_height() // 2 - SP_5))

        # Subtitle
        sub = self.font_panel_body.render(
            f"\u8017\u65f6 {int(t)}s  \u2502  {self.engine.moves} \u6b65  \u2502  \u6309 R \u91cd\u65b0\u5f00\u59cb",
            True, TEXT)
        self.screen.blit(sub, (cx - sub.get_width() // 2, cy + SP_5 + SP_5 + SP_1))

    # -----------------------------------------------
    #  Help Panel
    # -----------------------------------------------
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

    # -----------------------------------------------
    #  Rules Panel
    # -----------------------------------------------
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
            x_off = SP_8 + SP_6 + SP_5 if i >= 2 else 0  # 720px second column
            self._draw_rule_box(label, lines, x_offset=x_off)
        hint = self.font_hud_small.render(
            "\u6309 F1 \u5173\u95ed  \u2502  \u5b8c\u6574\u89c4\u5219\u89c1 README.md", True, TEXT_MUTED)
        self.screen.blit(hint, ((SCREEN_W - hint.get_width()) // 2, SCREEN_H - SP_6 - SP_2 + SP_2))

    # -----------------------------------------------
    #  Panel Rendering Helpers
    # -----------------------------------------------
    def _draw_overlay_panel(self, lines: List[str], width: int) -> None:
        """Centered semi-transparent panel: gold border + title deco line + body."""
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        line_h = SP_6 + SP_1 + SP_2  # 30px line height
        box_h = len(lines) * line_h + SP_6 + SP_6  # 48px padding
        box = pygame.Rect((SCREEN_W - width) // 2, (SCREEN_H - box_h) // 2, width, box_h)

        # Panel background
        panel = pygame.Surface((width, box_h), pygame.SRCALPHA)
        panel.fill((16, 16, 24, 210))
        self.screen.blit(panel, box.topleft)
        # Gold double border
        pygame.draw.rect(self.screen, GOLD, box, 2, border_radius=SP_3)
        inner = box.inflate(-SP_2, -SP_2)
        pygame.draw.rect(self.screen, GOLD_FAINT, inner, 1, border_radius=SP_2)
        # Corner diamonds
        for cx, cy in [(box.x + 3, box.y + 3), (box.right - 3, box.y + 3),
                       (box.x + 3, box.bottom - 3), (box.right - 3, box.bottom - 3)]:
            pygame.draw.polygon(self.screen, GOLD_BRIGHT, [
                (cx, cy - SP_1), (cx + 3, cy), (cx, cy + SP_1), (cx - 3, cy)
            ])

        for i, ln in enumerate(lines):
            y = box.y + SP_6 + i * line_h  # 24px top padding
            if ln.startswith("\u2500"):
                t = self.font_panel_title.render(ln, True, GOLD_BRIGHT)
                tx = box.x + (width - t.get_width()) // 2
                self.screen.blit(t, (tx, y - 2))
            elif ln.endswith("\u3011"):
                t = self.font_panel_header.render(ln, True, GOLD)
                self.screen.blit(t, (box.x + SP_6 + SP_1 + SP_1, y))  # 30px left padding
            elif ln == "":
                continue
            else:
                t = self.font_panel_body.render(ln, True, TEXT)
                self.screen.blit(t, (box.x + SP_6 + SP_1 + SP_1, y + 2))

    def _draw_rule_box(self, title: str, lines: List[str], x_offset: int = 0) -> None:
        """Single text box in the rules panel."""
        box_w = 680
        line_h = SP_6 + SP_1 + SP_1  # 28px
        box_h = len(lines) * line_h + SP_6 + SP_6 + SP_1 + SP_2  # 64px padding
        box_x = LEFT_MARGIN + x_offset
        box_y = (SCREEN_H - box_h) // 2 - SP_5
        box = pygame.Rect(box_x, box_y, box_w, box_h)

        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill((14, 14, 22, 210))
        self.screen.blit(panel, box.topleft)
        pygame.draw.rect(self.screen, GOLD_DIM, box, 2, border_radius=SP_2 + SP_1)  # 10px
        inner = box.inflate(-SP_1 - SP_2, -SP_1 - SP_2)  # -6px
        pygame.draw.rect(self.screen, GOLD_FAINT, inner, 1, border_radius=SP_3 + SP_1)  # 6px

        # Title
        t = self.font_panel_header.render(title, True, GOLD)
        self.screen.blit(t, (box.x + SP_6, box.y + SP_5 + SP_2 - SP_1))  # 18px top
        # Title underline
        pygame.draw.line(self.screen, GOLD_DIM,
                         (box.x + SP_6, box.y + SP_6 + SP_2), (box.right - SP_6, box.y + SP_6 + SP_2), 1)

        for i, ln in enumerate(lines):
            text = self.font_panel_body.render(ln, True, TEXT)
            self.screen.blit(text, (box.x + SP_6, box.y + SP_6 + SP_2 + SP_1 + SP_2 + i * line_h))
