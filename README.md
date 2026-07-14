# Klondike Solitaire v3.0 — 重写可玩版

> 本版是对原 v3.0（声称"完全可玩"但实际无法运行）的重写。原版在入口初始化、发牌规则、
> 渲染层存在大量确定性运行阻断缺陷（详见下文）。本版已实机验证可运行。

## 快速开始

```bash
# 用项目内隔离环境运行（pygame 已装好）
cd solitaire/v3.0
python main.py
```

或用本工作区的隔离 venv：

```bash
"C:/Users/52648/.workbuddy/binaries/python/envs/default/Scripts/python.exe" main.py
```

## 操作

| 操作 | 功能 |
|------|------|
| 左键单击 stock（左上牌堆） | 抽 1 张到 waste |
| 左键拖拽 | 移动牌：颜色相反 + 点数递减；可整段序列移动 |
| 右键单击 | 自动归位 foundation（若可放） |
| R / N | 重开新局 |
| H | 帮助叠层 |
| T | 引导开关（默认关） |
| ESC | 退出（拖拽中按 ESC 取消拖拽） |

## 规则（标准 Klondike）

- 7 列 tableau：第 i 列 i+1 张，仅末张面朝上
- tableau 堆叠：颜色相反（红/黑交替）+ 点数递减一级；空列只收 K
- foundation：同花色，A 起步，升序到 K
- stock 抽牌：draw-1 模式；stock 空时点击把 waste 倒回 stock
- 胜利：4 个 foundation 各集齐 13 张

## 验证

```bash
python test_smoke.py
```

覆盖：标准发牌张数/分布、面朝上规则、stock↔waste 回收、tableau/foundation 合法性、
合法序列判定、无显示渲染（dummy 驱动）、拖拽取出→放置→回退流程。

## 模块

| 文件 | 职责 |
|------|------|
| `game_engine.py` | Card/Deck/GameEngine：规则与状态，坐标无关，可单测 |
| `ui_manager.py` | 布局常量、hit_test、卡牌绘制、背景/HUD/胜利/帮助 |
| `move_handler.py` | DragHandler（取出暂存→放置/回退）、ClickHandler、MoveValidator |
| `tutorial.py` | 引导系统（接口完整，默认关闭） |
| `main.py` | 入口与主循环 |
| `test_smoke.py` | 逻辑 + 渲染 + 拖拽冒烟测试 |

## 相对原 v3.0 的修复（事实清单）

原 v3.0 经逐行核对，存在以下确定性缺陷，本版均已修复：

1. `Deck.create_deck` 引用 `self.suit`（Deck 无该属性）→ 改为循环变量
2. 发牌张数 `(col*5)+2`（得 2/7/12/.../32）→ 改为标准 `col+1`（1..7）
3. 强制把每列底牌设为 A（破坏规则）→ 删除，仅末张翻面
4. `waste` 存字符串而其余当 Card 用 → 统一存 Card
5. `UIManager.draw_all` 引用不存在的 `self.engine` → 构造时注入
6. `font.render(text, True)` 缺颜色参数 → 传颜色
7. `draw_card` 中 `screen` 未定义 → 改 `self.screen`
8. `ClickHandler(screen, ui_manager)` 与 `__init__(self, screen)` 参数不符 → 重写签名
9. `DragHandler` 类型标注 `UIManager` 未导入 → 用鸭子类型，不强制导入
10. `move_handler` 引用未定义的 `CARD_WIDTH` → 坐标统一走 `ui_manager`
11. `main` 从不调用 `new_game()` → 入口即初始化发牌
12. `ui_manager.draw_all(screen)` 传参但方法无参 → 对齐
13. `_draw_victory` 中非法 `\u{1f389}` 转义（SyntaxError）→ 字面量

## 已知限制

- 无音效、无动画过渡、无存档
- tableau 列较长时无滚动裁剪（极端牌局可能下溢屏幕底部）
- 引导系统为占位实现
