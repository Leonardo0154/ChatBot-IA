<template>
  <div class="layout">

    <!-- SIDEBAR -->
    <aside class="sidebar">

      <!-- Perfil -->
      <div class="profile-box">
        <div class="profile-info">
          <img class="profile-img" src="https://i.imgur.com/6VBx3io.png" />
          <div>
            <h3>{{ user?.username || "Invitado" }}</h3>
            <p>{{ roleLabel }}</p>
          </div>
        </div>
        <span class="arrow">›</span>
      </div>

      <!-- Botones -->
      <div class="sidebar-menu">
        <button class="menu-btn" @click="newChat"><img class="icon-img" :src="icons.add" />Nuevo chat</button>
        <router-link
          v-for="item in menuItems"
          :key="item.to"
          class="menu-btn"
          :to="item.to"
        >
          <img class="icon-img" :src="item.icon" />{{ item.label }}
        </router-link>
      </div>

      <!-- Robot abajo -->
      <img class="robot-img" :src="icons.robot" />
    </aside>

    <!-- MAIN -->
    <main class="main">

      <!-- TOPBAR -->
      <header class="topbar">
        <h2>Chat With AI</h2>

        <div class="topbar-actions">
          <label class="toggle">
            <input type="checkbox" v-model="ttsEnabled" />
            <span>Sonido</span>
          </label>
          <button class="logout-btn" @click="logout">Salir</button>
        </div>
      </header>

      <div class="chat-box">

        <!-- Chat -->
        <section class="chat-mode chat-columns">

          <div class="chat-pane">
            <!-- WELCOME -->
            <section class="welcome" v-if="chat.length === 0">
              <img class="welcome-img" :src="icons.welcome" />
              <h1>¡Bienvenido!</h1>
              <p>Empieza por crear un script para la tarea y deja que el chat siga el resto.</p>
            </section>

            <!-- MENSAJES -->
            <div class="messages" ref="messages">
              <transition-group name="fade" tag="div">
                <div
                  v-for="(msg, i) in chat"
                  :key="i"
                  :class="['bubble', msg.from]"
                >
                  <div>{{ msg.text }}</div>
                  <div v-if="msg.pictograms && msg.pictograms.length" class="pictogram-row">
                    <img
                      v-for="(pic, idx) in msg.pictograms"
                      :key="idx"
                      :src="buildPictogramUrl(pic.pictogram || pic.path || pic)"
                      :alt="pic.word || 'pictogram'"
                    />
                  </div>
                  <div class="meta-tags" v-if="msg.intent || msg.emotion">
                    <span class="chip" v-if="msg.intent">Intent: {{ msg.intent.label }} ({{ formatScore(msg.intent.score) }})</span>
                    <span class="chip alt" v-if="msg.emotion">Emoción: {{ msg.emotion.label }}</span>
                  </div>
                </div>
              </transition-group>
            </div>

            <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

            <!-- INPUT CHAT -->
            <div class="chat-input">
              <input
                v-model="message"
                type="text"
                placeholder="Escribe tu mensaje..."
                @keyup.enter="sendMessage"
              />

              <div class="chat-icons">
                <button
                  class="icon-btn"
                  :class="{ active: listening }"
                  :disabled="!speechSupported"
                  @click="toggleMic"
                  :title="speechSupported ? 'Hablar' : 'Mic no soportado'"
                >
                  <img :src="icons.mic" />
                </button>

                <button class="send-btn" @click="sendMessage" :disabled="loadingResponse">
                  <img :src="icons.send" />
                </button>
              </div>
            </div>
          </div>

          <aside class="side-panel">
            <div class="panel-block">
              <h3>Categorías</h3>
              <select v-model="selectedCategory">
                <option value="">Todas</option>
                <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>

            <div class="panel-block pictogram-gallery">
              <div class="panel-header">
                <h3>Galería de pictogramas</h3>
                <span v-if="galleryLoading">Cargando...</span>
              </div>
              <div class="pictogram-grid">
                <button
                  v-for="(p, idx) in filteredPictograms"
                  :key="idx"
                  class="pictogram-card"
                  @click="appendWord(p)"
                  :title="p.keywords?.[0]?.keyword || 'pictograma'"
                >
                  <img :src="buildPictogramUrl(p.path)" :alt="p.keywords?.[0]?.keyword || 'pictogram'" />
                  <small>{{ p.keywords?.[0]?.keyword }}</small>
                </button>
              </div>
            </div>

            <div class="panel-block suggestions" v-if="suggestedPictos.length">
              <div class="panel-header">
                <h3>Sugeridos por el asistente</h3>
                <div class="chips">
                  <span v-if="lastIntent" class="chip">Intención: {{ lastIntent.label }} ({{ formatScore(lastIntent.score) }})</span>
                  <span v-if="lastEmotion" class="chip alt">Emoción: {{ lastEmotion.label }}</span>
                </div>
              </div>
              <div class="pictogram-grid">
                <button
                  v-for="(p, idx) in suggestedPictos"
                  :key="p.path || idx"
                  class="pictogram-card suggested"
                  @click="useSuggested(p)"
                  :title="p.keyword || 'pictograma sugerido'"
                >
                  <img :src="buildPictogramUrl(p.path)" :alt="p.keyword || 'pictogram'" />
                  <small>{{ p.keyword || 'pictograma' }}</small>
                  <small class="score" v-if="p.score">{{ formatScore(p.score) }}</small>
                </button>
              </div>
            </div>

            <div class="panel-block actions" v-if="lastIntent">
              <h3>Acciones rápidas</h3>
              <button v-if="lastIntent.label === 'juego_cooperativo'" class="btn" @click="$router.push('/memory-game')">Ir a juego de memoria</button>
              <button v-if="lastIntent.label === 'autonomia_diaria'" class="btn" @click="$router.push('/assignments')">Ver pasos de autonomía</button>
            </div>
          </aside>

        </section>

      </div>
    </main>
  </div>
