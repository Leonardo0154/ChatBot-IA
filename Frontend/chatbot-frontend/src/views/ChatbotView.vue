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
        <button class="menu-btn" @click="newChat"><img class="icon-img" src="/src/assets/Add_Square.png"/>Nuevo chat</button>
        <button class="menu-btn" @click="mode = 'boty'"><img class="icon-img" src="/src/assets/robot_icon.png"/>Hablar con boty</button>
        <button class="menu-btn"><img class="icon-img" src="/src/assets/Edit.png"/>Aprender a escribir</button>
        <button class="menu-btn"><img class="icon-img" src="/src/assets/Book_duotone.png"/>Cuentos cortos</button>
        <button class="menu-btn"><img class="icon-img" src="/src/assets/historial_icon.png"/>Historial</button>
      </div>

      <!-- Robot abajo -->
      <img class="robot-img" src="/src/assets/robot_dancing.gif" />
    </aside>

    <!-- MAIN -->
    <main class="main">

      <!-- TOPBAR -->
      <header class="topbar">
        <h2>Chat With AI</h2>

        <div class="topbar-actions">
          <button class="logout-btn" @click="logout">Salir</button>
          <button class="upgrade-btn">Upgrade</button>

          <button class="circle-btn">
            <img src="../assets/Ajustes_icon.png" />
          </button>

          <button class="circle-btn">
            <img src="../assets/notificacion_icon.png" />
          </button>
        </div>
      </header>

      <div class="chat-box">

        <!-- MODO CHAT -->
        <section v-if="mode === 'chat'" class="chat-mode">

          <!-- WELCOME -->
          <section class="welcome" v-if="chat.length === 0">
            <img class="welcome-img" src="/src/assets/14.png" />
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
                {{ msg.text }}
              </div>
            </transition-group>
          </div>

          <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

          <!-- INPUT CHAT -->
          <div class="chat-input">
            <input
              v-model="message"
              type="text"
              placeholder="Write your message ..."
              @keyup.enter="sendMessage"
            />

            <div class="chat-icons">
              <button class="icon-btn">
                <img src="../assets/image_icon.png" />
              </button>

              <button class="icon-btn">
                <img src="../assets/micro_icon.png" />
              </button>

              <button class="send-btn" @click="sendMessage" :disabled="loadingResponse">
                <img src="../assets/sent.png" />
              </button>
            </div>
          </div>

        </section>

        <!-- MODO BOTY -->
        <section v-if="mode === 'boty'" class="boty-mode">
          <BotyVoice @exitBoty="mode = 'chat'" />
        </section>
      </div>
    </main>
  </div>
</template>


<script>
import BotyVoice from "./BotyVoice.vue";
import { processSentence, logoutUser } from "@/services/api";
import { getSession, clearSession } from "@/services/session";

const ROLE_LABELS = {
  child: "Estudiante / Niño",
  parent: "Familia",
  teacher: "Docente",
  therapist: "Terapeuta"
};

export default {
  name: "ChatBotView",
  components: { BotyVoice },
  data() {
    return {
      message: "",
      chat: [],
      user: null,
      token: null,
      currentChatId: null,
      mode: "chat",
      loadingResponse: false,
      errorMessage: ""
    };
  },
  computed: {
    roleLabel() {
      if (!this.user?.role) return "Sin rol asignado";
      return ROLE_LABELS[this.user.role] || this.user.role;
    }
  },
  created() {
    const session = getSession();
    if (!session) {
      this.$router.push("/login");
      return;
    }
    this.user = session.user;
    this.token = session.token;
  },
  methods: {
    async sendMessage() {
      if (!this.message.trim() || this.loadingResponse) return;
      if (!this.token) {
        this.handleAuthExpiration();
        return;
      }

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
        this.chat.push({
          text:
            botText || "No tengo una respuesta ahora mismo, pero sigamos practicando.",
          from: "bot",
          pictograms: response.processed_sentence
        });
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
