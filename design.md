# 设计文档 (Design Document)

## 项目概述

### 项目简介
本项目（Homework2）是一个基于大语言模型（LLM）的"代码解释Agent + Workflow文档生成流程MVP"系统。项目旨在通过智能体技术，实现对代码的深度理解、自动化解释，并通过工作流引擎编排，自动完成"代码输入 → 逻辑分析 → 文档生成"的全链路任务。

### 项目背景
在软件开发与课程教学场景中，代码解释与文档生成往往耗费大量人工精力。本项目利用大模型的语义理解能力，结合工具调用（Tool Use）与多Agent协作机制，构建一个轻量级但功能完备的自动化辅助系统，作为课程作业验证AI在软件工程辅助领域的落地可行性。

### 项目目标
- **智能交互**：提供基于自然语言的代码解释、审查与重构建议。
- **自动化文档**：通过Workflow引擎，一键生成包含逻辑分析、风险扫描的完整技术文档。
- **安全可控**：内置代码执行沙箱、文件读取安全检查及完善的LLM调用容错机制。
- **可视化编排**：支持Mermaid图表渲染，直观展示工作流执行逻辑。

---

## 技术栈

| 技术领域 | 选型 | 选型理由 |
| :--- | :--- | :--- |
| **后端框架** | FastAPI | 原生异步支持，性能高，自动生成API文档，适合AI Agent的并发调用。 |
| **大模型接口** | 阿里云 DashScope | 兼容 OpenAI SDK 协议，国内访问稳定，支持 qwen-plus 等高性能模型。 |
| **Agent 框架** | 自研轻量级框架 | 基于课程作业需求，避免过度封装，便于理解 Agent 核心循环与工具调用原理。 |
| **前端技术** | HTML5 + CSS3 + Vanilla JS | 零依赖，部署简单，通过 CSS 变量实现主题化，集成 Mermaid.js 实现图表渲染。 |
| **代码执行** | Python subprocess | 提供进程级隔离，配合超时机制防止死循环，保障服务端安全。 |
| **运行环境** | Uvicorn | 高性能 ASGI 服务器，支持热重载与线程池执行器。 |

---

## 系统架构

系统采用经典的 **前后端分离 + 异步事件驱动** 架构：

1. **表现层 (Frontend)**：index.html 提供响应式双栏布局，左侧为对话交互区，右侧为 Workflow 控制台。通过 Fetch API 与后端通信，前端负责 Mermaid 图表的实时渲染。
2. **接口层 (API Gateway)**：web_server.py 基于 FastAPI 构建，负责路由分发、环境变量注入及异步任务调度。通过 run_in_executor 将同步的 Agent 逻辑放入线程池，避免阻塞主事件循环。
3. **核心逻辑层 (Core)**：agent.py 包含 Agent 主循环、工具集、记忆管理及 Workflow 引擎。
    - **Agent Loop**：接收用户指令 → 检索记忆 → 调用 LLM → 解析工具命令 → 执行工具 → 更新记忆 → 返回结果。
    - **Workflow Engine**：支持 DAG（有向无环图）或顺序执行，管理节点间的数据流转（WorkflowState）。
4. **基础设施层 (Infrastructure)**：包括 LLM API 客户端（带重试机制）、本地文件系统（带安全校验）、子进程执行器。

### 模块依赖关系

```
index.html (前端)
    |
    v
web_server.py (FastAPI 后端)
    |
    +---> agent.py (核心逻辑)
            |
            +---> Tool 基类
            |       +---> CodeExecutionTool
            |       +---> FileReadTool
            |       +---> CodeSearchTool
            |
            +---> ConversationMemory (记忆管理)
            |
            +---> LLMClient (大模型客户端)
            |
            +---> CodeExplanationAgent (Agent核心)
            |
            +---> WorkflowState / BaseWorkflowAgent
            |       +---> CodeAnalyzeAgent
            |       +---> DocWriterAgent
            |       +---> RiskScanAgent
            |
            +---> SimpleWorkflowEngine / AdvancedWorkflowEngine
```

---

## 核心模块设计

### 工具模块 (Tools)

采用策略模式设计，所有工具继承自 Tool 基类：

