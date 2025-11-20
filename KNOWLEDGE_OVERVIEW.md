# 📚 TỔNG QUAN KIẾN THỨC DỰ ÁN CHAT REAL-TIME

## 🏗️ KIẾN TRÚC TỔNG QUAN

### Tech Stack
- **Backend Framework**: FastAPI (Python 3.11)
- **Database**: PostgreSQL 15
- **Cache/Pub-Sub**: Redis 7
- **Real-time Communication**: WebSocket
- **ORM**: SQLAlchemy 2.0.31
- **Database Migration**: Alembic 1.13.2
- **Authentication**: JWT (JSON Web Token)
- **Password Hashing**: Bcrypt
- **Containerization**: Docker + Docker Compose

### Kiến trúc hệ thống
```
┌─────────────────┐
│  Client Browser │
│   (HTML/JS)     │
└────────┬────────┘
         │ HTTP REST API
         │ WebSocket
┌────────▼────────┐
│  FastAPI Server │
│  (Python 3.11)  │
└────┬───────┬────┘
     │       │
     │       └──────► Redis (Real-time state, Pub/Sub)
     │
     └──────────────► PostgreSQL (Data persistence)
```

---

## 🔐 AUTHENTICATION & SECURITY

### JWT Authentication Flow
```python
# 1. Token Structure
{
    "id": user_id,           # User ID
    "username": "username",  # Username
    "iat": 1700000000,      # Issued at timestamp
    "exp": 1700003600       # Expiration timestamp (60 min)
}

# 2. Token Generation
SECRET_KEY = "skibidy_sigma_king"  # Thay đổi trong production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

**Authentication Flow:**
1. User đăng nhập với username/email + password
2. Server verify credentials với bcrypt
3. Server tạo JWT token với SECRET_KEY
4. Client lưu token trong `localStorage`
5. Client gửi token trong header: `Authorization: Bearer <token>`
6. Server decode & validate token cho mỗi protected request

### Password Security
- **Hashing Algorithm**: Bcrypt với automatic salt
- **Password Verification**: Constant-time comparison
- **Password Rehashing**: Tự động update hash nếu policy thay đổi

```python
# Hashing
password_hash = hash_password(plain_password)

# Verification
is_valid = verify_password(plain_password, password_hash)

# Auto rehashing
if needs_rehash(password_hash):
    password_hash = hash_password(plain_password)
```

---

## 🗄️ DATABASE DESIGN

### Entity Relationship Diagram
```
┌──────────┐         ┌─────────────┐         ┌──────────┐
│  User    │◄───────►│ Friendship  │◄───────►│  User    │
└────┬─────┘         └─────────────┘         └──────────┘
     │
     │ 1:N
     │
     ▼
┌─────────────────────┐
│ ConversationMember  │
└──────────┬──────────┘
           │ N:1
           ▼
     ┌─────────────┐
     │Conversation │
     └──────┬──────┘
            │ 1:N
            ▼
      ┌─────────┐
      │ Message │
      └─────────┘
```

### Database Models

#### 1. User (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
```

**Relationships:**
- `sent_friend_requests` → Friendship (1:N)
- `received_friend_requests` → Friendship (1:N)
- `conversation_memberships` → ConversationMember (1:N)
- `messages` → Message (1:N)

#### 2. Friendship (friendships)
```sql
CREATE TABLE friendships (
    id SERIAL PRIMARY KEY,
    requester_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_friendship_requester_receiver UNIQUE(requester_id, receiver_id),
    CONSTRAINT chk_friendship_status CHECK(status IN ('pending', 'accepted', 'rejected')),
    CONSTRAINT chk_friendship_no_self CHECK(requester_id <> receiver_id)
);
```

**Status Values:**
- `pending` - Lời mời chờ xác nhận
- `accepted` - Đã là bạn bè
- `rejected` - Đã từ chối