</template>


<script>
import { processSentence, logoutUser, fetchCategories, fetchPictograms, fetchPictogram } from "@/services/api";
import { getSession, clearSession } from "@/services/session";
import addIcon from "@/assets/Add_Square.png";
import assignmentsIcon from "@/assets/historial_icon.png";
import memoryIcon from "@/assets/Book_duotone.png";
import guidedIcon from "@/assets/Edit.png";
import robotIcon from "@/assets/robot_dancing.gif";
import micIcon from "@/assets/micro_icon.png";
import sendIcon from "@/assets/sent.png";
import welcomeIcon from "@/assets/14.png";

const ROLE_LABELS = {
  child: "Estudiante / Niño",
  parent: "Familia",
  teacher: "Docente",
  therapist: "Terapeuta"
};

export default {
  name: "ChatBotView",
  data() {
    return {
      message: "",
      chat: [],
      user: null,
      token: null,
      currentChatId: null,
      loadingResponse: false,
      errorMessage: "",
      categories: [],
      pictograms: [],
      galleryLoading: false,
      selectedCategory: "",
      speechSupported: false,
      listening: false,
      recognition: null,
      ttsEnabled: true,
      lastIntent: null,
      lastEmotion: null,
      suggestedPictos: [],
      icons: {
        add: addIcon,
        assignments: assignmentsIcon,
        memory: memoryIcon,
        guided: guidedIcon,
        robot: robotIcon,
        mic: micIcon,
        send: sendIcon,
        welcome: welcomeIcon
      }
    };
  },
  computed: {
    roleLabel() {
      if (!this.user?.role) return "Sin rol asignado";
      return ROLE_LABELS[this.user.role] || this.user.role;
    },
    menuItems() {
      const role = this.user?.role;
      const items = [];
      items.push({ to: "/assignments", label: "Asignaciones", icon: this.icons.assignments });
      if (role === "child" || role === "student") {
        items.push({ to: "/memory-game", label: "Juego de memoria", icon: this.icons.memory });
      }
      if (role === "teacher" || role === "therapist" || role === "parent") {
        items.push({ to: "/guided-session", label: "Sesión guiada", icon: this.icons.guided });
      }
      return items;
    },
    filteredPictograms() {
      const maxItems = 80;
      if (!this.selectedCategory) return this.pictograms.slice(0, maxItems);
      return this.pictograms
        .filter(p => (p.tags || p.keywords?.map(k => k.keyword)).some(tag => tag === this.selectedCategory))
        .slice(0, maxItems);
    }
  },
  created() {
    const session = getSession();
    if (!session) {
      this.$router.push("/login");
      return;
    }
    if (!['child', 'student'].includes(session.user?.role)) {
      this.$router.push({ path: '/' });
      return;
    }
    this.user = session.user;
    this.token = session.token;
    this.loadCategories();
    this.loadPictograms();
    this.initSpeech();
  },
  methods: {
    async sendMessage() {
      if (!this.token) {
        this.handleAuthExpiration();
        return;
      }
      if (!this.message.trim() || this.loadingResponse) return;

      const userText = this.message.trim();
      this.chat.push({ text: userText, from: "user" });
      this.message = "";
      this.errorMessage = "";
      this.loadingResponse = true;
      this.scrollDown();

      try {
        const response = await processSentence(this.token, userText);
        const botText = (response.processed_sentence || [])
          .map(item => item.word)
          .join(" ")
          .trim();
        this.lastIntent = response.intent;
        this.lastEmotion = response.emotion;
        this.suggestedPictos = response.suggested_pictograms || [];
        this.chat.push({
          text:
            botText || "No tengo una respuesta ahora mismo, pero sigamos practicando.",
          from: "bot",
          pictograms: response.processed_sentence,
          intent: response.intent,
          emotion: response.emotion
        });
        this.speak(botText, response.emotion?.label);
      } catch (error) {
        if (error.status === 401) {
          this.handleAuthExpiration();
          return;
        }
        const msg = error?.message || "No se pudo obtener respuesta del asistente.";
        this.errorMessage = msg;
        this.chat.push({ text: msg, from: "system" });
      } finally {
        this.loadingResponse = false;
        this.scrollDown();
      }
    },
    async logout() {
      try {
        if (this.token) {
          await logoutUser(this.token);
        }
      } catch (error) {
        // Ignorar errores del lado del servidor durante logout
      } finally {
        clearSession();
        this.$router.push("/login");
      }
    },
    handleAuthExpiration() {
      clearSession();
      this.$router.push({ name: "login", query: { redirect: this.$route.fullPath } });
    },
    scrollDown() {
      this.$nextTick(() => {
        const box = this.$refs.messages;
        if (box) {
          box.scrollTop = box.scrollHeight;
        }
      });
    },
    newChat() {
      this.chat = [];
      this.currentChatId = Date.now();
    },
    async loadCategories() {
      try {
        this.categories = await fetchCategories();
      } catch (error) {
        console.error("No se pudieron cargar las categorías", error);
      }
    },
    async loadPictograms() {
      this.galleryLoading = true;
      try {
        this.pictograms = await fetchPictograms();
      } catch (error) {
        console.error("No se pudo cargar la galería", error);
      } finally {
        this.galleryLoading = false;
      }
    },
    appendWord(pictogram) {
      const keyword = pictogram?.keywords?.[0]?.keyword;
      if (keyword) {
        this.message = `${this.message} ${keyword}`.trim();
        this.speak(keyword);
      }
    },
    appendSuggestedWord() {
      const first = this.filteredPictograms[0];
      if (first) this.appendWord(first);
    },
    buildPictogramUrl(path) {
      if (!path) return "";
      return fetchPictogram(path);
    },
    initSpeech() {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        this.speechSupported = false;
        return;
      }
      this.speechSupported = true;
      this.recognition = new SpeechRecognition();
      this.recognition.lang = "es-ES";
      this.recognition.interimResults = false;
      this.recognition.maxAlternatives = 1;

      this.recognition.onstart = () => {
        this.listening = true;
      };
      this.recognition.onend = () => {
        this.listening = false;
      };
      this.recognition.onresult = (event) => {
        const speechResult = event.results[0][0].transcript;
        this.message = speechResult;
        this.sendMessage();
      };
      this.recognition.onerror = () => {
        this.listening = false;
      };
    },
    toggleMic() {
      if (!this.recognition) return;
      if (this.listening) {
        this.recognition.stop();
      } else {
        this.recognition.start();
      }
    },
    speak(text, emotionLabel) {
      if (!this.ttsEnabled || !text || typeof window === 'undefined' || !window.speechSynthesis) return;
      const utter = new SpeechSynthesisUtterance(text);
      utter.lang = 'es-ES';
      // Ajusta el ritmo/tono según emoción detectada
      if (emotionLabel === 'ansioso' || emotionLabel === 'triste') {
        utter.rate = 0.9;
        utter.pitch = 0.95;
      } else if (emotionLabel === 'enojado') {
        utter.rate = 0.95;
        utter.pitch = 0.9;
      } else if (emotionLabel === 'orgulloso') {
        utter.rate = 1.05;
        utter.pitch = 1.05;
      }
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(utter);
    },
    useSuggested(pic) {
      if (!pic?.keyword) return;
      this.message = `${this.message} ${pic.keyword}`.trim();
      this.speak(pic.keyword, this.lastEmotion?.label);
    },
    formatScore(score) {
      if (score === undefined || score === null) return '';
      return `${Math.round(score * 100)}%`;
    }
  }
};
</script>

