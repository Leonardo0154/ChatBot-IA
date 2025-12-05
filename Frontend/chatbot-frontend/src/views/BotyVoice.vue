<template>
  <div class="voice-wrapper">

    <!-- BOTÓN SALIR -->
    <button class="exit-btn" @click="$emit('exitBoty')">
      ← Salir
    </button>

    <!-- CONTENEDOR PRINCIPAL CENTRADO -->
    <div class="voice-center">

      <!-- CÍRCULO ANIMADO PROFESIONAL -->
      <div class="mic-wrapper">
        <div
          class="mic-circle"
          :style="{ transform: `scale(${1 + intensity * 1.2})` }"
        ></div>
      </div>

      <!-- TEXTO -->
      <p class="voice-text">
        {{ listening ? "Te estoy escuchando..." : "Toca para hablar" }}
      </p>

      <!-- BOTÓN MIC -->
      <button class="mic-btn" @click="toggleListening">
        <img src="/src/assets/micro_icon.png" />
      </button>

    </div>

  </div>
</template>

<script>
export default {
  data() {
    return {
      listening: false,
      intensity: 0,
      audioStream: null
    };
  },

  methods: {
    toggleListening() {
      this.listening = !this.listening;

      if (this.listening) this.startMic();
      else this.stopMic();
    },

    startMic() {
      navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
        this.audioStream = stream;

        const ctx = new AudioContext();
        const src = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;

        src.connect(analyser);

        const data = new Uint8Array(analyser.frequencyBinCount);

        const loop = () => {
          analyser.getByteFrequencyData(data);
          const avg = data.reduce((a, b) => a + b, 0) / data.length;

          this.intensity = avg / 150;

          if (this.listening) requestAnimationFrame(loop);
        };

        loop();
      });
    },

    stopMic() {
      this.intensity = 0;
      if (this.audioStream) {
        this.audioStream.getTracks().forEach(t => t.stop());
      }
    }
  }
};
</script>

<style scoped>
/* ===== WRAPPER GENERAL ===== */
.voice-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

/* ===== BOTÓN SALIR ===== */
.exit-btn {
  position: absolute;
  top: 50%;
  left: 40px;
  background: #00c8b3;
  padding: 10px 18px;
  font-size: 16px;
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: 0.25s;
  box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15);
}

.exit-btn:hover {
  background: #009b88;
  transform: scale(1.05);
}

/* ===== CONTENEDOR CENTRAL ===== */
.voice-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-top: 30%;
  gap: 20px;
}

/* ===== CÍRCULO ANIMADO ===== */
.mic-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.mic-circle {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, #00c8b3, #009b88);
  border-radius: 50%;
  transition: transform 0.12s ease-out;
  animation: breathing 2.4s ease-in-out infinite;
  box-shadow: 0 0 25px rgba(0, 200, 179, 0.7);
}

@keyframes breathing {
  0%   { box-shadow: 0 0 20px #00c8b3; }
  50%  { box-shadow: 0 0 40px #00e6cc; }
  100% { box-shadow: 0 0 20px #00c8b3; }
}

/* ===== TEXTO ===== */
.voice-text {
  margin-top: 10px;
  font-size: 20px;
  color: #444;
  opacity: 0.9;
}

/* ===== BOTÓN MIC ===== */
.mic-btn {
  width: 85px;
  height: 85px;
  border-radius: 50%;
  background: white;
  border: 3px solid #00c8b3;
  cursor: pointer;
  transition: 0.25s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 18px rgba(0, 200, 179, 0.4);
}

.mic-btn img {
  width: 40px;
  height: 40px;
}

.mic-btn:hover {
  transform: scale(1.07);
}
</style>