#### 3. Conversation (conversations)
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    name TEXT,  -- NULL cho direct chat, có giá trị cho group chat
    type TEXT NOT NULL DEFAULT 'direct',
    private_pair_key TEXT,  -- Để tránh duplicate direct conversations
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_conversation_type CHECK(type IN ('direct', 'group'))
);
```

**Conversation Types:**
- `direct` - Chat 1-1 giữa 2 users
- `group` - Chat nhóm với nhiều users

**Private Pair Key:** `direct:{smaller_user_id}:{larger_user_id}`
- Ví dụ: `direct:1:5` cho conversation giữa user 1 và user 5
- Đảm bảo không tạo duplicate direct conversations

#### 4. ConversationMember (conversation_members)
```sql
CREATE TABLE conversation_members (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role TEXT NOT NULL DEFAULT 'member',
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT uq_conversation_user UNIQUE(conversation_id, user_id),
    CONSTRAINT chk_conversation_member_role CHECK(role IN ('admin', 'member'))
);
```

**Roles:**
- `admin` - Quản trị viên (group chat)
- `member` - Thành viên thường

#### 5. Message (messages)
```sql
CREATE TABLE messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

**Message Types:**
- `text` - Text message
- `image` - Image (future)
- `file` - File attachment (future)

---

## 🔌 WEBSOCKET ARCHITECTURE

### WebSocket Manager Pattern

```python
class SimpleWebSocketManager:
    def __init__(self):
        # user_id → Set[WebSocket connections]
        self.connections: Dict[int, Set] = defaultdict(set)
        
        # conversation_id → Set[user_ids]
        self.conversation_members: Dict[int, Set[int]] = defaultdict(set)
```

### Core Functions

#### 1. Connection Management
```python
async def connect(user_id: int, websocket: WebSocket):
    """
    - Add websocket to connections
    - Broadcast user online status to friends
    - Send friends' online status to this user
    """
    was_offline = user_id not in self.connections
    self.connections[user_id].add(websocket)
    
    if was_offline:
        await self.broadcast_user_status(user_id, True)
    
    await self.send_friends_status(user_id)

async def disconnect(user_id: int, websocket: WebSocket):
    """
    - Remove websocket from connections
    - Broadcast user offline status if no more connections
    """
    self.connections[user_id].discard(websocket)
    is_now_offline = not self.connections[user_id]
    
    if is_now_offline:
        self.connections.pop(user_id, None)
        await self.broadcast_user_status(user_id, False)
```

#### 2. Room/Conversation Management
```python
async def join_conversation(user_id: int, conversation_id: int):
    """User joins a conversation room to receive real-time messages"""
    self.conversation_members[conversation_id].add(user_id)

async def send_to_conversation(conversation_id: int, message: dict):
    """Broadcast message to all members in conversation"""
    user_ids = self.conversation_members.get(conversation_id, set())
    for user_id in user_ids:
        await self.send_to_user(user_id, message)

async def send_to_user(user_id: int, message: dict):
    """Send message to specific user (all their connections)"""
    connections = self.connections.get(user_id, set())
    message_text = json.dumps(message)
    for ws in connections:
        await ws.send_text(message_text)
```

### WebSocket Events

**Client → Server:**
```javascript
// Ping để keep connection alive
{type: "ping"}

// Join conversation để nhận messages
{type: "join_conversation", conversation_id: 123}

// Leave conversation
{type: "leave_conversation", conversation_id: 123}
```

**Server → Client:**
```javascript
// Pong response
{type: "pong"}

// Connection established
{type: "connected", message: "WebSocket connected successfully"}

// New message in conversation
{
    type: "new_message",
    message: {
        id: 456,
        conversation_id: 123,
        sender_id: 789,
        sender_username: "john_doe",
        content: "Hello!",
        created_at: "2025-11-20T10:30:00"
    }
}

// User came online
{type: "user_online", user_id: 789}

// User went offline
{type: "user_offline", user_id: 789}
```

### WebSocket Connection Flow
```
1. Client connects: ws://localhost:8000/ws/{jwt_token}
2. Server verifies JWT token
3. Server accepts connection
4. Server registers user in WebSocket manager
5. Server sends welcome message
6. Server broadcasts user online status to friends
7. Server sends friends' online status to user
8. Client can join conversations and send/receive messages
```