<style scoped>
/* ===== GENERAL LAYOUT ===== */

.layout {
  display: flex;
  height: 100vh;
  background: #f7f8fc;
}

/* ===== SIDEBAR ===== */

.sidebar {
  width: 270px;
  background: #00C8B3;
  padding: 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

/* Profile Box */
.profile-box {
  background: white;
  padding: 12px;
  border-radius: 12px;
  border: 2px solid #E5FFFA;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.profile-info {
  display: flex;
  align-items: center;
}

.profile-img {
  width: 45px;
  height: 45px;
  border-radius: 50%;
  margin-right: 10px;
}

.profile-box h3 {
  margin: 0;
  font-size: 16px;
  font-weight: bold;
}

.profile-box p {
  margin: 0;
  font-size: 12px;
  opacity: 0.8;
}

.arrow {
  font-size: 22px;
  opacity: 0.5;
}

/* Sidebar buttons */
.sidebar-menu {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.menu-btn {
  width: 100%;
  background: #0B1A1E;
  color: white;
  border: none;
  padding: 12px;
  font-size: 15px;
  border-radius: 10px;
  text-align: left;
  cursor: pointer;
  display: flex;
  gap: 10px;
  align-items: center;
  text-decoration: none;
}

.menu-btn:hover {
  background: #0f212a;
}

.icon {
  font-size: 18px;
}

/* Robot image */
.robot-img {
  width: 150%;
  margin-top: auto;
  align-self: center;
}

/* ===== MAIN AREA ===== */

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 30px;
}

/* TOPBAR */
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.topbar-actions {
  display: flex;
  gap: 15px;
}

.toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #333;
}

