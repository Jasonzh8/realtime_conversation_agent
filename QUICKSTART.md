# 快速启动指南

## 🚀 5 分钟快速上手

### 步骤 1: 安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 2: 配置环境变量

复制并编辑 `.env` 文件：

```bash
cp .env.example .env
nano .env  # 或使用你喜欢的编辑器
```

**必填项：**
```env
TWILIO_ACCOUNT_SID=ACxxxxx...        # 从 Twilio 控制台获取
TWILIO_AUTH_TOKEN=your_token         # 从 Twilio 控制台获取
TWILIO_PHONE_NUMBER=+12025551234     # 你购买的 Twilio 号码
OPENAI_API_KEY=sk-proj-xxxxx...      # 从 OpenAI 平台获取
PUBLIC_URL=https://xxx.ngrok-free.app  # ngrok 生成的 URL
```

### 步骤 3: 启动 ngrok

```bash
# 新开一个终端
ngrok http 5000
```

复制生成的 URL（如 `https://abc123.ngrok-free.app`），更新到 `.env` 的 `PUBLIC_URL`。

### 步骤 4: 启动服务

```bash
python twilio_openai_agent_fastapi.py
```

看到以下输出表示成功：
```
🚀 Twilio + OpenAI Realtime Agent 启动中...
📞 Twilio 号码: +12025551234
🤖 AI 模型: gpt-realtime
INFO:     Uvicorn running on http://0.0.0.0:5000
```

### 步骤 5: 发起测试呼叫

**方法 A：使用测试脚本（推荐）**

```bash
python test_call.py
```

按照提示选择场景和输入号码。

**方法 B：使用 curl**

```bash
curl -X POST http://localhost:5000/make-call \
  -H "Content-Type: application/json" \
  -d '{
    "to": "+8613800138000",
    "instructions": "你是一个友好的客服助手",
    "voice": "alloy"
  }'
```

## 📞 Twilio 账户设置

### 1. 注册账户
访问 https://www.twilio.com/try-twilio

### 2. 购买电话号码
1. 进入 [Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
2. 点击 "Buy a number"
3. 选择支持 **Voice** 功能的号码
4. 购买（约 $1/月）

### 3. 获取凭证
访问 [Console](https://console.twilio.com/)
- Account SID
- Auth Token

## 🔑 OpenAI API 设置

1. 访问 https://platform.openai.com/api-keys
2. 点击 "Create new secret key"
3. 复制并保存（只显示一次）
4. 确保账户有足够余额

## 🐛 常见问题

### ❌ 呼叫失败

**检查：**
```bash
# 1. 测试服务器
curl http://localhost:5000/

# 2. 检查环境变量
cat .env | grep -v "^#"

# 3. 查看详细日志
python twilio_openai_agent_fastapi.py
```

### ❌ 音频无声音

**可能原因：**
- ngrok URL 配置错误 → 重新检查 `PUBLIC_URL`
- WebSocket 未连接 → 查看日志是否有 "OpenAI WebSocket 已连接"

### ❌ OpenAI API 错误

```bash
# 测试 API Key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## 📚 下一步

✅ 阅读完整文档：[README_TWILIO.md](README_TWILIO.md)
✅ 自定义 AI 指令
✅ 调整语音参数
✅ 部署到生产环境

## 💡 实用示例

### 客服机器人

```python
import requests

requests.post("http://localhost:5000/make-call", json={
    "to": "+8613800138000",
    "instructions": """
你是某某公司的客服助手。任务：
1. 问候客户并确认身份
2. 询问需要什么帮助
3. 根据客户需求提供解决方案
4. 如无法解决，告知会转人工处理
保持礼貌专业，每次只说一个要点。
    """,
    "voice": "alloy"
})
```

### 预约提醒

```python
requests.post("http://localhost:5000/make-call", json={
    "to": "+8613800138000",
    "instructions": """
你是预约提醒助手。任务：
1. 告知客户有明天下午3点的预约
2. 确认是否能按时到达
3. 如不能，询问是否需要改期
4. 记录客户回复（确认/取消/改期）
简洁明了，避免啰嗦。
    """,
    "voice": "nova"
})
```

## 🎓 学习资源

- 📖 [Twilio 文档](https://www.twilio.com/docs/voice)
- 📖 [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime)
- 🎥 [视频教程](https://www.youtube.com/results?search_query=twilio+openai)

---

遇到问题？查看 [README_TWILIO.md](README_TWILIO.md) 的故障排除部分。