---

## 🚀 API ENDPOINTS

### Authentication Routes (`/auth`)

#### POST `/auth/register`
**Đăng ký user mới**
```json
Request:
{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123"
}

Response:
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
}
```

#### POST `/auth/login`
**Đăng nhập và lấy JWT token**
```json
Request:
{
    "username": "john_doe",  // hoặc email
    "password": "SecurePass123"
}

Response:
{
    "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### GET `/auth/me`
**Lấy thông tin user hiện tại**
```json
Headers: Authorization: Bearer {token}

Response:
{
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
}
```

### Friends Routes (`/friends`)

#### GET `/friends`
**Lấy danh sách bạn bè**
```json
Response:
[
    {
        "id": 2,
        "username": "jane_doe",
        "email": "jane@example.com",
        "is_online": true
    }
]
```

#### GET `/friends/requests`
**Lấy lời mời kết bạn đang pending**
```json
Response:
[
    {
        "id": 1,
        "requester": {
            "id": 3,
            "username": "bob",
            "email": "bob@example.com"
        },
        "created_at": "2025-11-20T10:00:00",
        "status": "pending"
    }
]
```

#### POST `/friends/request`
**Gửi lời mời kết bạn**
```json
Request:
{
    "username": "jane_doe"
}

Response:
{
    "message": "Friend request sent successfully"
}
```

#### PUT `/friends/requests/{request_id}/accept`
**Chấp nhận lời mời kết bạn**
```json
Response:
{
    "message": "Friend request accepted"
}
```

#### PUT `/friends/requests/{request_id}/reject`
**Từ chối lời mời kết bạn**
```json
Response:
{
    "message": "Friend request rejected"
}
```

### Conversations Routes (`/conversations`)

#### GET `/conversations`
**Lấy tất cả conversations của user**
```json
Response:
[
    {
        "id": 1,
        "name": null,
        "type": "direct",
        "private_pair_key": "direct:1:2",
        "member_ids": [1, 2]
    },
    {
        "id": 2,
        "name": "Team Chat",
        "type": "group",
        "private_pair_key": null,
        "member_ids": [1, 2, 3, 4]
    }
]
```

#### GET `/conversations/{conversation_id}`
**Lấy chi tiết một conversation**
```json
Response:
{
    "id": 1,
    "name": null,
    "type": "direct",
    "private_pair_key": "direct:1:2",
    "member_ids": [1, 2]
}
```

#### POST `/conversations`
**Tạo conversation mới**
```json
Request (Direct chat):
{
    "type": "direct",
    "member_user_ids": [2]
}

Request (Group chat):
{
    "type": "group",
    "name": "Team Chat",
    "member_user_ids": [2, 3, 4]
}

Response:
{
    "id": 1,
    "name": null,
    "type": "direct",
    "member_ids": [1, 2]
}
```

### Messages Routes (`/messages`)

#### GET `/messages/conversation/{conversation_id}`
**Lấy messages với pagination**
```json
Query Params:
- skip: 0 (default)
- limit: 50 (default, max 100)

Response:
[
    {
        "id": 1,
        "conversation_id": 1,
        "sender_id": 2,
        "sender_username": "jane_doe",
        "content": "Hello!",
        "created_at": "2025-11-20T10:00:00"
    }
]
```

#### POST `/messages`
**Gửi message mới**
```json
Request:
{
    "conversation_id": 1,
    "content": "Hello, how are you?"
}

Response:
{
    "id": 1,
    "conversation_id": 1,
    "sender_id": 1,
    "sender_username": "john_doe",
    "content": "Hello, how are you?",
    "created_at": "2025-11-20T10:00:00"
}
```

---

## 📡 REAL-TIME FEATURES

### 1. Online/Offline Status
```
User A connects
    ↓
WebSocket Manager tracks connection
    ↓
Query database for User A's friends
    ↓
Broadcast "user_online" event to all friends
    ↓
