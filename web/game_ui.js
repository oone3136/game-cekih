/**
 * GAME UI JAVASCRIPT: REMI CEKIH POS RONDA
 * Menangani:
 * - Rendering kartu dengan kembang otentik (♠, ♥, ♣, ♦)
 * - Timer 10 Detik per pemain dengan auto-buang (Joker dilindungi)
 * - Fitur Gusar-Geser Kartu di tangan (Drag & Drop Reordering)
 * - Tombol susun kartu cepat (Susun Kembang & Susun Angka)
 * - Sintesis efek suara (Web Audio API)
 * - Partikel animasi kemenangan & Toko Custom Skin
 */

// ============================================================
// 1. SOUND SYNTHESIZER (Web Audio API - Zero External Files)
// ============================================================
class SoundFX {
  constructor() {
    this.ctx = null;
  }

  init() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playCardSlide() {
    this.init();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'triangle';
    osc.frequency.setValueAtTime(320, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(120, this.ctx.currentTime + 0.12);
    gain.gain.setValueAtTime(0.15, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.12);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.12);
  }

  playCardSnap() {
    this.init();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(180, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(40, this.ctx.currentTime + 0.1);
    gain.gain.setValueAtTime(0.3, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.1);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.1);
  }

  playTick() {
    this.init();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(750, this.ctx.currentTime);
    gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + 0.05);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.05);
  }

  playThrowSound() {
    this.init();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(380, this.ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(70, this.ctx.currentTime + 0.3);
    gain.gain.setValueAtTime(0.25, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.3);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.3);
  }

  playHitSound(type = 'batu_ronda') {
    this.init();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    if (type === 'siram_air') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(260, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(60, this.ctx.currentTime + 0.3);
    } else {
      osc.type = 'square';
      osc.frequency.setValueAtTime(140, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(30, this.ctx.currentTime + 0.18);
    }
    gain.gain.setValueAtTime(0.35, this.ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + 0.2);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start();
    osc.stop(this.ctx.currentTime + 0.2);
  }

  playVictory() {
    this.init();
    const notes = [261.63, 329.63, 392.00, 523.25]; // C E G C chord
    notes.forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0.15, this.ctx.currentTime + idx * 0.1);
      gain.gain.exponentialRampToValueAtTime(0.01, this.ctx.currentTime + idx * 0.1 + 0.5);
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      osc.start(this.ctx.currentTime + idx * 0.1);
      osc.stop(this.ctx.currentTime + idx * 0.1 + 0.5);
    });
  }
}

const sounds = new SoundFX();

// ============================================================
// 2. CANVAS PARTICLE EFFECTS (VICTORY ANIMATIONS)
// ============================================================
const canvas = document.getElementById('fx-canvas');
const ctx = canvas.getContext('2d');
let particles = [];

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

function triggerVictoryFX(fxType) {
  particles = [];
  const count = (fxType === 'gold_rain') ? 120 : 150;
  for (let i = 0; i < count; i++) {
    particles.push({
      x: fxType === 'gold_rain' ? Math.random() * canvas.width : canvas.width / 2,
      y: fxType === 'gold_rain' ? -20 : canvas.height / 2,
      vx: (Math.random() - 0.5) * 16,
      vy: fxType === 'gold_rain' ? Math.random() * 6 + 3 : (Math.random() - 0.7) * 18,
      size: fxType === 'gold_rain' ? 14 : Math.random() * 8 + 4,
      color: fxType === 'gold_rain' ? '#f5b041' : `hsl(${Math.random() * 360}, 90%, 60%)`,
      type: fxType,
      life: 1.0,
      decay: Math.random() * 0.015 + 0.008
    });
  }
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (particles.length > 0) {
    particles.forEach((p, idx) => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += (p.type === 'gold_rain' ? 0.15 : 0.4);
      p.life -= p.decay;

      ctx.save();
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.fillStyle = p.color;

      if (p.type === 'gold_rain') {
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size / 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = '#fff';
        ctx.stroke();
      } else {
        ctx.fillRect(p.x, p.y, p.size, p.size);
      }
      ctx.restore();

      if (p.life <= 0) particles.splice(idx, 1);
    });
  }
  requestAnimationFrame(animateParticles);
}
animateParticles();

// ============================================================
// 3. GAME STATE & UI CONTROLLER
// ============================================================
let gameState = null;
let selectedHandCardIndices = [];
let selectedDiscardDepth = null;
let isBotProcessing = false;
let draggedCardIndex = null;

// Timer constants & variables (30 Detik)
const TURN_DURATION = 30;
let turnTimerInterval = null;
let turnRemainingSeconds = TURN_DURATION;
let lastTimerSecondFloored = TURN_DURATION;
let currentTimerTarget = null; // 'HUMAN' atau index bot

const SUIT_ICONS = {
  "SEKOP": "♠",
  "HATI": "♥",
  "KERITING": "♣",
  "TAHU": "♦"
};

