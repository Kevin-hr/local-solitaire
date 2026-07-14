(function (app) {
  "use strict";

  function cardSource(cardElement) {
    const type = cardElement.dataset.sourceType;
    if (type === "tableau") return { type, column: Number(cardElement.dataset.column), index: Number(cardElement.dataset.index) };
    if (type === "foundation") return { type, suit: cardElement.dataset.suit };
    return { type };
  }

  function dropTarget(element) {
    const target = element.closest("[data-drop-type]");
    if (!target) return null;
    const type = target.dataset.dropType;
    if (type === "tableau") return { type, column: Number(target.dataset.column) };
    if (type === "foundation") return { type, suit: target.dataset.suit };
    return { type };
  }

  function createInteractions(game, feedback) {
    const board = document.getElementById("game-board");
    let dragSourceElement = null;

    function invalid(element) {
      feedback.invalid();
      const target = element && (element.closest(".pile, .tableau-column") || element);
      if (!target) return;
      target.classList.remove("invalid-shake");
      void target.offsetWidth;
      target.classList.add("invalid-shake");
      window.setTimeout(() => target.classList.remove("invalid-shake"), 260);
    }

    board.addEventListener("click", (event) => {
      const card = event.target.closest(".card");
      const pile = event.target.closest(".pile, .tableau-column");
      if (!pile) return;

      if (pile.id === "stock") {
        if (!game.drawFromStock()) invalid(pile); else feedback.flip();
        return;
      }

      const target = dropTarget(pile);
      const selected = game.getState().selected;
      if (selected && target && (target.type === "tableau" || target.type === "foundation")) {
        if (game.moveSelectedTo(target)) { feedback.move(); return; }
        if (!card) { invalid(pile); return; }
      }

      if (card && card.dataset.sourceType !== "stock") {
        const source = cardSource(card);
        if (!game.selectSource(source) && game.getState().selected) invalid(card);
      }
    });

    board.addEventListener("dblclick", (event) => {
      const card = event.target.closest(".card.face-up");
      if (!card || card.dataset.sourceType === "foundation" || card.dataset.sourceType === "stock") return;
      event.preventDefault();
      if (game.moveToFoundation(cardSource(card))) feedback.move(); else invalid(card);
    });

    board.addEventListener("keydown", (event) => {
      const card = event.target.closest(".card.face-up");
      if (!card || (event.key !== "Enter" && event.key !== " ")) return;
      event.preventDefault();
      card.click();
    });

    board.addEventListener("dragstart", (event) => {
      const card = event.target.closest(".card.face-up");
      if (!card || card.dataset.sourceType === "stock") { event.preventDefault(); return; }
      const source = cardSource(card);
      game.selectSource(source);
      if (!game.getState().selected) { event.preventDefault(); return; }
      dragSourceElement = card;
      card.classList.add("dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", card.dataset.cardId || "card");
    });

    board.addEventListener("dragover", (event) => {
      const target = dropTarget(event.target);
      if (!target || (target.type !== "tableau" && target.type !== "foundation")) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      const element = event.target.closest("[data-drop-type]");
      if (element) element.classList.add("drop-active");
    });

    board.addEventListener("dragleave", (event) => {
      const element = event.target.closest("[data-drop-type]");
      if (element && !element.contains(event.relatedTarget)) element.classList.remove("drop-active");
    });

    board.addEventListener("drop", (event) => {
      event.preventDefault();
      document.querySelectorAll(".drop-active").forEach((element) => element.classList.remove("drop-active"));
      const target = dropTarget(event.target);
      if (target && game.moveSelectedTo(target)) feedback.move(); else invalid(event.target);
    });

    board.addEventListener("dragend", () => {
      if (dragSourceElement) dragSourceElement.classList.remove("dragging");
      dragSourceElement = null;
      document.querySelectorAll(".drop-active").forEach((element) => element.classList.remove("drop-active"));
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") game.clearSelection();
    });
  }

  app.interactions = { createInteractions };
})(window.Solitaire = window.Solitaire || {});
