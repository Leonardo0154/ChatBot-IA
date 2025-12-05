<template>
  <div class="auth-bg">
    <div class="auth-card">

      <div class="profile-icon">
        <img src="../assets/14.png" alt="profile" />
      </div>

      <h1 class="title">Crear cuenta</h1>

      <form @submit.prevent="register" class="form">

        <div class="input-group">
          <img class="icon" src="../assets/person.png" alt="">
          <input
            type="text"
            v-model="username"
            placeholder="Usuario (sin espacios)"
            required
            autocomplete="username"
          />
        </div>

        <div class="input-group">
          <img class="icon" src="../assets/email.png" alt="">
          <select v-model="role" required>
            <option value="child">Estudiante / Niño</option>
            <option value="parent">Padre / Madre</option>
            <option value="teacher">Docente</option>
            <option value="therapist">Terapeuta</option>
          </select>
        </div>

        <div class="input-group" v-if="role !== 'child'">
          <img class="icon" src="../assets/person.png" alt="">
          <input
            type="text"
            v-model="studentsRaw"
            placeholder="Estudiantes vinculados (coma)"
          />
        </div>

        <div class="input-group">
          <img class="icon" src="../assets/lock.png" alt="">
          <input type="password" v-model="password" placeholder="Contraseña" required />
        </div>

        <div class="input-group">
          <img class="icon" src="../assets/lock.png" alt="">
          <input type="password" v-model="confirmPassword" placeholder="Confirmar contraseña" required />
        </div>

        <button class="btn-login" :disabled="loading">
          {{ loading ? 'Creando...' : 'Registrarse' }}
        </button>
      </form>

      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success">{{ successMessage }}</p>

      <p class="bottom-text">
        ¿Ya tienes cuenta?
        <router-link to="/login">Inicia sesión</router-link>
      </p>

    </div>
  </div>
</template>


<script>
import { registerUser } from "@/services/api";

export default {
  data() {
    return {
      username: "",
      role: "child",
      studentsRaw: "",
      password: "",
      confirmPassword: "",
      loading: false,
      errorMessage: "",
      successMessage: ""
    }
  },
  methods: {
    async register() {
      if (this.loading) return
      this.errorMessage = ""
      this.successMessage = ""

      if (this.password !== this.confirmPassword) {
        this.errorMessage = "Las contraseñas no coinciden"
        return
      }

      this.loading = true
      try {
        const username = this.username.trim().toLowerCase()
        const students = this.studentsRaw
          .split(',')
          .map(s => s.trim())
          .filter(Boolean)
        await registerUser({
          username,
          role: this.role,
          password: this.password,
          students: this.role === 'child' ? undefined : students
        })
        this.successMessage = 'Cuenta creada correctamente. Ahora puedes iniciar sesión.'
        setTimeout(() => this.$router.push('/login'), 1200)
      } catch (error) {
        this.errorMessage = error?.message || 'No se pudo crear la cuenta.'
      } finally {
        this.loading = false
      }
    }
  }
}
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

.input-group select {
  width: 100%;
  border: none;
  outline: none;
  font-size: 15px;
  background: transparent;
}

.icon {
  margin-right: 10px;
  font-size: 18px;
}

.toggle {
  margin-left: 10px;
  cursor: pointer;
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

.success {
  color: #0f9d58;
  margin-top: 15px;
}

</style>
