# Windows 本地测试指南

本指南专门针对 Windows 系统的本地开发和测试。

## 🎯 测试分为两种场景

### 场景 1: 本地功能测试（不需要 ngrok）✅

**可以测试：**
- ✅ OpenAI Realtime API 连接
- ✅ 音频格式转换
- ✅ FastAPI 服务器
- ✅ 文本对话功能
- ✅ 代码逻辑验证

**不需要：**
- ❌ Twilio 账户
- ❌ ngrok
- ❌ 公网访问

### 场景 2: 完整外呼测试（需要 ngrok）📞

**可以测试：**
- ✅ 真实电话呼叫
- ✅ 语音对话
- ✅ 端到端流程

**需要：**
- ✅ Twilio 账户
- ✅ ngrok
- ✅ 公网访问

---

## 🚀 快速开始：本地测试（推荐新手）

### 步骤 1: 安装依赖

```cmd
# 在项目目录下
pip install -r requirements.txt

# 安装额外的测试依赖
pip install httpx
```

### 步骤 2: 配置环境变量

创建 `.env` 文件（复制 `.env.example`）：

```env
# 只需要配置 OpenAI API Key
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 以下可以暂时留空（本地测试不需要）
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
PUBLIC_URL=
```

### 步骤 3: 运行本地测试

```cmd
python test_local.py
```

**输出示例：**
```
🚀 开始本地测试
============================================================
✅ OPENAI_API_KEY: sk-proj-abc123...

============================================================
🧪 测试 1: OpenAI Realtime API 连接
============================================================
✅ WebSocket 连接成功
✅ 会话配置已发送
✅ 收到响应: session.created
✅ 会话创建成功

============================================================
🧪 测试 2: 音频格式转换
============================================================
✅ 生成测试音频: 16000 字节 (8kHz PCM)
✅ PCM → μ-law: 8000 字节
✅ μ-law → PCM: 16000 字节
✅ 重采样 8kHz → 24kHz: 48000 字节
✅ 重采样 24kHz → 8kHz: 16000 字节
✅ 音频处理测试通过

============================================================
🧪 测试 3: FastAPI 服务器
============================================================
⚠️ 无法连接到服务器
💡 提示: 请先启动服务器
   python twilio_openai_agent_fastapi.py

============================================================
🧪 测试 4: 模拟对话（文本输入）
============================================================
✅ WebSocket 已连接
✅ 会话已创建
📤 发送消息: 你好，这是一个测试。请简短回复。
⏳ 等待 AI 回复...
✅ AI 回复: 你好！收到测试消息。

============================================================
📊 测试结果汇总
============================================================
OpenAI 连接: ✅ 通过
音频处理: ✅ 通过
FastAPI 服务器: ❌ 失败
模拟对话: ✅ 通过

通过率: 3/4 (75%)

⚠️ 部分测试失败，请检查配置
```

### 步骤 4: 启动 FastAPI 服务器（可选）

```cmd
python twilio_openai_agent_fastapi.py
```

然后在新窗口再次运行测试：
```cmd
python test_local.py
```

此时所有测试应该都通过。

---

## 📝 不同测试场景

### 场景 A: 只测试 OpenAI API 连接

**最简单，只需要 OpenAI API Key**

```cmd
python test_local.py
```

这会测试：
- OpenAI WebSocket 连接
- 音频处理功能
- 文本对话

### 场景 B: 测试 FastAPI 服务器

**需要完整配置 .env**

1. 启动服务器：
```cmd
python twilio_openai_agent_fastapi.py
```

2. 访问 API 文档：
```
http://localhost:5000/docs
```

3. 测试健康检查：
```cmd
curl http://localhost:5000/
```

### 场景 C: 完整外呼测试

**需要 Twilio + ngrok**

参见下面的 "完整外呼测试设置"。

---

## 🪟 Windows 特定说明

### 使用 PowerShell（推荐）

```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 如果遇到执行策略错误
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 运行测试
python test_local.py
```

### 使用命令提示符（CMD）

```cmd
# 激活虚拟环境
venv\Scripts\activate.bat

# 运行测试
python test_local.py
```

### 使用 Git Bash

```bash
# 激活虚拟环境
source venv/Scripts/activate

# 运行测试
python test_local.py
```

---

## 🔧 完整外呼测试设置（需要 ngrok）

### 步骤 1: 安装 ngrok

**方法 A: 下载安装（推荐）**

1. 访问 https://ngrok.com/download
2. 下载 Windows 版本（ngrok.zip）
3. 解压到 `C:\ngrok` 或任意目录
4. 双击 `ngrok.exe`

**方法 B: 使用 Chocolatey**

```powershell
# 以管理员身份运行
choco install ngrok
```

**方法 C: 使用 Scoop**

```powershell
scoop install ngrok
```

### 步骤 2: 注册并认证 ngrok

1. 注册账户：https://dashboard.ngrok.com/signup
2. 获取 authtoken：https://dashboard.ngrok.com/get-started/your-authtoken
3. 认证：

```cmd
# 导航到 ngrok.exe 所在目录
cd C:\ngrok

# 认证（替换为你的 token）
ngrok.exe config add-authtoken YOUR_TOKEN_HERE
```

