/**
 * API Service for Real-time Chat Application
 */

class APIService {
    constructor() {
        this.baseURL = 'http://127.0.0.1:8000';
        this.token = localStorage.getItem('access_token');
    }

    // Set authorization token
    setToken(token) {
        this.token = token;
        localStorage.setItem('access_token', token);
    }

    // Remove authorization token
    removeToken() {
        this.token = null;
        localStorage.removeItem('access_token');
    }

    // Get authorization headers
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getAuthHeaders(),
            ...options,
        };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API Request failed:', error);
            throw error;
        }
    }

    // Auth endpoints
    async register(userData) {
        return await this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async login(credentials) {
        return await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({
                username: credentials.username,
                password: credentials.password
            }),
        });
    }

    async getCurrentUser() {
        return await this.request('/auth/me');
    }

    // User endpoints
    async getUsers() {
        return await this.request('/users');
    }

    async getUserByUsername(username) {
        return await this.request(`/users/username/${username}`);
    }

    // Friend endpoints
    async getFriends() {
        return await this.request('/friends');
    }

    async sendFriendRequest(username) {
        return await this.request('/friends/request', {
            method: 'POST',
            body: JSON.stringify({ username }),
        });
    }

    async getFriendRequests() {
        return await this.request('/friends/requests');
    }

    async respondToFriendRequest(requestId, accept) {
        const action = accept ? 'accept' : 'reject';
        return await this.request(`/friends/requests/${requestId}/${action}`, {
            method: 'PUT',
        });
    }

    // Conversation endpoints
    async getConversations() {
        return await this.request('/conversations');
    }

    async createConversation(userData) {
        return await this.request('/conversations', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async getConversation(conversationId) {
        return await this.request(`/conversations/${conversationId}`);
    }

    async updateConversation(conversationId, name) {
        return await this.request(`/conversations/${conversationId}`, {
            method: 'PUT',
            body: JSON.stringify({ name: name }),
        });
    }

    async getConversationMembers(conversationId) {
        return await this.request(`/conversations/${conversationId}/members`);
    }

    async kickMember(conversationId, memberId) {
        return await this.request(`/conversations/${conversationId}/members/${memberId}`, {
            method: 'DELETE',
        });
    }

    async addMember(conversationId, userId) {
        return await this.request(`/conversations/${conversationId}/members`, {
            method: 'POST',
            body: JSON.stringify({ user_id: userId }),
        });
    }

    async updateConversationSettings(conversationId, settings) {
        return await this.request(`/conversations/${conversationId}/settings`, {
            method: 'PUT',
            body: JSON.stringify(settings),
        });
    }

    async createGroup(name, memberUserIds = []) {
        return await this.request('/conversations/groups', {
            method: 'POST',
            body: JSON.stringify({
                name: name,
                member_user_ids: memberUserIds
            }),
        });
    }

    async leaveGroup(conversationId) {
        return await this.request(`/conversations/${conversationId}/leave`, {
            method: 'DELETE',
        });
    }

    async transferAdmin(conversationId, newAdminId) {
        return await this.request(`/conversations/${conversationId}/transfer-admin`, {
            method: 'PUT',
            body: JSON.stringify({ new_admin_id: newAdminId }),
        });
    }

    // User profile endpoints
    async getCurrentUser() {
        return await this.request('/users/me');
    }

    async updateUserProfile(profileData) {
        return await this.request('/users/me', {
            method: 'PUT',
            body: JSON.stringify(profileData),
        });
    }

    async updateUserPassword(passwordData) {
        return await this.request('/users/me/password', {
            method: 'PUT',
            body: JSON.stringify(passwordData),
        });
    }

    // Message endpoints
    async getMessages(conversationId, skip = 0, limit = 50) {
        return await this.request(`/messages/conversation/${conversationId}?skip=${skip}&limit=${limit}`);
    }

    async sendMessage(conversationId, content) {
        return await this.request('/messages', {
            method: 'POST',
            body: JSON.stringify({
                conversation_id: conversationId,
                content: content,
            }),
        });
    }
}

// Create global API instance
const api = new APIService();