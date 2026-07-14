---
title: Local Solitaire GitHub 对标调研
date: 2026-07-15
tags: [GitHub, Klondike, 对标, 调研]
---

# Local Solitaire GitHub 对标调研

关联：[[README]] · [[GAME_RULES]] · [[TEST_CHECKLIST]]

调研时间：2026-07-15 06:09（Asia/Shanghai）

## 结论

Local Solitaire 值得作为独立开源项目发布。它没有创造新的 Klondike 规则，独特价值来自一组同时成立的交付条件：

1. 中文界面、中文规则、中文验收清单和中文通关攻略成套交付。
2. 双击 `index.html` 即可通过 `file://` 运行，不需要本地服务器或构建工具。
3. 运行时零第三方依赖、零图片素材、零外部字体、零网络请求。
4. 同时提供可维护的拆分源码和可复制的单文件版本。
5. 覆盖完整牌局存档恢复、损坏存档保护、100 步撤销、分优先级提示、设置和 Web Audio 音效。
6. 规则逻辑与 DOM 渲染分离，附零依赖自动测试和手工验收清单。

这个组合对中文学习者、需要内网或离线运行的 Windows 用户、希望审计游戏规则的开发者有明确采用价值。

## 先排除名称误判

用户提供的 [chriseldredge/Klondike](https://github.com/chriseldredge/Klondike) 是建立在 NuGet.Lucene 上的私有 NuGet 包托管前端，与纸牌游戏无关。截至调研时，该仓库约有 297 stars、72 forks，采用 Apache-2.0 许可证。它不能作为游戏功能对标。

## 可比项目

| 项目 | 主要优势 | 相对 Local Solitaire 的优势 | Local Solitaire 的相对优势 |
|---|---|---|---|
| [jhatzimalis/solitaire](https://github.com/jhatzimalis/solitaire) | 单文件、零依赖、离线、移动端、主题定制和流畅动画 | 移动端体验、视觉主题和动画更丰富 | 拆分源码、完整牌局恢复、撤销、提示、音效、规则测试与中文文档更完整 |
| [igapyon/klondike](https://github.com/igapyon/klondike) | TypeScript 源码、求解器、可解性提示、智能发牌、Vitest 测试、离线和在线构建 | 求解能力、自动测试深度、牌局可解性处理明显更强 | 无需构建即可阅读和运行；运行时不含第三方库；中文交付、单文件与拆分源码同时面向普通用户 |
| [rdtect/mrax-solitaire](https://github.com/rdtect/mrax-solitaire) | 模块化 ES6 架构、教程和架构文档、键盘快捷键 | 教学文档粒度和键盘操作更完整 | 仓库未归档、直接 `file://` 运行、MIT 许可证、100 步撤销、提示、音效和中文验收材料；对标仓库已于 2026-03-26 归档 |
| [HectorVilas/solitaire](https://github.com/HectorVilas/solitaire) | 169 次提交记录、开发过程文档、两套牌面图片 | 开发历史和视觉素材更丰富 | 体积更小、无图片依赖，包含撤销、提示、存档、音效、设置、测试和单文件交付 |
| [michelc/www.solitaire-play.com](https://github.com/michelc/www.solitaire-play.com) | 多种纸牌玩法、长期维护、面向在线站点 | 玩法数量、内容规模和在线产品成熟度更高 | 单一用途、无广告代码、无 jQuery、无服务器依赖，适合下载后离线使用和代码学习 |

## 五重过滤结果

对标方法原本用于商业项目，本次把“赚钱”替换为开源项目的“采用价值”。

| 筛子 | 结果 | 判断 |
|---|---|---|
| 1. 有采用价值 | ✅ | 中文、纯离线、双交付、可恢复存档和验收材料组合能解决具体使用需求 |
| 2. 能看懂 | ✅ | 原生 HTML/CSS/JavaScript，状态、规则、渲染和交互分开 |
| 3. 能复用 | ✅ | MIT 许可、无依赖、无需构建，可直接复制单文件或修改拆分源码 |
| 4. 排除无关噪音 | ✅ | 聚焦 Klondike V1.0，不加入账号、排行、广告和后端 |
| 5. 可以执行 | ✅ | 已有可运行版本、测试、文档和 GitHub 发布所需元数据 |

## 我们的短板

- 最低桌面宽度为 1024px，没有针对手机触控做完整适配。
- 没有求解器、牌局编号、必定可解发牌或数学无解判断。
- 自动测试只覆盖核心规则，缺少浏览器端端到端测试和无障碍审计。
- 只支持单张翻牌，没有三张翻牌和难度档位。
- GitHub 项目刚发布，没有外部用户、贡献者、issue 反馈或长期维护记录。
- 视觉主题和动画定制少于 `jhatzimalis/solitaire`。

## 应该模仿的部分

1. 模仿 `igapyon/klondike`：增加可重复的牌局种子、浏览器集成测试和可解性辅助，但保持运行时零依赖。
2. 模仿 `jhatzimalis/solitaire`：补充移动端布局和主题设置。
3. 模仿 `rdtect/mrax-solitaire`：增加键盘快捷键表和架构说明。
4. 模仿成熟项目：发布在线演示、截图、版本标签和变更记录。

## GitHub 传播文案

推荐仓库描述：

> Chinese-first, zero-dependency Klondike Solitaire. Double-click to play offline, with modular source + single-file build, save/restore, undo, hints, tests, and acceptance docs.

推荐主题：

```text
klondike, solitaire, vanilla-javascript, offline-first, zero-dependency,
single-file, localstorage, chinese, browser-game, windows
```

## 证据边界

- 功能判断来自各仓库 README、文件树、许可证元数据和源码关键词核验。
- stars、forks、归档状态和更新时间会变化，本报告记录的是调研时状态。
- 没有把 README 未声明的能力推定为缺陷；源码未发现对应实现时使用“未发现”或限定性描述。

#GitHub #Klondike #对标 #调研
