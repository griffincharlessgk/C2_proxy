# Hệ thống C2 Reverse Proxy/Relay (asyncio)

Hệ thống C2 dùng asyncio để tạo tunnel ngược từ Bot về C2 và cung cấp proxy HTTP (8080) & SOCKS5 (1080). Lưu lượng client được multiplex qua các Bot bằng giao thức frame (JSON + tiền tố độ dài) có xác thực token và heartbeat.

## ✅ Tính năng
- Bất đồng bộ hoàn toàn (asyncio), hiệu năng cao
- Bot kết nối ngược (TCP/TLS) về C2, tunnel bền vững
- Giao thức frame: JSON + 4 byte độ dài (big-endian), payload base64
- Multiplex nhiều phiên trên một tunnel qua `request_id`
- Proxy HTTP (8080) và SOCKS5 (1080)
- Cân bằng tải vòng tròn (round-robin) giữa nhiều Bot
- Xác thực Bot bằng token, heartbeat PING/PONG, logging có cấu trúc

## 📁 Cấu trúc mã nguồn
- `protocol.py`: Định nghĩa Frame, FramedStream, Heartbeat
- `c2_server.py`: Server C2 (nhận tunnel từ Bot; mở proxy HTTP/SOCKS5)
- `bot_agent.py`: Bot (kết nối C2; mở upstream tới đích; bơm dữ liệu)

## 🔧 Yêu cầu
- Python 3.10+
- Không phụ thuộc bên thứ ba (chỉ dùng stdlib). TLS là tùy chọn nhưng nên bật khi production.

## 🔐 Tạo Bot Token
Dùng chuỗi ngẫu nhiên đủ dài và dùng chung cho C2 và các Bot.
```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))  # ~64 ký tự an toàn
PY
```

## 🔒 (Tùy chọn) Tạo chứng chỉ TLS tự ký cho C2
```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -sha256 -days 365 -nodes \
  -subj "/CN=localhost"
```
Chạy C2 kèm `--certfile cert.pem --keyfile key.pem` để bật TLS cho cổng Bot.

## 🚀 Chạy C2
```bash
export BOT_TOKEN="<token_vua_tao>"
python3 c2_server.py \
  --host 0.0.0.0 \
  --bot-port 4443 \
  --http-port 8080 \
  --socks-port 1080 \
  --bot-token "$BOT_TOKEN" \
  [--certfile cert.pem --keyfile key.pem]
```

## 🤖 Chạy Bot
```bash
export BOT_TOKEN="<token_vua_tao>"
bot_id=bot_1
python3 bot_agent.py \
  --c2-host <IP_C2> \
  --c2-port 4443 \
  --token "$BOT_TOKEN" \
  --bot-id "$bot_id"
```
- Bot sẽ tự động reconnect khi mất kết nối.
- Có thể chạy nhiều Bot (trên nhiều máy) trỏ về cùng C2 và token.

## 🧪 Kiểm thử Proxy
- HTTP qua proxy HTTP
```bash
curl -v -x http://<IP_C2>:8080 http://httpbin.org/ip
```
- HTTPS (CONNECT) qua proxy HTTP
```bash
curl -v -x http://<IP_C2>:8080 https://httpbin.org/ip
```
- HTTPS qua SOCKS5
```bash
curl -v --socks5-hostname <IP_C2>:1080 https://httpbin.org/ip
```

## 🧠 Cách hoạt động (tổng quan)
- Bot tạo tunnel ngược tới C2 (có thể TLS) và xác thực bằng token.
- C2 lắng nghe client ở 8080 (HTTP) và 1080 (SOCKS5).
- Mỗi kết nối client, C2 chọn Bot theo round-robin, sinh `request_id`.
- C2 gửi `PROXY_REQUEST {host, port}` tới Bot và stream `DATA/END`.
- Bot mở socket tới đích và trả về `PROXY_RESPONSE/END` cho C2.
- Nhiều kết nối được multiplex trên cùng tunnel bằng `request_id`.
- Heartbeat giúp loại bỏ tunnel chết; Bot reconnect sẽ được thêm lại.

## 📦 Định dạng Frame (JSON + 4 byte độ dài)
```json
{
  "type": "AUTH|OK|ERR|PING|PONG|PROXY_REQUEST|DATA|PROXY_RESPONSE|END",
  "request_id": "uuid-string",
  "payload": "base64-bytes",
  "meta": { "host": "example.com", "port": 443, "token": "..." }
}
```
- 4 byte đầu là độ dài (big-endian) của phần JSON.
- Payload nhị phân được mã hóa base64.

## 📈 Nhiều Bot
- Mỗi Bot là một phiên tunnel độc lập.
- C2 phân phối kết nối mới theo round-robin.
- Bot rớt kết nối chỉ ảnh hưởng các `request_id` đang chạy trên Bot đó; yêu cầu mới sẽ dùng Bot khác.
- Có thể mở rộng chiến lược chọn Bot (ít kết nối nhất, độ trễ thấp, v.v.).

## 🔐 Ghi chú bảo mật
- Nên bật TLS cho cổng Bot trong production (`--certfile/--keyfile`).
- Bảo mật token (không log/commit), xoay vòng định kỳ.
- Cân nhắc token riêng cho từng Bot và allowlist IP.

## 🛠️ Khắc phục sự cố
- Không có phản hồi: xác nhận có ít nhất một Bot đã kết nối và xác thực (xem log C2).
- Lỗi TLS: kiểm tra đường dẫn cert/key; nếu kiểm tra chứng chỉ ở Bot, đảm bảo Bot tin cậy chứng chỉ C2.
- 502/timeout: kiểm tra khả năng truy cập đích từ máy Bot.
- Tăng mức log bằng `PYTHONASYNCIODEBUG=1` hoặc chỉnh `logging.basicConfig` trong mã.


