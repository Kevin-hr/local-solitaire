(function (app) {
  "use strict";

  const settings = app.storage.loadSettings();
  const game = app.game.createGame({ settings });
  const renderer = app.renderer.createRenderer();
  const statusElement = document.getElementById("status-message");
  let messageTimer = null;
  let audioContext = null;

  function message(text) {
    window.clearTimeout(messageTimer);
    statusElement.textContent = text;
    statusElement.classList.add("show");
    messageTimer = window.setTimeout(() => statusElement.classList.remove("show"), 2300);
  }

  function tone(kind) {
    if (!game.getSettings().sound) return;
    try {
      audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gain = audioContext.createGain();
      const presets = {
        flip: { frequency: 360, duration: .045, type: "triangle", volume: .035 },
        move: { frequency: 520, duration: .06, type: "sine", volume: .04 },
        invalid: { frequency: 145, duration: .09, type: "square", volume: .025 },
        win: { frequency: 660, duration: .28, type: "sine", volume: .05 }
      };
      const preset = presets[kind];
      oscillator.type = preset.type;
      oscillator.frequency.setValueAtTime(preset.frequency, audioContext.currentTime);
      if (kind === "win") oscillator.frequency.exponentialRampToValueAtTime(990, audioContext.currentTime + preset.duration);
      gain.gain.setValueAtTime(preset.volume, audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(.0001, audioContext.currentTime + preset.duration);
      oscillator.connect(gain).connect(audioContext.destination);
      oscillator.start();
      oscillator.stop(audioContext.currentTime + preset.duration);
    } catch (_error) { /* sound is optional when Web Audio is unavailable */ }
  }

  const feedback = { flip: () => tone("flip"), move: () => tone("move"), invalid: () => tone("invalid") };
  app.interactions.createInteractions(game, feedback);

  function saveCurrentGame() {
    app.storage.saveGame(game.exportState());
  }

  function showWin() {
    const state = game.getState();
    document.getElementById("win-time").textContent = renderer.formatTime(game.getElapsedTime());
    document.getElementById("win-moves").textContent = String(state.moves);
    document.getElementById("win-modal").hidden = false;
    tone("win");
  }

  game.subscribe((state, eventName) => {
    renderer.render(state, game.getSettings());
    renderer.updateTimer(game.getElapsedTime());
    if (game.getSettings().autoSave && eventName !== "selection") saveCurrentGame();
    if (eventName === "win") showWin();
  });

  function newGame(force) {
    const state = game.getState();
    if (!force && state.status === "playing" && state.moves > 0 && !window.confirm("当前游戏尚未结束，确定开始新游戏吗？")) return;
    document.getElementById("win-modal").hidden = true;
    game.startNewGame();
    app.storage.saveGame(game.exportState());
    message("新牌局已开始");
  }

  document.getElementById("new-game-btn").addEventListener("click", () => newGame(false));
  document.getElementById("play-again-btn").addEventListener("click", () => newGame(true));
  document.getElementById("undo-btn").addEventListener("click", () => {
    if (game.undoMove()) { tone("move"); message("已撤销上一步"); }
  });
  document.getElementById("hint-btn").addEventListener("click", () => {
    const hint = game.findHint();
    renderer.showHint(hint);
    if (hint) message(hint.message); else message("当前未发现可用移动，请重新开始一局。");
  });

  const settingsModal = document.getElementById("settings-modal");
  const settingInputs = {
    sound: document.getElementById("setting-sound"),
    autoFoundation: document.getElementById("setting-auto-foundation"),
    autoSave: document.getElementById("setting-autosave"),
    unlimitedStock: document.getElementById("setting-unlimited"),
    showTimer: document.getElementById("setting-timer"),
    showMoves: document.getElementById("setting-moves")
  };

  function fillSettings() {
    const current = game.getSettings();
    Object.keys(settingInputs).forEach((key) => { settingInputs[key].checked = Boolean(current[key]); });
  }

  function closeSettings() {
    const next = Object.fromEntries(Object.entries(settingInputs).map(([key, input]) => [key, input.checked]));
    game.setSettings(next);
    app.storage.saveSettings(next);
    if (next.autoSave) saveCurrentGame();
    settingsModal.hidden = true;
  }

  document.getElementById("settings-btn").addEventListener("click", () => { fillSettings(); settingsModal.hidden = false; });
  document.getElementById("settings-done-btn").addEventListener("click", closeSettings);
  settingsModal.querySelectorAll("[data-close-modal='settings']").forEach((element) => element.addEventListener("click", closeSettings));

  window.addEventListener("beforeunload", () => {
    if (game.getSettings().autoSave) saveCurrentGame();
  });
  window.setInterval(() => renderer.updateTimer(game.getElapsedTime()), 1000);

  const saved = app.storage.loadGame();
  const shouldRestore = saved && saved.status !== "won" && window.confirm("发现一局未完成的游戏，是否继续？\n\n选择“取消”将开始新游戏。");
  if (shouldRestore && game.restore(saved)) {
    message("已恢复上一局");
  } else {
    if (saved) app.storage.clearGame();
    game.startNewGame();
  }

  renderer.render(game.getState(), game.getSettings());
  renderer.updateTimer(game.getElapsedTime());
  window.LocalSolitaireGame = game;
})(window.Solitaire = window.Solitaire || {});
