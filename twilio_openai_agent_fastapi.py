"""
Twilio + OpenAI Realtime API 语音代理 (FastAPI 版本)
实现主动外呼功能，通过 OpenAI Realtime API 进行智能对话
使用 FastAPI 框架支持原生 WebSocket
"""

import os
import json
import base64
import asyncio
import audioop
from typing import Dict, Optional
from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
import websockets
from dotenv import load_dotenv
import logging

load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 应用
app = FastAPI(
    title="Twilio + OpenAI Realtime Agent",
    description="基于 Twilio 和 OpenAI Realtime API 的智能语音代理",
    version="1.0.0"
)

# Twilio 配置
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

# OpenAI 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-realtime"

# 服务器配置
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))
PUBLIC_URL = os.getenv("PUBLIC_URL")  # 公网访问地址（如 ngrok URL）

# AI 助手配置
DEFAULT_INSTRUCTIONS = os.getenv(
    "AI_INSTRUCTIONS",
    "你是一个友好、专业的客服助手。用中文与用户交流，保持礼貌和耐心。"
)
DEFAULT_VOICE = os.getenv("AI_VOICE", "alloy")

# 存储活动会话
active_sessions: Dict[str, dict] = {}


# ==================== Pydantic 模型 ====================

class CallRequest(BaseModel):
    """发起呼叫请求模型"""
    to: str  # 被叫号码（E.164格式）
    instructions: Optional[str] = None  # AI 指令
    voice: Optional[str] = "alloy"  # 语音风格


class CallResponse(BaseModel):
    """呼叫响应模型"""
    success: bool
    call_sid: Optional[str] = None
    to: Optional[str] = None
    from_: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    active_sessions: int


# ==================== 音频处理 ====================

class AudioProcessor:
    """音频格式转换处理器"""

    @staticmethod
    def mulaw_to_pcm24k(mulaw_data: bytes) -> bytes:
        """
        将 μ-law 8kHz 转换为 PCM 24kHz
        Twilio 使用 μ-law, OpenAI 使用 PCM
        """
        try:
            # μ-law 解码为 PCM 16-bit
            pcm_8k = audioop.ulaw2lin(mulaw_data, 2)
            # 重采样 8kHz → 24kHz
            pcm_24k, _ = audioop.ratecv(pcm_8k, 2, 1, 8000, 24000, None)
            return pcm_24k
        except Exception as e:
            logger.error(f"音频转换错误 (μ-law→PCM): {e}")
            return b""

    @staticmethod
    def pcm24k_to_mulaw(pcm_data: bytes) -> bytes:
        """
        将 PCM 24kHz 转换为 μ-law 8kHz
        OpenAI 输出 PCM, Twilio 需要 μ-law
        """
        try:
            # 重采样 24kHz → 8kHz
            pcm_8k, _ = audioop.ratecv(pcm_data, 2, 1, 24000, 8000, None)
            # PCM 编码为 μ-law
            mulaw = audioop.lin2ulaw(pcm_8k, 2)
            return mulaw
        except Exception as e:
            logger.error(f"音频转换错误 (PCM→μ-law): {e}")
            return b""


# ==================== 音频转发任务 ====================

async def forward_twilio_to_openai(websocket: WebSocket, call_sid: str):
    """转发音频：Twilio → OpenAI"""
    logger.info(f"[{call_sid}] 开始转发 Twilio → OpenAI")
    session = active_sessions.get(call_sid)

    if not session:
        logger.error(f"[{call_sid}] 会话不存在")
        return

    openai_ws = session["openai_ws"]

    try:
        while True:
            # 从 Twilio WebSocket 接收消息
            try:
                message = await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"[{call_sid}] Twilio WebSocket 断开连接")
                break

            data = json.loads(message)

            # 保存 stream SID
            if data.get("event") == "start":
                stream_sid = data["start"]["streamSid"]
                session["stream_sid"] = stream_sid
                logger.info(f"[{call_sid}] 媒体流已启动: {stream_sid}")

            # 处理音频数据
            elif data.get("event") == "media":
                payload = data["media"]["payload"]
                # Twilio 发送的是 base64 编码的 μ-law 音频
                mulaw_data = base64.b64decode(payload)
                # 转换为 PCM 24kHz
                pcm_data = AudioProcessor.mulaw_to_pcm24k(mulaw_data)

                if pcm_data:
                    # 发送给 OpenAI (base64 编码)
                    pcm_base64 = base64.b64encode(pcm_data).decode("utf-8")
                    await openai_ws.send(json.dumps({
                        "type": "input_audio_buffer.append",
                        "audio": pcm_base64
                    }))

            # 呼叫结束
            elif data.get("event") == "stop":
                logger.info(f"[{call_sid}] Twilio 媒体流已停止")
                break

    except Exception as e:
        logger.error(f"[{call_sid}] Twilio→OpenAI 转发错误: {e}")


