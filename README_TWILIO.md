# Twilio + OpenAI Realtime Agent

基于 Twilio 和 OpenAI Realtime API 的智能语音代理，支持主动外呼功能。

## 🎯 功能特性

- ✅ **主动外呼**：通过 API 发起电话呼叫
- ✅ **智能对话**：基于 OpenAI GPT-4 Realtime 模型的自然语音交互
- ✅ **实时音频**：低延迟的双向音频流处理
- ✅ **自定义指令**：灵活配置 AI 助手的行为和人格
- ✅ **多语音选择**：支持多种语音风格
- ✅ **对话转录**：自动记录对话内容

## 📋 前置要求

### 1. Twilio 账户
- 注册 Twilio 账户：https://www.twilio.com/try-twilio
- 购买一个电话号码（支持语音功能）
- 获取 Account SID 和 Auth Token

### 2. OpenAI 账户
- 注册 OpenAI 账户：https://platform.openai.com/
- 创建 API Key
- 确保账户有足够的额度（Realtime API 按分钟计费）

### 3. 公网访问
- 本地开发推荐使用 [ngrok](https://ngrok.com/)
- 生产环境需要一个公网可访问的服务器

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目（如果需要）
cd realtime_conversation_agent

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入实际值：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Twilio 配置
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+12025551234

# OpenAI 配置
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 公网地址（使用 ngrok）
PUBLIC_URL=https://your-domain.ngrok-free.app

# AI 配置
AI_VOICE=alloy
AI_INSTRUCTIONS=你是一个友好、专业的客服助手。用中文与用户交流，保持礼貌和耐心。
```

### 3. 启动 ngrok（本地开发）

```bash
# 在新终端运行
ngrok http 5000

# 复制生成的 URL（如 https://abc123.ngrok-free.app）
# 并更新 .env 文件中的 PUBLIC_URL
```

### 4. 启动服务

```bash
python twilio_openai_agent_quart.py
```

看到以下输出表示启动成功：

```
============================================================
🚀 Twilio + OpenAI Realtime Agent 启动中...
📞 Twilio 号码: +12025551234
🤖 AI 模型: gpt-realtime
🎤 默认语音: alloy
🌐 公网地址: https://abc123.ngrok-free.app
============================================================
```

### 5. 发起呼叫

使用 curl 或 Postman 发送请求：

```bash
curl -X POST http://localhost:5000/make-call \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+8613800138000",
    "instructions": "你是一个预约确认助手，礼貌地确认客户的预约时间。",
    "voice": "alloy"
  }'
```

响应示例：

```json
{
  "success": true,
  "call_sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "to": "+8613800138000",
  "from": "+12025551234",
  "status": "queued"
}
```

## 📖 API 文档

### POST /make-call

发起外呼

**请求体：**

```json
{
  "to": "+8613800138000",        // 必填：被叫号码（E.164格式）
  "instructions": "你是...",     // 可选：AI 助手指令
  "voice": "alloy"               // 可选：语音风格
}
```

**可用语音：**
- `alloy` - 中性、均衡
- `echo` - 温暖、友好
- `fable` - 表现力强
- `onyx` - 深沉、权威
- `nova` - 明亮、活泼
- `shimmer` - 柔和、舒缓

**响应：**

```json
{
  "success": true,
  "call_sid": "CAxxxx...",
  "to": "+8613800138000",
  "from": "+12025551234",
  "status": "queued"
}
```

### GET /

健康检查

**响应：**

```json
{
  "status": "running",
  "service": "Twilio + OpenAI Realtime Agent",
  "active_sessions": 2
}
```

## 🏗️ 架构说明

```
┌─────────────┐
│   客户端    │
│  (你的应用)  │
└──────┬──────┘
       │ HTTP POST
       │ /make-call
       ▼
┌─────────────────────────────────┐
│   Twilio + OpenAI Agent         │
│  (本服务, Quart + WebSocket)     │
└──────┬─────────────────┬────────┘
       │                 │
       │ Twilio API      │ WebSocket
       ▼                 ▼
┌─────────────┐   ┌──────────────┐
│   Twilio    │   │   OpenAI     │
│  (SIP/VoIP) │   │  Realtime API│
└──────┬──────┘   └──────────────┘
       │
       │ 电话呼叫
       ▼
┌─────────────┐
│   被叫方    │
│ (手机/座机)  │
└─────────────┘
```

**音频流处理：**

```
被叫方 ←→ Twilio (μ-law 8kHz)
              ↕
        [音频转码]
              ↕
本服务 ←→ OpenAI (PCM 24kHz)
```

## 🔧 高级配置

### 自定义 AI 指令

在调用 `/make-call` 时传入 `instructions` 参数：

```python
import requests

