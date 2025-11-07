/**
 * UI Service for managing interface interactions
 */

class UIService {
    constructor() {
        this.currentUser = null;
        this.conversations = [];
        this.friends = [];
        this.friendRequests = [];
    }

    // Show/Hide loading spinner
    showLoading() {
        document.getElementById('loading').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    // Show auth container
    showAuthContainer() {
        document.getElementById('auth-container').style.display = 'flex';
        document.getElementById('chat-container').classList.remove('active');
    }

    // Show chat container
    showChatContainer() {
        document.getElementById('auth-container').style.display = 'none';
        document.getElementById('chat-container').classList.add('active');
    }

    // Show/Hide modals
    showModal(modalId) {
        document.getElementById(modalId).classList.add('active');
    }

    hideModal(modalId) {
        document.getElementById(modalId).classList.remove('active');
    }

    // Display notifications
    showNotification(message, type = 'info', duration = 5000) {
        const container = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;

        const icon = this.getNotificationIcon(type);
        notification.innerHTML = `
            <i class="${icon}"></i>
            <span>${message}</span>
        `;

        container.appendChild(notification);

        // Auto remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);
    }

    getNotificationIcon(type) {
        switch (type) {
            case 'success': return 'fas fa-check-circle';
            case 'error': return 'fas fa-exclamation-circle';
            case 'warning': return 'fas fa-exclamation-triangle';
            default: return 'fas fa-info-circle';
        }
    }

    // Display error messages
    showError(message, elementId = 'auth-message') {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.className = 'message error';
            element.style.display = 'block';
        }
    }