async def forward_openai_to_twilio(websocket: WebSocket, call_sid: str):
    """转发音频：OpenAI → Twilio"""
    logger.info(f"[{call_sid}] 开始转发 OpenAI → Twilio")
    session = active_sessions.get(call_sid)

    if not session:
        logger.error(f"[{call_sid}] 会话不存在")
        return

    openai_ws = session["openai_ws"]

    try:
        async for message in openai_ws:
            data = json.loads(message)
            event_type = data.get("type")

            # 记录重要事件
            if event_type == "session.created":
                logger.info(f"[{call_sid}] OpenAI 会话已创建")

            elif event_type == "session.updated":
                logger.info(f"[{call_sid}] OpenAI 会话已更新")

            elif event_type == "response.audio.delta":
                # OpenAI 返回的音频增量
                audio_base64 = data.get("delta")

                if audio_base64 and session:
                    # 解码 PCM 音频
                    pcm_data = base64.b64decode(audio_base64)
                    # 转换为 μ-law 8kHz
                    mulaw_data = AudioProcessor.pcm24k_to_mulaw(pcm_data)

                    if mulaw_data:
                        # 发送给 Twilio (base64 编码)
                        mulaw_base64 = base64.b64encode(mulaw_data).decode("utf-8")
                        stream_sid = session.get("stream_sid")

                        if stream_sid:
                            await websocket.send_json({
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": mulaw_base64
                                }
                            })

            elif event_type == "response.audio_transcript.done":
                transcript = data.get("transcript", "")
                logger.info(f"[{call_sid}] AI 回复: {transcript}")

            elif event_type == "conversation.item.input_audio_transcription.completed":
                transcript = data.get("transcript", "")
                logger.info(f"[{call_sid}] 用户说: {transcript}")

            elif event_type == "error":
                error_msg = data.get("error", {})
                logger.error(f"[{call_sid}] OpenAI 错误: {error_msg}")

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"[{call_sid}] OpenAI WebSocket 连接已关闭")
    except Exception as e:
        logger.error(f"[{call_sid}] OpenAI→Twilio 转发错误: {e}")


# ==================== FastAPI 路由 ====================

@app.get("/", response_model=HealthResponse)
async def index():
    """健康检查"""
    return HealthResponse(
        status="running",
        service="Twilio + OpenAI Realtime Agent",
        active_sessions=len(active_sessions)
    )


@app.post("/make-call", response_model=CallResponse)
async def make_call(call_request: CallRequest):
    """
    发起外呼

    Args:
        call_request: 包含被叫号码、指令和语音的请求体

    Returns:
        CallResponse: 呼叫结果
    """
    try:
        to_number = call_request.to
        instructions = call_request.instructions or DEFAULT_INSTRUCTIONS
        voice = call_request.voice or DEFAULT_VOICE

        # 初始化 Twilio 客户端
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        # 发起呼叫
        logger.info(f"📞 发起呼叫: {TWILIO_PHONE_NUMBER} → {to_number}")

        # URL 编码参数
        from urllib.parse import quote
        twiml_url = f"{PUBLIC_URL}/twiml?instructions={quote(instructions)}&voice={voice}"

        call = client.calls.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            url=twiml_url,
            status_callback=f"{PUBLIC_URL}/call-status",
            status_callback_event=["initiated", "ringing", "answered", "completed"]
        )

        logger.info(f"✅ 呼叫已创建: {call.sid}")

        return CallResponse(
            success=True,
            call_sid=call.sid,
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            status=call.status
        )

    except Exception as e:
        logger.error(f"❌ 发起呼叫失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/twiml")
