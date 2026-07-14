(function (app) {
  "use strict";

  const SAVE_KEY = "local-solitaire-save-v1";
  const SETTINGS_KEY = "local-solitaire-settings-v1";
  const DEFAULT_SETTINGS = {
    sound: true,
    autoFoundation: false,
    autoSave: true,
    unlimitedStock: true,
    showTimer: true,
    showMoves: true
  };

  function safeParse(value) {
    try { return JSON.parse(value); } catch (_error) { return null; }
  }

  function saveGame(gameState) {
    try {
      localStorage.setItem(SAVE_KEY, JSON.stringify({ version: 1, savedAt: Date.now(), gameState }));
      return true;
    } catch (_error) { return false; }
  }

  function loadGame() {
    try {
      const raw = localStorage.getItem(SAVE_KEY);
      if (!raw) return null;
      const save = safeParse(raw);
      if (!save || save.version !== 1 || !save.gameState) throw new Error("Invalid save");
      return save.gameState;
    } catch (_error) {
      clearGame();
      return null;
    }
  }

  function clearGame() {
    try { localStorage.removeItem(SAVE_KEY); } catch (_error) { /* localStorage unavailable */ }
  }

  function saveSettings(settings) {
    try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings)); } catch (_error) { /* ignore */ }
  }

  function loadSettings() {
    try {
      const saved = safeParse(localStorage.getItem(SETTINGS_KEY));
      return { ...DEFAULT_SETTINGS, ...(saved || {}) };
    } catch (_error) { return { ...DEFAULT_SETTINGS }; }
  }

  app.storage = { SAVE_KEY, DEFAULT_SETTINGS, saveGame, loadGame, clearGame, saveSettings, loadSettings };
})(window.Solitaire = window.Solitaire || {});
