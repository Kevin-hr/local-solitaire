(function (app) {
  "use strict";

  const { SUITS, createDeck, shuffleDeck, dealCards } = app.cards;
  const { isDescendingAlternating, canMoveToTableau, canMoveToFoundation } = app.rules;

  function clone(value) { return JSON.parse(JSON.stringify(value)); }

  function emptyFoundations() {
    return { hearts: [], diamonds: [], clubs: [], spades: [] };
  }

  function createInitialState(randomFn) {
    const dealt = dealCards(shuffleDeck(createDeck(), randomFn));
    return {
      stock: dealt.stock,
      waste: [],
      foundations: emptyFoundations(),
      tableau: dealt.tableau,
      selected: null,
      history: [],
      moves: 0,
      elapsedTime: 0,
      timerStartedAt: Date.now(),
      status: "playing",
      stockPasses: 0
    };
  }

  function snapshot(state) {
    return clone({
      stock: state.stock,
      waste: state.waste,
      foundations: state.foundations,
      tableau: state.tableau,
      moves: state.moves,
      elapsedTime: getElapsedTime(state),
      status: state.status,
      stockPasses: state.stockPasses || 0
    });
  }

  function normalizeLoadedState(saved) {
    if (!saved || !Array.isArray(saved.stock) || !Array.isArray(saved.waste) || !Array.isArray(saved.tableau) || saved.tableau.length !== 7) return null;
    if (!saved.foundations || SUITS.some((suit) => !Array.isArray(saved.foundations[suit]))) return null;
    const allCards = [
      ...saved.stock,
      ...saved.waste,
      ...SUITS.flatMap((suit) => saved.foundations[suit]),
      ...saved.tableau.flat()
    ];
    if (allCards.length !== 52 || new Set(allCards.map((card) => card.id)).size !== 52) return null;
    return {
      ...clone(saved),
      selected: null,
      history: [],
      moves: Number(saved.moves) || 0,
      elapsedTime: Number(saved.elapsedTime) || 0,
      timerStartedAt: Date.now(),
      status: saved.status === "won" ? "won" : "playing",
      stockPasses: Number(saved.stockPasses) || 0
    };
  }

  function getElapsedTime(state) {
    const base = Number(state.elapsedTime) || 0;
    if (state.status !== "playing" || !state.timerStartedAt) return base;
    return base + Math.max(0, Math.floor((Date.now() - state.timerStartedAt) / 1000));
  }

  function createGame(options) {
    const config = options || {};
    let state = createInitialState(config.randomFn);
    let settings = { ...app.storage.DEFAULT_SETTINGS, ...(config.settings || {}) };
    const listeners = new Set();

    function emit(eventName, detail) {
      listeners.forEach((listener) => listener(state, eventName || "change", detail));
    }

    function saveHistory() {
      state.history.push(snapshot(state));
      if (state.history.length > 100) state.history.shift();
    }

    function pauseClockIntoState() {
      state.elapsedTime = getElapsedTime(state);
      state.timerStartedAt = state.status === "playing" ? Date.now() : null;
    }

    function flipExposedCard(columnIndex) {
      const column = state.tableau[columnIndex];
      const top = column && column[column.length - 1];
      if (top && !top.faceUp) { top.faceUp = true; return true; }
      return false;
    }

    function checkWin() {
      const won = SUITS.reduce((total, suit) => total + state.foundations[suit].length, 0) === 52;
      if (won && state.status !== "won") {
        state.elapsedTime = getElapsedTime(state);
        state.timerStartedAt = null;
        state.status = "won";
      }
      return won;
    }

    function sourceCards(selection) {
      if (!selection) return [];
      if (selection.type === "waste") {
        const card = state.waste[state.waste.length - 1];
        return card ? [card] : [];
      }
      if (selection.type === "foundation") {
        const pile = state.foundations[selection.suit];
        const card = pile[pile.length - 1];
        return card ? [card] : [];
      }
      if (selection.type === "tableau") {
        return state.tableau[selection.column].slice(selection.index);
      }
      return [];
    }

    function removeSource(selection) {
      if (selection.type === "waste") return state.waste.pop();
      if (selection.type === "foundation") return state.foundations[selection.suit].pop();
      if (selection.type === "tableau") return state.tableau[selection.column].splice(selection.index);
      return null;
    }

    function tryAutoFoundation() {
      if (!settings.autoFoundation || state.status !== "playing") return 0;
      let moved = 0;
      let progress = true;
      while (progress) {
        progress = false;
        const candidates = [];
        const wasteTop = state.waste[state.waste.length - 1];
        if (wasteTop) candidates.push({ card: wasteTop, source: { type: "waste" } });
        state.tableau.forEach((column, columnIndex) => {
          const card = column[column.length - 1];
          if (card && card.faceUp) candidates.push({ card, source: { type: "tableau", column: columnIndex, index: column.length - 1 } });
        });
        const candidate = candidates.find(({ card }) => canMoveToFoundation(card, state.foundations[card.suit], card.suit));
        if (candidate) {
          const card = removeSource(candidate.source);
          state.foundations[card.suit].push(card);
          if (candidate.source.type === "tableau") flipExposedCard(candidate.source.column);
          moved += 1;
          progress = true;
        }
      }
      return moved;
    }

    function finishLegalMove(eventName, sourceColumn) {
      if (typeof sourceColumn === "number") flipExposedCard(sourceColumn);
      state.selected = null;
      state.moves += 1;
      tryAutoFoundation();
      const won = checkWin();
      emit(won ? "win" : eventName, { won });
      return true;
    }

    function startNewGame(randomFn) {
      state = createInitialState(randomFn || config.randomFn);
      emit("new-game");
      return state;
    }

    function restore(savedState) {
      const restored = normalizeLoadedState(savedState);
      if (!restored) return false;
      state = restored;
      emit(state.status === "won" ? "win" : "restore");
      return true;
    }

    function drawFromStock() {
      if (state.status !== "playing") return false;
      if (state.stock.length === 0) return resetStock();
      saveHistory();
      const card = state.stock.pop();
      card.faceUp = true;
      state.waste.push(card);
      return finishLegalMove("draw");
    }

    function resetStock() {
      if (state.status !== "playing" || state.stock.length || !state.waste.length) return false;
      if (!settings.unlimitedStock && state.stockPasses >= 1) return false;
      saveHistory();
      state.stock = state.waste.reverse();
      state.stock.forEach((card) => { card.faceUp = false; });
      state.waste = [];
      state.stockPasses += 1;
      return finishLegalMove("recycle");
    }

    function selectSource(selection) {
      if (state.status !== "playing") return false;
      if (selection && selection.type === "tableau") {
        const column = state.tableau[selection.column];
        const cards = column && column.slice(selection.index);
        if (!cards || !isDescendingAlternating(cards)) return false;
      }
      if (!sourceCards(selection).length) return false;
      const same = state.selected && JSON.stringify(state.selected) === JSON.stringify(selection);
      state.selected = same ? null : { ...selection };
      emit("selection");
      return !same;
    }

    function clearSelection() {
      if (!state.selected) return;
      state.selected = null;
      emit("selection");
    }

    function moveCards(selection, target) {
      const source = selection || state.selected;
      if (!source || !target || state.status !== "playing") return false;
      const cards = sourceCards(source);
      if (!cards.length) return false;

      if (target.type === "tableau") {
        if (source.type === "tableau" && source.column === target.column) return false;
        if (!canMoveToTableau(cards, state.tableau[target.column])) return false;
        saveHistory();
        const removed = removeSource(source);
        state.tableau[target.column].push(...(Array.isArray(removed) ? removed : [removed]));
        return finishLegalMove("move", source.type === "tableau" ? source.column : undefined);
      }

      if (target.type === "foundation") {
        if (cards.length !== 1 || source.type === "foundation") return false;
        const card = cards[0];
        if (!canMoveToFoundation(card, state.foundations[target.suit], target.suit)) return false;
        saveHistory();
        removeSource(source);
        state.foundations[target.suit].push(card);
        return finishLegalMove("foundation", source.type === "tableau" ? source.column : undefined);
      }
      return false;
    }

    function moveSelectedTo(target) { return moveCards(state.selected, target); }

    function moveToFoundation(selection) {
      const cards = sourceCards(selection);
      if (cards.length !== 1) return false;
      return moveCards(selection, { type: "foundation", suit: cards[0].suit });
    }

    function undoMove() {
      if (state.status === "won" || !state.history.length) return false;
      const previous = state.history.pop();
      const remainingHistory = state.history;
      state = { ...previous, selected: null, history: remainingHistory, timerStartedAt: Date.now() };
      emit("undo");
      return true;
    }

    function findHint() {
      const foundationCandidates = [];
      const wasteTop = state.waste[state.waste.length - 1];
      if (wasteTop) foundationCandidates.push({ card: wasteTop, source: { type: "waste" } });
      state.tableau.forEach((column, columnIndex) => {
        const card = column[column.length - 1];
        if (card && card.faceUp) foundationCandidates.push({ card, source: { type: "tableau", column: columnIndex, index: column.length - 1 } });
      });
      for (const candidate of foundationCandidates) {
        if (canMoveToFoundation(candidate.card, state.foundations[candidate.card.suit], candidate.card.suit)) {
          return { source: candidate.source, target: { type: "foundation", suit: candidate.card.suit }, message: `${candidate.card.id} 可以移到基础牌堆` };
        }
      }

      for (let sourceColumn = 0; sourceColumn < 7; sourceColumn += 1) {
        const column = state.tableau[sourceColumn];
        const firstFaceUp = column.findIndex((card) => card.faceUp);
        if (firstFaceUp <= 0) continue;
        const movable = column.slice(firstFaceUp);
        if (!isDescendingAlternating(movable)) continue;
        for (let targetColumn = 0; targetColumn < 7; targetColumn += 1) {
          if (sourceColumn !== targetColumn && canMoveToTableau(movable, state.tableau[targetColumn])) {
            return {
              source: { type: "tableau", column: sourceColumn, index: firstFaceUp },
              target: { type: "tableau", column: targetColumn },
              message: "移动这组牌可以翻开一张暗牌"
            };
          }
        }
      }

      if (wasteTop) {
        for (let targetColumn = 0; targetColumn < 7; targetColumn += 1) {
          if (canMoveToTableau([wasteTop], state.tableau[targetColumn])) {
            return { source: { type: "waste" }, target: { type: "tableau", column: targetColumn }, message: "废牌可以移到桌面列" };
          }
        }
      }

      for (let sourceColumn = 0; sourceColumn < 7; sourceColumn += 1) {
        const column = state.tableau[sourceColumn];
        for (let index = 0; index < column.length; index += 1) {
          const cards = column.slice(index);
          if (!isDescendingAlternating(cards)) continue;
          for (let targetColumn = 0; targetColumn < 7; targetColumn += 1) {
            if (sourceColumn !== targetColumn && canMoveToTableau(cards, state.tableau[targetColumn])) {
              return { source: { type: "tableau", column: sourceColumn, index }, target: { type: "tableau", column: targetColumn }, message: "这组牌可以移到另一列" };
            }
          }
        }
      }

      for (const suit of SUITS) {
        const pile = state.foundations[suit];
        const card = pile[pile.length - 1];
        if (!card) continue;
        for (let targetColumn = 0; targetColumn < 7; targetColumn += 1) {
          if (canMoveToTableau([card], state.tableau[targetColumn])) {
            return {
              source: { type: "foundation", suit },
              target: { type: "tableau", column: targetColumn },
              message: "基础牌堆的顶牌可以移回桌面"
            };
          }
        }
      }

      if (state.stock.length || (state.waste.length && (settings.unlimitedStock || state.stockPasses < 1))) {
        return { source: { type: "stock" }, target: { type: "stock" }, message: state.stock.length ? "从牌库翻出下一张牌" : "回收废牌并继续翻牌" };
      }
      return null;
    }

    function setSettings(nextSettings) {
      settings = { ...settings, ...nextSettings };
      emit("settings");
    }

    function exportState() {
      pauseClockIntoState();
      return snapshot(state);
    }

    return {
      subscribe(listener) { listeners.add(listener); return () => listeners.delete(listener); },
      getState: () => state,
      getSettings: () => ({ ...settings }),
      setSettings,
      startNewGame,
      restore,
      drawFromStock,
      resetStock,
      selectSource,
      clearSelection,
      moveCards,
      moveSelectedTo,
      moveToFoundation,
      flipExposedCard,
      undoMove,
      findHint,
      checkWin,
      getElapsedTime: () => getElapsedTime(state),
      exportState,
      sourceCards: () => sourceCards(state.selected)
    };
  }

  app.game = { createGame, createInitialState, normalizeLoadedState, getElapsedTime };
})(window.Solitaire = window.Solitaire || {});
