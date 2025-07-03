from mcp.server.fastmcp import FastMCP
import requests
import logging
import re
from typing import Dict, Any
from ai_helper import AIHelper

logging.basicConfig(level=logging.DEBUG)

mcp = FastMCP(
    "weather",
    description="天气查询",
    version="1.0.0"
)

API_KEY = "3208a48dcdc285e6ef965b4ef293b622"
ai_helper = AIHelper()

def extract_city_from_text(text: str) -> str:
    """
    从文本中提取城市名称（简单的规则匹配方案，作为 AI 的后备方案）
    """
    # 去掉常见的询问词
    text = text.replace("天气", "").replace("查询", "").replace("告诉我", "")
    text = text.replace("怎么样", "").replace("如何", "").replace("查一下", "")
    text = text.replace("今天", "").replace("现在", "").strip()
    
    # 如果文本很短，可能直接就是城市名
    if len(text) <= 4:
        return text
        
    # 尝试提取城市名
    city_match = re.search(r'([^市省县]+?)[市省县]', text)
    if city_match:
        return city_match.group(1)
    
    # 如果没有明显的标识，返回第一个词
    words = re.split(r'[,，。！？\s]+', text)
    return words[0] if words else ""

@mcp.tool()
async def get_weather(query: str) -> dict:
    """
    获取指定城市或查询的天气信息。
    Args:
        query: 用户的查询文本，可以是城市名或自然语言查询
    Returns:
        包含温度、湿度、天气描述和风速的 JSON 字典
    """
    try:
        # 使用 OpenAI 处理查询
        query_info = await ai_helper.process_weather_query(query)
        
        # 如果 AI 处理失败，使用后备方案
        if not query_info.get("is_weather_query"):
            city = extract_city_from_text(query)
        else:
            city = query_info.get("city")
            
        if not city:
            return {"error": "未能识别城市名称，请说明具体城市，例如：'北京天气怎么样？'"}
        
        # 调用天气 API
        url = (
            f"http://api.openweathermap.org/data/2.5/weather?q={city}"
            f"&appid={API_KEY}&units=metric&lang=zh_cn"
        )
        
        response = requests.get(url)
        data = response.json()
        
        if "main" not in data:
            return {"error": f"未找到 {city} 的天气信息"}
        
        # 获取天气数据
        weather_data = {
            "city": city,
            "temperature": f"{data['main']['temp']} °C",
            "description": data["weather"][0]["description"],
            "humidity": f"{data['main']['humidity']}%",
            "wind_speed": f"{data['wind']['speed']} m/s",
            "focus": query_info.get("focus", ["天气"])  # 用户关注的天气信息
        }
        
        # 使用 OpenAI 生成自然语言回复
        response = await ai_helper.generate_weather_response(weather_data)
        
        # 返回结果
        return {
            **weather_data,
            "response": response  # AI 生成的自然语言回复
        }

    except Exception as e:
        return {"error": f"查询天气时出错：{str(e)}"}

if __name__ == "__main__":
    print("启动天气查询服务...")
    try:
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\n服务已停止")
    except Exception as e:
        print(f"服务出错: {str(e)}") 