async function fetchGameState() {
  try {
    const res = await fetch('/api/state');
    if (!res.ok) return;
    const newState = await res.json();
    
    // Sinkronisasi urutan custom kartu tangan jika pemain sudah gusar-geser kartu
    syncHandCardOrder(newState);

    gameState = newState;
    renderUI();

    // Manajemen Timer Giliran (10 Detik)
    manageTurnTimer();

    // Jalankan bot otomatis jika bukan giliran pemain
    if (!gameState.is_human_turn && gameState.turn_step !== 'ROUND_OVER' && !isBotProcessing) {
      triggerBotStep();
    }
  } catch (err) {
    console.error("Gagal mengambil state game:", err);
  }
}

// Menjaga susunan urutan kartu yang sudah digeser pemain agar tidak loncat kembali
function syncHandCardOrder(newState) {
  if (!gameState || !gameState.human_hand || !newState.human_hand) return;
  if (gameState.human_hand.length !== newState.human_hand.length) return;

  const currentIds = gameState.human_hand.map(c => `${c.rank}_${c.suit}_${c.is_joker}`);
  const newMap = new Map();
  newState.human_hand.forEach(c => {
    newMap.set(`${c.rank}_${c.suit}_${c.is_joker}`, c);
  });

  const reordered = [];
  currentIds.forEach(id => {
    if (newMap.has(id)) {
      reordered.push(newMap.get(id));
      newMap.delete(id);
    }
  });

  // Tambahkan kartu baru yang mungkin belum ada di tangan sebelumnya
  newMap.forEach(c => reordered.push(c));
  if (reordered.length === newState.human_hand.length) {
    newState.human_hand = reordered;
  }
}

function renderUI() {
  if (!gameState) return;

  // Header info
  document.getElementById('round-indicator').textContent = `Putaran ${gameState.round_number}`;
  document.getElementById('deck-counter').textContent = `Kocokan: ${gameState.deck_remaining} kartu`;
  
  const wildEl = document.getElementById('wild-indicator');
  if (gameState.wild_indicator) {
    wildEl.style.display = 'inline-block';
    wildEl.textContent = gameState.wild_indicator;
  } else if (gameState.wild_rank_name) {
    wildEl.style.display = 'inline-block';
    wildEl.textContent = `★ JOKER GANTUNG: [${gameState.wild_rank_name}] (3 Aktif, 1 Mati)`;
  } else {
    wildEl.style.display = 'inline-block';
    wildEl.textContent = `★ JOKER ASLI: 2 Fisik`;
  }

  const modeLabelEl = document.getElementById('mode-joker-label');
  if (modeLabelEl && gameState.joker_mode_name) {
    modeLabelEl.textContent = gameState.joker_mode_name;
  }

  // Announcer Banner
  document.getElementById('action-banner').textContent = gameState.last_message;

  // Render Bot Seats (P1: Pak RT, P2: Pak RW, P3: Pak Sukardi)
  gameState.players.forEach(p => {
    if (p.index === 0) {
      document.getElementById('score-p0').textContent = `Skor: ${p.score} pt`;
    } else {
      const scoreEl = document.getElementById(`score-p${p.index}`);
      const countEl = document.getElementById(`count-p${p.index}`);
      const seatEl = document.getElementById(`seat-player-${p.index}`);
      if (scoreEl) scoreEl.textContent = `${p.score} pt`;
      if (countEl) countEl.textContent = `${p.card_count} kartu`;
      if (seatEl) {
        seatEl.classList.toggle('active-turn', p.is_current);
      }

      // Render Kartu Terbuka Bot (Hasil Serok)
      const meldsContainer = document.getElementById(`open-melds-p${p.index}`);
      if (meldsContainer) {
        meldsContainer.innerHTML = '';
        if (p.open_melds && p.open_melds.length > 0) {
          p.open_melds.forEach(meld => {
            const group = document.createElement('div');
            group.className = 'mini-meld-group';
            meld.forEach(card => {
              const mini = document.createElement('div');
              const isRed = (card.suit === 'HATI' || card.suit === 'TAHU');
              mini.className = `mini-card ${isRed ? 'is-red' : ''}`;
              mini.textContent = `${card.rank_name}${card.suit_symbol || ''}`;
              group.appendChild(mini);
            });
            meldsContainer.appendChild(group);
          });
        }
      }
    }
  });

  // Render Kartu Terbuka Manusia (Hasil Serok)
  const humanMeldsBox = document.getElementById('human-open-melds-box');
  const humanMeldsRow = document.getElementById('human-open-melds-row');
  if (humanMeldsBox && humanMeldsRow) {
    if (gameState.human_open_melds && gameState.human_open_melds.length > 0) {
      humanMeldsBox.style.display = 'flex';
      humanMeldsRow.innerHTML = '';
      gameState.human_open_melds.forEach(meld => {
        const cluster = document.createElement('div');
        cluster.className = 'open-meld-cluster';
        meld.forEach(card => {
          cluster.appendChild(createCardElement(card));
        });
        humanMeldsRow.appendChild(cluster);
      });
    } else {
      humanMeldsBox.style.display = 'none';
      humanMeldsRow.innerHTML = '';
    }
  }

  // Render Discard Pile
  renderDiscardPile();

  // Render Human Hand
  renderHumanHand();

  // Update Action Buttons
  updateControls();

  // Cek Modal Round Over
  if (gameState.turn_step === 'ROUND_OVER' && gameState.round_result) {
    stopTurnTimer();
    showRoundResultModal(gameState.round_result);
  }
}

