<template>
    <v-container fluid fill-height>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="4">
          <v-card class="elevation-12">
            <v-toolbar dark color="primary">
              <v-toolbar-title>Create StellarStudio Account</v-toolbar-title>
            </v-toolbar>
            
            <v-card-text>
              <v-form @submit.prevent="handleSubmit">
                <v-text-field
                  v-model="formData.username"
                  prepend-icon="mdi-account"
                  label="Username"
                  type="text"
                  required
                ></v-text-field>
  
                <v-text-field
                  v-model="formData.email"
                  prepend-icon="mdi-email"
                  label="Email"
                  type="email"
                  required
                ></v-text-field>
  
                <v-text-field
                  v-model="formData.password"
                  prepend-icon="mdi-lock"
                  label="Password"
                  :type="showPassword ? 'text' : 'password'"
                  :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  @click:append="showPassword = !showPassword"
                  required
                ></v-text-field>
  
                <v-text-field
                  v-model="formData.confirmPassword"
                  prepend-icon="mdi-lock-check"
                  label="Confirm Password"
                  :type="showPassword ? 'text' : 'password'"
                  :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  @click:append="showPassword = !showPassword"
                  required
                  :error-messages="passwordMatchError"
                ></v-text-field>
              </v-form>
            </v-card-text>
  
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                @click="handleSubmit"
                :loading="loading"
                :disabled="!isFormValid"
              >
                Register
              </v-btn>
            </v-card-actions>
  
            <v-card-text class="text-center">
              <router-link to="/login">
                Already have an account? Login here
              </router-link>
            </v-card-text>
          </v-card>
  
          <!-- Error Snackbar -->
          <v-snackbar
            v-model="showError"
            color="error"
            timeout="3000"
          >
            {{ errorMessage }}
          </v-snackbar>
  
          <!-- Success Snackbar -->
          <v-snackbar
            v-model="showSuccess"
            color="success"
            timeout="3000"
          >
            Registration successful! Redirecting to login...
          </v-snackbar>
        </v-col>
      </v-row>
    </v-container>
  </template>
  
  <script>
  import { useAuthStore } from '../../stores/auth'
  
  export default {
    name: 'Register',
    
    data() {
      return {
        formData: {
          username: '',
          email: '',
          password: '',
          confirmPassword: ''
        },
        showPassword: false,
        loading: false,
        showError: false,
        errorMessage: '',
        showSuccess: false
      }
    },
  
    computed: {
      passwordMatchError() {
        return this.formData.password && this.formData.confirmPassword && 
               this.formData.password !== this.formData.confirmPassword
          ? ["Passwords don't match"]
          : []
      },
  
      isFormValid() {
        return this.formData.username &&
               this.formData.email &&
               this.formData.password &&
               this.formData.confirmPassword &&
               this.formData.password === this.formData.confirmPassword
      }
    },
  
    methods: {
      async handleSubmit() {
        if (!this.isFormValid) {
          this.errorMessage = 'Please fill in all fields correctly'
          this.showError = true
          return
        }
  
        this.loading = true
        const authStore = useAuthStore()
  
        try {
          const { confirmPassword, ...registrationData } = this.formData
          await authStore.register(registrationData)
          
          this.showSuccess = true
          setTimeout(() => {
            this.$router.push('/login')
          }, 2000)
        } catch (error) {
          this.errorMessage = error.response?.data?.detail || 'Registration failed'
          this.showError = true
        } finally {
          this.loading = false
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .v-card {
    margin-top: 2rem;
  }
  </style>
  