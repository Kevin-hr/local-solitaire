# Klondike Solitaire — Emerald Velour Edition

> Python / Pygame 实现的经典接龙游戏，采用 Emerald Velour 主题（深绿天鹅绒桌面 + 金色点缀 + Art Deco 卡背 + 衬线字体排版），经 frontend-design-pro 设计原则重构。

## 快速开始

```bash
cd solitaire/v3.0
python main.py
```

或指定 Python 路径：

```bash
"C:/Users/52648/.workbuddy/binaries/python/versions/3.13.12/python.exe" main.py
```

## 操作

| 操作 | 功能 |
|------|------|
| 左键单击 stock（左上牌堆） | 抽 1 张到 waste |
| 左键拖拽 | 移动牌：颜色相反 + 点数递减；可整段序列移动 |
| 右键单击 | 自动归位 foundation（若可放） |
| R / N | 重开新局 |
| H | 帮助叠层 |
| ESC | 退出（拖拽中按 ESC 取消拖拽） |

## 规则（标准 Klondike）

- **7 列 tableau**：第 i 列 i+1 张，仅末张面朝上
- **tableau 堆叠**：颜色相反（红/黑交替）+ 点数递减一级；空列只收 K
- **foundation**：同花色，A 起步，升序到 K
- **stock 抽牌**：draw-1 模式；stock 空时点击把 waste 倒回 stock
- **胜利**：4 个 foundation 各集齐 13 张

## 交互反馈

| 事件 | 视觉反馈 |
|------|----------|
| 卡牌悬停 | 平滑渐变（~150ms，指数逼近） |
| 无效移动 | 红色脉冲闪烁（300ms sine pulse） |
| 成功放置 | 绿色辉光扩散（350ms ease-out） |

## 模块

| 文件 | 职责 |
|------|------|
| `game_engine.py` | Card / Deck / GameEngine：规则与状态，坐标无关，可单测 |
| `ui_manager.py` | 布局常量、hit_test、卡牌绘制、背景/HUD/胜利/帮助 + 动画系统 |
| `move_handler.py` | DragHandler（取出暂存→放置/回退）、ClickHandler、MoveValidator |
| `tutorial.py` | 引导系统（接口完整，默认关闭） |
| `main.py` | 入口与主循环 |
| `test_smoke.py` | 逻辑 + 渲染 + 拖拽冒烟测试 |

## 设计系统

本版本的 UI 经 [frontend-design-pro](https://skillhub.lightmake.com) 设计原则重构，采用以下设计令牌：

| 维度 | 规范 |
|------|------|
| **字体** | Corbel（人文无衬线），1.25 倍率 Modular Type Scale (TS_BASE=16px → TS_4XL=31px) |
| **间距** | 4px 基础间距系统（SP_1=4, SP_2=8, SP_3=12… SP_12=48） |
| **色彩** | TEXT_MUTED 对比度 ~5.5:1（符合 WCAG 2.1 AA） |
| **动效** | ease_out_cubic 缓动 + 指数逼近悬停 + 正弦脉冲闪烁 + 辉光扩散 |

## 验证

```bash
python test_smoke.py
```

覆盖：标准发牌张数/分布、面朝上规则、stock↔waste 回收、tableau/foundation 合法性、
合法序列判定、无显示渲染（dummy 驱动）、拖拽取出→放置→回退流程。

## 开发历史

- **v3.0 重写**：修复原版 13 个确定性缺陷（发牌规则、属性引用、类型一致性、初始化顺序等）
- **Emerald Velour 主题**：深绿天鹅绒质感桌面、金色点缀、Art Deco 卡背
- **frontend-design-pro 重构**：设计令牌系统、动效、交互反馈

## 已知限制

- 无音效、无存档
- tableau 列较长时无滚动裁剪（极端牌局可能下溢屏幕底部）
- 引导系统为占位实现

## License

MIT