Send online status of all friends to User A
```

**Implementation:**
- Sử dụng `websocket_manager.connections` để track
- Chỉ notify friends (không broadcast đến tất cả users)
- Support multiple connections per user (mobile + desktop)

### 2. Real-time Messaging Flow
```
User A gửi message
    ↓
POST /messages API endpoint
    ↓
Validate user là member của conversation
    ↓
Lưu message vào PostgreSQL
    ↓
websocket_manager.send_to_conversation()
    ↓
Broadcast đến tất cả members đang online
    ↓
Client nhận qua WebSocket listener
    ↓
UI update real-time
```

### 3. Conversation Rooms
- User phải "join" conversation để nhận real-time messages
- Khi chuyển conversation, leave old và join new
- Auto-rejoin sau reconnect

---

## 🎨 FRONTEND ARCHITECTURE

### File Structure
```
frontend/
├── index.html              # Main application
├── ws-test.html           # WebSocket testing
├── css/
│   └── style.css          # All styling
└── js/
    ├── app.js             # Main app logic & state
    ├── api.js             # HTTP API calls
    ├── ui.js              # DOM manipulation
    └── websocket.js       # WebSocket service
```

### JavaScript Architecture

#### ChatApp Class (app.js)
```javascript
class ChatApp {
    // State management
    currentUser = null;
    currentConversationId = null;
    conversations = [];
    friends = [];
    friendRequests = [];
    
    // Lifecycle
    async init()
    connectWebSocket(token)
    
    // UI switching
    showAuthPage()
    showMainApp()
    switchSidebarTab(tab)
    switchConversation(id)
    
    // User actions
    async handleLogin(e)
    async handleRegister(e)
    async sendMessage()
    async loadConversations()
    async loadFriends()
    
    // Real-time
    addMessageToUI(message)
}
```

#### API Service (api.js)
```javascript
class API {
    baseURL = 'http://127.0.0.1:8000';
    token = null;
    
    setToken(token)
    
    // Auth
    async login(username, password)
    async register(username, email, password)
    async getCurrentUser()
    
    // Conversations
    async getConversations()
    async createConversation(data)
    
    // Messages
    async getMessages(conversationId, skip, limit)
    async sendMessage(conversationId, content)
    
    // Friends
    async getFriends()
    async getFriendRequests()
    async sendFriendRequest(username)
    async acceptFriendRequest(requestId)
    async rejectFriendRequest(requestId)
}
```

#### WebSocket Service (websocket.js)
```javascript
class WebSocketService {
    ws = null;
    token = null;
    currentConversationId = null;
    reconnectAttempts = 0;
    maxReconnectAttempts = 5;
    
    // Connection
    connect(token)
    disconnect()
    handleReconnect()
    
    // Room management
    joinConversation(conversationId)
    leaveConversation()
    
    // Messaging
    send(data)
    
    // Event handlers
    onMessage(handler)
    onConnection(handler)
    setupEventHandlers()
}
```

#### UI Manager (ui.js)
```javascript
const UI = {
    // Display
    showLoading()
    hideLoading()
    showNotification(message, type)
    
    // Conversations
    updateConversationList(conversations)
    
    // Messages
    clearMessages()
    addMessage(message, isSent)
    
    // Friends
    updateFriendsList(friends)
    updateFriendRequestsList(requests)
    updateOnlineStatus(userId, isOnline)
}
```

---

## 🐳 DOCKER & DEPLOYMENT

### Docker Compose Services

```yaml
version: "3.8"

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: 123456789
      POSTGRES_DB: chat_real_time
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  # Redis Cache
  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: ["redis-server", "--save", "", "--appendonly", "no"]

  # FastAPI Application
  web:
    build: .
    depends_on:
      - redis
      - postgres
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # RedisInsight (Optional)
  redisinsight:
    image: redislabs/redisinsight:latest
    ports:
      - "8001:8001"
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc libpq-dev build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Environment Variables (.env)
```bash
# Database
DATABASE_URL=postgresql://postgres:123456789@postgres:5432/chat_real_time

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=skibidy_sigma_king  # THAY ĐỔI TRONG PRODUCTION!
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application
CREATE_DB_ON_STARTUP=true
```