response = requests.post("http://localhost:5000/make-call", json={
    "to": "+8613800138000",
    "instructions": """
你是一个餐厅预约助手。任务：
1. 礼貌地确认客户姓名
2. 确认预约时间（今晚7点）
3. 确认人数
4. 告知餐厅地址
5. 结束时说"期待您的光临"
    """,
    "voice": "nova"
})

print(response.json())
```

### 修改语音检测参数

编辑 `twilio_openai_agent_quart.py` 中的 `session_config`：

```python
"turn_detection": {
    "type": "server_vad",
    "threshold": 0.5,           # 语音检测阈值 (0-1)
    "prefix_padding_ms": 300,   # 语音前缓冲
    "silence_duration_ms": 500  # 静默判定时长
}
```

### 启用对话转录

代码中已自动启用，在日志中可以看到：

```
[CAxxxx] 用户说: 你好，我想预约今晚的位置
[CAxxxx] AI 回复: 好的，请问您的姓名是？
```

## 📊 成本估算

### Twilio 费用
- 美国号码租赁：~$1/月
- 拨打电话：~$0.013-0.09/分钟（取决于目标国家）
- 中国大陆：~$0.085/分钟

### OpenAI Realtime API 费用
- 音频输入：$0.06/分钟
- 音频输出：$0.24/分钟
- 文本输入：$5.00/1M tokens
- 文本输出：$20.00/1M tokens

**示例：**
一通 5 分钟的对话成本约：
- Twilio: $0.085 × 5 = $0.425
- OpenAI: ($0.06 + $0.24) × 5 = $1.50
- **总计：~$1.93**

## 🐛 故障排除

### 1. 呼叫没有接通

**检查清单：**
- ✅ Twilio 号码是否支持语音功能
- ✅ 被叫号码格式是否正确（E.164 格式：+国家码+号码）
- ✅ Twilio 账户余额是否充足
- ✅ 检查 Twilio 控制台的呼叫日志

### 2. 音频没有声音

**可能原因：**
- ngrok URL 配置错误
- WebSocket 连接失败
- 音频转码错误

**调试方法：**

```bash
# 查看详细日志
python twilio_openai_agent_quart.py

# 检查 WebSocket 连接
# 应该看到：
# [CAxxxx] 🔌 WebSocket 连接已建立
# [CAxxxx] ✅ OpenAI WebSocket 已连接
```

### 3. OpenAI API 错误

**常见错误：**
- `401 Unauthorized`: API Key 错误
- `429 Rate Limit`: 超出速率限制
- `insufficient_quota`: 账户余额不足

### 4. ngrok 连接问题

```bash
# 确保 ngrok 正在运行
ngrok http 5000

# 检查 PUBLIC_URL 是否正确
curl https://your-domain.ngrok-free.app/
```

## 📝 生产环境部署

### 使用 Supervisor

创建 `/etc/supervisor/conf.d/twilio_agent.conf`：

```ini
[program:twilio_agent]
command=/path/to/venv/bin/python /path/to/twilio_openai_agent_quart.py
directory=/path/to/realtime_conversation_agent
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/twilio_agent.err.log
stdout_logfile=/var/log/twilio_agent.out.log
```

### 使用 Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "twilio_openai_agent_quart.py"]
```

```bash
docker build -t twilio-openai-agent .
docker run -p 5000:5000 --env-file .env twilio-openai-agent
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔐 安全建议

1. **保护 API 端点**：添加认证中间件
2. **验证来电号码**：限制允许的目标号码
3. **日志脱敏**：不要记录敏感信息
4. **使用 HTTPS**：生产环境必须使用 SSL
5. **限流**：防止滥用

## 📚 相关资源

- [Twilio 文档](https://www.twilio.com/docs)
- [OpenAI Realtime API 文档](https://platform.openai.com/docs/guides/realtime)
- [Quart 文档](https://quart.palletsprojects.com/)
- [ngrok 文档](https://ngrok.com/docs)

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## ❓ 常见问题

### Q: 支持接收来电吗？
A: 当前版本专注于外呼。如需接收来电，可以参考 OpenAI 官方的 SIP 接口文档。

### Q: 可以录音吗？
A: 可以，Twilio 提供录音功能。在 `create_call` 时添加 `record=True` 参数。

### Q: 支持中文吗？
A: 完全支持。在 `instructions` 中使用中文即可。

### Q: 延迟有多少？
A: 端到端延迟通常在 300-800ms 之间，取决于网络质量。

### Q: 可以打断 AI 说话吗？
A: 可以。OpenAI Realtime API 支持实时打断（通过 VAD 检测）。
