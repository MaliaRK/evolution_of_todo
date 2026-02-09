// Auth client service for handling authentication operations
class AuthClient {
  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';
  }

  // Register a new user
  async register(userData) {
    try {
      const response = await fetch(`${this.baseURL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      return { success: true, user: data };
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: error.message };
    }
  }

  // Login user and return token
  async login(credentials) {
    try {
      const response = await fetch(`${this.baseURL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      // Store the token in localStorage
      if (data.access_token) {
        localStorage.setItem('auth_token', data.access_token);
      }

      return { success: true, token: data.access_token, tokenType: data.token_type };
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: error.message };
    }
  }

  // Logout user
  async logout() {
    try {
      // Remove token from localStorage
      localStorage.removeItem('auth_token');

      // Optionally notify the backend (in stateless JWT systems, this is often not needed)
      const response = await fetch(`${this.baseURL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });

      return { success: response.ok };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: error.message };
    }
  }

  // Get the current user's token
  getAuthToken() {
    return localStorage.getItem('auth_token');
  }

  // Check if user is authenticated
  isAuthenticated() {
    const token = this.getAuthToken();
    if (!token) {
      return false;
    }

    // Check if token is expired
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp > currentTime;
    } catch (error) {
      console.error('Error checking token expiration:', error);
      return false;
    }
  }

  // Get headers with authorization token
  getAuthHeaders() {
    const token = this.getAuthToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

}

// Create a singleton instance
const authClient = new AuthClient();
export default authClient;