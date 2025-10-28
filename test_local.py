"""
本地测试脚本 - 不需要 ngrok
测试 OpenAI Realtime API 连接和音频处理功能
"""

import os
import json
import base64
import asyncio
import websockets
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-realtime"


async def test_openai_connection():
    """测试 OpenAI Realtime API 连接"""
    print("=" * 60)
    print("🧪 测试 1: OpenAI Realtime API 连接")
    print("=" * 60)

    url = f"wss://api.openai.com/v1/realtime?model={OPENAI_MODEL}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print("✅ WebSocket 连接成功")

            # 配置会话
            session_config = {
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "model": OPENAI_MODEL,
                    "instructions": "你是一个测试助手，简短回复即可。",
                    "modalities": ["text"],  # 测试模式只使用文本
                }
            }

            await ws.send(json.dumps(session_config))
            print("✅ 会话配置已发送")

            # 接收响应
            response = await ws.recv()
            data = json.loads(response)
            print(f"✅ 收到响应: {data.get('type')}")

            if data.get("type") == "session.created":
                print("✅ 会话创建成功")
                return True
            else:
                print(f"⚠️ 意外响应: {data}")
                return False

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ 连接失败: {e}")
        if e.status_code == 401:
            print("💡 提示: 请检查 OPENAI_API_KEY 是否正确")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


async def test_audio_processing():
    """测试音频处理功能"""
    print("\n" + "=" * 60)
    print("🧪 测试 2: 音频格式转换")
    print("=" * 60)

    try:
        import audioop

        # 创建测试音频数据（1秒的静音）
        sample_rate_8k = 8000
        duration = 1
        silence_8k = b'\x00' * (sample_rate_8k * duration * 2)  # 16-bit = 2 bytes

        print(f"✅ 生成测试音频: {len(silence_8k)} 字节 (8kHz PCM)")

        # 测试 PCM → μ-law
        mulaw_data = audioop.lin2ulaw(silence_8k, 2)
        print(f"✅ PCM → μ-law: {len(mulaw_data)} 字节")

        # 测试 μ-law → PCM
        pcm_data = audioop.ulaw2lin(mulaw_data, 2)
        print(f"✅ μ-law → PCM: {len(pcm_data)} 字节")

        # 测试重采样 8kHz → 24kHz
        pcm_24k, _ = audioop.ratecv(pcm_data, 2, 1, 8000, 24000, None)
        print(f"✅ 重采样 8kHz → 24kHz: {len(pcm_24k)} 字节")

        # 测试重采样 24kHz → 8kHz
        pcm_8k_back, _ = audioop.ratecv(pcm_24k, 2, 1, 24000, 8000, None)
        print(f"✅ 重采样 24kHz → 8kHz: {len(pcm_8k_back)} 字节")

        print("✅ 音频处理测试通过")
        return True

    except Exception as e:
        print(f"❌ 音频处理错误: {e}")
        return False


async def test_fastapi_server():
    """测试 FastAPI 服务器"""
    print("\n" + "=" * 60)
    print("🧪 测试 3: FastAPI 服务器")
    print("=" * 60)

    try:
        import httpx

        # 测试健康检查
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get("http://localhost:5000/", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 服务器运行正常")
                    print(f"   状态: {data.get('status')}")
                    print(f"   活跃会话: {data.get('active_sessions')}")
                    return True
                else:
                    print(f"⚠️ 服务器响应异常: {response.status_code}")
                    return False
            except httpx.ConnectError:
                print("⚠️ 无法连接到服务器")
                print("💡 提示: 请先启动服务器")
                print("   python twilio_openai_agent_fastapi.py")
                return False

    except ImportError:
        print("⚠️ httpx 未安装")
        print("💡 安装: pip install httpx")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


async def test_text_to_speech():
    """测试文本转语音（模拟对话）"""
    print("\n" + "=" * 60)
    print("🧪 测试 4: 模拟对话（文本输入）")
    print("=" * 60)

    url = f"wss://api.openai.com/v1/realtime?model={OPENAI_MODEL}"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}

    try:
        async with websockets.connect(url, additional_headers=headers) as ws:
            print("✅ WebSocket 已连接")

            # 配置会话
            await ws.send(json.dumps({
                "type": "session.update",
                "session": {
                    "type": "realtime",
                    "model": OPENAI_MODEL,
                    "modalities": ["text"],  # 只使用文本模式测试
                    "instructions": "你是一个测试助手，用一句话简短回复。",
                }
            }))

            # 等待 session.created
            response = await ws.recv()
            data = json.loads(response)
            if data.get("type") != "session.created":
                print(f"⚠️ 意外响应: {data.get('type')}")
                return False

            print("✅ 会话已创建")

            # 发送测试消息
            test_message = "你好，这是一个测试。请简短回复。"
            print(f"📤 发送消息: {test_message}")

            await ws.send(json.dumps({
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": test_message
                        }
                    ]
                }
            }))

            # 请求生成响应
            await ws.send(json.dumps({
                "type": "response.create"
            }))

            print("⏳ 等待 AI 回复...")

            # 接收响应
            timeout_count = 0
            max_timeout = 20  # 20秒超时

            while timeout_count < max_timeout:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    data = json.loads(response)
                    event_type = data.get("type")

                    if event_type == "response.output_item.done":
                        # 获取响应内容
                        item = data.get("item", {})
                        content = item.get("content", [])
                        if content:
                            text = content[0].get("text", "")
                            print(f"✅ AI 回复: {text}")
                            return True

                    elif event_type == "error":
                        error = data.get("error", {})
                        print(f"❌ API 错误: {error}")
                        return False

                except asyncio.TimeoutError:
                    timeout_count += 1
                    continue

            print("⚠️ 响应超时")
            return False

    except Exception as e:
        print(f"❌ 错误: {e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀 开始本地测试")
    print("=" * 60)

    results = {}

    # 检查环境变量
    if not OPENAI_API_KEY:
        print("❌ 错误: 未设置 OPENAI_API_KEY")
        print("💡 请在 .env 文件中配置 OPENAI_API_KEY")
        return

    print(f"✅ OPENAI_API_KEY: {OPENAI_API_KEY[:20]}...")
    print()

    # 测试 1: OpenAI 连接
    results['openai_connection'] = await test_openai_connection()

    # 测试 2: 音频处理
    results['audio_processing'] = await test_audio_processing()

    # 测试 3: FastAPI 服务器（可选）
    results['fastapi_server'] = await test_fastapi_server()

    # 测试 4: 模拟对话
    if results['openai_connection']:
        results['text_to_speech'] = await test_text_to_speech()

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        test_display = {
            'openai_connection': 'OpenAI 连接',
            'audio_processing': '音频处理',
            'fastapi_server': 'FastAPI 服务器',
            'text_to_speech': '模拟对话'
        }
        print(f"{test_display.get(test_name, test_name)}: {status}")

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    print()
    print(f"通过率: {passed}/{total} ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n下一步:")
        print("1. 配置 Twilio 账户")
        print("2. 设置 ngrok（用于接收 Twilio 回调）")
        print("3. 运行 python test_call.py 发起真实呼叫")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