// ============================================================
// 4. SISTEM TIMER DUA FASE (30s AMBIL + 30s BUANG) & AUTO-DISCARD
// ============================================================
function manageTurnTimer() {
  if (!gameState || gameState.turn_step === 'ROUND_OVER') {
    stopTurnTimer();
    return;
  }

  const isHuman = gameState.is_human_turn;
  const step = gameState.turn_step; // 'DRAW', 'DISCARD', 'CHOICE_TUTUP'
  const targetId = isHuman ? `HUMAN_${step}` : `BOT_${gameState.current_player_idx}_${step}`;

  // Update label fase waktu
  const labelEl = document.getElementById('timer-step-label');
  if (labelEl) {
    labelEl.textContent = (step === 'DRAW') ? 'Ambil' : 'Buang';
  }

  if (currentTimerTarget === targetId) {
    return; // Timer sudah berjalan untuk fase ini
  }

  stopTurnTimer();
  currentTimerTarget = targetId;
  turnRemainingSeconds = TURN_DURATION;
  lastTimerSecondFloored = TURN_DURATION;

  updateTimerDisplay(isHuman, turnRemainingSeconds);

  turnTimerInterval = setInterval(() => {
    turnRemainingSeconds -= 0.1;
    if (turnRemainingSeconds <= 0) {
      turnRemainingSeconds = 0;
      updateTimerDisplay(isHuman, 0);
      stopTurnTimer();

      if (isHuman) {
        handleHumanTimeout();
      }
    } else {
      updateTimerDisplay(isHuman, turnRemainingSeconds);

      // Suara detak jam saat kritis (<= 5 detik)
      const currentFloor = Math.ceil(turnRemainingSeconds);
      if (currentFloor <= 5 && currentFloor < lastTimerSecondFloored) {
        sounds.playTick();
        lastTimerSecondFloored = currentFloor;
      }
    }
  }, 100);
}

function stopTurnTimer() {
  if (turnTimerInterval) {
    clearInterval(turnTimerInterval);
    turnTimerInterval = null;
  }
  currentTimerTarget = null;
}

function updateTimerDisplay(isHuman, seconds) {
  const displaySec = Math.ceil(seconds);
  const percent = Math.max(0, Math.min(100, (seconds / TURN_DURATION) * 100));

  if (isHuman) {
    const valEl = document.getElementById('timer-val-p0');
    const barEl = document.getElementById('timer-progress-p0');
    const textEl = document.querySelector('.human-timer-box .timer-text');

    if (valEl) valEl.textContent = displaySec;
    if (barEl) {
      barEl.style.width = `${percent}%`;
      barEl.classList.toggle('is-critical', displaySec <= 5);
    }
    if (textEl) {
      textEl.classList.toggle('is-critical', displaySec <= 5);
    }
  } else {
    // Tampilkan timer pada bot yang sedang aktif
    const botIdx = gameState.current_player_idx;
    const botValEl = document.getElementById(`timer-val-p${botIdx}`);
    if (botValEl) {
      botValEl.textContent = displaySec;
    }
  }
}

// Timeout handler untuk pemain manusia (Dua Fase 30 Detik)
async function handleHumanTimeout() {
  if (!gameState || !gameState.is_human_turn) return;

  // 1. Jika waktu habis saat tahap DRAW: otomatis tarik kocokan -> timer di-reset ke 30s untuk tahap DISCARD!
  if (gameState.turn_step === 'DRAW') {
    document.getElementById('action-banner').textContent = "⏰ Waktu ambil kartu (30s) habis! Otomatis menarik kocokan...";
    sounds.playCardSlide();
    try {
      const res = await fetch('/api/draw_deck', { method: 'POST' });
      if (res.ok) {
        selectedHandCardIndices = [];
        selectedDiscardDepth = null;
        await fetchGameState(); // State berpindah ke DISCARD, memulai 30 detik baru!
      }
    } catch (err) {
      console.error(err);
    }
    return;
  }

  // 2. Jika tahap CHOICE_TUTUP: otomatis Tutup
  if (gameState.turn_step === 'CHOICE_TUTUP') {
    document.getElementById('btn-confirm-tutup').click();
    return;
  }

  // 3. Jika waktu habis saat tahap DISCARD: otomatis buang 1 kartu BUKAN JOKER
  if (gameState.turn_step === 'DISCARD') {
    const nonJokers = gameState.human_hand.filter(c => !c.is_joker);
    let chosenCard = nonJokers.length > 0 ? nonJokers[nonJokers.length - 1] : gameState.human_hand[0];

    if (chosenCard) {
      try {
        const res = await fetch('/api/discard', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ card_index: chosenCard.index })
        });
        if (res.ok) {
          sounds.playCardSnap();
          document.getElementById('action-banner').textContent = `⏰ Waktu buang kartu (30s) habis: Kartu [${chosenCard.display}] dibuang otomatis. (Joker terlindungi!)`;
          selectedHandCardIndices = [];
          await fetchGameState();
        }
      } catch (err) {
        console.error(err);
      }
    }
  }
}

