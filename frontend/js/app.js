/**
 * Main Application Logic
 */

class ChatApp {
    constructor() {
        this.currentUser = null;
        this.currentConversationId = null;
        this.conversations = [];
        this.friends = [];
        this.friendRequests = [];

        this.init();
    }

    // Initialize the application
    async init() {
        UI.showLoading();

        // Check if user is already logged in
        const token = localStorage.getItem('access_token');
        if (token) {
            try {
                api.setToken(token);
                await this.loadCurrentUser();
                await this.showMainApp();

                // Connect to WebSocket for real-time features
                this.connectWebSocket(token);
            } catch (error) {
                console.error('Failed to load user:', error);
                this.showAuthPage();
            }
        } else {
            this.showAuthPage();
        }

        UI.hideLoading();
        this.setupEventListeners();
    }

    // Connect to WebSocket
    connectWebSocket(token) {
        if (window.webSocket) {
            console.log('🔌 Connecting to WebSocket with token...');
            window.webSocket.connect(token);
        } else {
            console.error('❌ WebSocket service not available');
        }
    }

    // Add message to UI in real-time
    addMessageToUI(message) {
        console.log('🔍 addMessageToUI called with message:', message);

        // Prevent duplicate messages
        const existingMessage = document.querySelector(`[data-message-id="${message.id}"]`);
        if (existingMessage) {
            console.log('⚠️ Message already exists, skipping duplicate:', message.id);
            return;
        }

        // Determine if this message is from current user
        const isSent = message.sender_id === this.currentUser.id;

        // Use UI.addMessage to properly add the message
        UI.addMessage(message, isSent);

        console.log('✅ Added message to UI via WebSocket:', message);
    }    // Setup event listeners
    setupEventListeners() {
        // Auth tab switching
        document.querySelectorAll('.auth-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchAuthTab(tab);
            });
        });

        // Auth forms
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin(e);
        });

        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister(e);
        });

        // Sidebar tabs
        document.querySelectorAll('.sidebar-tabs .tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchSidebarTab(tab);
            });
        });

        // Logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            this.logout();
        });

        // Profile button
        document.getElementById('profile-btn').addEventListener('click', () => {
            this.showUserProfile();
        });

        // Message form
        document.getElementById('message-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Modal controls
        document.querySelectorAll('.close-modal').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal');
                if (modal) {
                    UI.hideModal(modal.id);
                }
            });
        });

        // Add friend button
        document.getElementById('add-friend-btn').addEventListener('click', () => {
            UI.showModal('add-friend-modal');
        });

        // New chat button - toggle dropdown
        document.getElementById('new-chat-btn').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleNewChatDropdown();
        });

        // New direct chat button
        document.getElementById('new-direct-chat-btn').addEventListener('click', () => {
            this.hideNewChatDropdown();
            this.showNewChatModal();
        });

        // New group chat button
        document.getElementById('new-group-chat-btn').addEventListener('click', () => {
            this.hideNewChatDropdown();
            this.showCreateGroupModal();
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', () => {
            this.hideNewChatDropdown();
        });

        // Conversation settings button
        document.getElementById('conversation-settings-btn').addEventListener('click', () => {
            this.showConversationSettings();
        });

        // Conversation settings form
        document.getElementById('conversation-settings-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateConversationSettings(e);
        });

        // Add member button
        document.getElementById('add-member-btn').addEventListener('click', () => {
            this.showAddMemberModal();
        });

        // Transfer admin button
        document.getElementById('transfer-admin-btn').addEventListener('click', () => {
            this.transferAdmin();
        });

        // Leave group button
        document.getElementById('leave-group-btn').addEventListener('click', () => {
            this.leaveGroup();
        });

        // Transfer admin select change
        document.getElementById('transfer-admin-select').addEventListener('change', (e) => {
            const transferBtn = document.getElementById('transfer-admin-btn');
            transferBtn.disabled = !e.target.value;
        });

        // Add friend form
        document.getElementById('add-friend-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendFriendRequest();
        });

        // Profile update form
        document.getElementById('profile-update-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateUserProfile(e);
        });

        // Password update form
        document.getElementById('password-update-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updateUserPassword(e);
        });

        // Profile tab buttons
        document.querySelectorAll('.profile-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchProfileTab(tab);
            });
        });

        // Create group form
        document.getElementById('create-group-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createGroup(e);
        });

        // Conversation clicks (delegated)
        document.getElementById('conversations-list').addEventListener('click', (e) => {
            const conversationItem = e.target.closest('.conversation-item');
            if (conversationItem) {
                const conversationId = parseInt(conversationItem.dataset.conversationId);
                this.selectConversation(conversationId);
            }
        });

        // Search functionality
        document.getElementById('search-input').addEventListener('input', (e) => {
            this.handleSearch(e.target.value);
        });

        // WebSocket message handler
        if (window.webSocket) {
            console.log('📡 Setting up WebSocket message handler...');
            window.webSocket.onMessage((data) => {
                console.log('📩 WebSocket message received in app:', data);
                this.handleWebSocketMessage(data);
            });
        } else {
            console.error('❌ WebSocket service not found during setup');
        }

        // Click outside modal to close
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                UI.hideModal(e.target.id);
            }
        });
    }

    // Switch auth tabs
    switchAuthTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.auth-tabs .tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update forms
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.toggle('active', form.id === `${tabName}-form`);
        });

        UI.clearMessage();
    }

    // Switch sidebar tabs
    switchSidebarTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.sidebar-tabs .tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tabName);
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });

        // Load data for the selected tab
        if (tabName === 'friends') {
            this.loadFriends();
            this.loadFriendRequests();
        }
    }

    // Handle login
    async handleLogin(event) {
        const formData = new FormData(event.target);
        const credentials = {
            username: formData.get('username'),
            password: formData.get('password')
        };

        try {
            UI.clearMessage();
            const response = await api.login(credentials);

            api.setToken(response.access_token);
            await this.loadCurrentUser();
            await this.showMainApp();

            UI.showNotification('Đăng nhập thành công!', 'success');
        } catch (error) {
            UI.showError(error.message);
        }
    }

    // Handle registration
    async handleRegister(event) {
        const formData = new FormData(event.target);
        const userData = {
            username: formData.get('username'),
            email: formData.get('email'),
            password: formData.get('password')
        };

        const confirmPassword = formData.get('confirmPassword');

        if (userData.password !== confirmPassword) {
            UI.showError('Mật khẩu xác nhận không khớp');
            return;
        }

        try {
            UI.clearMessage();
            await api.register(userData);

            UI.showSuccess('Đăng ký thành công! Bây giờ bạn có thể đăng nhập.');
            this.switchAuthTab('login');

            // Pre-fill login form
            document.getElementById('login-username').value = userData.username;
        } catch (error) {
            UI.showError(error.message);
        }
    }

    // Load current user
    async loadCurrentUser() {
        try {
            this.currentUser = await api.getCurrentUser();
            UI.updateCurrentUser(this.currentUser);
        } catch (error) {
            throw new Error('Failed to load user data');
        }
    }

    // Show auth page
    showAuthPage() {
        UI.showAuthContainer();
        if (window.webSocket) {
            window.webSocket.disconnect();
        }
    }

    // Show main app
    async showMainApp() {
        UI.showChatContainer();

        // Connect to WebSocket for real-time features
        const token = localStorage.getItem('access_token');
        if (token && (!window.webSocket || !window.webSocket.isConnected())) {
            console.log('🔌 Connecting WebSocket after login...');
            this.connectWebSocket(token);
        }

        // Load initial data
        await this.loadConversations();
        await this.loadFriends(); // Load friends to get online status
        await this.loadFriendRequests();

        // Select first conversation if available
        if (this.conversations.length > 0) {
            this.selectConversation(this.conversations[0].id);
        }
    }

    // Load conversations
    async loadConversations() {
        try {
            this.conversations = await api.getConversations();
            UI.renderConversations(this.conversations);
        } catch (error) {
            console.error('Failed to load conversations:', error);
            UI.showNotification('Không thể tải danh sách cuộc trò chuyện', 'error');
        }
    }

    // Load friends
    async loadFriends() {
        try {
            this.friends = await api.getFriends();
            UI.renderFriends(this.friends);
        } catch (error) {
            console.error('Failed to load friends:', error);
            UI.showNotification('Không thể tải danh sách bạn bè', 'error');
        }
    }

    // Load friend requests
    async loadFriendRequests() {
        try {
            this.friendRequests = await api.getFriendRequests();
            UI.renderFriendRequests(this.friendRequests);
        } catch (error) {
            console.error('Failed to load friend requests:', error);
            UI.showNotification('Không thể tải lời mời kết bạn', 'error');
        }
    }

    // Select conversation
    async selectConversation(conversationId) {
        try {
            // Leave current conversation room
            if (window.webSocket && this.currentConversationId) {
                window.webSocket.leaveConversation();
            }

            this.currentConversationId = conversationId;
            UI.setActiveConversation(conversationId);

            // Load conversation details
            const conversation = await api.getConversation(conversationId);
            UI.updateChatHeader(conversation);

            // Load messages
            const messages = await api.getMessages(conversationId);
            UI.renderMessages(messages);

            // Join new conversation room for real-time messages
            console.log('🔄 Selecting conversation:', conversationId);

            // Delay to ensure WebSocket is connected
            setTimeout(() => {
                if (window.webSocket && window.webSocket.isConnected()) {
                    console.log('🚪 Joining conversation via WebSocket:', conversationId);
                    window.webSocket.joinConversation(conversationId);
                } else {
                    console.error('❌ WebSocket not available or not connected for joining conversation');
                    console.log('WebSocket object:', window.webSocket);
                    console.log('Is connected:', window.webSocket ? window.webSocket.isConnected() : 'N/A');
                }
            }, 100); // 100ms delay

        } catch (error) {
            console.error('Failed to select conversation:', error);
            UI.showNotification('Không thể tải cuộc trò chuyện', 'error');
        }
    }

    // Send message
    async sendMessage() {
        const input = document.getElementById('message-input');
        const content = input.value.trim();

        if (!content || !this.currentConversationId) {
            return;
        }

        try {
            // Send through API
            const message = await api.sendMessage(this.currentConversationId, content);

            // DON'T add to UI here - let WebSocket handle it for real-time experience
            // UI.addMessage(message, true);

            // Clear input
            input.value = '';

            // Update conversation in sidebar
            UI.updateConversationLastMessage(
                this.currentConversationId,
                content,
                message.created_at
            );

        } catch (error) {
            console.error('Failed to send message:', error);
            UI.showNotification('Không thể gửi tin nhắn', 'error');
        }
    }

    // Send friend request
    async sendFriendRequest() {
        const input = document.getElementById('friend-username');
        const username = input.value.trim();

        if (!username) {
            return;
        }

        try {
            await api.sendFriendRequest(username);
            UI.showNotification('Đã gửi lời mời kết bạn!', 'success');
            UI.hideModal('add-friend-modal');
            UI.clearForm('add-friend-form');
        } catch (error) {
            UI.showNotification(error.message, 'error');
        }
    }

    // Respond to friend request
    async respondToFriendRequest(requestId, accept) {
        try {
            await api.respondToFriendRequest(requestId, accept);

            const action = accept ? 'chấp nhận' : 'từ chối';
            UI.showNotification(`Đã ${action} lời mời kết bạn`, 'success');

            // Reload friend requests and friends
            await this.loadFriendRequests();
            if (accept) {
                await this.loadFriends();
            }
        } catch (error) {
            UI.showNotification(error.message, 'error');
        }
    }

    // Show new chat modal
    async showNewChatModal() {
        try {
            // Load friends if not already loaded
            if (this.friends.length === 0) {
                await this.loadFriends();
            }

            UI.renderFriendsForChat(this.friends);
            UI.showModal('new-chat-modal');
        } catch (error) {
            UI.showNotification('Không thể tải danh sách bạn bè', 'error');
        }
    }

    // Create direct conversation
    async createDirectConversation(friendId) {
        try {
            const friend = this.friends.find(f => f.id === friendId);
            if (!friend) {
                throw new Error('Friend not found');
            }

            const conversation = await api.createConversation({
                type: 'direct',
                member_user_ids: [friendId]
            });

            UI.hideModal('new-chat-modal');
            UI.showNotification(`Đã tạo cuộc trò chuyện với ${friend.username}`, 'success');

            // Reload conversations and select the new one
            await this.loadConversations();
            this.selectConversation(conversation.id);

        } catch (error) {
            UI.showNotification(error.message, 'error');
        }
    }

    // Handle search
    handleSearch(query) {
        if (!query.trim()) {
            // Show all conversations
            UI.renderConversations(this.conversations);
            return;
        }

        // Filter conversations
        const filtered = this.conversations.filter(conv => {
            const name = UI.getConversationName(conv).toLowerCase();
            return name.includes(query.toLowerCase());
        });

        UI.renderConversations(filtered);
    }

    // Handle WebSocket messages
    updateConversationPreview(conversationId, lastMessage, timestamp) {
        const conversationElement = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (conversationElement) {
            const messagePreview = conversationElement.querySelector('.message-preview');
            const timeElement = conversationElement.querySelector('.timestamp');

            if (messagePreview) {
                messagePreview.textContent = lastMessage.length > 30 ? lastMessage.substring(0, 30) + '...' : lastMessage;
            }

            if (timeElement) {
                const time = new Date(timestamp);
                timeElement.textContent = time.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
            }

            // Move conversation to top of list
            const conversationsList = document.getElementById('conversations-list');
            if (conversationsList && conversationElement.parentNode === conversationsList) {
                conversationsList.insertBefore(conversationElement, conversationsList.firstChild);
            }
        }
    }

    handleWebSocketMessage(data) {
        console.log('🎯 App received WebSocket message:', JSON.stringify(data, null, 2));

        if (data.type === 'new_message') {
            const message = data.message;
            console.log('📨 Processing new message:', JSON.stringify(message, null, 2));
            console.log('🏠 Current conversation ID:', this.currentConversationId);
            console.log('💌 Message conversation ID:', message.conversation_id);

            // Add message to UI if we're in the right conversation
            if (this.currentConversationId == message.conversation_id) {
                console.log('✅ Adding message to UI...');
                this.addMessageToUI(message);
                console.log('📍 Added real-time message to UI:', message);
            } else {
                console.log('❌ Message not for current conversation');
            }

            // Update conversation preview in sidebar
            this.updateConversationPreview(message.conversation_id, message.content, message.created_at);
        } else {
            console.log('🔍 Non-message WebSocket data:', data.type);
        }
    }

    // Show conversation settings modal
    async showConversationSettings() {
        if (!this.currentConversationId) {
            UI.showNotification('Vui lòng chọn cuộc trò chuyện trước', 'warning');
            return;
        }

        try {
            // Load current conversation details
            const conversation = await api.getConversation(this.currentConversationId);

            // Fill form with current data
            document.getElementById('conversation-name').value = conversation.name || '';

            // Show/hide advanced settings based on conversation type
            const advancedSettings = document.getElementById('advanced-settings');
            if (conversation.type === 'group') {
                advancedSettings.style.display = 'block';
                await this.loadTransferAdminOptions();
            } else {
                advancedSettings.style.display = 'none';
            }

            // Load members
            await this.loadConversationMembers();

            UI.showModal('conversation-settings-modal');
        } catch (error) {
            console.error('Failed to load conversation settings:', error);
            UI.showNotification('Không thể tải cài đặt cuộc trò chuyện', 'error');
        }
    }

    // Load conversation members for settings
    async loadConversationMembers() {
        const membersContainer = document.getElementById('conversation-members');

        try {
            // Get detailed member information from API
            const members = await api.getConversationMembers(this.currentConversationId);

            membersContainer.innerHTML = members.map(member => `
                <div class="member-item">
                    <div class="member-info">
                        <i class="fas fa-user"></i>
                        <span class="member-name">${member.username}</span>
                        ${member.is_owner ? '<span class="owner-badge">👑 Chủ nhóm</span>' : ''}
                    </div>
                    ${member.id !== this.currentUser.id && this.isConversationAdmin() ? `
                        <button type="button" class="btn-small btn-danger" onclick="app.kickMember(${member.id}, '${member.username}')">
                            <i class="fas fa-user-times"></i> Loại
                        </button>
                    ` : ''}
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load members:', error);
            membersContainer.innerHTML = '<p>Không thể tải danh sách thành viên</p>';
        }
    }

    // Update conversation settings
    async updateConversationSettings(event) {
        const formData = new FormData(event.target);
        const name = formData.get('name').trim();
        const allowMemberAdd = document.getElementById('allow-member-add').checked;

        if (!name) {
            UI.showNotification('Vui lòng nhập tên cuộc trò chuyện', 'warning');
            return;
        }

        try {
            // Update conversation name
            const updatedConversation = await api.updateConversation(this.currentConversationId, name);

            // Update conversation settings
            const settings = {
                allow_member_add: allowMemberAdd
            };
            await api.updateConversationSettings(this.currentConversationId, settings);

            // Update UI
            document.getElementById('chat-title').textContent = updatedConversation.name;

            // Update in conversations list
            await this.loadConversations();

            UI.hideModal('conversation-settings-modal');
            UI.showNotification('Đã cập nhật cài đặt cuộc trò chuyện', 'success');
        } catch (error) {
            console.error('Failed to update conversation:', error);
            UI.showNotification('Không thể cập nhật cuộc trò chuyện', 'error');
        }
    }

    // Check if current user is admin of current conversation
    isConversationAdmin() {
        // For simplicity, assume first member is admin (creator)
        // In real implementation, you should store admin info
        return true; // TODO: implement proper admin check
    }

    // Kick member from conversation
    async kickMember(memberId, memberName) {
        if (!confirm(`Bạn có chắc muốn loại ${memberName} khỏi cuộc trò chuyện?`)) {
            return;
        }

        try {
            await api.kickMember(this.currentConversationId, memberId);

            // Reload members list
            await this.loadConversationMembers();

            UI.showNotification(`Đã loại ${memberName} khỏi cuộc trò chuyện`, 'success');
        } catch (error) {
            console.error('Failed to kick member:', error);
            if (error.message.includes('403')) {
                UI.showNotification('Bạn không có quyền loại thành viên', 'error');
            } else {
                UI.showNotification('Không thể loại thành viên', 'error');
            }
        }
    }

    // Show add member modal
    async showAddMemberModal() {
        try {
            // Load friends who are not already members
            await this.loadAvailableFriends();
            UI.showModal('add-member-modal');
        } catch (error) {
            console.error('Failed to load available friends:', error);
            UI.showNotification('Không thể tải danh sách bạn bè', 'error');
        }
    }

    // Load available friends for adding to conversation
    async loadAvailableFriends() {
        const friendsContainer = document.getElementById('available-friends');

        try {
            // Get all friends
            const allFriends = await api.getFriends();

            // Get current conversation members
            const currentMembers = await api.getConversationMembers(this.currentConversationId);
            const memberIds = currentMembers.map(m => m.id);

            // Filter friends who are not already members
            const availableFriends = allFriends.filter(friend => !memberIds.includes(friend.id));

            if (availableFriends.length === 0) {
                friendsContainer.innerHTML = '<p class="text-muted">Không có bạn bè nào có thể thêm</p>';
                return;
            }

            friendsContainer.innerHTML = availableFriends.map(friend => `
                <div class="friend-item" data-friend-id="${friend.id}">
                    <div class="friend-info">
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
                    <button class="btn-small btn-primary" onclick="app.addMemberToConversation(${friend.id}, '${friend.username}')">
                        <i class="fas fa-plus"></i> Thêm
                    </button>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load available friends:', error);
            friendsContainer.innerHTML = '<p>Không thể tải danh sách bạn bè</p>';
        }
    }

    // Add member to conversation
    async addMemberToConversation(friendId, friendName) {
        try {
            await api.addMember(this.currentConversationId, friendId);

            // Reload members list
            await this.loadConversationMembers();

            // Reload available friends (to remove the added friend)
            await this.loadAvailableFriends();

            UI.showNotification(`Đã thêm ${friendName} vào cuộc trò chuyện`, 'success');
        } catch (error) {
            console.error('Failed to add member:', error);
            if (error.message.includes('Cannot add members to direct conversations')) {
                UI.showNotification('Không thể thêm thành viên vào cuộc trò chuyện riêng', 'error');
            } else if (error.message.includes('Only conversation admin can add members')) {
                UI.showNotification('Chỉ admin mới có thể thêm thành viên', 'error');
            } else if (error.message.includes('403')) {
                UI.showNotification('Bạn không có quyền thêm thành viên', 'error');
            } else if (error.message.includes('400')) {
                UI.showNotification('Người này đã là thành viên của cuộc trò chuyện', 'warning');
            } else {
                UI.showNotification('Không thể thêm thành viên', 'error');
            }
        }
    }

    // Remove member from conversation (placeholder)
    async removeMemberFromConversation(memberId) {
        // This would require additional backend endpoint
        console.log('Remove member:', memberId);
        UI.showNotification('Tính năng xóa thành viên sẽ được phát triển', 'info');
    }

    // Dropdown management
    toggleNewChatDropdown() {
        const dropdown = document.getElementById('new-chat-menu');
        dropdown.style.display = dropdown.style.display === 'block' ? 'none' : 'block';
    }

    hideNewChatDropdown() {
        const dropdown = document.getElementById('new-chat-menu');
        dropdown.style.display = 'none';
    }

    // Show create group modal
    async showCreateGroupModal() {
        try {
            // Load friends list for group creation
            await this.loadGroupFriendsList();
            UI.showModal('create-group-modal');
        } catch (error) {
            console.error('Error loading friends for group:', error);
            UI.showNotification('Không thể tải danh sách bạn bè', 'error');
        }
    }

    // Load friends list with checkboxes for group creation
    async loadGroupFriendsList() {
        try {
            const friends = await api.getFriends();
            const container = document.getElementById('group-friends-list');

            if (friends.length === 0) {
                container.innerHTML = '<p class="no-data">Bạn chưa có bạn bè nào</p>';
                return;
            }

            container.innerHTML = friends.map(friend => `
                <div class="friend-item">
                    <label class="friend-checkbox">
                        <input type="checkbox" value="${friend.id}" data-name="${friend.username}">
                        <span class="friend-info">
                            <strong>${friend.username}</strong>
                            <small>${friend.email}</small>
                        </span>
                    </label>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error loading friends for group:', error);
            throw error;
        }
    }

    // Create group
    async createGroup(event) {
        try {
            const formData = new FormData(event.target);
            const groupName = formData.get('name').trim();

            if (!groupName) {
                UI.showNotification('Vui lòng nhập tên nhóm', 'error');
                return;
            }

            // Get selected friends
            const selectedFriends = [];
            const checkboxes = document.querySelectorAll('#group-friends-list input[type="checkbox"]:checked');
            checkboxes.forEach(checkbox => {
                selectedFriends.push(parseInt(checkbox.value));
            });

            // Create group via API
            const group = await api.createGroup(groupName, selectedFriends);

            // Close modal and reset form
            UI.hideModal('create-group-modal');
            event.target.reset();

            // Reload conversations
            await this.loadConversations();

            // Select the new group
            this.selectConversation(group.id);

            UI.showNotification(`Đã tạo nhóm "${groupName}" thành công`, 'success');

        } catch (error) {
            console.error('Error creating group:', error);
            UI.showNotification('Không thể tạo nhóm. Vui lòng thử lại.', 'error');
        }
    }

    // Load transfer admin options
    async loadTransferAdminOptions() {
        try {
            const members = await api.getConversationMembers(this.currentConversationId);
            const select = document.getElementById('transfer-admin-select');

            // Clear existing options
            select.innerHTML = '<option value="">Chọn thành viên...</option>';

            // Add members except current user
            members.forEach(member => {
                if (member.id !== this.currentUser.id && member.role !== 'admin') {
                    const option = document.createElement('option');
                    option.value = member.id;
                    option.textContent = member.username;
                    select.appendChild(option);
                }
            });

            // Disable transfer button
            document.getElementById('transfer-admin-btn').disabled = true;

        } catch (error) {
            console.error('Error loading transfer admin options:', error);
        }
    }

    // Transfer admin
    async transferAdmin() {
        const select = document.getElementById('transfer-admin-select');
        const newAdminId = parseInt(select.value);
        const newAdminName = select.options[select.selectedIndex].text;

        if (!newAdminId) {
            UI.showNotification('Vui lòng chọn thành viên để chuyển quyền admin', 'warning');
            return;
        }

        // Confirm transfer
        if (!confirm(`Bạn có chắc chắn muốn chuyển quyền admin cho ${newAdminName}? Bạn sẽ trở thành thành viên thường.`)) {
            return;
        }

        try {
            const result = await api.transferAdmin(this.currentConversationId, newAdminId);

            // Close modal
            UI.hideModal('conversation-settings-modal');

            // Reload conversation members
            await this.loadConversationMembers();

            UI.showNotification(result.message, 'success');

        } catch (error) {
            console.error('Error transferring admin:', error);
            UI.showNotification('Không thể chuyển quyền admin. Vui lòng thử lại.', 'error');
        }
    }

    // Leave group
    async leaveGroup() {
        // Confirm leave
        if (!confirm('Bạn có chắc chắn muốn rời khỏi nhóm này? Bạn sẽ không thể xem tin nhắn và tham gia cuộc trò chuyện này nữa.')) {
            return;
        }

        try {
            await api.leaveGroup(this.currentConversationId);

            // Close modal
            UI.hideModal('conversation-settings-modal');

            // Remove conversation from list and reload
            await this.loadConversations();

            // Clear current conversation
            this.currentConversationId = null;
            document.getElementById('messages-container').innerHTML = '';
            document.getElementById('chat-header').style.display = 'none';

            UI.showNotification('Đã rời khỏi nhóm thành công', 'success');

        } catch (error) {
            console.error('Error leaving group:', error);
            UI.showNotification('Không thể rời nhóm. Vui lòng thử lại.', 'error');
        }
    }

    // User Profile Management
    async showUserProfile() {
        try {
            // Load current user data
            const user = await api.getCurrentUser();

            // Fill profile form
            document.getElementById('profile-username').value = user.username;
            document.getElementById('profile-email').value = user.email;

            // Reset password form
            document.getElementById('password-update-form').reset();

            // Show profile info tab by default
            this.switchProfileTab('profile-info');

            UI.showModal('user-profile-modal');
        } catch (error) {
            console.error('Error loading user profile:', error);
            UI.showNotification('Không thể tải thông tin cá nhân', 'error');
        }
    }

    switchProfileTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.profile-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update tab content
        document.querySelectorAll('.profile-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');
    }

    async updateUserProfile(event) {
        try {
            const formData = new FormData(event.target);
            const profileData = {};

            const username = formData.get('username').trim();
            const email = formData.get('email').trim();

            if (!username || !email) {
                UI.showNotification('Vui lòng điền đầy đủ thông tin', 'warning');
                return;
            }

            if (username) profileData.username = username;
            if (email) profileData.email = email;

            const updatedUser = await api.updateUserProfile(profileData);

            // Update UI
            document.getElementById('current-username').textContent = updatedUser.username;
            this.currentUser = updatedUser;

            UI.hideModal('user-profile-modal');
            UI.showNotification('Cập nhật thông tin thành công', 'success');

        } catch (error) {
            console.error('Error updating profile:', error);
            if (error.message.includes('Username already exists')) {
                UI.showNotification('Tên đăng nhập đã tồn tại', 'error');
            } else if (error.message.includes('Email already exists')) {
                UI.showNotification('Email đã được sử dụng', 'error');
            } else {
                UI.showNotification('Không thể cập nhật thông tin. Vui lòng thử lại.', 'error');
            }
        }
    }

    async updateUserPassword(event) {
        try {
            const formData = new FormData(event.target);
            const currentPassword = formData.get('current_password');
            const newPassword = formData.get('new_password');
            const confirmPassword = formData.get('confirm_password');

            if (!currentPassword || !newPassword || !confirmPassword) {
                UI.showNotification('Vui lòng điền đầy đủ thông tin', 'warning');
                return;
            }

            if (newPassword !== confirmPassword) {
                UI.showNotification('Mật khẩu xác nhận không khớp', 'warning');
                return;
            }

            if (newPassword.length < 6) {
                UI.showNotification('Mật khẩu mới phải có ít nhất 6 ký tự', 'warning');
                return;
            }

            await api.updateUserPassword({
                current_password: currentPassword,
                new_password: newPassword
            });

            // Reset form
            event.target.reset();

            UI.hideModal('user-profile-modal');

            // Show countdown notification
            UI.showNotification('Đổi mật khẩu thành công. Đăng xuất trong 3 giây để bảo mật...', 'success');

            let countdown = 3;
            const countdownInterval = setInterval(() => {
                countdown--;
                if (countdown > 0) {
                    UI.showNotification(`Đổi mật khẩu thành công. Đăng xuất trong ${countdown} giây...`, 'success');
                } else {
                    clearInterval(countdownInterval);
                    this.logout();
                }
            }, 1000);

        } catch (error) {
            console.error('Error updating password:', error);
            if (error.message.includes('Current password is incorrect')) {
                UI.showNotification('Mật khẩu hiện tại không đúng', 'error');
            } else {
                UI.showNotification('Không thể đổi mật khẩu. Vui lòng thử lại.', 'error');
            }
        }
    }

    // Logout
    logout() {
        api.removeToken();

        // Disconnect WebSocket
        if (window.webSocket) {
            window.webSocket.disconnect();
        }

        this.currentUser = null;
        this.currentConversationId = null;
        this.conversations = [];
        this.friends = [];
        this.friendRequests = [];

        this.showAuthPage();
        UI.showNotification('Đã đăng xuất', 'info');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();  // Make globally accessible for WebSocket
    window.app = window.chatApp;     // Keep backward compatibility
});

// Global error handler
window.addEventListener('error', (e) => {
    console.error('Global error:', e.error);
    UI.showNotification('Đã xảy ra lỗi. Vui lòng thử lại.', 'error');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (e) => {
    console.error('Unhandled promise rejection:', e.reason);
    UI.showNotification('Đã xảy ra lỗi. Vui lòng thử lại.', 'error');
});