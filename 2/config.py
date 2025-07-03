import os
from dotenv import load_dotenv

# Load environment variables from .env file (本地调试用)
load_dotenv()

# ✅ 支持 OpenAI 或 OpenRouter 二选一
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("请设置 OPENAI_API_KEY 或 OPENROUTER_API_KEY 环境变量")

# ✅ OpenWeatherMap 配置
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
if not WEATHER_API_KEY:
    raise ValueError("请设置 WEATHER_API_KEY 环境变量")

# ✅ 飞书配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
    raise ValueError("请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量")

# ✅ 可选配置（用于飞书加密验证）
FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")

# ✅ MCP Server 地址（用于连接你的天气、地图、记录类 MCP）
MCP_API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000")

# ✅ Claude（Anthropic）模型调用配置（可选）
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")
