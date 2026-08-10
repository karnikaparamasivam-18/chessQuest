// Subtle game sounds synthesised with the Web Audio API. Generating tones in
// the browser keeps the project free of external audio files and licensing
// concerns while still giving each event its own gentle cue.

let context = null;
let muted = false;

function ensureContext() {
  if (context === null) {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (AudioCtx) context = new AudioCtx();
  }
  // Browsers start the context suspended until a user gesture occurs.
  if (context && context.state === "suspended") context.resume();
  return context;
}

function tone(frequency, duration, { type = "sine", gain = 0.08, delay = 0 } = {}) {
  const ctx = ensureContext();
  if (!ctx) return;

  const oscillator = ctx.createOscillator();
  const envelope = ctx.createGain();
  const start = ctx.currentTime + delay;

  oscillator.type = type;
  oscillator.frequency.value = frequency;
  envelope.gain.setValueAtTime(0.0001, start);
  envelope.gain.exponentialRampToValueAtTime(gain, start + 0.01);
  envelope.gain.exponentialRampToValueAtTime(0.0001, start + duration);

  oscillator.connect(envelope);
  envelope.connect(ctx.destination);
  oscillator.start(start);
  oscillator.stop(start + duration + 0.02);
}

export const sounds = {
  setMuted(value) {
    muted = value;
  },
  isMuted() {
    return muted;
  },
  move() {
    if (muted) return;
    tone(320, 0.12, { type: "triangle", gain: 0.05 });
  },
  capture() {
    if (muted) return;
    tone(200, 0.18, { type: "square", gain: 0.06 });
    tone(150, 0.2, { type: "square", gain: 0.05, delay: 0.04 });
  },
  check() {
    if (muted) return;
    tone(660, 0.16, { type: "sine", gain: 0.07 });
    tone(880, 0.16, { type: "sine", gain: 0.06, delay: 0.08 });
  },
  victory() {
    if (muted) return;
    const notes = [523, 659, 784, 1047];
    notes.forEach((freq, i) =>
      tone(freq, 0.28, { type: "triangle", gain: 0.07, delay: i * 0.12 })
    );
  },
  click() {
    if (muted) return;
    tone(440, 0.06, { type: "sine", gain: 0.03 });
  },
};
