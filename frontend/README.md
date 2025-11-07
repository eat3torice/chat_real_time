# Real-time Chat Application Frontend

Giao diện người dùng hoàn chỉnh cho ứng dụng chat real-time với FastAPI backend.

## 🌟 Tính năng

### ✅ **Authentication (Xác thực)**
- Đăng ký tài khoản mới
- Đăng nhập/Đăng xuất
- Tự động lưu trạng thái đăng nhập

### 💬 **Chat Real-time**
- Gửi/nhận tin nhắn real-time qua WebSocket
- Hiển thị trạng thái online/offline
- Cuộc trò chuyện 1-1 và nhóm
- Tự động cuộn xuống tin nhắn mới

### 👥 **Quản lý bạn bè**
- Gửi lời mời kết bạn
- Chấp nhận/Từ chối lời mời
- Danh sách bạn bè với trạng thái online

### 🔍 **Tìm kiếm**
- Tìm kiếm cuộc trò chuyện
- Tìm kiếm bạn bè

### 📱 **Responsive Design**
- Tương thích với desktop và mobile
- Giao diện hiện đại, thân thiện

## 📁 Cấu trúc Frontend

```
frontend/
├── index.html          # Trang chính
├── css/
│   └── style.css       # Styles chính
└── js/
    ├── api.js          # API Service (HTTP requests)
    ├── websocket.js    # WebSocket Service
    ├── ui.js           # UI Management
    └── app.js          # Main Application Logic
```

## 🚀 Cách sử dụng

### 1. **Khởi động Backend**
```bash
cd d:/chat_real_time
uvicorn app.main:app --reload
```

### 2. **Truy cập ứng dụng**
Mở trình duyệt và truy cập: `http://127.0.0.1:8000`

### 3. **Đăng ký tài khoản**
- Click tab "Đăng ký"
- Nhập thông tin: Username, Email, Password
- Click "Đăng ký"

### 4. **Đăng nhập**
- Click tab "Đăng nhập"
- Nhập Username và Password
- Click "Đăng nhập"

### 5. **Sử dụng chat**
- **Thêm bạn**: Click icon "+" ở tab Bạn bè
- **Tạo cuộc trò chuyện**: Click icon "+" ở tab Trò chuyện
- **Gửi tin nhắn**: Chọn cuộc trò chuyện và nhập tin nhắn

## 🛠️ Technical Stack

### Frontend
- **HTML5** - Cấu trúc trang
- **CSS3** - Styling với Flexbox/Grid
- **Vanilla JavaScript** - Logic ứng dụng
- **WebSocket API** - Real-time communication
- **Fetch API** - HTTP requests

### Backend Integration
- **FastAPI** - REST API endpoints
- **WebSocket** - Real-time messaging
- **JWT** - Authentication
- **PostgreSQL** - Database

## 📡 API Endpoints sử dụng

### Authentication
- `POST /auth/register` - Đăng ký
- `POST /auth/login` - Đăng nhập  
- `GET /auth/me` - Thông tin user hiện tại

### Friends
- `GET /friends` - Danh sách bạn bè
- `POST /friends/request` - Gửi lời mời kết bạn
- `GET /friends/requests` - Lời mời kết bạn
- `PUT /friends/requests/{id}/accept` - Chấp nhận lời mời
- `PUT /friends/requests/{id}/reject` - Từ chối lời mời

### Conversations
- `GET /conversations` - Danh sách cuộc trò chuyện
- `POST /conversations` - Tạo cuộc trò chuyện mới
- `GET /conversations/{id}` - Chi tiết cuộc trò chuyện

### Messages
- `GET /messages/conversation/{id}` - Lấy tin nhắn
- `POST /messages` - Gửi tin nhắn

### WebSocket
- `WS /ws/{user_id}` - Real-time connection

## 🎨 UI Components

### Auth Container
- Login/Register forms
- Tab switching
- Validation messages

### Chat Container
- Sidebar với tabs (Conversations/Friends)
- Main chat area
- Message input với emoji support

### Modals
- Add Friend modal
- New Chat modal
- Settings modal

### Notifications
- Toast notifications
- Real-time alerts
- Success/Error messages

## 🔧 Configuration

### API Configuration
Sửa file `js/api.js`:
```javascript
this.baseURL = 'http://your-api-url.com';
```

### WebSocket Configuration  
Sửa file `js/websocket.js`:
```javascript
this.url = 'ws://your-websocket-url.com/ws';
```

## 🐛 Troubleshooting

### Lỗi kết nối API
- Kiểm tra backend đang chạy
- Kiểm tra CORS settings
- Xem Network tab trong DevTools

### Lỗi WebSocket
- Kiểm tra WebSocket endpoint
- Xem Console logs
- Kiểm tra authentication token

### Lỗi hiển thị
- Clear browser cache
- Kiểm tra CSS/JS files
- Xem Console errors

## 📱 Mobile Support

Ứng dụng được tối ưu cho mobile với:
- Responsive breakpoints
- Touch-friendly buttons
- Optimized layouts
- Mobile-first design

## 🔒 Security Features

- JWT token authentication
- XSS protection với HTML escaping
- CORS configuration
- Secure WebSocket connections

## 🎯 Future Enhancements

- [ ] File/Image sharing
- [ ] Voice messages
- [ ] Push notifications
- [ ] Dark/Light theme
- [ ] Message reactions
- [ ] Typing indicators
- [ ] Message editing/deletion
- [ ] Group admin features
- [ ] User profiles

## 📞 Support

Nếu gặp vấn đề, hãy:
1. Kiểm tra Console logs
2. Xem Network requests
3. Kiểm tra backend logs
4. Restart cả frontend và backend