.logout-btn {
  background: transparent;
  border: 1px solid #ddd;
  padding: 8px 16px;
  border-radius: 20px;
  cursor: pointer;
}

.logout-btn:hover {
  background: #f5f5f5;
}

.circle-btn {
  width: 40px;
  height: 40px;
  background: white;
  border-radius: 50%;
  border: 1px solid #ddd;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
}

.upgrade-btn {
  background: #00C8B3;
  border: none;
  padding: 8px 18px;
  color: rgb(0, 0, 0);
  border-radius: 20px;
  cursor: pointer;
}
      
/* WELCOME SECTION */
.welcome {
  text-align: center;
  margin-top: 260px;
}

.welcome h1 {
  margin-top: 15px;
  font-size: 32px;
}

.welcome p {
  color: #555;
  margin-top: 8px;
}

.welcome img {
  width: 8%;
  border-radius: 100px;
  object-fit: cover;
}
/* CHAT INPUT */

.chat-input {
  width: 100%;
  border: 2px solid #00c8b3;
  border-radius: 15px;
  padding: 15px 6px;
  background: white;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 40px auto 0 auto;
  transition: all 0.3s ease;
}

.chat-input input {
  border: none;
  width: 80%;
  font-size: 17px;
  outline: none;
}

.chat-icons {
  display: flex;
  gap: 15px;
  font-size: 20px;
}

.send-btn {
  background: #00c8b3;
  border: none;
  border-radius: 12px;
  padding: 8px 12px;
  cursor: pointer;
}

.send-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.send:hover {
  cursor: pointer;
  opacity: 0.7;
}

.boty-mode {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-bottom: 40px;
}

.voice-container {
  text-align: center;
  margin-top: 0;   
}

/* Burbujas de chat */
.messages {
  flex: 1;
  margin-top: 10px;
  padding-right: 20px;
  max-height: 1000px;
  overflow-y: auto;
}