// ============================================================
// 5. RENDER KARTU TANGAN & DRAG-AND-DROP (GUSAR-GESER)
// ============================================================
function renderHumanHand() {
  const container = document.getElementById('human-hand-cards');
  container.innerHTML = '';

  if (!gameState.human_hand || gameState.human_hand.length === 0) return;

  gameState.human_hand.forEach((cardData, posIdx) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'hand-card-wrapper';
    wrapper.setAttribute('draggable', 'true');
    wrapper.dataset.position = posIdx;

    const isSelected = selectedHandCardIndices.includes(cardData.index);
    if (isSelected) wrapper.classList.add('selected');

    const cardEl = createCardElement(cardData);
    wrapper.appendChild(cardEl);

    // Click handler untuk pilih buang / serok
    wrapper.addEventListener('click', (e) => {
      handleHandCardClick(cardData.index);
    });

    // DRAG AND DROP EVENTS (Gusar-Geser Kartu di Meja)
    wrapper.addEventListener('dragstart', (e) => {
      draggedCardIndex = posIdx;
      wrapper.classList.add('dragging');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', posIdx);
    });

    wrapper.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      wrapper.classList.add('drag-over');
    });

    wrapper.addEventListener('dragleave', () => {
      wrapper.classList.remove('drag-over');
    });

    wrapper.addEventListener('drop', (e) => {
      e.preventDefault();
      wrapper.classList.remove('drag-over');
      const targetPos = posIdx;
      if (draggedCardIndex !== null && draggedCardIndex !== targetPos) {
        // Pindahkan posisi kartu dalam array human_hand
        const movedCard = gameState.human_hand.splice(draggedCardIndex, 1)[0];
        gameState.human_hand.splice(targetPos, 0, movedCard);
        sounds.playCardSlide();
        renderHumanHand();
      }
    });

    wrapper.addEventListener('dragend', () => {
      wrapper.classList.remove('dragging');
      document.querySelectorAll('.hand-card-wrapper').forEach(el => el.classList.remove('drag-over'));
      draggedCardIndex = null;
    });

    container.appendChild(wrapper);
  });
}

function handleHandCardClick(cardIndex) {
  sounds.playCardSlide();

  if (gameState.turn_step === 'DRAW') {
    // Mode Serok: Pilih minimal 2 kartu (bisa 2, 3, 4, 5, 6 kartu untuk menyambung)
    const pos = selectedHandCardIndices.indexOf(cardIndex);
    if (pos > -1) {
      selectedHandCardIndices.splice(pos, 1);
    } else {
      selectedHandCardIndices.push(cardIndex);
    }
  } else if (gameState.turn_step === 'DISCARD') {
    // Mode Buang: Pilih 1 kartu
    selectedHandCardIndices = [cardIndex];
  }

  renderHumanHand();
  updateControls();
}

// Susun Kartu Cepat: Berdasarkan Kembang
document.getElementById('btn-sort-suit').addEventListener('click', () => {
  if (!gameState || !gameState.human_hand) return;
  const suitOrder = { "SEKOP": 0, "HATI": 1, "KERITING": 2, "TAHU": 3 };
  gameState.human_hand.sort((a, b) => {
    if (a.is_joker !== b.is_joker) return a.is_joker ? -1 : 1;
    const sA = suitOrder[a.suit] ?? 4;
    const sB = suitOrder[b.suit] ?? 4;
    if (sA !== sB) return sA - sB;
    return a.rank - b.rank;
  });
  sounds.playCardSlide();
  renderHumanHand();
});

// Susun Kartu Cepat: Berdasarkan Angka
document.getElementById('btn-sort-rank').addEventListener('click', () => {
  if (!gameState || !gameState.human_hand) return;
  gameState.human_hand.sort((a, b) => {
    if (a.is_joker !== b.is_joker) return a.is_joker ? -1 : 1;
    if (a.rank !== b.rank) return a.rank - b.rank;
    const suitOrder = { "SEKOP": 0, "HATI": 1, "KERITING": 2, "TAHU": 3 };
    return (suitOrder[a.suit] ?? 4) - (suitOrder[b.suit] ?? 4);
  });
  sounds.playCardSlide();
  renderHumanHand();
});