---

## 🔧 APPLICATION LIFECYCLE

### Startup Sequence
```python
@app.on_event("startup")
async def on_startup():
    # 1. Create database tables (development only)
    if settings.CREATE_DB_ON_STARTUP:
        Base.metadata.create_all(bind=engine)
    
    # 2. Start WebSocket manager
    await websocket_manager.start()
    
    # 3. Connect to Redis (if using Redis pub/sub)
    # await redis_client.connect()
```

### Shutdown Sequence
```python
@app.on_event("shutdown")
async def on_shutdown():
    # 1. Stop WebSocket manager gracefully
    await websocket_manager.stop()
    
    # 2. Close Redis connections
    # await redis_client.close()
    
    # 3. Close database connections
    # engine.dispose()
```

---

## 🛡️ SECURITY BEST PRACTICES

### 1. Authentication
- ✅ JWT tokens với expiration (60 minutes)
- ✅ Bcrypt password hashing
- ✅ Token validation trên mọi protected routes
- ⚠️ Cần thay đổi SECRET_KEY trong production
- 🔄 TODO: Implement refresh tokens
- 🔄 TODO: Rate limiting cho login attempts

### 2. Authorization
- ✅ Verify user là member trước khi access conversation
- ✅ Verify user là member trước khi send message
- ✅ Check friendship status trước khi create direct conversation

### 3. Input Validation
- ✅ Pydantic schemas validate tất cả input
- ✅ SQL injection prevented by SQLAlchemy ORM
- ✅ XSS prevention: sanitize user input

### 4. CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # THAY ĐỔI trong production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 5. WebSocket Security
- ✅ Token-based authentication
- ✅ Verify JWT trước khi accept connection
- ✅ Validate user permissions cho mọi action

---

## 📈 PERFORMANCE & SCALABILITY

### Current Architecture
- **Single server** instance
- **In-memory** WebSocket manager
- **Connection limit**: Depends on server resources

### Scalability Strategies

#### 1. Horizontal Scaling với Redis Pub/Sub
```python
# Publisher (Server A)
await redis.publish('conversation:123', message_json)

# Subscriber (Server B)
async for message in pubsub.listen():
    await websocket_manager.send_to_conversation(...)
```

#### 2. Load Balancing
```nginx
upstream chat_backend {
    least_conn;
    server server1:8000;
    server server2:8000;
    server server3:8000;
}

# Sticky sessions cho WebSocket
hash $remote_addr consistent;
```

#### 3. Database Optimization
- ✅ Indexes trên frequently queried columns
- 🔄 TODO: Connection pooling tuning
- 🔄 TODO: Read replicas cho scaling reads
- 🔄 TODO: Partitioning messages table by date

#### 4. Caching Strategy
```python
# Cache conversation members
@cache(ttl=300)  # 5 minutes
async def get_conversation_members(conversation_id):
    ...

# Cache user friends list
@cache(ttl=600)  # 10 minutes
async def get_user_friends(user_id):
    ...
```

---

## 🔍 DEBUGGING & MONITORING

### Logging Strategy
```python
import logging

logger = logging.getLogger("app.main")

# Levels
logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error occurred", exc_info=True)
logger.critical("Critical failure")
```

### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "message": "chat_real_time running",
        "websocket_connections": len(websocket_manager.connections),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### WebSocket Debugging
```javascript
// Browser console
webSocket.ws.readyState
// 0 = CONNECTING
// 1 = OPEN
// 2 = CLOSING
// 3 = CLOSED

// Monitor messages
webSocket.onMessage((data) => {
    console.log('📨 Received:', data);
});
```

---

## 🎯 KEY DESIGN PATTERNS

