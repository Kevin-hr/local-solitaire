(function (app) {
  "use strict";

  function isDescendingAlternating(cards) {
    if (!Array.isArray(cards) || cards.length === 0) return false;
    if (cards.some((card) => !card.faceUp)) return false;
    for (let index = 0; index < cards.length - 1; index += 1) {
      const upper = cards[index];
      const lower = cards[index + 1];
      if (upper.rank !== lower.rank + 1 || upper.color === lower.color) return false;
    }
    return true;
  }

  function canMoveToTableau(cards, targetPile) {
    if (!isDescendingAlternating(cards)) return false;
    const first = cards[0];
    if (!targetPile || targetPile.length === 0) return first.rank === 13;
    const target = targetPile[targetPile.length - 1];
    return target.faceUp && target.rank === first.rank + 1 && target.color !== first.color;
  }

  function canMoveToFoundation(card, foundation, foundationSuit) {
    if (!card || !card.faceUp || card.suit !== foundationSuit) return false;
    if (!foundation || foundation.length === 0) return card.rank === 1;
    const top = foundation[foundation.length - 1];
    return top.suit === card.suit && card.rank === top.rank + 1;
  }

  app.rules = { isDescendingAlternating, canMoveToTableau, canMoveToFoundation };
})(window.Solitaire = window.Solitaire || {});
