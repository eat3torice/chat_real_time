# Chat Realtime

## Mô tả

Ứng dụng chat real-time được xây dựng bằng FastAPI, SQLAlchemy, PostgreSQL, Redis và WebSockets.

## Cấu trúc hệ thống

```
.
├── app/                      # Backend code
│   ├── __init__.py
│   ├── auth/                 # Authentication logic
│   ├── chat/                 # Chat logic
│   ├── crud/                 # Database CRUD operations
│   ├── database/             # Database connection and models
│   ├── dependencies/         # Dependencies injection
│   ├── routers/              # API routers
│   ├── schemas/              # Data schemas
│   ├── tests/                # Tests
│   ├── utils/                # Utility functions
│   ├── websocket/            # WebSocket logic
│   ├── config.py             # Application configuration
│   └── main.py               # Main application entrypoint
├── frontend/                 # Frontend code
│   ├── css/                  # CSS styles
│   ├── js/                   # JavaScript logic
│   ├── index.html            # Main HTML file
│   └── ...
├── .dockerignore
├── .env                      # Environment variables
├── docker-compose.yml        # Docker configuration
├── Dockerfile
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Cài đặt Dependencies

1.  Tạo môi trường ảo:

    ```bash
    python -m venv .venv
    ```
2.  Kích hoạt môi trường ảo:

    *   Trên Windows:

        ```bash
        .venv\Scripts\activate
        ```
    *   Trên macOS và Linux:

        ```bash
        source .venv/bin/activate
        ```
3.  Cài đặt các dependencies:

    ```bash
    pip install -r requirements.txt
    ```

    Các dependencies cần cài đặt:

    ```
    fastapi==0.111.0
    uvicorn[standard]==0.30.1
    SQLAlchemy==2.0.31
    alembic==1.13.2
    psycopg[binary]==3.2.3
    python-jose==3.3.0
    passlib[bcrypt]==1.7.4
    bcrypt==4.1.3
    python-multipart==0.0.9
    websockets==12.0
    aiofiles==23.2.1
    redis==5.0.4
    aioredis==2.0.1
    pydantic==2.8.2
    pydantic-settings==2.3.4
    python-dotenv==1.0.1
    requests==2.32.3
    httpx==0.27.0
    black==24.4.2
    ruff==0.5.6
    ```

## Build Project

1.  Cấu hình các biến môi trường:

    *   Tạo file `.env` và cấu hình các biến môi trường như `DATABASE_URL`, `SECRET_KEY`, `REDIS_URL`, ...

2.  Chạy Docker Compose:

    ```bash
    docker-compose up -d
    ```

## Chạy ứng dụng

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Hướng dẫn sử dụng Frontend

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

## Technical Stack

### Backend
* FastAPI
* SQLAlchemy
* PostgreSQL
* Redis
* WebSockets

### Frontend
* HTML
* CSS
* JavaScript

## API Endpoints

### Authentication
* `POST /auth/register` - Đăng ký
* `POST /auth/login` - Đăng nhập
* `GET /auth/me` - Thông tin user hiện tại

### Friends
* `GET /friends` - Danh sách bạn bè
* `POST /friends/request` - Gửi lời mời kết bạn
* `GET /friends/requests` - Lời mời kết bạn
* `PUT /friends/requests/{id}/accept` - Chấp nhận lời mời
* `PUT /friends/requests/{id}/reject` - Từ chối lời mời

### Conversations
* `GET /conversations` - Danh sách cuộc trò chuyện
* `POST /conversations` - Tạo cuộc trò chuyện mới
* `GET /conversations/{id}` - Chi tiết cuộc trò chuyện

### Messages
* `GET /messages/conversation/{id}` - Lấy tin nhắn
* `POST /messages` - Gửi tin nhắn

### WebSocket
* `WS /ws/{user_id}` - Real-time connection

## Cấu trúc thư mục

*   `app/`: Chứa code backend.
    *   `auth/`: Chứa các file liên quan đến authentication (ví dụ: `jwt_handler.py`, `hashing.py`).
    *   `chat/`: Chứa các file liên quan đến chat logic (ví dụ: `manager.py`, `services.py`).
    *   `crud/`: Chứa các file liên quan đến database CRUD operations (ví dụ: `user_crud.py`, `message_crud.py`).
    *   `database/`: Chứa các file liên quan đến database connection và models (ví dụ: `connection.py`, `models.py`).
    *   `dependencies/`: Chứa các file liên quan đến dependencies injection.
    *   `routers/`: Chứa các file định nghĩa API endpoints (ví dụ: `auth_router.py`, `message_router.py`).
    *   `schemas/`: Chứa các file định nghĩa data schemas (ví dụ: `user_schema.py`, `message_schema.py`).
    *   `tests/`: Chứa các file test.
    *   `utils/`: Chứa các utility functions.
    *   `websocket/`: Chứa các file liên quan đến WebSocket logic.
    *   `config.py`: Chứa các cấu hình của ứng dụng.
    *   `main.py`: Điểm vào chính của ứng dụng.
*   `frontend/`: Chứa code frontend.
    *   `css/`: Chứa các file CSS.
    *   `js/`: Chứa các file JavaScript.
    *   `index.html`: File HTML chính.
*   `.dockerignore`: Chỉ định các file và thư mục mà Docker nên bỏ qua.
*   `.env`: Chứa các biến môi trường.
*   `docker-compose.yml`: Mô tả cách containerize ứng dụng.
*   `Dockerfile`: Chứa các instructions để build Docker image.
*   `requirements.txt`: Liệt kê các dependencies của project.
*   `README.md`: File này.

## Liên hệ

Nếu bạn có bất kỳ câu hỏi nào, xin vui lòng liên hệ.
