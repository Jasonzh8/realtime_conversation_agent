"""
测试脚本：发起 Twilio + OpenAI 语音呼叫
"""

import requests
import sys
import json
from dotenv import load_dotenv
import os

load_dotenv()

# 服务器地址
SERVER_URL = "http://localhost:5000"


def make_call(to_number: str, instructions: str = None, voice: str = "alloy"):
    """
    发起呼叫

    Args:
        to_number: 被叫号码（E.164格式，如 +8613800138000）
        instructions: AI 指令（可选）
        voice: 语音风格（可选）
    """
    url = f"{SERVER_URL}/make-call"

    payload = {
        "to": to_number,
        "voice": voice
    }

    if instructions:
        payload["instructions"] = instructions

    print(f"📞 正在呼叫 {to_number}...")
    print(f"🎤 语音: {voice}")
    if instructions:
        print(f"📝 指令: {instructions[:100]}...")

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()

        if result.get("success"):
            print("\n✅ 呼叫已发起！")
            print(f"Call SID: {result.get('call_sid')}")
            print(f"状态: {result.get('status')}")
            return result
        else:
            print(f"\n❌ 呼叫失败: {result.get('error')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求失败: {e}")
        return None


def check_server():
    """检查服务器是否运行"""
    try:
        response = requests.get(f"{SERVER_URL}/", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✅ 服务器运行正常")
        print(f"活跃会话: {data.get('active_sessions', 0)}")
        return True
    except:
        print(f"❌ 无法连接到服务器 {SERVER_URL}")
        print("请确保服务器正在运行：python twilio_openai_agent_quart.py")
        return False


# ==================== 预设场景 ====================

SCENARIOS = {
    "1": {
        "name": "客服助手",
        "instructions": "你是一个友好、专业的客服助手。用中文与用户交流，保持礼貌和耐心。先问候用户，然后询问有什么可以帮助的。",
        "voice": "alloy"
    },
    "2": {
        "name": "预约确认",
        "instructions": """你是一个餐厅预约确认助手。任务：
1. 礼貌地问候客户
2. 确认客户姓名
3. 确认预约时间（今晚7点）
4. 确认用餐人数
5. 告知餐厅地址：北京市朝阳区xxx路123号
6. 结束时说"期待您的光临"
保持简洁，每次只问一个问题。""",
        "voice": "nova"
    },
    "3": {
        "name": "问卷调查",
        "instructions": """你是一个客户满意度调查员。任务：
1. 简单介绍调查目的（耗时约2分钟）
2. 询问客户是否方便接受调查
3. 如果同意，依次询问以下问题：
   - 对我们服务的整体满意度（1-10分）
   - 最满意的方面
   - 需要改进的地方
4. 感谢客户的反馈
语气要友好但专业，不要过于冗长。""",
        "voice": "echo"
    },
    "4": {
        "name": "快递通知",
        "instructions": """你是一个快递配送员。任务：
1. 自我介绍（某某快递）
2. 告知有客户的快递需要配送
3. 询问客户是否在家
4. 如果在家，告知10分钟内送达
5. 如果不在家，询问是否放在快递柜
保持简洁高效。""",
        "voice": "onyx"
    },
    "5": {
        "name": "自定义",
        "instructions": None,  # 需要手动输入
        "voice": "alloy"
    }
}


def interactive_mode():
    """交互式模式"""
    print("=" * 60)
    print("🤖 Twilio + OpenAI 语音呼叫测试工具")
    print("=" * 60)

    # 检查服务器
    if not check_server():
        return

    print("\n请选择场景：")
    for key, scenario in SCENARIOS.items():
        print(f"  {key}. {scenario['name']}")

    choice = input("\n请输入选择（1-5）: ").strip()

    if choice not in SCENARIOS:
        print("❌ 无效的选择")
        return

    scenario = SCENARIOS[choice]

    # 自定义场景
    if choice == "5":
        instructions = input("\n请输入 AI 指令：\n").strip()
        voice = input(f"请输入语音风格（默认 alloy）：").strip() or "alloy"
    else:
        instructions = scenario["instructions"]
        voice = scenario["voice"]

    # 输入电话号码
    to_number = input("\n请输入被叫号码（如 +8613800138000）: ").strip()

    if not to_number:
        print("❌ 号码不能为空")
        return

    # 确认信息
    print("\n" + "=" * 60)
    print("📋 呼叫信息确认")
    print("=" * 60)
    print(f"场景: {scenario['name']}")
    print(f"号码: {to_number}")
    print(f"语音: {voice}")
    print(f"指令预览: {instructions[:100] if instructions else '无'}...")

    confirm = input("\n确认发起呼叫？(y/n): ").strip().lower()

    if confirm != 'y':
        print("❌ 已取消")
        return

    # 发起呼叫
    print()
    make_call(to_number, instructions, voice)


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 命令行模式
        to_number = sys.argv[1]
        instructions = sys.argv[2] if len(sys.argv) > 2 else None
        voice = sys.argv[3] if len(sys.argv) > 3 else "alloy"

        if check_server():
            make_call(to_number, instructions, voice)
    else:
        # 交互式模式
        interactive_mode()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
