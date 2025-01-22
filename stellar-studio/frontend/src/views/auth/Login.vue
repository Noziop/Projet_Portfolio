<template>
    <v-container fluid fill-height>
      <v-row align="center" justify="center">
        <v-col cols="12" sm="8" md="4">
          <v-card class="elevation-12">
            <v-toolbar dark color="primary">
              <v-toolbar-title>Login to StellarStudio</v-toolbar-title>
            </v-toolbar>
            
            <v-card-text>
              <v-form @submit.prevent="handleSubmit">
                <v-text-field
                  v-model="username"
                  prepend-icon="mdi-account"
                  label="Username"
                  type="text"
                  required
                ></v-text-field>
  
                <v-text-field
                  v-model="password"
                  prepend-icon="mdi-lock"
                  label="Password"
                  :type="showPassword ? 'text' : 'password'"
                  :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                  @click:append="showPassword = !showPassword"
                  required
                ></v-text-field>
              </v-form>
            </v-card-text>
  
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                @click="handleSubmit"
                :loading="loading"
              >
                Login
              </v-btn>
            </v-card-actions>
  
            <v-card-text class="text-center">
              <router-link to="/register">
                Don't have an account? Register here
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
        </v-col>
      </v-row>
    </v-container>
  </template>
  
  <script>
  import { useAuthStore } from '../../stores/auth'
  
  export default {
    name: 'Login',
    
    data() {
      return {
        username: '',
        password: '',
        showPassword: false,
        loading: false,
        showError: false,
        errorMessage: ''
      }
    },
  
    methods: {
      async handleSubmit() {
        if (!this.username || !this.password) {
          this.errorMessage = 'Please fill in all fields'
          this.showError = true
          return
        }
  
        this.loading = true
        const authStore = useAuthStore()
  
        try {
          await authStore.login(this.username, this.password)
          this.$router.push('/')
        } catch (error) {
          this.errorMessage = error.response?.data?.detail || 'Login failed'
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
  