// ============================================================
// 6. RENDER DISCARD PILE & SEROK BUANGAN
// ============================================================
function renderDiscardPile() {
  const container = document.getElementById('discard-pile-row');
  container.innerHTML = '';

  if (!gameState.discard_pile || gameState.discard_pile.length === 0) {
    container.innerHTML = '<div style="color: #a0aec0; font-size: 13px; padding: 20px;">(Tumpukan buangan masih kosong)</div>';
    return;
  }

  gameState.discard_pile.forEach((cardData, idx) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'discard-card-wrapper';
    if (cardData.is_dead) {
      wrapper.classList.add('is-dead-card');
    } else if (!cardData.is_valid_depth) {
      wrapper.classList.add('is-hangus');
    }
    if (selectedDiscardDepth === idx) wrapper.classList.add('selected');

    // Label tag kedalaman
    const tag = document.createElement('div');
    tag.className = 'discard-order-tag';
    if (cardData.is_dead) {
      tag.textContent = `[💀 KARTU MATI]`;
    } else if (!cardData.is_valid_depth) {
      tag.textContent = `[Hangus #${idx + 1}]`;
    } else {
      tag.textContent = `#${idx + 1} (${cardData.discarded_by_name})`;
    }
    wrapper.appendChild(tag);

    // Kartu visual
    const cardEl = createCardElement(cardData);
    wrapper.appendChild(cardEl);

    // Interaksi klik untuk serok
    wrapper.addEventListener('click', () => {
      if (!gameState.is_human_turn || gameState.turn_step !== 'DRAW') return;
      if (cardData.is_dead) {
        alert("Kartu pembuka Joker Gantung adalah KARTU MATI dan dilarang diserok!");
        return;
      }
      if (!cardData.is_valid_depth) {
        alert("Kartu ini sudah hangus (lebih dari 7 langkah ke belakang)!");
        return;
      }

      if (selectedDiscardDepth === idx) {
        selectedDiscardDepth = null;
      } else {
        selectedDiscardDepth = idx;
        sounds.playCardSlide();
      }
      renderDiscardPile();
      updateControls();
    });

    container.appendChild(wrapper);
  });
}

function createCardElement(cardData) {
  const card = document.createElement('div');
  card.className = 'card';

  if (cardData.is_joker) {
    card.classList.add('is-joker');
    const isPhysical = (cardData.rank === 99 || cardData.rank_name === 'JKR');
    const rankLabel = isPhysical ? '★' : `★${cardData.rank_name}`;
    const suitLabel = isPhysical ? 'JKR' : (SUIT_ICONS[cardData.suit] || 'JKR');
    const centerIcon = isPhysical ? '🃏' : '★';
    card.innerHTML = `
      <div class="card-corner">
        <span class="card-rank">${rankLabel}</span>
        <span class="card-suit">${suitLabel}</span>
      </div>
      <div class="card-center-suit">${centerIcon}</div>
      <div class="card-corner card-corner-bottom">
        <span class="card-rank">${rankLabel}</span>
        <span class="card-suit">${suitLabel}</span>
      </div>
    `;
    return card;
  }

  const isRed = (cardData.suit === 'HATI' || cardData.suit === 'TAHU');
  card.classList.add(isRed ? 'is-red' : 'is-black');
  const icon = SUIT_ICONS[cardData.suit] || '?';

  card.innerHTML = `
    <div class="card-corner">
      <span class="card-rank">${cardData.rank_name}</span>
      <span class="card-suit">${icon}</span>
    </div>
    <div class="card-center-suit">${icon}</div>
    <div class="card-corner card-corner-bottom">
      <span class="card-rank">${cardData.rank_name}</span>
      <span class="card-suit">${icon}</span>
    </div>
  `;
  return card;
}

function updateControls() {
  const btnDraw = document.getElementById('btn-draw-deck');
  const btnScoop = document.getElementById('btn-scoop');
  const btnDiscard = document.getElementById('btn-discard');
  const btnTutup = document.getElementById('btn-tutup-ready');

  const isHumanTurn = gameState.is_human_turn;
  const step = gameState.turn_step;

  btnDraw.disabled = !(isHumanTurn && step === 'DRAW');

  const canScoop = isHumanTurn && step === 'DRAW' && selectedDiscardDepth !== null && selectedHandCardIndices.length >= 2;
  btnScoop.disabled = !canScoop;

  const canDiscard = isHumanTurn && step === 'DISCARD' && selectedHandCardIndices.length === 1;
  btnDiscard.disabled = !canDiscard;

  if (isHumanTurn && step === 'CHOICE_TUTUP') {
    btnTutup.style.display = 'inline-block';
    showTutupModal();
  } else {
    btnTutup.style.display = 'none';
  }
}

// ============================================================
// 7. BOT STEP AUTOMATION
// ============================================================
async function triggerBotStep() {
  if (isBotProcessing) return;
  isBotProcessing = true;

  setTimeout(async () => {
    try {
      const res = await fetch('/api/bot_step', { method: 'POST' });
      if (res.ok) {
        sounds.playCardSnap();
        await fetchGameState();
      }
    } catch (err) {
      console.error("Error bot step:", err);
    } finally {
      isBotProcessing = false;
    }
  }, 1400);
}

// ============================================================
// 8. TOMBOL AKSI UTAMA (DRAW, SCOOP, DISCARD)
// ============================================================

// Tarik Kocokan
document.getElementById('btn-draw-deck').addEventListener('click', async () => {
  sounds.playCardSlide();
  try {
    const res = await fetch('/api/draw_deck', { method: 'POST' });
    if (res.ok) {
      selectedHandCardIndices = [];
      selectedDiscardDepth = null;
      await fetchGameState();
    }
  } catch (err) {
    console.error(err);
  }
});
document.getElementById('deck-clickable').addEventListener('click', () => {
  if (gameState && gameState.is_human_turn && gameState.turn_step === 'DRAW') {
    document.getElementById('btn-draw-deck').click();
  }
});

