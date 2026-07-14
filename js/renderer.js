(function (app) {
  "use strict";

  const { SUITS, SUIT_SYMBOLS, rankLabel } = app.cards;

  function selectionMatches(selected, type, details) {
    if (!selected || selected.type !== type) return false;
    if (type === "tableau") return selected.column === details.column && selected.index === details.index;
    if (type === "foundation") return selected.suit === details.suit;
    return true;
  }

  function createCardElement(card, source, topExpression) {
    const element = document.createElement("div");
    element.className = `card ${card.faceUp ? `face-up ${card.color}` : "face-down"}`;
    element.dataset.cardId = card.id;
    element.dataset.sourceType = source.type;
    if (typeof source.column === "number") element.dataset.column = String(source.column);
    if (typeof source.index === "number") element.dataset.index = String(source.index);
    if (source.suit) element.dataset.suit = source.suit;
    element.style.zIndex = String((source.index || 0) + 2);
    if (topExpression) element.style.top = topExpression;
    element.draggable = Boolean(card.faceUp);
    element.setAttribute("aria-label", card.faceUp ? `${rankLabel(card.rank)} ${SUIT_SYMBOLS[card.suit]}` : "背面朝上的牌");
    element.setAttribute("role", "button");
    element.tabIndex = card.faceUp ? 0 : -1;

    if (card.faceUp) {
      const rank = rankLabel(card.rank);
      const symbol = SUIT_SYMBOLS[card.suit];
      element.innerHTML = `<span class="card-corner"><span>${rank}</span><span class="suit">${symbol}</span></span><span class="card-center" aria-hidden="true">${symbol}</span><span class="card-corner bottom" aria-hidden="true"><span>${rank}</span><span class="suit">${symbol}</span></span>`;
    }
    return element;
  }

  function createRenderer() {
    const elements = {
      stock: document.getElementById("stock"),
      waste: document.getElementById("waste"),
      foundations: Object.fromEntries(SUITS.map((suit) => [suit, document.getElementById(`foundation-${suit}`)])),
      columns: Array.from(document.querySelectorAll(".tableau-column")),
      undo: document.getElementById("undo-btn"),
      moves: document.getElementById("moves"),
      timer: document.getElementById("timer"),
      movesStat: document.getElementById("moves-stat"),
      timerStat: document.getElementById("timer-stat")
    };

    SUITS.forEach((suit) => { elements.foundations[suit].dataset.symbol = SUIT_SYMBOLS[suit]; });

    function render(state, settings) {
      elements.stock.innerHTML = "";
      elements.stock.classList.toggle("has-cards", state.stock.length > 0);
      elements.stock.setAttribute("aria-label", state.stock.length ? `牌库，剩余 ${state.stock.length} 张` : "空牌库，点击回收废牌");
      if (state.stock.length) {
        const card = state.stock[state.stock.length - 1];
        elements.stock.appendChild(createCardElement(card, { type: "stock" }));
      }

      elements.waste.innerHTML = "";
      const wasteTop = state.waste[state.waste.length - 1];
      if (wasteTop) {
        const card = createCardElement(wasteTop, { type: "waste" });
        if (selectionMatches(state.selected, "waste", {})) card.classList.add("selected");
        elements.waste.appendChild(card);
      }

      SUITS.forEach((suit) => {
        const pile = elements.foundations[suit];
        pile.innerHTML = "";
        const cards = state.foundations[suit];
        pile.classList.toggle("has-cards", cards.length > 0);
        const top = cards[cards.length - 1];
        if (top) {
          const card = createCardElement(top, { type: "foundation", suit });
          if (selectionMatches(state.selected, "foundation", { suit })) card.classList.add("selected");
          pile.appendChild(card);
        }
      });

      state.tableau.forEach((column, columnIndex) => {
        const pile = elements.columns[columnIndex];
        pile.innerHTML = "";
        let downCount = 0;
        let upCount = 0;
        column.forEach((card, index) => {
          const top = `calc(${downCount} * var(--down-step) + ${upCount} * var(--up-step))`;
          const cardElement = createCardElement(card, { type: "tableau", column: columnIndex, index }, top);
          if (selectionMatches(state.selected, "tableau", { column: columnIndex, index })) cardElement.classList.add("selected");
          pile.appendChild(cardElement);
          if (card.faceUp) upCount += 1; else downCount += 1;
        });
        pile.style.minHeight = `calc(var(--card-h) + ${downCount} * var(--down-step) + ${upCount} * var(--up-step))`;
      });

      elements.undo.disabled = state.history.length === 0 || state.status !== "playing";
      elements.moves.textContent = String(state.moves);
      elements.movesStat.hidden = !settings.showMoves;
      elements.timerStat.hidden = !settings.showTimer;
      document.getElementById("game-board").classList.toggle("game-won", state.status === "won");
    }

    function formatTime(totalSeconds) {
      const seconds = Math.max(0, Math.floor(totalSeconds));
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const remainder = seconds % 60;
      return hours > 0
        ? `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`
        : `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
    }

    function updateTimer(seconds) { elements.timer.textContent = formatTime(seconds); }

    function descriptorElement(descriptor, sourceMode) {
      if (!descriptor) return null;
      if (descriptor.type === "stock") return elements.stock;
      if (descriptor.type === "waste") return elements.waste.querySelector(".card") || elements.waste;
      if (descriptor.type === "foundation") {
        return sourceMode ? (elements.foundations[descriptor.suit].querySelector(".card") || elements.foundations[descriptor.suit]) : elements.foundations[descriptor.suit];
      }
      if (descriptor.type === "tableau") {
        if (sourceMode && typeof descriptor.index === "number") return elements.columns[descriptor.column].querySelector(`[data-index="${descriptor.index}"]`);
        return elements.columns[descriptor.column];
      }
      return null;
    }

    function showHint(hint) {
      document.querySelectorAll(".hint-source, .hint-target").forEach((element) => element.classList.remove("hint-source", "hint-target"));
      if (!hint) return;
      const source = descriptorElement(hint.source, true);
      const target = descriptorElement(hint.target, false);
      if (source) source.classList.add("hint-source");
      if (target && target !== source) target.classList.add("hint-target");
      window.setTimeout(() => {
        if (source) source.classList.remove("hint-source");
        if (target) target.classList.remove("hint-target");
      }, 1900);
    }

    return { render, updateTimer, formatTime, showHint, elements };
  }

  app.renderer = { createRenderer };
})(window.Solitaire = window.Solitaire || {});
