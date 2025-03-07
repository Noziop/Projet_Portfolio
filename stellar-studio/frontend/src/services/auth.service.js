import apiClient from './api'

const AUTH_URL = '/auth'

class AuthService {
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await apiClient.post(`${AUTH_URL}/login`, formData, {
            headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
        return response.data;
    }
      

  async register(userData) {
    const response = await apiClient.post(`${AUTH_URL}/register`, userData)
    return response.data
  }

  async getMe() {
    const response = await apiClient.get(`${AUTH_URL}/me`)
    return response.data
  }

  async changePassword(oldPassword, newPassword) {
    const response = await apiClient.post(`${AUTH_URL}/password`, {
      old_password: oldPassword,
      new_password: newPassword
    })
    return response.data
  }

  setAuthHeader(token) {
    if (token) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete apiClient.defaults.headers.common['Authorization']
    }
  }
}

export default new AuthService()