### 步骤 3: 启动 ngrok

**方法 A: 图形界面**

双击 `ngrok.exe`，会打开命令行窗口，然后输入：
```
http 5000
```

**方法 B: 命令行**

```cmd
# 在 ngrok 目录
ngrok.exe http 5000

# 或者添加到 PATH 后
ngrok http 5000
```

**输出示例：**
```
ngrok

Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        United States (us)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

复制 `https://abc123.ngrok-free.app` 这个 URL。

### 步骤 4: 更新 .env

```env
PUBLIC_URL=https://abc123.ngrok-free.app
```

### 步骤 5: 启动服务器

```cmd
python twilio_openai_agent_fastapi.py
```

### 步骤 6: 发起呼叫

```cmd
python test_call.py
```

---

## 🐛 常见问题

### 问题 1: Python 命令不存在

**错误：**
```
'python' 不是内部或外部命令
```

**解决：**
```cmd
# 使用 py 命令
py test_local.py

# 或者使用完整路径
C:\Python311\python.exe test_local.py
```

### 问题 2: pip install 失败

**错误：**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**解决：**
```cmd
# 安装 Visual C++ Build Tools
# 下载：https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 或使用预编译的 wheel
pip install --only-binary :all: package-name
```

### 问题 3: 端口被占用

**错误：**
```
OSError: [WinError 10048] 通常每个套接字地址只允许使用一次
```

**解决：**
```cmd
# 查看占用端口 5000 的进程
netstat -ano | findstr :5000

# 杀死进程（替换 PID）
taskkill /PID 12345 /F

# 或使用其他端口
# 修改 .env
SERVER_PORT=8000
```

### 问题 4: 虚拟环境激活失败

**错误：**
```
无法加载文件 venv\Scripts\Activate.ps1，因为在此系统上禁止运行脚本
```

**解决：**
```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 问题 5: ngrok 连接不稳定

**症状：**
- ngrok 频繁断开
- 请求超时

**解决：**
```cmd
# 使用更稳定的区域
ngrok http 5000 --region=us

# 使用付费版（更稳定）
# 升级：https://dashboard.ngrok.com/billing/subscription
```

---

## 📊 测试检查清单

### 本地功能测试 ✅
- [ ] Python 3.8+ 已安装
- [ ] 依赖已安装（`pip install -r requirements.txt`）
- [ ] `.env` 文件已创建
- [ ] OPENAI_API_KEY 已配置
- [ ] 运行 `python test_local.py` 通过

### FastAPI 服务器测试 ✅
- [ ] 服务器成功启动
- [ ] 访问 http://localhost:5000/ 返回 200
- [ ] 访问 http://localhost:5000/docs 显示 API 文档

### 完整外呼测试 📞
- [ ] Twilio 账户已注册
- [ ] 电话号码已购买
- [ ] ngrok 已安装并认证
- [ ] ngrok 正在运行
- [ ] PUBLIC_URL 已配置
- [ ] Twilio 凭证已配置
- [ ] 运行 `python test_call.py` 成功

---

## 🎓 推荐学习路径

### 第 1 天：本地环境
1. ✅ 安装 Python 和依赖
2. ✅ 配置 OpenAI API Key
3. ✅ 运行 `test_local.py`
4. ✅ 理解代码结构

### 第 2 天：FastAPI 服务
1. ✅ 启动 FastAPI 服务器
2. ✅ 查看 API 文档（/docs）
3. ✅ 测试健康检查端点
4. ✅ 理解 WebSocket 流程

### 第 3 天：Twilio 集成
1. ✅ 注册 Twilio 账户
2. ✅ 购买电话号码
3. ✅ 安装和配置 ngrok
4. ✅ 发起第一通测试呼叫

---

## 💡 提示

1. **先本地测试**：确保代码逻辑正确后再配置 Twilio
2. **使用 API 文档**：FastAPI 的 `/docs` 非常有用
3. **查看日志**：所有输出都有详细日志
4. **小步迭代**：一步步测试，不要一次配置所有

---

## 🆘 获取帮助

如果遇到问题：

1. **查看日志**：运行程序时的详细输出
2. **检查配置**：确认 `.env` 文件正确
3. **运行测试**：`python test_local.py`
4. **查看文档**：
   - OpenAI: https://platform.openai.com/docs
   - FastAPI: https://fastapi.tiangolo.com/
   - Twilio: https://www.twilio.com/docs

---

## ✅ 总结

**本地测试（无需 ngrok）：**
```cmd
# 1. 安装依赖
pip install -r requirements.txt httpx

# 2. 配置 .env（只需 OPENAI_API_KEY）
copy .env.example .env
notepad .env

# 3. 运行测试
python test_local.py
```

**完整外呼测试（需要 ngrok）：**
```cmd
# 1. 启动 ngrok
ngrok http 5000

# 2. 更新 PUBLIC_URL
notepad .env

# 3. 启动服务器
python twilio_openai_agent_fastapi.py

# 4. 发起呼叫
python test_call.py
```

开始愉快地开发吧！🎉
