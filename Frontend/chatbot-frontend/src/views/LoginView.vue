<template>
  <div class="auth-bg">
    <div class="auth-card">

      <!-- Icono de perfil -->
      <div class="profile-icon">
        <img src="../assets/14.png" alt="profile" />
      </div>

      <h1 class="title">Login</h1>

      <form @submit.prevent="login" class="form">

        <!-- Email -->
        <div class="input-group">
          <img class="icon" src="../assets/person.png" alt="">
          <input
            type="text"
            v-model="username"
            placeholder="Usuario o correo registrado"
            required
            autocomplete="username"
          />
        </div>

        <!-- Password -->
        <div class="input-group">
          <img class="icon" src="../assets/lock.png" alt="">

          <input
            :type="showPass ? 'text' : 'password'"
            v-model="password"
            placeholder="Contraseña"
            required
          />

          <!-- OJO -->
          <img
            class="toggle-eye"
            :src="showPass ? eyeOpen : eyeClosed"
            @click="showPass = !showPass"
            alt="toggle password"
          />
        </div>

        <div class="options">
          <label>
            <input type="checkbox" /> Recuérdame
          </label>
          <a href="#" class="forgot">¿Olvidaste tu contraseña?</a>
        </div>

        <button class="btn-login" :disabled="loading">
          {{ loading ? 'Ingresando...' : 'Login' }}
        </button>
      </form>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

      <p class="bottom-text">
        ¿Aún no te has registrado?
        <router-link to="/register">Crear una cuenta</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import eyeOpen from "../assets/eye.png";
import eyeClosed from "../assets/eye_closed.png";
import { login as loginRequest, fetchProfile } from "@/services/api";
import { saveSession } from "@/services/session";

export default {
  data() {
    return {
      username: "",
      password: "",
      showPass: false,
      loading: false,
      errorMessage: "",
      eyeOpen,
      eyeClosed
    };
  },
  methods: {
    async login() {
      if (this.loading) return;
      this.errorMessage = "";
      this.loading = true;
      try {
        const username = this.username.trim().toLowerCase();
        const tokenResponse = await loginRequest(username, this.password);
        const user = await fetchProfile(tokenResponse.access_token);
        saveSession({ token: tokenResponse.access_token, user });
        const redirect = this.$route.query.redirect || "/chat";
        this.$router.push(redirect);
      } catch (error) {
        this.errorMessage = error?.message || "No se pudo iniciar sesión.";
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.auth-bg {
  height: 100vh;
  background: #050815;
  display: flex;
  justify-content: center;
  align-items: center;
}

.auth-card {
  width: 450px;
  background: #ffffff;
  padding: 60px 50px;
  border-radius: 22px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  text-align: center;
  position: relative;
}

.profile-icon img {
  width: 15%;
  border-radius: 50%;
  object-fit: cover;
  margin: 0 auto 10px;
}

.title {
  font-size: 34px;
  font-weight: 600;
  margin-bottom: 30px;
}

.form {
  width: 100%;
}

.input-group {
  width: 94%;
  display: flex;
  align-items: center;
  background: #fff;
  border: 2px solid #00C8B3;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 15px;
}

.input-group input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 15px;
}

.icon {
  margin-right: 10px;
  width: 20px;
}

.toggle-eye {
  width: 22px;
  height: 22px;
  cursor: pointer;
  margin-left: 10px;
  opacity: 0.7;
}

.toggle-eye:hover {
  opacity: 1;
}

.options {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 18px;
}

.options .forgot {
  color: #00C8B3;
  text-decoration: none;
}

.btn-login {
  width: 100%;
  background: #0A0C19;
  color: #00C8B3;
  padding: 15px;
  font-size: 16px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: 0.2s;
}

.btn-login:hover {
  background: #111428;
}

.btn-login:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.bottom-text {
  margin-top: 25px;
}

.bottom-text a {
  color: #00C8B3;
  text-decoration: none;
  font-weight: 600;
}

.error {
  color: #e63946;
  margin-top: 15px;
}
</style>