| 工具类 | 功能描述 | 关键实现细节 |
| :--- | :--- | :--- |
| **Tool (基类)** | 工具抽象基类 | 定义 name、description 属性和 execute() 方法接口 |
| **CodeExecutionTool** | 代码执行工具 | 使用 subprocess.run 执行 Python 代码，设置 timeout=30 防止资源耗尽，捕获 stdout 和 stderr 返回执行结果 |
| **FileReadTool** | 文件读取工具 | 读取本地文件，内置路径清洗逻辑，检测 ../ 等目录遍历特征，防止敏感文件泄露 |
| **CodeSearchTool** | 代码搜索工具 | 当前为 Mock 实现，预留 DuckDuckGo/Bing API 接口，用于检索外部代码片段或文档 |

#### CodeExecutionTool 安全机制

```python
# 超时保护：30秒超时防止无限循环
result = subprocess.run(
    [sys.executable, "-c", argument],
    capture_output=True,
    text=True,
    timeout=30
)
```

#### FileReadTool 路径安全检查

```python
# 防止目录遍历攻击 (如 ../../etc/passwd)
filepath = os.path.abspath(argument)
if not filepath.startswith(self.base_dir):
    return "[错误] 不允许访问项目目录之外的文件"
```

### 记忆模块 (Memory)

**ConversationMemory** 采用固定滑动窗口策略：

- **窗口大小**：默认 20 轮对话（即最多保留 40 条消息记录：20轮 x 2条/轮）
- **过期策略**：当对话轮次超过阈值，自动丢弃最早的对话记录
- **设计考量**：既保证了上下文的连贯性，又避免了 Token 溢出，同时降低了 API 调用成本

```python
class ConversationMemory:
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.history: List[Dict[str, str]] = []
    
    def add_turn(self, role: str, content: str):
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # 固定窗口策略: 保留最近 max_turns * 2 条
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-self.max_turns * 2:]
```

### LLM 调用模块 (LLMClient)

封装了与阿里云 DashScope 的交互，具备企业级健壮性：

| 特性 | 说明 |
| :--- | :--- |
| **双模支持** | 兼容 LangChain OpenAI 和原生 OpenAI SDK 两种方式，自动检测可用库并选择 |
| **默认端点** | 阿里云 DashScope: https://dashscope.aliyuncs.com/compatible-mode/v1 |
| **智能重试** | 最多重试 3 次，针对不同错误类型采用不同重试策略 |
| **健康检查** | health_check() 方法用于启动时验证 API Key 有效性 |

#### 错误分类处理策略

| HTTP状态码/错误类型 | 处理策略 | 是否重试 |
| :--- | :--- | :--- |
| **Timeout/超时** | 等比递增等待（5s → 10s → 15s）后重试 | 是（最多3次） |
| **401 Unauthorized** | 直接返回错误提示，提示用户检查 API Key | 否 |
| **403 Forbidden** | 直接返回错误提示，提示用户检查权限 | 否 |
| **429 Rate Limit** | 等比递增等待（10s → 20s → 30s）后重试 | 是（最多3次） |
| **404 Not Found** | 直接返回错误提示，提示用户检查模型名称 | 否 |
| **其他错误** | 等比递增等待后重试，最多3次 | 是（最多3次） |

### Agent 核心 (CodeExplanationAgent)

Agent 主循环实现了标准的 ReAct（Reasoning + Acting）模式：

```
用户输入 → 构建消息(含System Prompt + 历史记忆) → 调用LLM → 
保存对话到记忆 → 返回结果
```

#### 支持的斜杠命令

| 命令 | 功能 | 示例 |
| :--- | :--- | :--- |
| `/exec <代码>` | 执行Python代码并返回输出 | `/exec print(1+2)` |
| `/read <文件路径>` | 读取指定路径文件内容 | `/read agent.py` |
| `/search <关键词>` | 搜索代码相关知识 | `/search Python装饰器` |
| `/generate <需求>` | 根据需求直接生成代码方案 | `/generate 写一个快速排序` |
| `/fix <问题>` | 帮助定位并修复代码问题 | `/fix 这个函数有bug` |
| `/review <代码>` | 审查代码质量并给出改进建议 | `/review def foo():...` |
| `/testgen <代码>` | 根据代码自动生成测试用例 | `/testgen 测试这个函数` |
| `/refactor <代码>` | 分析代码坏味道并给出重构建议 | `/refactor 重构这段代码` |
| `/help` | 显示帮助信息 | `/help` |
| `/clear` | 清空对话记忆 | `/clear` |
| `/status` | 显示Agent状态 | `/status` |

---

## Web界面设计

### 前端交互 (index.html)

