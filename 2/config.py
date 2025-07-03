import os
from dotenv import load_dotenv

# 本地调试时从 .env 文件加载环境变量，生产环境中一般通过运行环境变量注入
load_dotenv()

# OpenAI 或 OpenRouter API Key，二选一即可
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
API_KEY = OPENROUTER_API_KEY or OPENAI_API_KEY
if not API_KEY:
    raise ValueError("请设置 OPENAI_API_KEY 或 OPENROUTER_API_KEY 环境变量")

# OpenWeatherMap API Key
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
if not WEATHER_API_KEY:
    raise ValueError("请设置 WEATHER_API_KEY 环境变量")

# 飞书 App ID 和 App Secret
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
    raise ValueError("请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量")

# 飞书可选安全配置，若启用消息加密等
FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")
FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")

# MCP Server 基础地址，用于调用其他 MCP 服务（默认本地）
MCP_API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000")

# Claude (Anthropic) 相关配置（可选）
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")

