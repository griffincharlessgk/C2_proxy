# 🔒 C2 Security Management Guide

## 🚨 Tình huống: Bot lạ tự kết nối vào C2

Khi bạn dựng C2 server lên, có thể có các bot không mong muốn tự động kết nối vào. Đây là hướng dẫn xử lý tình huống này.

## 🛠️ Các Script Bảo Mật

### 1. **Emergency Bot Cleanup** - Xử lý khẩn cấp
```bash
# Chạy cleanup khẩn cấp
python3 scripts/emergency_bot_cleanup.py --cleanup

# Xem danh sách IP đáng tin cậy
python3 scripts/emergency_bot_cleanup.py --trusted

# Thêm IP đáng tin cậy
python3 scripts/emergency_bot_cleanup.py --add-trusted 192.168.1.100

# Xem log khẩn cấp
python3 scripts/emergency_bot_cleanup.py --log
```

### 2. **Bot Monitor** - Giám sát liên tục
```bash
# Quét một lần
python3 scripts/bot_monitor.py --scan

# Giám sát liên tục (mỗi 30 giây)
python3 scripts/bot_monitor.py --monitor

# Giám sát với interval tùy chỉnh
python3 scripts/bot_monitor.py --monitor --interval 60
```

### 3. **Bot Security Manager** - Quản lý bảo mật
```bash
# Chạy interactive mode
python3 scripts/bot_security_manager.py

# Các lệnh trong interactive mode:
# - scan: Quét bots đang kết nối
# - block: Block IP
# - unblock: Unblock IP
# - report: Tạo báo cáo bảo mật
# - trusted: Quản lý IP đáng tin cậy
```

### 4. **Secure C2 Config** - Cấu hình bảo mật
```bash
# Tạo config bảo mật
python3 scripts/secure_c2_config.py --create

# Thêm IP đáng tin cậy
python3 scripts/secure_c2_config.py --add-trusted 192.168.1.100

# Block IP
python3 scripts/secure_c2_config.py --block 203.0.113.1

# Tạo firewall rules
python3 scripts/secure_c2_config.py --firewall

# Xem trạng thái bảo mật
python3 scripts/secure_c2_config.py --status
```

### 5. **Secure C2 Server** - Server bảo mật
```bash
# Khởi động server bảo mật
python3 scripts/secure_c2_server.py --start

# Xem trạng thái server
python3 scripts/secure_c2_server.py --status

# Thêm IP đáng tin cậy
python3 scripts/secure_c2_server.py --add-trusted 192.168.1.100

# Block IP
python3 scripts/secure_c2_server.py --block 203.0.113.1
```

## 🚨 Xử Lý Khẩn Cấp

### Bước 1: Dừng C2 server hiện tại
```bash
# Tìm và kill process C2
ps aux | grep hybrid_botnet_manager
sudo kill -9 <PID>

# Hoặc dừng bằng Ctrl+C nếu đang chạy
```

### Bước 2: Quét và phân tích
```bash
# Quét các kết nối đang hoạt động
python3 scripts/emergency_bot_cleanup.py --cleanup

# Hoặc quét nhanh
python3 scripts/bot_monitor.py --scan
```

### Bước 3: Xử lý bot lạ
```bash
# Block tất cả IP lạ
python3 scripts/emergency_bot_cleanup.py --cleanup
# Chọn option 1: Block all suspicious IPs

# Hoặc block thủ công
sudo iptables -A INPUT -s <IP_LẠ> -j DROP
```

### Bước 4: Cấu hình bảo mật
```bash
# Tạo config bảo mật mới
python3 scripts/secure_c2_config.py --create

# Thêm IP đáng tin cậy
python3 scripts/secure_c2_config.py --add-trusted 192.168.1.100

# Tạo firewall rules
python3 scripts/secure_c2_config.py --firewall

# Áp dụng firewall rules
sudo bash c2_firewall_rules.sh
```

### Bước 5: Khởi động lại với bảo mật
```bash
# Sử dụng secure C2 server
python3 scripts/secure_c2_server.py --start

# Hoặc sử dụng config bảo mật với hybrid manager
python3 hybrid_botnet_manager.py
```

## 🔒 Biện Pháp Bảo Mật

### 1. **IP Whitelist**
```bash
# Tạo file trusted_ips.txt
echo "192.168.1.100" >> trusted_ips.txt
echo "10.0.0.50" >> trusted_ips.txt
```

### 2. **Firewall Rules**
```bash
# Block tất cả, chỉ allow IP đáng tin cậy
sudo iptables -A INPUT -s 192.168.1.100 -j ACCEPT
sudo iptables -A INPUT -s 10.0.0.50 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 7777 -j DROP
```

### 3. **Rate Limiting**
```bash
# Giới hạn số kết nối
sudo iptables -A INPUT -p tcp --dport 7777 -m limit --limit 5/minute -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 7777 -j DROP
```

### 4. **Authentication**
```bash
# Sử dụng secure C2 server với authentication
python3 scripts/secure_c2_server.py --start
```

## 📊 Monitoring và Logging

### 1. **Continuous Monitoring**
```bash
# Chạy monitor liên tục
python3 scripts/bot_monitor.py --monitor --interval 30
```

### 2. **Log Analysis**
```bash
# Xem log bảo mật
tail -f secure_c2.log

# Xem log khẩn cấp
python3 scripts/emergency_bot_cleanup.py --log
```

### 3. **Security Reports**
```bash
# Tạo báo cáo bảo mật
python3 scripts/bot_security_manager.py
# Chọn option: report
```

## ⚠️ Lưu Ý Quan Trọng

### 1. **Legal và Ethical**
- Chỉ sử dụng trên hệ thống của bạn
- Có authorization rõ ràng
- Tuân thủ luật pháp địa phương

### 2. **Security Best Practices**
- Thay đổi default credentials
- Sử dụng encryption
- Enable logging
- Regular security audits

### 3. **Network Security**
- Sử dụng VPN
- Isolate network
- Monitor traffic
- Regular updates

## 🆘 Troubleshooting

### 1. **Không thể block IP**
```bash
# Kiểm tra iptables
sudo iptables -L

# Reset iptables
sudo iptables -F
```

### 2. **Bot vẫn kết nối**
```bash
# Kill connection trực tiếp
sudo netstat -tulpn | grep 7777
sudo kill -9 <PID>
```

### 3. **Config không load**
```bash
# Kiểm tra file config
cat secure_c2_config.json

# Tạo lại config
python3 scripts/secure_c2_config.py --create
```

## 📞 Emergency Contacts

Nếu gặp vấn đề nghiêm trọng:
1. Dừng C2 server ngay lập tức
2. Block tất cả kết nối
3. Review logs
4. Contact security team

---

**⚠️ Disclaimer**: Các script này chỉ dành cho mục đích educational và research. Sử dụng có trách nhiệm và tuân thủ luật pháp.

