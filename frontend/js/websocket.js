/**
 * WebSocket Service for Real-time Chat
 */

class WebSocketService {
    constructor() {
        this.ws = null;
        // Auto-detect WebSocket URL
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.origin.includes('onrender.com')
            ? window.location.host
            : '127.0.0.1:8000';
        this.url = `${protocol}//${host}/ws`;
        this.token = null;
        this.currentConversationId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000; // 3 seconds
        this.messageHandlers = [];
        this.connectionHandlers = [];
        this.pingInterval = null;
    }

    // Connect to WebSocket with token-based auth
    connect(token) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        this.token = token;
        // Use simplified endpoint for now
        const wsUrl = `${this.url}/${token}`;

        try {
            this.ws = new WebSocket(wsUrl);
            this.setupEventHandlers();
            console.log(`Connecting to WebSocket with token auth`);
        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleReconnect();
        }
    }

    // Join a conversation room for real-time messages
    joinConversation(conversationId) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.currentConversationId = conversationId;
            const joinMessage = {
                type: 'join_conversation',
                conversation_id: conversationId
            };
            console.log('🚪 Sending join_conversation message:', JSON.stringify(joinMessage));
            this.send(joinMessage);
            console.log(`✅ Joined conversation ${conversationId}`);
        } else {
            console.error('❌ Cannot join conversation - WebSocket not connected');
            console.log('WebSocket state:', this.ws ? this.ws.readyState : 'null');
        }
    }

    // Leave current conversation room
    leaveConversation() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN && this.currentConversationId) {
            this.send({
                type: 'leave_conversation',
                conversation_id: this.currentConversationId
            });
            console.log(`Left conversation ${this.currentConversationId}`);
            this.currentConversationId = null;
        }
    }

    // Setup WebSocket event handlers
    setupEventHandlers() {
        this.ws.onopen = (event) => {
            console.log('WebSocket connected successfully');
            this.reconnectAttempts = 0;
            this.notifyConnectionHandlers('connected');
            UI.showNotification('Đã kết nối real-time chat', 'success');

            // Send ping to keep connection alive every 30 seconds
            if (this.pingInterval) {
                clearInterval(this.pingInterval);
            }
            this.pingInterval = setInterval(() => {
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.send({ type: 'ping' });
                }
            }, 30000);

            // Auto-rejoin current conversation if exists
            if (this.currentConversationId) {
                console.log('🔄 Auto-rejoining conversation after reconnect:', this.currentConversationId);
                setTimeout(() => {
                    console.log('⏰ Auto-rejoin timeout triggered');
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        console.log('✅ WebSocket ready for auto-rejoin');
                        this.joinConversation(this.currentConversationId);
                    } else {
                        console.error('❌ WebSocket not ready for auto-rejoin');
                        console.log('WebSocket state:', this.ws ? this.ws.readyState : 'null');
                    }
                }, 100);
            } else {
                console.log('ℹ️ No current conversation to auto-rejoin');
            }
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', JSON.stringify(data, null, 2));
                this.handleMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
                console.log('Raw message:', event.data);
            }
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket connection closed:', event.code, event.reason);
            this.notifyConnectionHandlers('disconnected');

            if (event.code !== 1000) { // Not a normal closure
                this.handleReconnect();
            }
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.notifyConnectionHandlers('error');
        };
    }

    // Handle incoming messages
    handleMessage(data) {
        // Notify all message handlers
        this.messageHandlers.forEach(handler => {
            try {
                handler(data);
            } catch (error) {
                console.error('Error in message handler:', error);
            }
        });

        // Handle different message types
        switch (data.type) {
            case 'new_message':
                this.handleNewMessage(data);
                break;
            case 'pong':
                // Keep-alive response
                console.log('Received pong from server');
                break;
            case 'user_online':
                this.handleUserOnline(data);
                break;
            case 'user_offline':
                this.handleUserOffline(data);
                break;
            case 'conversation_updated':
                this.handleConversationUpdated(data);
                break;
            case 'member_kicked':
                this.handleMemberKicked(data);
                break;
            case 'member_added':
                this.handleMemberAdded(data);
                break;
            case 'kicked_from_conversation':
                this.handleKickedFromConversation(data);
                break;
            default:
                console.log('Unknown message type:', data.type);
        }
    }

    // Handle new message
    handleNewMessage(data) {
        const message = data.message;
        console.log('New message received:', message);

        // Let app.js handle UI updates
        // The main app already handles WebSocket messages in handleWebSocketMessage()

        // Show notification if not in current conversation
        if (!window.chatApp || window.chatApp.currentConversationId != message.conversation_id) {
            UI.showNotification(`${message.sender_username}: ${message.content}`, 'info');
        }
    }

    // Handle user online status
    handleUserOnline(data) {
        console.log('User online:', data.user_id);
        UI.updateUserOnlineStatus(data.user_id, true);
    }

    // Handle user offline status
    handleUserOffline(data) {
        console.log('User offline:', data.user_id);
        UI.updateUserOnlineStatus(data.user_id, false);
    }

    // Handle conversation updated
    handleConversationUpdated(data) {
        console.log('Conversation updated:', data.conversation);

        const conversation = data.conversation;

        // Update chat header if this is the current conversation
        if (window.chatApp && window.chatApp.currentConversationId === conversation.id) {
            document.getElementById('chat-title').textContent = conversation.name;
        }

        // Update in conversations list
        const conversationItem = document.querySelector(`[data-conversation-id="${conversation.id}"] .conversation-title`);
        if (conversationItem) {
            conversationItem.textContent = conversation.name;
        }

        // Show notification
        UI.showNotification(`Cuộc trò chuyện "${conversation.name}" đã được cập nhật`, 'info');
    }

    // Handle member kicked
    handleMemberKicked(data) {
        console.log('Member kicked:', data);

        const { conversation_id, kicked_user, kicked_by } = data;

        // Add system message to chat if this is the current conversation
        if (window.chatApp && window.chatApp.currentConversationId === conversation_id) {
            const systemMessage = {
                id: `system_${Date.now()}`,
                conversation_id: conversation_id,
                content: `${kicked_user.username} đã bị loại khỏi cuộc trò chuyện bởi ${kicked_by.username}`,
                created_at: new Date().toISOString(),
                is_system: true
            };

            // Add system message to UI
            UI.addSystemMessage(systemMessage);
        }

        // Reload conversations list
        if (window.chatApp) {
            window.chatApp.loadConversations();
        }

        UI.showNotification(`${kicked_user.username} đã bị loại khỏi cuộc trò chuyện`, 'warning');
    }

    // Handle member added
    handleMemberAdded(data) {
        console.log('Member added:', data);

        const { conversation_id, new_user, added_by } = data;

        // Add system message to chat if this is the current conversation
        if (window.chatApp && window.chatApp.currentConversationId === conversation_id) {
            const systemMessage = {
                id: `system_${Date.now()}`,
                conversation_id: conversation_id,
                content: `${new_user.username} đã được thêm vào cuộc trò chuyện bởi ${added_by.username}`,
                created_at: new Date().toISOString(),
                is_system: true
            };

            // Add system message to UI
            UI.addSystemMessage(systemMessage);
        }

        // Reload conversations list
        if (window.chatApp) {
            window.chatApp.loadConversations();
        }

        UI.showNotification(`${new_user.username} đã được thêm vào cuộc trò chuyện`, 'success');
    }

    // Handle being kicked from conversation
    handleKickedFromConversation(data) {
        console.log('Kicked from conversation:', data);

        UI.showNotification(data.message, 'error');

        // If user is currently in this conversation, redirect them
        if (window.chatApp && window.chatApp.currentConversationId === data.conversation_id) {
            // Clear current conversation
            window.chatApp.currentConversationId = null;
            document.getElementById('chat-title').textContent = 'Chọn cuộc trò chuyện';
            document.getElementById('messages-list').innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-ban" style="font-size: 48px; opacity: 0.3;"></i>
                    <p>Bạn đã bị loại khỏi cuộc trò chuyện này</p>
                </div>
            `;
        }

        // Reload conversations
        if (window.chatApp) {
            window.chatApp.loadConversations();
        }
    }

    // Send message through WebSocket
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            console.log('📤 Sending WebSocket message:', JSON.stringify(data));
            this.ws.send(JSON.stringify(data));
            console.log('✅ Message sent successfully');
        } else {
            console.warn('❌ WebSocket not connected, cannot send message:', data);
            console.log('WebSocket state:', this.ws ? this.ws.readyState : 'null');
        }
    }

    // Add message handler
    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    // Add connection handler
    onConnection(handler) {
        this.connectionHandlers.push(handler);
    }

    // Notify connection handlers
    notifyConnectionHandlers(status) {
        this.connectionHandlers.forEach(handler => {
            try {
                handler(status);
            } catch (error) {
                console.error('Error in connection handler:', error);
            }
        });
    }

    // Handle reconnection
    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            UI.showNotification('Mất kết nối WebSocket', 'error');
            return;
        }

        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

        setTimeout(() => {
            if (this.token) {
                this.connect(this.token);
            }
        }, this.reconnectInterval);
    }

    // Disconnect WebSocket
    disconnect() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
    }

    // Check if connected
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Create global instance
window.webSocket = new WebSocketService();