// Serok Buangan
document.getElementById('btn-scoop').addEventListener('click', async () => {
  if (selectedDiscardDepth === null || selectedHandCardIndices.length < 2) return;
  try {
    const res = await fetch('/api/scoop_discard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        depth: selectedDiscardDepth,
        pair_indices: selectedHandCardIndices
      })
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Gagal serok buangan!");
    } else {
      sounds.playCardSnap();
      selectedDiscardDepth = null;
      selectedHandCardIndices = [];
      await fetchGameState();
    }
  } catch (err) {
    console.error(err);
  }
});

// Buang Kartu
document.getElementById('btn-discard').addEventListener('click', async () => {
  if (selectedHandCardIndices.length !== 1) return;
  const targetCard = gameState.human_hand.find(c => c.index === selectedHandCardIndices[0]);

  if (targetCard && targetCard.is_joker) {
    alert("⚠️ DILARANG MEMBUANG JOKER! Joker tidak boleh dibuang karena dendanya -250 poin!");
    return;
  }

  try {
    const res = await fetch('/api/discard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card_index: selectedHandCardIndices[0] })
    });
    const data = await res.json();
    if (!res.ok) {
      alert(data.error || "Gagal buang kartu!");
    } else {
      sounds.playCardSnap();
      selectedHandCardIndices = [];
      await fetchGameState();
    }
  } catch (err) {
    console.error(err);
  }
});

// Gertak Cekih! (Lempar batu/air/sandal ke pemain sebelum kita: Pak Sukardi)
const btnTaunt = document.getElementById('btn-taunt-cekih');
if (btnTaunt) {
  btnTaunt.addEventListener('click', async () => {
    btnTaunt.disabled = true;
    try {
      const res = await fetch('/api/taunt', { method: 'POST' });
      if (!res.ok) {
        btnTaunt.disabled = false;
        return;
      }
      const data = await res.json();
      sounds.playThrowSound();

      // Animasi Terbang Proyektil Lemparan
      const proj = document.getElementById('flying-projectile');
      const humanSeat = document.getElementById('seat-player-0');
      const targetSeat = document.getElementById('seat-player-3'); // Pak Sukardi (pemain sebelum kita)
      const bubbleTarget = document.getElementById('bubble-p3');

      if (proj && humanSeat && targetSeat) {
        const fromRect = humanSeat.getBoundingClientRect();
        const toRect = targetSeat.getBoundingClientRect();

        proj.textContent = data.icon || '🪨';
        proj.style.display = 'block';
        proj.style.opacity = '1';
        proj.style.left = `${fromRect.left + fromRect.width / 2}px`;
        proj.style.top = `${fromRect.top + 20}px`;
        proj.style.transform = 'translate(-50%, -50%) scale(1)';

        // Force reflow
        proj.getBoundingClientRect();

        const dx = (toRect.left + toRect.width / 2) - (fromRect.left + fromRect.width / 2);
        const dy = (toRect.top + toRect.height / 2) - (fromRect.top + 20);

        proj.style.transform = `translate(calc(-50% + ${dx}px), calc(-50% + ${dy}px)) scale(1.4) rotate(360deg)`;

        setTimeout(() => {
          proj.style.opacity = '0';
          setTimeout(() => { proj.style.display = 'none'; }, 300);

          // Efek Kena Hantam (Hit Sound & Shake)
          sounds.playHitSound(data.taunt_type);
          targetSeat.classList.add('shake-hit');
          setTimeout(() => { targetSeat.classList.remove('shake-hit'); }, 600);

          // Dialog Respon Bot
          if (bubbleTarget) {
            bubbleTarget.textContent = data.bot_reply;
            bubbleTarget.style.opacity = '1';
            bubbleTarget.style.transform = 'translateY(0) scale(1.1)';
            setTimeout(() => {
              bubbleTarget.style.opacity = '0';
              bubbleTarget.style.transform = 'translateY(5px) scale(1)';
            }, 3500);
          }

          if (data.state) {
            renderState(data.state);
          }
        }, 600);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setTimeout(() => { btnTaunt.disabled = false; }, 2000);
    }
  });
}

// ============================================================
// 9. MODAL TUTUP / CEKIH SEKARANG VS GANTUNG
// ============================================================
let chosenTutupOptIndex = 0;

function showTutupModal() {
  const container = document.getElementById('tutup-options-container');
  container.innerHTML = '';

  if (!gameState.tutup_options || gameState.tutup_options.length === 0) return;

  gameState.tutup_options.forEach((opt, idx) => {
    const div = document.createElement('div');
    div.style.cssText = 'background: rgba(255,255,255,0.08); padding: 12px; border-radius: 10px; margin-bottom: 10px; cursor: pointer; border: 2px solid transparent;';
    if (idx === chosenTutupOptIndex) div.style.borderColor = '#f5b041';

    div.innerHTML = `
      <div style="font-weight: 700; color: #f5b041; font-size: 15px;">
        Opsi #${idx + 1}: Tutup dengan Kartu Kunci [${opt.closing_card.display}] (+${opt.close_value} Poin)
      </div>
      <div style="font-size: 12px; color: #cbd5e0; margin-top: 4px;">
        Rangkaian Kombinasi: ${opt.melds_summary.join(' & ')}
      </div>
    `;

    div.addEventListener('click', () => {
      chosenTutupOptIndex = idx;
      showTutupModal();
    });
    container.appendChild(div);
  });

  document.getElementById('modal-tutup').classList.add('show');
}

// Konfirmasi Tutup Sekarang
document.getElementById('btn-confirm-tutup').addEventListener('click', async () => {
  document.getElementById('modal-tutup').classList.remove('show');
  sounds.playVictory();
  triggerVictoryFX(gameState.active_skins.victory_fx || 'petasan_ronda');

  try {
    await fetch('/api/action_tutup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'TUTUP', option_index: chosenTutupOptIndex })
    });
    await fetchGameState();
  } catch (err) {
    console.error(err);
  }
});

