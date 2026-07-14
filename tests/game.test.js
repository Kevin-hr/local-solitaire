const assert = require("assert");
global.window = global;
global.Solitaire = {};
global.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };

require("../js/cards.js");
require("../js/rules.js");
require("../js/storage.js");
require("../js/game.js");

const { cards, rules, game: gameModule } = global.Solitaire;
const tests = [];
function test(name, fn) { tests.push({ name, fn }); }
function card(suit, rank, faceUp = true) {
  return {
    id: `${suit.charAt(0).toUpperCase()}-${rank}`,
    suit,
    rank,
    color: suit === "hearts" || suit === "diamonds" ? "red" : "black",
    faceUp
  };
}

test("创建 52 张不重复的牌", () => {
  const deck = cards.createDeck();
  assert.strictEqual(deck.length, 52);
  assert.strictEqual(new Set(deck.map((item) => item.id)).size, 52);
});

test("发牌为七列 1–7 张，牌库剩余 24 张，每列仅底牌翻开", () => {
  const dealt = cards.dealCards(cards.createDeck());
  assert.deepStrictEqual(dealt.tableau.map((column) => column.length), [1, 2, 3, 4, 5, 6, 7]);
  assert.strictEqual(dealt.stock.length, 24);
  dealt.tableau.forEach((column) => {
    assert(column[column.length - 1].faceUp);
    assert(column.slice(0, -1).every((item) => !item.faceUp));
  });
});

test("桌面列只接受递减且红黑交替，空列只接受 K", () => {
  assert(rules.canMoveToTableau([card("hearts", 9)], [card("spades", 10)]));
  assert(!rules.canMoveToTableau([card("clubs", 9)], [card("spades", 10)]));
  assert(!rules.canMoveToTableau([card("hearts", 10)], [card("spades", 10)]));
  assert(rules.canMoveToTableau([card("hearts", 13)], []));
  assert(!rules.canMoveToTableau([card("hearts", 12)], []));
});

test("基础牌堆从 A 开始并按同花色递增", () => {
  assert(rules.canMoveToFoundation(card("hearts", 1), [], "hearts"));
  assert(!rules.canMoveToFoundation(card("hearts", 2), [], "hearts"));
  assert(rules.canMoveToFoundation(card("hearts", 2), [card("hearts", 1)], "hearts"));
  assert(!rules.canMoveToFoundation(card("diamonds", 2), [card("hearts", 1)], "hearts"));
});

test("合法连续牌组可以整体移动，移动后自动翻开暗牌", () => {
  const instance = gameModule.createGame();
  const state = instance.getState();
  state.tableau = [
    [card("clubs", 11, false), card("hearts", 10), card("clubs", 9)],
    [card("spades", 11)], [], [], [], [], []
  ];
  assert(instance.moveCards({ type: "tableau", column: 0, index: 1 }, { type: "tableau", column: 1 }));
  assert.strictEqual(state.tableau[1].length, 3);
  assert(state.tableau[0][0].faceUp);
  assert.strictEqual(state.moves, 1);
});

test("非法移动不改变状态和步数", () => {
  const instance = gameModule.createGame();
  const state = instance.getState();
  state.tableau = [[card("hearts", 9)], [card("diamonds", 10)], [], [], [], [], []];
  const before = JSON.stringify(state.tableau);
  assert(!instance.moveCards({ type: "tableau", column: 0, index: 0 }, { type: "tableau", column: 1 }));
  assert.strictEqual(JSON.stringify(state.tableau), before);
  assert.strictEqual(state.moves, 0);
});

test("牌库单张翻牌，回收后保持原翻牌顺序", () => {
  const instance = gameModule.createGame();
  const state = instance.getState();
  state.stock = [card("clubs", 3, false), card("hearts", 2, false), card("spades", 1, false)];
  state.waste = [];
  assert(instance.drawFromStock());
  assert.strictEqual(state.waste[0].id, "S-1");
  assert(instance.drawFromStock());
  assert(instance.drawFromStock());
  assert(instance.resetStock());
  assert(instance.drawFromStock());
  assert.strictEqual(state.waste[0].id, "S-1");
});

test("撤销完整恢复牌堆、步数和翻牌状态", () => {
  const instance = gameModule.createGame();
  const state = instance.getState();
  const before = JSON.stringify({ stock: state.stock, waste: state.waste, tableau: state.tableau, moves: state.moves });
  instance.drawFromStock();
  assert(instance.undoMove());
  const restored = instance.getState();
  const after = JSON.stringify({ stock: restored.stock, waste: restored.waste, tableau: restored.tableau, moves: restored.moves });
  assert.strictEqual(after, before);
});

test("存档只接受完整且不重复的 52 张牌", () => {
  const instance = gameModule.createGame();
  const save = instance.exportState();
  assert(gameModule.normalizeLoadedState(save));
  save.stock.pop();
  assert.strictEqual(gameModule.normalizeLoadedState(save), null);
});

test("提示优先选择可进入基础牌堆的牌", () => {
  const instance = gameModule.createGame();
  const state = instance.getState();
  state.waste = [card("hearts", 1)];
  const hint = instance.findHint();
  assert.deepStrictEqual(hint.source, { type: "waste" });
  assert.deepStrictEqual(hint.target, { type: "foundation", suit: "hearts" });
});

test("四个基础牌堆共 52 张时判定胜利并停止计时", () => {
  const instance = gameModule.createGame();
  const state = instance.getState();
  state.foundations = Object.fromEntries(cards.SUITS.map((suit) => [suit, Array.from({ length: 13 }, (_, index) => card(suit, index + 1))]));
  assert(instance.checkWin());
  assert.strictEqual(state.status, "won");
  assert.strictEqual(state.timerStartedAt, null);
});

let passed = 0;
for (const { name, fn } of tests) {
  try {
    fn();
    passed += 1;
    console.log(`✓ ${name}`);
  } catch (error) {
    console.error(`✗ ${name}`);
    throw error;
  }
}
console.log(`\n${passed}/${tests.length} 项测试通过`);
