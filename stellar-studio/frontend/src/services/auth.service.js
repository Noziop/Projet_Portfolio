import axios from 'axios'

const API_URL = '/api/v1/auth'

class AuthService {
    async login(username, password) {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);
        
        const response = await axios.post(`${API_URL}/login`, formData, {
            headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
            }
        });
        return response.data;
    }
      

  async register(userData) {
    const response = await axios.post(`${API_URL}/register`, userData)
    return response.data
  }

  async getMe() {
    const response = await axios.get(`${API_URL}/me`)
    return response.data
  }

  async changePassword(oldPassword, newPassword) {
    const response = await axios.post(`${API_URL}/password`, {
      old_password: oldPassword,
      new_password: newPassword
    })
    return response.data
  }

  setAuthHeader(token) {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
    } else {
      delete axios.defaults.headers.common['Authorization']
    }
  }
}

export default new AuthService()
