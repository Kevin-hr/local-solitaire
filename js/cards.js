(function (app) {
  "use strict";

  const SUITS = ["hearts", "diamonds", "clubs", "spades"];
  const SUIT_SYMBOLS = { hearts: "♥", diamonds: "♦", clubs: "♣", spades: "♠" };
  const RANK_LABELS = { 1: "A", 11: "J", 12: "Q", 13: "K" };

  function createDeck() {
    const deck = [];
    for (const suit of SUITS) {
      for (let rank = 1; rank <= 13; rank += 1) {
        deck.push({
          id: `${suit.charAt(0).toUpperCase()}-${rank}`,
          suit,
          rank,
          color: suit === "hearts" || suit === "diamonds" ? "red" : "black",
          faceUp: false
        });
      }
    }
    return deck;
  }

  function shuffleDeck(deck, randomFn) {
    const result = deck.map((card) => ({ ...card }));
    const random = randomFn || Math.random;
    for (let index = result.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(random() * (index + 1));
      [result[index], result[swapIndex]] = [result[swapIndex], result[index]];
    }
    return result;
  }

  function dealCards(deck) {
    const cards = deck.map((card) => ({ ...card, faceUp: false }));
    const tableau = Array.from({ length: 7 }, () => []);
    for (let column = 0; column < 7; column += 1) {
      for (let row = 0; row <= column; row += 1) {
        const card = cards.pop();
        card.faceUp = row === column;
        tableau[column].push(card);
      }
    }
    return { stock: cards, tableau };
  }

  function rankLabel(rank) {
    return RANK_LABELS[rank] || String(rank);
  }

  app.cards = { SUITS, SUIT_SYMBOLS, createDeck, shuffleDeck, dealCards, rankLabel };
})(window.Solitaire = window.Solitaire || {});
