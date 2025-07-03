import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI 配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("请设置 OPENAI_API_KEY 环境变量")

# OpenWeatherMap 配置
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
if not WEATHER_API_KEY:
    raise ValueError("请设置 WEATHER_API_KEY 环境变量")

# Feishu 配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET")
if not FEISHU_APP_ID or not FEISHU_APP_SECRET:
    raise ValueError("请设置 FEISHU_APP_ID 和 FEISHU_APP_SECRET 环境变量")
FEISHU_VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "")  # 需要从飞书开放平台获取
FEISHU_ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "")  # 如果启用了加密，需要设置

# MCP Configuration
MCP_API_BASE_URL = os.getenv("MCP_API_BASE_URL", "http://localhost:8000")  # MCP 服务地址

# Claude API Configuration
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")  # 需要从 Anthropic 获取
CLAUDE_MODEL = "claude-3-opus-20240229"  # 或其他可用的模型版本 