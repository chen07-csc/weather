import aiohttp
from config import MCP_API_BASE_URL, MCP_API_KEY
from typing import Dict, Any

class MCPClient:
    def __init__(self):
        self.base_url = MCP_API_BASE_URL
        self.api_key = MCP_API_KEY
        
    async def get_weather(self, city: str) -> Dict[str, Any]:
        """
        获取指定城市的天气信息
        Args:
            city: 城市名称（如 Beijing）
        Returns:
            dict: 天气信息
        """
        async with aiohttp.ClientSession() as session:
            # 调用 MCP 的天气服务
            async with session.post(
                f"{self.base_url}/invoke/weather/get_weather",
                json={"city": city}
            ) as response:
                if response.status == 200:
                    weather_data = await response.json()
                    if "error" in weather_data:
                        raise Exception(weather_data["error"])
                    return weather_data
                else:
                    error_text = await response.text()
                    raise Exception(f"Failed to get weather: {error_text}")

    async def stream_weather(self, city: str):
        """
        流式获取天气信息
        Args:
            city: 城市名称
        Yields:
            dict: 天气信息的各个部分
        """
        try:
            weather_data = await self.get_weather(city)
            
            # 将天气信息分成多个部分返回
            # 1. 城市和温度
            yield {
                "type": "current",
                "data": {
                    "city": weather_data["city"],
                    "temperature": weather_data["temperature"]
                }
            }
            
            # 2. 天气描述
            yield {
                "type": "description",
                "data": {
                    "description": weather_data["description"]
                }
            }
            
            # 3. 湿度和风速
            yield {
                "type": "details",
                "data": {
                    "humidity": weather_data["humidity"],
                    "wind_speed": weather_data["wind_speed"]
                }
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "data": {
                    "error": str(e)
                }
            } 