.error {
  color: #e63946;
  margin-top: 10px;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  margin-bottom: 10px;
  border-radius: 16px;
  font-size: 15px;
  line-height: 1.3;
}

/* Usuario = verde */
.bubble.user {
  background: #00c8b3;
  color: white;
  margin-left: auto;
}

/* Bot = blanco suave */
.bubble.bot {
  background: #d6d6d6;
  color: #333;
}

/* Animación fade */
.fade-enter-active, .fade-leave-active {
  transition: all .25s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

/* CONTENEDOR CENTRAL DEL CHAT */
.chat-box {
  width: 70%;
  max-width: 900px;
  margin: 0 auto;
  padding-top: 40px;
  flex-direction: column;
  display: flex;
}

.chat-columns {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.chat-pane {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* burbujas */
.bubble {
  align-self: flex-start;   
  max-width: 75%;
  width: fit-content;       
  padding: 12px 18px;
  border-radius: 14px;
  line-height: 1.4;
  font-size: 1rem;
  word-break: break-word;
}

/* Solo cuando el usuario ha empezado a escribir */
.chat-input input:not(:placeholder-shown) {
  margin-bottom: 10px;  
}

/* Estilo input */
.chat-input input {
  border: none;
  width: 100%;
  font-size: 1.05rem;
  outline: none;
  margin-left: 12px;
}


/* iconos */
/* Contenedor */
.chat-icons {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Botón base */
.icon-btn {
  width: 36px;
  height: 36px;
  background: #f3f3f3;
  border-radius: 50%;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.15s ease;
}

/* Icono dentro */
.icon-btn img {
  width: 22px;
  height: 22px;
}

/* Hover */
.icon-btn:hover {
  background: #e6e6e6;
  transform: scale(1.05);
}

.icon-btn.active {
  background: #00c8b3;
  color: #fff;
}

/* Botón de enviar */
.send-btn {
  width: 40px;
  height: 40px;
  background: #000000;
  border-radius: 50%;
  border: none;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: background 0.2s, transform 0.15s;
}

.send-btn img {
  width: 22px;
  height: 22px;
  filter: brightness(0) invert(1);
}

/* Hover enviar */
.send-btn:hover {
  background: #00b8a5;
  transform: scale(1.07);
}

.side-panel {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 720px;
  overflow: hidden;
}

.panel-block {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.panel-block select {
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #dcdcdc;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pictogram-gallery {
  flex: 1;
  overflow: hidden;
}

.pictogram-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
  gap: 8px;
  max-height: 600px;
  overflow-y: auto;
  padding-right: 4px;
}

.pictogram-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: #f7f8fc;
  border: 1px solid #e5e5e5;
  border-radius: 10px;
  padding: 6px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.pictogram-card.suggested {
  border-color: #00c8b3;
  background: #f0fffc;
}

.pictogram-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
}

.pictogram-card img {
  width: 60px;
  height: 60px;
  object-fit: contain;
}

.pictogram-row {
  display: flex;
  gap: 6px;
  margin-top: 6px;
}

.pictogram-row img {
  width: 38px;
  height: 38px;
  object-fit: contain;
  background: #fff;
  border-radius: 8px;
  border: 1px solid #eee;
  padding: 4px;
}

.meta-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 6px;
}

.chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.chip {
  background: #0a0c19;
  color: #00c8b3;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.chip.alt {
  background: #f2f7ff;
  color: #0b1a1e;
}

.suggestions .score {
  color: #0a0c19;
  font-size: 11px;
}
.exit-button {
  margin-top: 20px;
  padding: 10px 18px;
  background: #00c8b3;
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 15px;
  cursor: pointer;
  transition: background 0.25s;
}

.exit-button:hover {
  background: #009b88;
}


/* RESPONSIVE */

@media (max-width: 1200px) {
  .chat-box {
    width: 80%;
  }
}

@media (max-width: 900px) {
  .chat-box {
    width: 90%;
  }

  .bubble {
    max-width: 75%;
  }
}

@media (max-width: 600px) {
  .chat-box {
    width: 95%;
  }

  .bubble {
    max-width: 85%;
    font-size: 0.95rem;
  }

  .chat-input {
    padding: 12px;
  }

  .chat-input input {
    font-size: 1rem;
  }
}

</style>
