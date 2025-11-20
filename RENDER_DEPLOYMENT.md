# 🚀 HƯỚNG DẪN DEPLOY LÊN RENDER

## 📋 Checklist Trước Khi Deploy

### 1. Chuẩn bị Repository
- [x] Đã có Dockerfile
- [x] Đã có render.yaml
- [x] Đã có requirements.txt
- [x] Đã có .env.example
- [x] Code đã push lên GitHub

### 2. Tạo Tài Khoản & Dịch Vụ

#### A. Đăng ký Render
1. Truy cập https://render.com
2. Sign up với GitHub account
3. Authorize Render để access repositories

#### B. Tạo PostgreSQL Database
1. Dashboard → **New** → **PostgreSQL**
2. Cấu hình:
   - **Name**: `chat-db`
   - **Database**: `chat_real_time`
   - **User**: `chatuser`
   - **Region**: Singapore
   - **Plan**: Free
3. Click **Create Database**
4. Đợi database ready (2-3 phút)
5. Copy **Internal Database URL** (dạng: `postgresql://...`)

#### C. Tạo Redis (Optional - dùng Upstash)
Redis không có trong free tier của Render, nên dùng Upstash:

1. Truy cập https://upstash.com
2. Sign up (free)
3. Create Redis Database:
   - **Name**: `chat-redis`
   - **Region**: Singapore
   - **Type**: Regional
4. Copy **Redis URL** (dạng: `redis://...`)

### 3. Deploy Web Service

#### Cách 1: Dùng Dashboard (Đơn giản)

1. Dashboard → **New** → **Web Service**

2. **Connect Repository**
   - Chọn `eat3torice/chat_real_time`
   - Click **Connect**

3. **Cấu hình Service**
   ```
   Name: chat-real-time
   Region: Singapore
   Branch: main
   Runtime: Docker
   ```

4. **Environment Variables** (Tab Environment)
   Click **Add Environment Variable** và thêm:
   
   ```bash
   DATABASE_URL=<paste Internal Database URL từ bước B>
   REDIS_URL=<paste Redis URL từ Upstash>
   SECRET_KEY=<generate random key - xem bên dưới>
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   CREATE_DB_ON_STARTUP=false
   ```

   **Generate SECRET_KEY:**
   ```bash
   # Chạy trong terminal local
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

5. **Health Check Path**
   ```
   /health
   ```

6. Click **Create Web Service**

7. Đợi build & deploy (5-10 phút)

#### Cách 2: Dùng render.yaml (Tự động)

1. Dashboard → **New** → **Blueprint**
2. Connect repository
3. Render sẽ tự động detect `render.yaml`
4. Review services → Apply
5. Thêm `REDIS_URL` manually trong Environment tab

### 4. Chạy Database Migrations

Sau khi deploy xong:

1. Vào Web Service Dashboard
2. Click **Shell** tab
3. Chạy lệnh:
   ```bash
   alembic upgrade head
   ```

Hoặc nếu bạn set `CREATE_DB_ON_STARTUP=true`, tables sẽ tự động được tạo.

### 5. Kiểm tra Deploy

#### Health Check
```bash
curl https://chat-real-time.onrender.com/health
```

Response:
```json
{
  "status": "ok",
  "message": "chat_real_time running"
}
```

#### Test API
```bash
# Register user
curl -X POST https://chat-real-time.onrender.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"test123"}'

# Login
curl -X POST https://chat-real-time.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
```

#### Test WebSocket
Update `frontend/js/websocket.js`:
```javascript
this.url = 'wss://chat-real-time.onrender.com/ws';
```

### 6. Update Frontend

Nếu frontend chạy riêng, update API base URL:

```javascript
// frontend/js/api.js
this.baseURL = 'https://chat-real-time.onrender.com';

// frontend/js/websocket.js
this.url = 'wss://chat-real-time.onrender.com/ws';
```

## 🔧 Troubleshooting

### Build Failed
- Kiểm tra Dockerfile syntax
- Xem logs trong Render dashboard
- Đảm bảo requirements.txt đúng format

### Database Connection Error
- Kiểm tra `DATABASE_URL` đúng format
- Verify database đã ready
- Check firewall/network settings

### WebSocket Connection Failed
- Verify CORS settings trong `app/main.py`
- Check WebSocket endpoint: `wss://` (not `ws://`)
- Ensure token authentication đúng

### 500 Internal Server Error
- Check logs: Dashboard → Logs tab
- Verify all environment variables
- Check database migrations đã chạy

## 📊 Giám sát & Logs

### Xem Logs
```bash
# Dashboard → Logs tab
# Hoặc dùng CLI
render logs <service-id>
```

### Metrics
- Dashboard → Metrics tab
- CPU, Memory, Request count
- Response times

## 🔄 Update & Redeploy

### Auto Deploy
Mỗi khi push code lên `main` branch:
```bash
git add .
git commit -m "update: your changes"
git push origin main
```
→ Render tự động build & deploy

### Manual Deploy
Dashboard → Manual Deploy → Deploy latest commit

## 💰 Free Tier Limits

**Render Free Tier:**
- ✅ 750 hours/month
- ✅ Tự động sleep sau 15 phút không hoạt động
- ✅ Wake up khi có request (~30 giây)
- ❌ Không persistent storage
- ❌ Shared CPU/Memory

**PostgreSQL Free:**
- ✅ 1GB storage
- ✅ 90 days retention
- ⚠️ Expires after 90 days (need to upgrade)

**Recommendations:**
- Use Upstash Redis (free tier: 10k commands/day)
- Monitor usage trong dashboard
- Upgrade nếu cần production-ready

## 🎯 Production Checklist

- [ ] Đổi `SECRET_KEY` thành giá trị mạnh
- [ ] Set `CREATE_DB_ON_STARTUP=false`
- [ ] Sử dụng Alembic migrations
- [ ] Update CORS với domain cụ thể
- [ ] Enable HTTPS only
- [ ] Setup monitoring & alerts
- [ ] Backup database regularly
- [ ] Test WebSocket với production URL
- [ ] Configure proper logging
- [ ] Set up error tracking (Sentry)

## 🔗 Useful Links

- **Your App**: https://chat-real-time.onrender.com
- **Dashboard**: https://dashboard.render.com
- **API Docs**: https://chat-real-time.onrender.com/docs
- **Database**: Render Dashboard → PostgreSQL
- **Logs**: Render Dashboard → Logs

## 📞 Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- FastAPI Docs: https://fastapi.tiangolo.com

---

**Chuẩn bị xong! Giờ bạn có thể deploy lên Render** 🚀
