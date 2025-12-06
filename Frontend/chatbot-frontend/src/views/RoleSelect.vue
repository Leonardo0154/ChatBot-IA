<template>
  <div class="roles-wrapper">
    <h1 class="title">Selecciona tu Rol</h1>

    <div class="roles-grid">
      <!-- Alumno -->
      <div class="role-card alumno" @click="selectRole('child')">
        <div class="icon">🎓</div>
        <h2>Alumno</h2>
        <p>Acceso al chat educativo y guía personalizada.</p>
      </div>

      <!-- Profesor -->
      <div class="role-card profesor" @click="selectRole('teacher')">
        <div class="icon">👨‍🏫</div>
        <h2>Profesor</h2>
        <p>Monitorea y apoya a tus estudiantes.</p>
      </div>

      <!-- Padre -->
      <div class="role-card padre" @click="selectRole('parent')">
        <div class="icon">👨‍👧</div>
        <h2>Padre</h2>
        <p>Acompaña el avance académico y emocional.</p>
      </div>

      <!-- Terapeuta -->
      <div class="role-card terapeuta" @click="selectRole('therapist')">
        <div class="icon">🧠</div>
        <h2>Terapeuta</h2>
        <p>Brinda orientación emocional y apoyo.</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  methods: {
    selectRole(role) {
      console.log("Rol seleccionado:", role)
      localStorage.setItem('selectedRole', role)
      this.$router.push("/register-form")
    }
  }
};
</script>

<style scoped>
/* === FONDO COMPLETO === */
.roles-wrapper {
  width: 100vw;
  height: 100vh;
  background: #050815;
  display: flex;
  flex-direction: column;
  justify-content: center; 
  align-items: center;
  color: white;
  padding: 0;
  overflow: hidden;
}

/* === TÍTULO === */
.title {
  font-size: 40px;
  font-weight: 700;
  margin-bottom: 40px;
  text-align: center;
  color: #b9d5ff;
  animation: fadeInDown 0.7s ease forwards;
  margin-top: -50px
}

/* === GRID MEJORADO === */
.roles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 31px;
  width: 93%;
  max-width: 1400px;
}

/* === TARJETAS (BASE) === */
.role-card {
  border-radius: 20px;
  padding: 32px 25px;
  text-align: center;
  cursor: pointer;
  backdrop-filter: blur(8px);
  transition: transform 0.25s ease, box-shadow 0.4s ease;
  color: white;
  animation: fadeInUp 0.7s ease forwards;
  font-size: 17px;
}

/* === ICONOS === */
.icon {
  font-size: 60px;
  margin-bottom: 15px;
  display: block;
}

/* Estilos individuales para cada rol */
.role-card.alumno {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: 2px solid rgba(102, 126, 234, 0.3);
}

.role-card.alumno:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
}

.role-card.profesor {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border: 2px solid rgba(245, 87, 108, 0.3);
}

.role-card.profesor:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 40px rgba(245, 87, 108, 0.4);
}

.role-card.padre {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  border: 2px solid rgba(79, 172, 254, 0.3);
}

.role-card.padre:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 40px rgba(79, 172, 254, 0.4);
}

.role-card.terapeuta {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
  border: 2px solid rgba(250, 112, 154, 0.3);
}

.role-card.terapeuta:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 40px rgba(250, 112, 154, 0.4);
}

.role-card h2 {
  font-size: 22px;
  margin-bottom: 10px;
  font-weight: 600;
}

.role-card p {
  font-size: 14px;
  line-height: 1.4;
  opacity: 0.9;
}

/* Animaciones */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>