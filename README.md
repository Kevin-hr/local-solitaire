# Local Solitaire

A Chinese-first, zero-dependency Klondike Solitaire game for Windows desktop browsers. Double-click and play: no install, server, account, build step, CDN, image asset, or network access required.

Local Solitaire ships in two forms from the same source:

- `index.html` with readable, separated game logic, rendering, interactions, and storage code.
- `solitaire.html` as a fully self-contained file for copying, archiving, and offline play.

Unlike minimal single-file demos, this repository also includes resumable game saves, 100-step undo, prioritized hints, settings, zero-dependency rule tests, a manual acceptance checklist, Chinese game rules, and a practical winning guide.

## Quick start

Download the repository and double-click `index.html` or `solitaire.html`. Current Microsoft Edge and Google Chrome are recommended. The desktop layout targets windows 1024px wide or larger.

Run the zero-dependency rule checks with Node.js when developing:

```text
node tests/game.test.js
```

The game itself does not require Node.js.

## 中文说明

一款可离线运行的经典 Klondike 纸牌游戏。无需安装、登录、构建或联网。

## 运行方式

双击 `index.html` 即可开始。也可以双击 `solitaire.html` 使用完全独立的单文件版。

建议使用当前版本的 Microsoft Edge 或 Google Chrome，窗口宽度不低于 1024px。

## 游戏操作

- 单击牌库：翻一张牌；牌库为空时回收废牌。
- 单击明牌：选中牌或连续牌组；再单击目标列或基础牌堆完成移动。
- 双击废牌或桌面顶牌：尝试自动移入对应基础牌堆。
- 拖拽明牌：移动单牌或合法连续牌组。
- 撤销：恢复上一步合法操作，最多保留 100 步。
- 提示：高亮一个来源和目标，不会自动执行。
- Esc：取消当前选择。

详细规则见 [GAME_RULES.md](GAME_RULES.md)，通关方法见 [WINNING_GUIDE.md](WINNING_GUIDE.md)，手工验收步骤见 [TEST_CHECKLIST.md](TEST_CHECKLIST.md)。项目对标结论见 [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md)。

## 项目结构

```text
local-solitaire/
├─ index.html                 拆分源码入口
├─ solitaire.html             可独立运行的单文件版
├─ css/style.css              界面样式
├─ js/cards.js                牌组生成、洗牌和发牌
├─ js/rules.js                纯规则判断
├─ js/storage.js              本地存档和设置
├─ js/game.js                 游戏状态与操作
├─ js/renderer.js             DOM 渲染
├─ js/interactions.js         点击、键盘和拖拽
├─ js/main.js                 启动、音效和界面控制
├─ tests/game.test.js         核心规则自动测试
├─ GAME_RULES.md              游戏规则说明
├─ WINNING_GUIDE.md           通关攻略
├─ BENCHMARK_REPORT.md        同类开源项目调研
└─ TEST_CHECKLIST.md          手工测试清单
```

## 已实现功能

- 标准 52 张牌、单张翻牌、七列 Klondike 发牌
- 桌面递减红黑交替、空列仅放 K、同花色基础牌堆
- 点击选择、拖拽、连续牌组移动、双击收牌
- 暗牌露出后自动翻开，非法操作不改变状态
- 牌库循环、撤销、分优先级提示、胜利判定
- 计时、步数、新游戏确认、胜利结果
- localStorage 自动存档、刷新后选择恢复、损坏存档保护
- 音效、自动收牌、自动保存、牌库循环、统计显示设置
- 1024px 以上桌面窗口响应式缩放

## 未实现功能

- Spider、FreeCell、Pyramid、TriPeaks 等其他玩法
- 在线排行、账号、云存档、多人和移动端适配
- 对牌局是否数学上必然无解的穷举判断

## 测试方式

浏览器功能按 `TEST_CHECKLIST.md` 手工验收。

如果电脑已安装 Node.js，可在本目录运行：

```text
node tests/game.test.js
```

游戏运行本身不依赖 Node.js。

## 数据与隐私

游戏状态和设置只保存在当前浏览器的 localStorage 中，不发送任何网络请求。

## Open-source positioning

The repository focuses on a narrow, auditable promise: a complete Chinese desktop Klondike package that works directly from `file://`, remains easy to read, and is documented well enough to learn from or verify manually. It does not claim to have a solver, mobile-first controls, draw-three mode, or the largest automated test suite. See the [benchmark report](BENCHMARK_REPORT.md) for the evidence and trade-offs.

## License

MIT. See [LICENSE](LICENSE).

#游戏 #本地应用 #Klondike