// Konfirmasi Cekih Gantung
document.getElementById('btn-confirm-gantung').addEventListener('click', async () => {
  document.getElementById('modal-tutup').classList.remove('show');
  try {
    await fetch('/api/action_tutup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'GANTUNG', option_index: 0 })
    });
    await fetchGameState();
  } catch (err) {
    console.error(err);
  }
});

// ============================================================
// 10. MODAL HASIL RONDE (ROUND RECAP)
// ============================================================
function showRoundResultModal(res) {
  const detailsBox = document.getElementById('result-details-list');
  detailsBox.innerHTML = '';
  res.details.forEach(line => {
    const p = document.createElement('div');
    p.textContent = line;
    detailsBox.appendChild(p);
  });

  const tbody = document.getElementById('scoreboard-body');
  tbody.innerHTML = '';
  
  const sortedPlayers = [...gameState.players].sort((a, b) => b.score - a.score);
  sortedPlayers.forEach((p, idx) => {
    const tr = document.createElement('tr');
    const roundPts = res.round_scores ? res.round_scores[p.name] : 0;
    tr.innerHTML = `
      <td>#${idx + 1}</td>
      <td><strong>${p.name}</strong></td>
      <td style="color: ${roundPts >= 0 ? '#48bb78' : '#f56565'}; font-weight: 700;">
        ${roundPts >= 0 ? '+' : ''}${roundPts} pt
      </td>
      <td style="color: #f5b041; font-weight: 800;">${p.score} pt</td>
    `;
    tbody.appendChild(tr);
  });

  document.getElementById('modal-round-result').classList.add('show');
}

document.getElementById('btn-next-round').addEventListener('click', async () => {
  document.getElementById('modal-round-result').classList.remove('show');
  try {
    await fetch('/api/new_round', { method: 'POST' });
    selectedHandCardIndices = [];
    selectedDiscardDepth = null;
    await fetchGameState();
  } catch (err) {
    console.error(err);
  }
});

document.getElementById('btn-new-round').addEventListener('click', async () => {
  if (confirm("Mulai ronde baru dan reset kocokan?")) {
    await fetch('/api/new_round', { method: 'POST' });
    selectedHandCardIndices = [];
    selectedDiscardDepth = null;
    await fetchGameState();
  }
});

// ============================================================
// 11. TOKO SKIN & KUSTOMISASI MODAL
// ============================================================
const modalShop = document.getElementById('modal-shop');
document.getElementById('btn-open-shop').addEventListener('click', async () => {
  await loadShopCatalog();
  modalShop.classList.add('show');
});
document.getElementById('btn-close-shop').addEventListener('click', () => {
  modalShop.classList.remove('show');
});

document.querySelectorAll('.shop-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.shop-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  });
});

async function loadShopCatalog() {
  try {
    const res = await fetch('/api/skins');
    if (!res.ok) return;
    const data = await res.json();
    renderShopItems(data.catalog, data.active);
  } catch (err) {
    console.error(err);
  }
}