**布局设计**：
- PC端采用左右分栏 Grid Layout（1fr 1fr），移动端（max-width: 900px）自动折叠为单栏
- 左侧卡片：对话交互面板（聊天历史区域 + 文本输入框 + 发送按钮）
- 右侧卡片：Workflow运行面板（代码输入区 + 运行按钮 + 输出结果区）

**视觉规范**：
- 使用 CSS 自定义属性（CSS Variables）定义主题色，便于主题切换
- 主色调：#2563eb（蓝色系）
- 消息气泡：用户消息右对齐（蓝色背景白色文字），Agent消息左对齐（灰色背景深色文字）
- 代码块：深色主题（#0f172a背景），提升阅读体验
- 卡片式布局：圆角 + 阴影 + 悬停上浮效果

**JavaScript 功能**：
- Mermaid 图表初始化与自动渲染（识别 ```mermaid 代码块）
- sendChat()：发送聊天消息到 /api/chat 接口
- runWorkflow(mode)：运行Workflow（base基础模式/adv高级模式）到 /api/workflow_run 接口
- Ctrl+Enter 快捷键发送消息
- 自动滚动至最新消息区域

### 后端服务 (web_server.py)

**架构特点**：
- **全局单例模式**：Agent 实例在应用启动时初始化（开发MVP阶段，生产环境建议注入）
- **异步桥接**：POST /api/chat 和 POST /api/workflow_run 接口内部使用 loop.run_in_executor(None, ...) 包装同步的 Agent 方法，确保高并发下 FastAPI 事件循环不卡顿
- **完整异常处理**：try-except 捕获所有异常，格式化错误信息后返回 JSON 响应

---

## 工作流设计

### 基础工作流 (Base Workflow)

采用**顺序执行**模式，模拟标准文档生成 SOP：

```
代码输入 → CodeAnalyzeAgent(代码分析) → DocWriterAgent(文档撰写) → 输出文档
```

**执行流程**：
1. **CodeAnalyzeAgent**：接收源码，分析核心逻辑、依赖关系与复杂度
2. **DocWriterAgent**：基于分析结果，生成结构化的 Markdown 技术文档

### 高级工作流 (Advanced Workflow)

支持 **DAG 编排**，具备以下特性：

```
代码输入 → [CodeAnalyzeAgent] ──┐
                  ↓              │
            [RiskScanAgent] ─────┤ (可并行)
                  ↓              │
            [DocWriterAgent] ────┘
                  ↓
            输出文档 + 风险报告
```

**高级特性**：
- **并行执行**：CodeAnalyzeAgent 与 RiskScanAgent 可并行运行，缩短总耗时
- **循环/条件分支**：支持根据风险扫描结果决定是否触发 /fix 修复节点
- **状态共享**：通过 WorkflowState 对象在节点间传递数据，解耦节点逻辑
- **执行日志**：完整的状态追踪与日志输出，便于调试

### WorkflowState 状态对象

WorkflowState 是工作流中各 Agent 节点之间共享数据的桥梁：

| 属性 | 类型 | 说明 |
| :--- | :--- | :--- |
| doc_output | str | 最终生成的文档内容 |
| error | str | 错误信息（如有） |
| log | str | 执行日志 |
| risk_scan_result | str | 风险扫描结果（高级模式） |
| summary_result | str | 代码摘要结果 |

---

## 接口设计

### 1. 聊天接口

| 属性 | 说明 |
| :--- | :--- |
| **URL** | POST /api/chat |
| **Content-Type** | application/json |
| **请求体** | `{"user_text": "请解释这段代码的逻辑"}` |
| **响应体(成功)** | `{"ok": true, "reply": "这段代码实现了..."}` |
| **响应体(失败)** | `{"ok": false, "msg": "后端异常：..."}` |
| **说明** | 同步阻塞返回（内部通过 run_in_executor 异步执行），支持多轮对话上下文 |

### 2. 工作流运行接口

| 属性 | 说明 |
| :--- | :--- |
| **URL** | POST /api/workflow_run |
| **Content-Type** | application/json |
| **请求体** | `{"code_text": "def hello():...", "mode": "base"}` |
| **mode 参数** | "base"（顺序执行）或 "adv"（高级并行执行） |
| **响应体(成功)** | `{"ok": true, "error": "", "log": "...", "document": "...", "risk_scan": "...", "summary": "..."}` |
| **响应体(失败)** | `{"ok": false, "error": "异常信息"}` |
| **说明** | mode 可选 base(顺序) 或 adv(高级并行)。返回完整的执行日志与生成产物 |

### 3. 页面接口

| 属性 | 说明 |
| :--- | :--- |
| **URL** | GET / |
| **响应** | 返回 index.html 前端页面内容 |
| **Content-Type** | text/html; charset=utf-8 |

---

## 配置说明

### 环境变量

请在项目根目录配置以下环境变量（或通过 .env 文件加载）：

| 环境变量 | 是否必填 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- |
| **DASHSCOPE_API_KEY** | 必填 | (无) | 阿里云 DashScope API 密钥，用于调用大模型 |
| **AGENT_MODEL** | 选填 | qwen-plus | 使用的模型名称，可选 qwen-turbo / qwen-plus / qwen-max |
| **DASHSCOPE_API_BASE** | 选填 | https://dashscope.aliyuncs.com/compatible-mode/v1 | API 基础 URL，用于兼容非 OpenAI 的接口 |

### 依赖安装

```bash
# 安装核心依赖
pip install fastapi uvicorn openai langchain langchain-openai python-dotenv
```

### 项目文件结构

```
project/
├── agent.py              # 核心逻辑：Tools、Memory、LLMClient、Agent、Workflow
├── web_server.py         # FastAPI 后端服务
├── index.html            # 前端 Web 界面
├── design.md             # 本设计文档
└── requirements.txt      # 依赖清单
```

---

## 使用方法

### 1. 快速启动

```bash
# 步骤1：配置环境变量
export DASHSCOPE_API_KEY="sk-你的API密钥"

