# Python AI Agent & Web Interface

这是一个基于 Python 的智能代码助手项目，集成了 LLM（大语言模型）能力与 Web 交互界面。项目采用轻量级架构，支持通过 Web 界面进行自然语言交互，并具备代码解释、策略执行等 Agent 能力。

## 主要功能

- **Web 交互界面**：提供现代化的聊天窗口，支持流式输出。
- **智能 Agent 核心**：基于 ReAct 模式，能够理解意图并调用工具。
- **代码解释与分析**：专门针对代码理解场景进行了优化。
- **轻量级部署**：无需复杂的前端构建工具，直接运行即可使用。

## 项目结构

```text
.
├── agent.py          # [核心] Agent 逻辑实现，包含工具定义、LLM 调用及推理循环
├── web_server.py     # [后端] Web 服务器入口，处理 HTTP 请求及 API 路由
├── index.html        # [前端] 用户交互界面，包含 HTML/CSS/JS
├── design.md         # [文档] 详细的设计文档，包含架构图、类图及设计思路
├── requirements.txt  # [配置] Python 依赖包列表
└── README.md         # [文档] 本说明文件
```

## 快速开始

### 1. 环境准备

确保你的电脑上安装了 Python 3.8+。

### 2. 安装依赖

在项目根目录下运行以下命令安装所需的库：

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

本项目依赖大模型服务（如 DashScope/阿里云通义千问）。请在运行前配置环境变量：

```bash
# Linux/Mac
export DASHSCOPE_API_KEY="your-api-key-here"

# Windows (CMD)
set DASHSCOPE_API_KEY=your-api-key-here

# Windows (PowerShell)
$env:DASHSCOPE_API_KEY="your-api-key-here"
```

### 4. 启动服务

运行 Web 服务器脚本：

```bash
python web_server.py
```

服务启动后，打开浏览器访问 `http://127.0.0.1:8000`（或终端显示的端口号）即可开始对话。

## 详细设计

关于系统的架构设计、核心模块实现原理、接口定义及扩展指南，请参阅 [design.md](design.md)。

## 技术栈

- **Backend**: Python, FastAPI/Uvicorn, Subprocess
- **AI Model**: DashScope (Qwen), LangChain (Optional)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (Fetch API)

## 注意事项

- 本项目仅供学习与研究使用。
- 请妥善保管您的 API Key，不要将其上传至公共代码仓库。
