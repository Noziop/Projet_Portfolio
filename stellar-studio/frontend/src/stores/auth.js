import { defineStore } from 'pinia'
import AuthService from '../services/auth.service'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token')
  }),

  actions: {
    async login(username, password) {
      try {
        const data = await AuthService.login(username, password)
        this.token = data.access_token
        localStorage.setItem('token', data.access_token)
        AuthService.setAuthHeader(data.access_token)
        this.isAuthenticated = true
        await this.getMe()
        return true
      } catch (error) {
        console.error('Login error:', error)
        throw error
      }
    },

    async register(userData) {
      try {
        const data = await AuthService.register(userData)
        return data
      } catch (error) {
        console.error('Register error:', error)
        throw error
      }
    },

    async getMe() {
      try {
        const data = await AuthService.getMe()
        this.user = data
        localStorage.setItem('user', JSON.stringify(data))
        return data
      } catch (error) {
        console.error('GetMe error:', error)
        throw error
      }
    },

    async changePassword(oldPassword, newPassword) {
      try {
        const data = await AuthService.changePassword(oldPassword, newPassword)
        return data
      } catch (error) {
        console.error('Change password error:', error)
        throw error
      }
    },

    logout() {
      this.user = null
      this.token = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      AuthService.setAuthHeader(null)
    },

    checkAuth() {
      return this.isAuthenticated && !!this.token
    }
  }
})
