<template>
  <div class="page">
    <header class="page-header">
      <h1>Memorama de pictogramas</h1>
      <div class="actions">
        <button class="icon-circle" @click="openHelp" title="Ayuda">?</button>
        <select v-model="selectedTopic" @change="restartGame">
          <option value="">Tema: aleatorio</option>
          <option v-for="t in topics" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <button class="btn" @click="restartGame">Reiniciar</button>
        <router-link class="btn" to="/chat">Volver al chat</router-link>
      </div>
    </header>

    <section class="card">
      <div v-if="loading" class="status">Cargando pictogramas...</div>
      <div v-else-if="error" class="status error">{{ error }}</div>
      <div v-else>
        <div class="grid">
          <div
            v-for="card in cards"
            :key="card.id"
            class="mem-card"
            :class="{ flipped: card.flipped || card.matched }"
            @click="onCardClick(card)"
          >
            <div class="face front">?</div>
            <div class="face back">
              <img :src="card.url" :alt="card.keyword" />
            </div>
          </div>
        </div>
        <div class="status" v-if="matchedMessage">{{ matchedMessage }}</div>
        <div class="status" v-if="matchedPairs === targetPairs">¡Ganaste!</div>
      </div>
    </section>

    <div v-if="showHelp" class="help-modal">
      <div class="help-content">
        <header class="help-header">
          <h3>Guía rápida</h3>
          <button class="icon-circle" @click="showHelp = false" title="Cerrar">×</button>
        </header>
        <div class="help-body">
          <p>Gira dos cartas para encontrar parejas de pictogramas.</p>
          <ul>
            <li>Elige un tema o deja aleatorio.</li>
            <li>Si no coinciden, se voltean de nuevo.</li>
            <li>Mensaje de acierto te dice qué pictograma encontraste.</li>
            <li>Usa "Reiniciar" para empezar otra partida.</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { fetchPictograms, fetchPictogram } from '@/services/api'

export default {
  name: 'MemoryGameView',
  data() {
    return {
      loading: false,
      error: '',
      cards: [],
      flipped: [],
      matchedPairs: 0,
      targetPairs: 8,
      matchedMessage: '',
      allPictograms: [],
      selectedTopic: '',
      topics: [
        { value: 'animals', label: 'Animales', keywords: ['animal', 'perro', 'gato', 'pez', 'pajaro', 'caballo'] },
        { value: 'colors', label: 'Colores', keywords: ['rojo', 'azul', 'verde', 'amarillo'] },
        { value: 'professions', label: 'Profesiones', keywords: ['doctor', 'profesor', 'bombero', 'policia'] },
        { value: 'daily', label: 'Rutinas', keywords: ['comer', 'dormir', 'cepillar', 'banar', 'lavar'] }
      ],
      showHelp: false
    }
  },
  created() {
    this.restartGame()
  },
  methods: {
    openHelp() {
      this.showHelp = true
    },
    async restartGame() {
      this.loading = true
      this.error = ''
      this.cards = []
      this.flipped = []
      this.matchedPairs = 0
      this.matchedMessage = ''
      try {
        if (!this.allPictograms.length) {
          this.allPictograms = await fetchPictograms()
        }
        const source = this.filteredByTopic()
        const selection = [...source].sort(() => 0.5 - Math.random()).slice(0, this.targetPairs)
        const paired = [...selection, ...selection]
          .map((pic, index) => {
            const kw = pic.keywords?.[0]?.keyword || pic.keyword || 'pictograma'
            return {
              id: `${pic.path}-${index}-${Math.random()}`,
              key: pic.path,
              keyword: kw,
              url: fetchPictogram(pic.path),
              flipped: false,
              matched: false
            }
          })
          .sort(() => 0.5 - Math.random())
        this.cards = paired
      } catch (err) {
        this.error = err?.message || 'No se pudo cargar el juego.'
      } finally {
        this.loading = false
      }
    },
    filteredByTopic() {
      if (!this.selectedTopic) return this.allPictograms
      const topic = this.topics.find((t) => t.value === this.selectedTopic)
      if (!topic) return this.allPictograms
      const keywords = topic.keywords.map((k) => k.toLowerCase())
      return this.allPictograms.filter((p) =>
        (p.keywords || []).some((k) => keywords.includes((k.keyword || '').toLowerCase()))
      )
    },
    onCardClick(card) {
      if (this.loading || card.flipped || card.matched || this.flipped.length === 2) return
      card.flipped = true
      this.flipped.push(card)
      if (this.flipped.length === 2) {
        setTimeout(this.checkMatch, 600)
      }
    },
    checkMatch() {
      const [c1, c2] = this.flipped
      if (!c1 || !c2) return
      if (c1.key === c2.key) {
        c1.matched = true
        c2.matched = true
        this.matchedPairs += 1
        const name = c1.keyword || 'el pictograma'
        this.matchedMessage = `¡Bien! Emparejaste ${name}.`
      } else {
        c1.flipped = false
        c2.flipped = false
        this.matchedMessage = ''
      }
      this.flipped = []
    }
  }
}
</script>

<style scoped>
.page {
  padding: 24px;
  min-height: 100vh;
  background: #f4f6fb;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.icon-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid #d7d9e4;
  background: #fff;
  color: #0a0c19;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  cursor: pointer;
  margin-right: 8px;
  transition: background 0.2s ease, transform 0.15s ease;
}

.icon-circle:hover {
  background: #f3f4f8;
  transform: scale(1.05);
}

.actions select {
  border: 1px solid #d7d9e4;
  border-radius: 8px;
  padding: 6px 8px;
  margin-right: 8px;
}

.card {
  background: #fff;
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
  perspective: 800px;
}

.mem-card {
  border: 1px solid #e6e8f0;
  border-radius: 10px;
  height: 140px;
  position: relative;
  cursor: pointer;
  transform-style: preserve-3d;
  transition: transform 0.4s ease;
  background: transparent;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}

.mem-card.flipped {
  transform: rotateY(180deg);
}

.mem-card .face {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  backface-visibility: hidden;
  border-radius: 10px;
}

.mem-card .front {
  background: #0a0c19;
  color: #00c8b3;
  font-size: 32px;
}

.mem-card .back {
  background: #fff;
  border: 1px solid #d7d9e4;
  transform: rotateY(180deg);
}

.mem-card img {
  max-width: 80px;
  max-height: 80px;
}

.status {
  margin-top: 12px;
  color: #4a4f5c;
}

.help-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.help-content {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  width: min(420px, 90vw);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
}

.help-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.help-body p {
  margin: 4px 0 8px;
}

.help-body ul {
  padding-left: 16px;
  margin: 0 0 8px;
}

.help-body li {
  margin-bottom: 4px;
  font-size: 14px;
}

.status.error {
  color: #c22;
}

.btn {
  background: #0a0c19;
  color: #00c8b3;
  border: none;
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
}
</style>
