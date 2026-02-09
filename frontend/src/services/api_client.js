// API client for communicating with the backend
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  // Helper method to get the auth token from localStorage
  getAuthToken() {
    return typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
  }

  // Helper method to add auth headers to requests
  getAuthHeaders() {
    const token = this.getAuthToken();
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    };
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        // If the response is 401, don't redirect here but let caller handle it
        if (response.status === 401) {
          // Clear the auth token to ensure logout state
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
          }
        }
        throw new Error(data.detail || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error(`API request error for ${url}:`, error);
      throw error;
    }
  }

  // Todo-related methods (using new event-driven endpoints)
  getTasks() {
    return this.request('/api/v1/todos');
  }

  createTask(taskData) {
    return this.request('/api/v1/todos', {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  }

  getTaskById(id) {
    return this.request(`/api/v1/todos/${id}`);
  }

  updateTask(id, taskData) {
    return this.request(`/api/v1/todos/${id}`, {
      method: 'PUT',
      body: JSON.stringify(taskData),
    });
  }

  deleteTask(id) {
    return this.request(`/api/v1/todos/${id}`, {
      method: 'DELETE',
    });
  }

  toggleTaskCompletion(id) {
    return this.request(`/api/v1/todos/${id}/complete`, {
      method: 'PATCH',
    });
  }
}

export default new ApiClient();