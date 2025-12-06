<template>
  <div class="page">
    <header class="page-header">
      <h1>Memorama de pictogramas</h1>
      <div class="actions">
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
        <div class="status" v-if="matchedPairs === targetPairs">¡Ganaste!</div>
      </div>
    </section>
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
      allPictograms: [],
      selectedTopic: '',
      topics: [
        { value: 'animals', label: 'Animales', keywords: ['animal', 'perro', 'gato', 'pez', 'pajaro', 'caballo'] },
        { value: 'colors', label: 'Colores', keywords: ['rojo', 'azul', 'verde', 'amarillo'] },
        { value: 'professions', label: 'Profesiones', keywords: ['doctor', 'profesor', 'bombero', 'policia'] },
        { value: 'daily', label: 'Rutinas', keywords: ['comer', 'dormir', 'cepillar', 'banar', 'lavar'] }
      ]
    }
  },
  created() {
    this.restartGame()
  },
  methods: {
    async restartGame() {
      this.loading = true
      this.error = ''
      this.cards = []
      this.flipped = []
      this.matchedPairs = 0
      try {
        if (!this.allPictograms.length) {
          this.allPictograms = await fetchPictograms()
        }
        const source = this.filteredByTopic()
        const selection = [...source].sort(() => 0.5 - Math.random()).slice(0, this.targetPairs)
        const paired = [...selection, ...selection]
          .map((pic, index) => ({
            id: `${pic.path}-${index}-${Math.random()}`,
            key: pic.path,
            keyword: pic.keywords?.[0]?.keyword || 'pictograma',
            url: fetchPictogram(pic.path),
            flipped: false,
            matched: false
          }))
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
      } else {
        c1.flipped = false
        c2.flipped = false
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