### 1. Dependency Injection (FastAPI)
```python
# Database session injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Usage
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# User authentication injection
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### 2. Repository Pattern (CRUD)
```python
# crud/user_crud.py
def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(**user_data.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_id(db: Session, user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()
```

### 3. Schema Separation
```python
# Database Model (models.py)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    password_hash = Column(String)

# Input Schema (schemas/auth_schema.py)
class UserCreate(BaseModel):
    username: str
    password: str

# Output Schema (schemas/auth_schema.py)
class UserOut(BaseModel):
    id: int
    username: str
    # No password!
```

### 4. Service Layer Pattern
```python
# chat/services.py
def get_or_create_direct_conversation(
    db: Session, 
    user_a: int, 
    user_b: int
) -> Dict:
    # Business logic
    conv = get_direct_conversation_between(db, user_a, user_b)
    if not conv:
        conv = create_direct_conversation(db, user_a, user_b)
    return conversation_to_dict(conv)
```

---

## 📚 LEARNING RESOURCES

### Core Technologies
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Alembic**: https://alembic.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/
- **Redis**: https://redis.io/docs/
- **WebSocket**: https://developer.mozilla.org/en-US/docs/Web/API/WebSocket

### Concepts & Patterns
- **REST API Design**: https://restfulapi.net/
- **JWT Authentication**: https://jwt.io/introduction
- **WebSocket Protocol**: https://datatracker.ietf.org/doc/html/rfc6455
- **Database Normalization**: https://en.wikipedia.org/wiki/Database_normalization
- **Dependency Injection**: https://en.wikipedia.org/wiki/Dependency_injection
- **Repository Pattern**: https://martinfowler.com/eaaCatalog/repository.html

### Python Async Programming
- **asyncio**: https://docs.python.org/3/library/asyncio.html
- **ASGI**: https://asgi.readthedocs.io/
- **Async/await**: https://realpython.com/async-io-python/

---

## 🚀 QUICK START GUIDE

### 1. Development Setup
```bash
# Clone repository
git clone https://github.com/eat3torice/chat_real_time.git
cd chat_real_time

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env với database credentials
```

### 2. Database Setup
```bash
# Start PostgreSQL & Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Or create tables directly (development)
# Set CREATE_DB_ON_STARTUP=true in .env
```

### 3. Run Application
```bash
# Development mode với auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Access application
# http://localhost:8000
# http://localhost:8000/docs (API documentation)
```

### 4. Testing
```bash
# Manual WebSocket test
# http://localhost:8000/manual_ws_test.html

# Frontend test
# http://localhost:8000
```

---

## 📋 TODO & IMPROVEMENTS

### High Priority
- [ ] Implement refresh tokens
- [ ] Add rate limiting
- [ ] File upload support (images, files)
- [ ] Message read receipts
- [ ] Typing indicators
- [ ] User avatars

### Medium Priority
- [ ] Search messages
- [ ] Delete messages
- [ ] Edit messages
- [ ] Group chat admin features
- [ ] User blocking
- [ ] Notification system

### Low Priority
- [ ] Voice messages
- [ ] Video calls
- [ ] Message reactions (emoji)
- [ ] Message threading
- [ ] Dark mode

### Infrastructure
- [ ] Redis Pub/Sub for multi-server
- [ ] Prometheus metrics
- [ ] ELK stack logging
- [ ] CI/CD pipeline
- [ ] Automated testing
- [ ] Performance benchmarking

---

## 🤝 CONTRIBUTING

### Code Style
- **Python**: Follow PEP 8
- **JavaScript**: ES6+ syntax
- **SQL**: Lowercase keywords, snake_case names

### Git Workflow
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Commit changes
git add .
git commit -m "feat: add your feature"

# Push to remote
git push origin feature/your-feature-name

# Create pull request
```

### Commit Message Convention
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Formatting
- `refactor:` - Code restructuring
- `test:` - Adding tests
- `chore:` - Maintenance

---

## 📞 SUPPORT & CONTACT

- **Repository**: https://github.com/eat3torice/chat_real_time
- **Issues**: https://github.com/eat3torice/chat_real_time/issues
- **Owner**: eat3torice

---

**Last Updated**: November 20, 2025
**Version**: 1.0.0
**License**: MIT
