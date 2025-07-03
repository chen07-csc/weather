# 飞书天气机器人

一个基于 OpenAI、MCP 和飞书的智能天气查询机器人。

## 功能特点

- 自然语言天气查询
- 智能出行建议
- 实时天气数据
- 支持多城市查询

## 环境变量

需要设置以下环境变量：

```bash
# OpenAI 配置
OPENAI_API_KEY=your_openai_api_key_here

# OpenWeatherMap 配置
WEATHER_API_KEY=your_weather_api_key_here

# 飞书配置
FEISHU_APP_ID=your_feishu_app_id_here
FEISHU_APP_SECRET=your_feishu_app_secret_here

# 可选的飞书配置
FEISHU_VERIFICATION_TOKEN=  # 如果需要验证
FEISHU_ENCRYPT_KEY=        # 如果需要加密

# MCP 配置（生产环境）
MCP_URL=https://your_mcp_service_url
```

## 本地开发

1. 克隆仓库
2. 复制 `.env.example` 到 `.env` 并填写配置：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入你的配置值
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 运行服务：
   ```bash
   ./start_services.sh
   ```

## Railway 部署

1. Fork 这个仓库
2. 在 Railway 中创建新项目
3. 选择从 GitHub 导入
4. 在 Railway 的 Variables 页面添加所有必要的环境变量
5. 部署完成后，将生成的域名 + `/webhook` 配置到飞书机器人的事件订阅 URL

## 安全说明

- 永远不要在代码中硬编码 API Keys
- 使用环境变量来管理敏感信息
- 确保 `.env` 文件已添加到 `.gitignore`
- 在生产环境中使用安全的方式管理密钥

## 开发说明

- `main.py`: 主应用入口
- `config.py`: 配置文件
- `feishu_bot.py`: 飞书机器人相关功能
- `mcp_client.py`: MCP 天气服务客户端

## 注意事项

- 请确保 `.env` 文件中的敏感信息安全
- 建议在生产环境中使用 HTTPS
- 定期检查 API 调用限制和配额 