function renderShopItems(catalog, activeSkins) {
  // 1. Table Skins
  const tableGrid = document.getElementById('skin-grid-tables');
  tableGrid.innerHTML = '';
  catalog.tables.forEach(item => {
    const card = document.createElement('div');
    const isActive = (activeSkins.table === item.id);
    card.className = `skin-card ${isActive ? 'is-active' : ''}`;
    card.innerHTML = `
      <div class="skin-preview-box" style="background: ${item.preview_color}; border: 2px solid #fff;"></div>
      <div class="skin-name">${item.name}</div>
      <div class="skin-price">${item.price}</div>
      <button class="btn-equip">${isActive ? '✓ Sedang Dipakai' : 'Pakai Skin'}</button>
    `;
    card.querySelector('.btn-equip').addEventListener('click', () => {
      applySkin('table', item.id);
    });
    tableGrid.appendChild(card);
  });

  // 2. Card Back Skins
  const cardGrid = document.getElementById('skin-grid-cards');
  cardGrid.innerHTML = '';
  catalog.card_backs.forEach(item => {
    const card = document.createElement('div');
    const isActive = (activeSkins.card_back === item.id);
    card.className = `skin-card ${isActive ? 'is-active' : ''}`;
    card.innerHTML = `
      <div class="skin-preview-box" style="background: #1a365d; font-size: 24px;">🎴</div>
      <div class="skin-name">${item.name}</div>
      <div class="skin-price">${item.price}</div>
      <button class="btn-equip">${isActive ? '✓ Sedang Dipakai' : 'Pakai Skin'}</button>
    `;
    card.querySelector('.btn-equip').addEventListener('click', () => {
      applySkin('card_back', item.id);
    });
    cardGrid.appendChild(card);
  });

  // 3. Victory FX Skins
  const fxGrid = document.getElementById('skin-grid-fx');
  fxGrid.innerHTML = '';
  catalog.victory_fx.forEach(item => {
    const card = document.createElement('div');
    const isActive = (activeSkins.victory_fx === item.id);
    card.className = `skin-card ${isActive ? 'is-active' : ''}`;
    card.innerHTML = `
      <div class="skin-preview-box" style="background: #2d3748;">${item.preview_icon}</div>
      <div class="skin-name">${item.name}</div>
      <div class="skin-price">${item.price}</div>
      <button class="btn-equip">${isActive ? '✓ Sedang Dipakai' : 'Pakai Skin'}</button>
    `;
    card.querySelector('.btn-equip').addEventListener('click', () => {
      applySkin('victory_fx', item.id);
    });
    fxGrid.appendChild(card);
  });

  // 4. Taunt FX Skins (Lemparan Gertak Cekih)
  const tauntGrid = document.getElementById('skin-grid-taunt');
  if (tauntGrid && catalog.taunt_fx) {
    tauntGrid.innerHTML = '';
    catalog.taunt_fx.forEach(item => {
      const card = document.createElement('div');
      const isActive = (activeSkins.taunt_fx === item.id);
      card.className = `skin-card ${isActive ? 'is-active' : ''}`;
      card.innerHTML = `
        <div class="skin-preview-box" style="background: #2d3748; font-size: 28px;">${item.preview_icon}</div>
        <div class="skin-name">${item.name}</div>
        <div class="skin-price">${item.price}</div>
        <button class="btn-equip">${isActive ? '✓ Sedang Dipakai' : 'Pakai Skin'}</button>
      `;
      card.querySelector('.btn-equip').addEventListener('click', () => {
        applySkin('taunt_fx', item.id);
      });
      tauntGrid.appendChild(card);
    });
  }
}

async function applySkin(category, skinId) {
  try {
    const res = await fetch('/api/skins/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, skin_id: skinId })
    });
    if (res.ok) {
      updateDOMSkins(category, skinId);
      await loadShopCatalog();
    }
  } catch (err) {
    console.error(err);
  }
}

function updateDOMSkins(category, skinId) {
  if (category === 'table') {
    document.body.classList.remove('skin-table-wood', 'skin-table-casino', 'skin-table-cyber');
    if (skinId === 'pos_ronda_wood') document.body.classList.add('skin-table-wood');
    else if (skinId === 'casino_royal_gold') document.body.classList.add('skin-table-casino');
    else if (skinId === 'cyber_neon_night') document.body.classList.add('skin-table-cyber');
  } else if (category === 'card_back') {
    document.body.classList.remove('skin-card-batik', 'skin-card-gold', 'skin-card-red');
    if (skinId === 'batik_ronda') document.body.classList.add('skin-card-batik');
    else if (skinId === 'gold_dragon') document.body.classList.add('skin-card-gold');
    else if (skinId === 'nusantara_red') document.body.classList.add('skin-card-red');
  }
}

// Modal Aturan
document.getElementById('btn-rules').addEventListener('click', () => {
  document.getElementById('modal-rules').classList.add('show');
});
document.getElementById('btn-close-rules').addEventListener('click', () => {
  document.getElementById('modal-rules').classList.remove('show');
});

// Toggle Joker Mode (Gantung vs Asli)
const btnToggleMode = document.getElementById('btn-toggle-joker-mode');
if (btnToggleMode) {
  btnToggleMode.addEventListener('click', async () => {
    if (!gameState) return;
    const currentMode = gameState.joker_mode;
    const nextMode = (currentMode === 'OPEN_CARD_WILD') ? 'TWO_JOKERS' : 'OPEN_CARD_WILD';
    const nextLabel = (nextMode === 'OPEN_CARD_WILD') ? 'Joker Gantung (3 Aktif, 1 Mati)' : 'Joker Asli (2 Fisik)';
    if (confirm(`Ganti aturan ke "${nextLabel}" dan mulai ronde baru?`)) {
      try {
        const res = await fetch('/api/set_joker_mode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: nextMode })
        });
        if (res.ok) {
          selectedHandCardIndices = [];
          selectedDiscardDepth = null;
          await fetchGameState();
        }
      } catch (err) {
        console.error(err);
      }
    }
  });
}

// START
fetchGameState();