# 步骤2：安装依赖
pip install fastapi uvicorn openai langchain langchain-openai

# 步骤3：启动服务
python web_server.py
```

服务启动后访问：http://127.0.0.1:8000

### 2. Web 界面使用

**对话交互面板（左侧）**：
- 直接输入自然语言问题，Agent 会自动理解并回复
- 使用斜杠命令调用工具：/exec、/read、/search、/generate、/fix、/review、/testgen、/refactor
- 按 Ctrl+Enter 快捷发送消息
- 输入 /help 查看所有可用命令

**Workflow 运行面板（右侧）**：
- 在代码输入区粘贴待分析的 Python 代码
- 点击"运行【基础Workflow】"执行顺序分析+文档生成
- 点击"运行【高级Workflow】"执行并行分析+风险扫描+文档生成
- 输出区域展示完整的执行日志、风险扫描报告和生成的 Markdown 文档

### 3. 命令行交互（调试用）

若需脱离 Web 界面直接调试 Agent：

```python
from agent import CodeExplanationAgent

# 初始化Agent
agent = CodeExplanationAgent(
    api_key="sk-你的API密钥",
    model="qwen-plus",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 单轮对话
response = agent.run("请解释快速排序算法")
print(response)

# 或使用工具命令
response = agent.run_tool("/exec print('Hello World')")
print(response)
```

---

## 安全设计

### 安全措施总览

| 安全层面 | 措施 | 防护目标 |
| :--- | :--- | :--- |
| **代码执行沙箱** | subprocess 强制 30 秒超时 + capture_output | 防止恶意代码无限循环占用 CPU/内存 |
| **路径遍历防护** | FileReadTool 绝对路径校验 + base_dir 前缀检查 | 防止读取 /etc/passwd 等系统敏感文件 |
| **API Key 隔离** | 仅通过环境变量注入，不硬编码、不返回给前端 | 防止密钥泄露 |
| **输入校验** | FastAPI + Pydantic 模型校验请求体 | 防止注入攻击和畸形数据 |
| **LLM 错误隔离** | 完善的异常捕获，不暴露内部堆栈给前端 | 防止信息泄露 |

### 路径遍历防护详解

FileReadTool 在读取文件前执行双重安全检查：

```python
# 1. 转换为绝对路径
filepath = os.path.abspath(argument)
# 2. 检查是否在允许的基础目录内
if not filepath.startswith(self.base_dir):
    return "[错误] 不允许访问项目目录之外的文件"
```

此机制有效防御以下攻击：
- `../../etc/passwd` — 目录遍历攻击
- `/etc/shadow` — 绝对路径越权访问
- `../.env` — 敏感配置文件读取

---

## 错误处理与容错

### LLM 调用容错机制

LLMClient 实现了多层容错策略：

| 容错层级 | 策略 | 说明 |
| :--- | :--- | :--- |
| **网络抖动** | 自动重试 3 次，间隔递增（5s → 10s → 15s） | 应对临时网络不稳定 |
| **配额限制 (429)** | 捕获异常后等待指定时间再重试 | 应对 API 调用频率限制 |
| **认证失败 (401/403)** | 不重试，直接返回友好错误提示 | 避免无效重试浪费资源 |
| **模型不存在 (404)** | 不重试，提示用户检查模型名称 | 配置错误无需重试 |
| **未知错误** | 重试 3 次后返回格式化错误信息 | 兜底策略 |

### 工具执行容错

| 工具 | 容错措施 |
| :--- | :--- |
| **CodeExecutionTool** | subprocess 异常捕获 + stderr 格式化返回 + 超时保护 |
| **FileReadTool** | FileNotFoundError / PermissionError 分别处理 + 路径安全校验 |
| **CodeSearchTool** | 当前为 Mock 实现，后续接入真实 API 时需添加请求超时和重试 |

### 工作流容错

- **节点失败处理**：高级引擎支持错误捕获，可配置"失败后跳过"或"重试当前节点"
- **状态持久化**：WorkflowState 记录每个节点的输入输出，便于断点调试与日志追踪
- **完整日志**：state.dump_log() 输出完整执行链路，便于问题定位

---

## 扩展性设计

### 扩展新工具

扩展新工具只需 4 步：

```python
# 步骤1：继承 Tool 基类
class MyNewTool(Tool):
    def __init__(self):
        super().__init__(
            name="my_new_tool",
            description="描述工具功能"
        )
    
    # 步骤2：实现 execute 方法
    def execute(self, argument: str) -> str:
        # 工具逻辑
        return "结果"

# 步骤3：在 CodeExplanationAgent.__init__ 中注册
self.tools["my_new_tool"] = MyNewTool()

# 步骤4：在 TOOL_DESCRIPTION 中补充使用说明
```

### 扩展新 Agent（Workflow 节点）

```python
# 步骤1：继承 BaseWorkflowAgent
class MyAgent(BaseWorkflowAgent):
    def __init__(self):
        super().__init__(name="my_agent", ...)
    
    # 步骤2：实现 process 方法
    def process(self, state: WorkflowState) -> WorkflowState:
        # 节点逻辑
        return state

# 步骤3：在 WorkflowEngine 中注册节点类型
# 步骤4：在 run_document_generation_workflow 或 run_adv_workflow 中编排节点
```

### 扩展 Workflow 模板

在 run_document_generation_workflow 或 run_adv_workflow 中修改节点连接关系，即可快速构建新的业务流，例如：
- **单元测试生成流**：代码分析 → 测试生成 → 测试执行 → 报告输出
- **API 文档生成流**：代码分析 → API接口提取 → Markdown文档生成 → 格式校验
- **代码审查流**：代码分析 → 风险扫描 → 质量评估 → 审查报告生成

---

## 未来改进方向

### 短期改进（1-2周）

| 改进项 | 描述 | 优先级 |
| :--- | :--- | :--- |
| **流式输出 (Streaming)** | 前端接入 SSE (Server-Sent Events)，实现打字机效果，提升长文本生成的用户体验 | 高 |
| **Markdown 文档导出** | 支持将生成的文档下载为 .md 或 .docx 文件 | 高 |
| **对话历史持久化** | 将对话历史存入 SQLite/JSON 文件，支持会话恢复 | 中 |

### 中期改进（1-2个月）

| 改进项 | 描述 | 优先级 |
| :--- | :--- | :--- |
| **向量检索 (RAG)** | 集成 ChromaDB/Faiss，支持基于项目历史代码的语义搜索，提升解释准确度 | 高 |
| **多模态支持** | 支持上传架构图/截图，让 Agent 结合图片与代码进行联合分析 | 中 |
| **容器化沙箱** | 将 subprocess 替换为 Docker/gVisor 容器执行，实现真正的进程级隔离 | 高 |

### 长期规划（3个月+）

| 改进项 | 描述 | 优先级 |
| :--- | :--- | :--- |
| **持久化记忆** | 将对话历史与生成的文档存入数据库，支持长期知识沉淀 | 中 |
| **可视化编排器** | 前端集成拖拽式 DAG 编辑器，让用户自定义 Workflow 节点与连线 | 中 |
| **多租户支持** | 支持多用户并发使用，隔离各自的工作空间和对话历史 | 低 |
| **插件市场** | 允许社区贡献工具和Agent节点，形成可扩展的插件生态 | 低 |