async def twiml(request: Request):
    """
    TwiML 响应端点
    当呼叫接通后，Twilio 会请求此端点获取指令
    """
    # 获取 URL 参数
    params = request.query_params
    instructions = params.get("instructions", DEFAULT_INSTRUCTIONS)
    voice = params.get("voice", DEFAULT_VOICE)

    # 获取表单数据
    form_data = await request.form()
    call_sid = form_data.get("CallSid")

    logger.info(f"[{call_sid}] 📋 生成 TwiML 响应")

    response = VoiceResponse()

    # 使用 <Connect><Stream> 将音频流转发到 WebSocket
    connect = Connect()

    # 构建 WebSocket URL（使用 wss:// 协议）
    ws_host = PUBLIC_URL.replace("https://", "").replace("http://", "")
    from urllib.parse import quote
    ws_url = f"wss://{ws_host}/media-stream?call_sid={call_sid}&instructions={quote(instructions)}&voice={voice}"

    stream = Stream(url=ws_url)
    connect.append(stream)
    response.append(connect)

    return Response(content=str(response), media_type="text/xml")


@app.post("/call-status")
async def call_status(request: Request):
    """呼叫状态回调"""
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    call_status = form_data.get("CallStatus")

    logger.info(f"[{call_sid}] 📞 呼叫状态: {call_status}")

    return Response(status_code=200)


@app.websocket("/media-stream")
async def media_stream(websocket: WebSocket):
    """
    WebSocket 端点：接收 Twilio 的媒体流
    """
    await websocket.accept()

    # 获取参数
    call_sid = websocket.query_params.get("call_sid", "unknown")
    instructions = websocket.query_params.get("instructions", DEFAULT_INSTRUCTIONS)
    voice = websocket.query_params.get("voice", DEFAULT_VOICE)

    logger.info(f"[{call_sid}] 🔌 WebSocket 连接已建立")

    # 连接到 OpenAI Realtime API
    url = f"wss://api.openai.com/v1/realtime?model={OPENAI_MODEL}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    try:
        async with websockets.connect(url, additional_headers=headers) as openai_ws:
            logger.info(f"[{call_sid}] ✅ OpenAI WebSocket 已连接")

            # 配置 OpenAI 会话
            session_config = {
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "model": OPENAI_MODEL,
                    "instructions": instructions,
                    "audio": {
                        "input": {
                            "format": {
                                "type": "audio/pcm",
                                "rate": 24000
                            },
                            "turn_detection": {
                                "type": "server_vad",
                                "threshold": 0.5,
                                "prefix_padding_ms": 300,
                                "silence_duration_ms": 500
                            }
                        },
                        "output": {
                            "format": {
                                "type": "audio/pcm"
                            },
                            "voice": voice
                        }
                    }
                }
            }

            await openai_ws.send(json.dumps(session_config))
            logger.info(f"[{call_sid}] ⚙️ 已发送会话配置")

            # 存储会话信息
            active_sessions[call_sid] = {
                "openai_ws": openai_ws,
                "stream_sid": None
            }

            # 创建两个并发任务处理双向音频流
            await asyncio.gather(
                forward_twilio_to_openai(websocket, call_sid),
                forward_openai_to_twilio(websocket, call_sid),
                return_exceptions=True
            )

    except Exception as e:
        logger.error(f"[{call_sid}] ❌ 错误: {e}")
    finally:
        if call_sid in active_sessions:
            del active_sessions[call_sid]
        logger.info(f"[{call_sid}] 🔚 会话已结束")


# ==================== 启动事件 ====================

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    # 检查必需的环境变量
    required_vars = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
        "TWILIO_PHONE_NUMBER",
        "OPENAI_API_KEY",
        "PUBLIC_URL"
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        logger.error("请在 .env 文件中配置这些变量")
        raise RuntimeError(f"Missing environment variables: {', '.join(missing_vars)}")

    logger.info("=" * 60)
    logger.info("🚀 Twilio + OpenAI Realtime Agent 启动中...")
    logger.info(f"📞 Twilio 号码: {TWILIO_PHONE_NUMBER}")
    logger.info(f"🤖 AI 模型: {OPENAI_MODEL}")
    logger.info(f"🎤 默认语音: {DEFAULT_VOICE}")
    logger.info(f"🌐 公网地址: {PUBLIC_URL}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("🔚 应用正在关闭...")
    # 清理所有活动会话
    active_sessions.clear()


# ==================== 主程序 ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "twilio_openai_agent_fastapi:app",
        host=SERVER_HOST,
        port=SERVER_PORT,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )
