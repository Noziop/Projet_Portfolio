<template>
    <v-container fluid class="auth-page">
      <div :class="['container', { 'panel-active': isPanelActive }]" id="container">
        <!-- Panneau de connexion (gauche) -->
        <div class="form-container sign-in-container">
          <form @submit.prevent="handleLogin">
            <h1>Se connecter</h1>
            <div class="social-container">
              <v-btn icon="mdi-facebook" variant="text" class="social-btn" />
              <v-btn icon="mdi-linkedin" variant="text" class="social-btn" />
            </div>
            <span>ou utilisez votre compte</span>
            <v-text-field
              v-model="loginForm.username"
              label="Email"
              variant="underlined"
              color="pink-accent-2"
              bg-color="transparent"
              class="input-field"
            />
            <v-text-field
              v-model="loginForm.password"
              label="Mot de passe"
              variant="underlined"
              type="password"
              color="pink-accent-2"
              bg-color="transparent"
              class="input-field"
            />
            <button type="submit" class="submit-btn">Se connecter</button>
          </form>
        </div>
  
        <!-- Panneau d'inscription (apparaît après glissement) -->
        <div class="form-container sign-up-container">
          <form @submit.prevent="handleRegister">
            <h1>Créer un compte</h1>
            <div class="social-container">
              <v-btn icon="mdi-facebook" variant="text" class="social-btn" />
              <v-btn icon="mdi-linkedin" variant="text" class="social-btn" />
            </div>
            <span>ou utilisez votre email</span>
            <v-text-field
              v-model="registerForm.username"
              label="Nom"
              variant="underlined"
              color="pink-accent-2"
              bg-color="transparent"
              class="input-field"
            />
            <v-text-field
              v-model="registerForm.email"
              label="Email"
              variant="underlined"
              color="pink-accent-2"
              bg-color="transparent"
              class="input-field"
            />
            <v-text-field
              v-model="registerForm.password"
              label="Mot de passe"
              variant="underlined"
              type="password"
              color="pink-accent-2"
              bg-color="transparent"
              class="input-field"
            />
            <button type="submit" class="submit-btn">S'inscrire</button>
          </form>
        </div>
  
        <!-- Panneau overlay avec animation -->
        <div class="overlay-container">
          <div class="overlay">
            <div class="overlay-panel overlay-left">
              <h1>Vous avez déjà un compte ?</h1>  
              <h1>Content de vous revoir !</h1>
              <p>Connectez-vous pour continuer votre voyage parmi les étoiles</p>
              <button class="ghost" @click="isPanelActive = false">Se connecter</button>
            </div>
            <div class="overlay-panel overlay-right">
              <h1>Bienvenue, Astronaute !</h1>
              <p>Embarquez pour un voyage spatial en créant votre compte</p>
              <button class="ghost" @click="isPanelActive = true">S'inscrire</button>
            </div>
          </div>
        </div>
      </div>
      <!-- Snackbar pour les notifications -->
  <v-snackbar
    v-model="snackbar.show"
    :color="snackbar.color"
    :timeout="3000"
    location="top right"
  >
    {{ snackbar.text }}
    <template v-slot:actions>
      <v-btn
        variant="text"
        @click="snackbar.show = false"
      >
        Fermer
      </v-btn>
    </template>
  </v-snackbar>
    </v-container>
  </template>
  
  <script>
  import { useAuthStore } from '../../stores/auth'
  import { ref } from 'vue'
  
  export default {
    name: 'AuthContainer',
    
    setup() {
      const authStore = useAuthStore()
      const isPanelActive = ref(false)
      
      return {
        isPanelActive,
        authStore
      }
    },
  
    data() {
    return {
      loading: false,
      loginForm: {
        username: '',
        password: ''
      },
      registerForm: {
        username: '',
        email: '',
        password: ''
      },
      snackbar: {
        show: false,
        text: '',
        color: 'success'
      }
    }
  },

  methods: {
    showNotification(text, color = 'success') {
      this.snackbar.text = text
      this.snackbar.color = color
      this.snackbar.show = true
    },

      async handleLogin() {
        if (!this.loginForm.username || !this.loginForm.password) return
        
        this.loading = true
        try {
          await this.authStore.login(this.loginForm.username, this.loginForm.password)
          this.$router.push('/')
        } catch (error) {
          console.error('Login error:', error)
        } finally {
          this.loading = false
        }
      },
  
      async handleRegister() {
      if (!this.registerForm.username || !this.registerForm.email || !this.registerForm.password) {
        this.showNotification('Veuillez remplir tous les champs', 'error')
        return
      }
      
      this.loading = true
      try {
        await this.authStore.register(this.registerForm)
        this.showNotification('Compte créé avec succès ! Vous pouvez maintenant vous connecter.')
        // Attendre que la notification soit visible avant de glisser
        setTimeout(() => {
          this.isPanelActive = false
        }, 1000)
      } catch (error) {
        this.showNotification(
          error.response?.data?.detail || 'Erreur lors de l\'inscription',
          'error'
        )
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

  
  <style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(130deg, #000000, #090909, #000000);
}

.container {
  position: relative;
  width: 768px;
  min-height: 480px;
  background: rgba(0, 0, 0, 0.8);
  border: 1px solid rgba(255, 105, 180, 0.3);
  border-radius: 15px;
  overflow: hidden;
  box-shadow: 5px 10px 20px rgba(255, 105, 180, 0.2);
  backdrop-filter: blur(5px);
}

.form-container {
  position: absolute;
  top: 0;
  height: 100%;
  transition: all 0.6s ease-in-out;
  background: rgba(0, 0, 0, 0.95);
}

.sign-in-container {
  left: 0;
  width: 50%;
  z-index: 2;
}

.sign-up-container {
  left: 0;
  width: 50%;
  z-index: 1;
  opacity: 0;
}

.container.panel-active .sign-in-container {
  transform: translateX(100%);
}

.container.panel-active .sign-up-container {
  transform: translateX(100%);
  opacity: 1;
  z-index: 5;
}

form {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 50px;
}

h1 {
  color: white;
  margin: 0 0 20px 0;
  font-size: 24px;
  text-transform: uppercase;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(255, 105, 180, 0.5);
}

span {
  color: #FF69B4;
  font-size: 14px;
  margin: 15px 0;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.input-field {
  margin-bottom: 10px;
  width: 100%;
}

.input-field:deep(.v-field__input) {
  color: white !important;
}

.input-field:deep(.v-field__outline) {
  color: #FF69B4 !important;
}

.input-field:deep(.v-field--focused) {
  box-shadow: 0 0 15px rgba(255, 105, 180, 0.3);
}

.social-container {
  margin: 20px 0;
  display: flex;
  justify-content: center;
  gap: 10px;
}

.social-btn {
  border: 1px solid #FF69B4 !important;
  border-radius: 50% !important;
  height: 40px;
  width: 40px;
  transition: all 0.3s ease;
}

.social-btn:hover {
  box-shadow: 0 0 15px rgba(255, 105, 180, 0.5);
  transform: scale(1.1);
}

button {
  padding: 12px 45px;
  background: transparent;
  border: 2px solid #FF69B4;
  color: white;
  font-size: 12px;
  font-weight: bold;
  letter-spacing: 1px;
  text-transform: uppercase;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

button:hover {
  animation: glitch 0.9s ease infinite;
  box-shadow: 0 0 20px rgba(64, 224, 208, 0.4);
  background: rgba(255, 105, 180, 0.1);
}

button:active {
  transform: scale(0.95);
}

.overlay-container {
  position: absolute;
  top: 0;
  left: 50%;
  width: 50%;
  height: 100%;
  overflow: hidden;
  transition: transform 0.6s ease-in-out;
  z-index: 100;
}

.container.panel-active .overlay-container {
  transform: translateX(-100%);
}

.overlay {
  position: relative;
  left: -100%;
  height: 100%;
  width: 200%;
  transform: translateX(0);
  transition: transform 0.6s ease-in-out;
}

.container.panel-active .overlay {
  transform: translateX(50%);
}

.overlay-panel {
  position: absolute;
  top: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 0 40px;
  height: 100%;
  width: 50%;
  text-align: center;
  transform: translateX(0);
  transition: transform 0.6s ease-in-out;
  background: linear-gradient(45deg, rgba(0,0,0,0.9), rgba(9,9,9,0.95));
  border-left: 2px solid #40E0D0;
}

.overlay-right {
  right: 0;
  transform: translateX(0);
}

.overlay-left {
  transform: translateX(-20%);
}

.container.panel-active .overlay-left {
  transform: translateX(0);
}

.container.panel-active .overlay-right {
  transform: translateX(20%);
}

button.ghost {
  border-color: #40E0D0;
}

button.ghost:hover {
  background: rgba(64, 224, 208, 0.1);
  box-shadow: 0 0 15px rgba(64, 224, 208, 0.3);
}

p {
  color: white;
  font-size: 14px;
  line-height: 20px;
  letter-spacing: 0.5px;
  margin: 20px 0 30px;
}

@keyframes glitch {
  0% { transform: translate(0) }
  20% { transform: translate(-2px, 2px) }
  40% { transform: translate(-2px, -2px) }
  60% { transform: translate(2px, 2px) }
  80% { transform: translate(2px, -2px) }
  100% { transform: translate(0) }
}

:deep(.v-field__input) {
  color: white !important;
}

:deep(.v-label) {
  color: rgba(255, 255, 255, 0.7) !important;
}

:deep(.v-snackbar) {
  backdrop-filter: blur(10px);
}

:deep(.v-snackbar__content) {
  font-weight: 500;
}

:deep(.v-snackbar.success) {
  background: rgba(76, 175, 80, 0.9) !important;
}

:deep(.v-snackbar.error) {
  background: rgba(244, 67, 54, 0.9) !important;
}
</style>