    // Display success messages
    showSuccess(message, elementId = 'auth-message') {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = message;
            element.className = 'message success';
            element.style.display = 'block';
        }
    }

    // Clear messages
    clearMessage(elementId = 'auth-message') {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    }

    // Update current user info
    updateCurrentUser(user) {
        this.currentUser = user;
        document.getElementById('current-username').textContent = user.username;
    }

    // Render conversations list
    renderConversations(conversations) {
        this.conversations = conversations;
        const container = document.getElementById('conversations-list');

        if (conversations.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted mt-20">
                    <i class="fas fa-comments" style="font-size: 48px; opacity: 0.3;"></i>
                    <p>Chưa có cuộc trò chuyện nào</p>
                </div>
            `;
            return;
        }

        container.innerHTML = conversations.map(conv => `
            <div class="conversation-item" data-conversation-id="${conv.id}">
                <div class="avatar">
                    <i class="fas fa-${conv.type === 'group' ? 'users' : 'user'}"></i>
                </div>
                <div class="conversation-details">
                    <h4>${this.getConversationName(conv)}</h4>
                    <p>${conv.last_message?.content || 'Chưa có tin nhắn'}</p>
                </div>
                <div class="conversation-meta">
                    <span class="conversation-time">
                        ${conv.last_message?.created_at ? this.formatTime(conv.last_message.created_at) : ''}
                    </span>
                    ${conv.unread_count ? `<span class="unread-badge">${conv.unread_count}</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    // Get conversation display name
    getConversationName(conversation) {
        if (conversation.name) {
            return conversation.name;
        }

        if (conversation.type === 'direct' && conversation.members) {
            const otherMember = conversation.members.find(m => m.user.id !== this.currentUser?.id);
            return otherMember ? otherMember.user.username : 'Unknown';
        }

        return `Cuộc trò chuyện ${conversation.id}`;
    }

    // Render friends list
    renderFriends(friends) {
        this.friends = friends;
        const container = document.getElementById('friends-list');

        if (friends.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted mt-20">
                    <i class="fas fa-users" style="font-size: 48px; opacity: 0.3;"></i>
                    <p>Chưa có bạn bè nào</p>
                </div>
            `;
            return;
        }

        container.innerHTML = friends.map(friend => `
            <div class="friend-item" data-friend-id="${friend.id}">
                <div class="avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="friend-details">
                    <h4>${friend.username}</h4>
                    <span class="status ${friend.is_online ? 'online' : 'offline'}">
                        ${friend.is_online ? 'Trực tuyến' : 'Không trực tuyến'}
                    </span>
                </div>
            </div>
        `).join('');
    }

    // Render friend requests
    renderFriendRequests(requests) {
        this.friendRequests = requests;
        const container = document.getElementById('friend-requests-list');

        if (requests.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted mt-20">
                    <i class="fas fa-user-plus" style="font-size: 48px; opacity: 0.3;"></i>
                    <p>Không có lời mời kết bạn</p>
                </div>
            `;
            return;
        }

        container.innerHTML = requests.map(request => `
            <div class="friend-request-item" data-request-id="${request.id}">
                <div class="avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="friend-request-details">
                    <h4>${request.requester.username}</h4>
                    <small class="text-muted">${this.formatTime(request.created_at)}</small>
                </div>
                <div class="friend-request-actions">
                    <button class="btn btn-sm btn-accept" onclick="app.respondToFriendRequest(${request.id}, true)">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="btn btn-sm btn-reject" onclick="app.respondToFriendRequest(${request.id}, false)">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    // Render friends for new chat modal
    renderFriendsForChat(friends) {
        const container = document.getElementById('friends-for-chat');

        if (friends.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <p>Không có bạn bè để tạo cuộc trò chuyện</p>
                </div>
            `;
            return;
        }

        container.innerHTML = friends.map(friend => `
            <div class="friend-item" onclick="app.createDirectConversation(${friend.id})">
                <div class="avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="friend-details">
                    <h4>${friend.username}</h4>
                    <span class="status ${friend.is_online ? 'online' : 'offline'}">
                        ${friend.is_online ? 'Trực tuyến' : 'Không trực tuyến'}
                    </span>
                </div>
            </div>
        `).join('');
    }

    // Update chat header
    updateChatHeader(conversation) {
        document.getElementById('chat-title').textContent = this.getConversationName(conversation);
        document.getElementById('chat-status').textContent = 'Trực tuyến';

        // Enable message input
        const messageInput = document.getElementById('message-input');
        const sendBtn = document.getElementById('send-btn');
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.placeholder = 'Nhập tin nhắn...';
    }

    // Render messages
    renderMessages(messages) {
        const container = document.getElementById('messages-list');

        if (messages.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-comments" style="font-size: 48px; opacity: 0.3;"></i>
                    <p>Chưa có tin nhắn nào. Hãy bắt đầu cuộc trò chuyện!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = messages.map(message =>
            this.createMessageElement(message)
        ).join('');

        this.scrollToBottom();
    }

    // Add single message
    addMessage(message, isSent = false) {
        const container = document.getElementById('messages-list');

        // Remove empty state if exists
        const emptyState = container.querySelector('.text-center');
        if (emptyState) {
            container.innerHTML = '';
        }

        const messageElement = this.createMessageElement(message, isSent);
        container.insertAdjacentHTML('beforeend', messageElement);
        this.scrollToBottom();
    }

    // Add system message
    addSystemMessage(message) {
        const container = document.getElementById('messages-list');

        // Remove empty state if exists
        const emptyState = container.querySelector('.text-center');
        if (emptyState) {
            container.innerHTML = '';
        }

        const systemElement = `
            <div class="system-message" data-message-id="${message.id}">
                <div class="system-content">
                    <i class="fas fa-info-circle"></i>
                    ${this.escapeHtml(message.content)}
                </div>
                <div class="system-time">${this.formatTime(message.created_at)}</div>
            </div>
        `;

        container.insertAdjacentHTML('beforeend', systemElement);
        this.scrollToBottom();
    }

    // Create message element HTML
    createMessageElement(message, isSent = null) {
        if (isSent === null) {
            isSent = message.sender_id === this.currentUser?.id;
        }

        return `
            <div class="message-bubble ${isSent ? 'sent' : 'received'}" data-message-id="${message.id}">
                <div class="message-content">${this.escapeHtml(message.content)}</div>
                <div class="message-time">
                    ${message.sender_username && !isSent ? message.sender_username + ' • ' : ''}
                    ${this.formatTime(message.created_at)}
                </div>
            </div>
        `;
    }

    // Update conversation last message
    updateConversationLastMessage(conversationId, content, timestamp) {
        const conversationItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (conversationItem) {
            const details = conversationItem.querySelector('.conversation-details p');
            const time = conversationItem.querySelector('.conversation-time');

            if (details) details.textContent = content;
            if (time) time.textContent = this.formatTime(timestamp);
        }
    }

    // Update user online status
    updateUserOnlineStatus(userId, isOnline) {
        console.log(`🔄 Updating user ${userId} status to: ${isOnline ? 'online' : 'offline'}`);

        // Update in friends list
        const friendElements = document.querySelectorAll(`[data-friend-id="${userId}"] .status`);
        friendElements.forEach(element => {
            element.className = `status ${isOnline ? 'online' : 'offline'}`;
            element.textContent = isOnline ? 'Trực tuyến' : 'Không trực tuyến';
        });

        console.log(`✅ Updated ${friendElements.length} friend status elements for user ${userId}`);
    }

    // Update user status (legacy)
    updateUserStatus(userId, status) {
        const elements = document.querySelectorAll(`[data-friend-id="${userId}"] .status`);
        elements.forEach(element => {
            element.className = `status ${status}`;
            element.textContent = status === 'online' ? 'Trực tuyến' : 'Không trực tuyến';
        });
    }

    // Scroll to bottom of messages
    scrollToBottom() {
        const container = document.getElementById('messages-container');
        setTimeout(() => {
            container.scrollTop = container.scrollHeight;
        }, 100);
    }

    // Format timestamp
    formatTime(timestamp) {
        if (!timestamp) return '';

        const date = new Date(timestamp);
        const now = new Date();
        const diffTime = Math.abs(now - date);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        if (diffDays === 1) {
            return date.toLocaleTimeString('vi-VN', {
                hour: '2-digit',
                minute: '2-digit'
            });
        } else if (diffDays <= 7) {
            return date.toLocaleDateString('vi-VN', {
                weekday: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        } else {
            return date.toLocaleDateString('vi-VN', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric'
            });
        }
    }

    // Escape HTML to prevent XSS
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Clear form
    clearForm(formId) {
        document.getElementById(formId).reset();
    }

    // Set active conversation
    setActiveConversation(conversationId) {
        // Remove active class from all conversations
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
        });

        // Add active class to selected conversation
        const activeItem = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }
}

// Create global UI instance
const UI = new UIService();