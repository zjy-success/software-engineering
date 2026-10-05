# AI Programming Assistant

一个基于大语言模型的命令行编程助手，目标是帮助开发者在日常编程过程中实现以下能力：

- 解释代码逻辑
- 自动生成代码
- 修复 Bug
- 审查代码质量
- 生成单元测试
- 提出代码重构建议
- 执行 Python 代码验证
- 读取项目文件并进行上下文分析

它不是一个单纯的聊天机器人，而是一个“带工具能力”的编程 Agent，适合在终端中直接使用。

---

## 1. 项目简介

这个项目的核心文件是 `agent.py`。程序启动后会进入交互式命令行界面，用户可以：

- 直接输入自然语言问题
- 发送代码片段
- 执行命令式工具操作
- 请求 Agent 帮助解释、生成、修复和审查代码

项目采用典型的 Agent + Tool + Memory + LLM 架构，适合二次开发和学习 AI Agent 的设计思路。

---

## 2. 适用场景

该项目适用于以下几类场景：

### 2.1 代码解释

当你拿到一段不熟悉的代码时，可以直接让 Agent 说明：

- 它的作用是什么
- 每一部分的逻辑是什么
- 函数调用链如何运行
- 是否存在潜在问题
- 时间复杂度和空间复杂度

### 2.2 代码生成

你可以描述需求，让 Agent 自动生成函数、类、脚本或代码模板。

例如：

```text
/generate 生成一个 Python 函数，用于判断字符串是否为回文
```

### 2.3 Bug 修复

你可以直接把错误代码或报错描述给 Agent：

```text
/fix 下面的 Python 代码报错，帮我修复：

def add(a, b):
    return a + b
```

### 2.4 代码审查

你可以上传代码或直接复制代码，要求 Agent 审查其结构、可维护性和潜在风险：

```text
/review
for i in range(len(items)):
    if items[i] % 2 == 0:
        print(items[i])
```

### 2.5 测试生成

Agent 可以为函数或代码生成 pytest / unittest 风格测试。

```text
/testgen
def add(a, b):
    return a + b
```

### 2.6 重构建议

当代码存在重复逻辑、长函数、耦合过高等问题时，Agent 可以识别坏味道并给出重构建议：

```text
/refactor
def process_order(items):
    total = 0
    for item in items:
        if item['active']:
            total += item['price']
    return total
```

### 2.7 执行验证

对于某些解释和代码行为，可以通过 `/exec` 直接执行 Python 代码进行验证：

```text
/exec print('hello world')
```

---

## 3. 功能清单

这个 Agent 目前支持以下能力：

| 功能 | 命令 | 说明 |
|---|---|---|
| 代码解释 | 普通对话 | 解释代码功能、逻辑和结构 |
| 代码生成 | `/generate` | 根据需求生成代码 |
| Bug 修复 | `/fix` | 分析问题并给出修复方案 |
| 代码审查 | `/review` | 发现问题并给出改进建议 |
| 测试生成 | `/testgen` | 自动生成单元测试 |
| 重构建议 | `/refactor` | 对代码坏味道给出重构建议 |
| 执行代码 | `/exec` | 运行 Python 代码进行验证 |
| 文件读取 | `/read` | 读取项目中的代码文件 |
| 搜索知识 | `/search` | 搜索 API / 文档 / 用法信息 |
| 清除记忆 | `clear` | 清空聊天上下文 |
| 查看状态 | `status` | 查看 Agent 状态 |
| 退出 | `exit` | 退出程序 |

---

## 4. 项目结构

```text
.
├── agent.py
├── read.md
├── README.md
├── .venv/
├── .venv-1/
├── .idea/
└── __pycache__/
```

### 4.1 `agent.py`

这是项目的核心文件，包含以下模块：

- 工具类定义
- LLM 封装
- 对话记忆管理
- Agent 主逻辑
- 命令行交互入口

### 4.2 `read.md`

详细说明文档，适合项目说明和开发者学习。

### 4.3 `README.md`

项目快速说明，适合展示项目概览、启动方法和开发使用说明。

---

## 5. 运行环境要求

### 5.1 Python 版本

推荐：Python 3.10 及以上。

当前环境中已验证可用：

- Python 3.12.4

### 5.2 依赖

项目依赖中最关键的是：

- `openai`

如果当前环境未安装，可以执行：

```powershell
pip install openai
```

或者在当前项目的虚拟环境中安装：

```powershell
.\.venv-1\Scripts\python.exe -m pip install openai
```

---

## 6. 安装与启动

### 6.1 使用系统 Python

```powershell
cd "E:\university\computer science\agent\1"
python agent.py
```

### 6.2 使用项目虚拟环境

```powershell
cd "E:\university\computer science\agent\1"
.\.venv-1\Scripts\python.exe .\agent.py
```

---

## 7. 模型配置

该项目支持 OpenAI 兼容接口，所以可以接入多种模型服务，并且在代码中已经处理了优先级逻辑：

- 优先使用 `OPENAI_API_KEY`
- 其次使用 `DASHSCOPE_API_KEY`

### 7.1 DeepSeek / OpenAI 兼容配置

```powershell
$env:OPENAI_API_KEY = "你的key"
$env:OPENAI_API_BASE = "https://api.deepseek.com"
$env:AGENT_MODEL = "deepseek-chat"
```

### 7.2 阿里云 DashScope 配置

```powershell
$env:DASHSCOPE_API_KEY = "你的key"
$env:DASHSCOPE_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:AGENT_MODEL = "qwen-plus"
```

### 7.3 注意事项

- `API Key` 必须与 `base_url` 对应的服务商匹配
- `model` 名称必须和目标服务兼容
- 不要把 DashScope 的模型名用于 DeepSeek 接口
- 不要把 DeepSeek 的 base_url 用在 DashScope 模型上

---

## 8. 启动示例

### 8.1 DeepSeek 配置示例

```powershell
Set-Location "E:\university\computer science\agent\1"
Remove-Item Env:DASHSCOPE_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:DASHSCOPE_API_BASE -ErrorAction SilentlyContinue
$env:OPENAI_API_KEY = "你的 DeepSeek key"
$env:OPENAI_API_BASE = "https://api.deepseek.com"
$env:AGENT_MODEL = "deepseek-chat"
.\.venv-1\Scripts\python.exe .\agent.py
```

### 8.2 阿里云 DashScope 配置示例

```powershell
Set-Location "E:\university\computer science\agent\1"
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:OPENAI_API_BASE -ErrorAction SilentlyContinue
$env:DASHSCOPE_API_KEY = "你的阿里云 key"
$env:DASHSCOPE_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:AGENT_MODEL = "qwen-plus"
.\.venv-1\Scripts\python.exe .\agent.py
```

---

## 9. 交互方式

程序启动后，终端会展示欢迎信息，然后等待输入：

```text
>
```

### 9.1 普通对话

```text
请解释这段代码的作用
```

### 9.2 代码解释

```text
def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
```

### 9.3 代码生成

```text
/generate 写一个 Python 函数，用来判断是否为回文字符串
```

### 9.4 修复 bug

```text
/fix 下面这段代码存在问题，请帮我修复：

def compute(x):
    return x / 0
```

### 9.5 代码审查

```text
/review
class UserService:
    def get_user(self, user_id):
        return db.query(user_id)
```

### 9.6 测试生成

```text
/testgen
def is_even(x):
    return x % 2 == 0
```

### 9.7 重构建议

```text
/refactor
def total_prices(items):
    total = 0
    for item in items:
        if item['active']:
            total += item['price']
    return total
```

### 9.8 执行代码

```text
/exec print('Hello from agent')
```

### 9.9 读取文件

```text
/read agent.py
```

### 9.10 搜索知识

```text
/search Python list comprehension
```

### 9.11 退出

```text
exit
```

---

## 10. 详细架构设计

### 10.1 Agent + Tool + Memory + LLM

这个项目采用的设计思路是一个经典的 Agent 结构：

- LLM 负责理解与生成
- Tools 提供执行能力
- Memory 保持上下文
- Agent 负责调度和控制

### 10.2 模块职责

#### 1) `LLMClient`

职责：

- 初始化大模型客户端
- 选择 OpenAI 兼容后端
- 处理 API 请求
- 处理错误和重试逻辑

关键特点：

- 兼容 OpenAI SDK
- 支持自定义 model / base_url
- 支持重试机制
- 统一错误提示

#### 2) `ConversationMemory`

职责：

- 存储历史对话
- 支持上下文记忆
- 维护最近 N 轮消息

这种设计使 Agent 不会丢失前文信息，同时不会因为消息过长导致 token 爆炸。

#### 3) `Tool`

所有工具都继承自 `Tool`，具备统一的 `execute` 方法。

目前包含的工具：

- `CodeExecutionTool`
- `FileReadTool`
- `CodeSearchTool`

这些工具让 Agent 不再只是“聊天”，而是能处理真实开发任务。

#### 4) `CodeExplanationAgent`

这是主控制器，负责：

- 读取用户输入
- 构建消息上下文
- 调用 LLM
- 执行工具命令
- 处理命令行逻辑
- 保存对话记录

---

## 11. 关键实现细节

### 11.1 安全性

为了避免潜在风险，项目实现了一些较基础的安全机制：

#### 文件读取限制

`FileReadTool` 会将路径转换为绝对路径，并校验其是否位于项目目录中：

- 避免目录穿越（比如 `../../secret`）
- 防止读取项目外的文件

#### 代码执行超时

`CodeExecutionTool` 会通过 `subprocess.run(..., timeout=30)` 执行 Python 代码：

- 超过 30 秒的任务会被判定超时
- 避免死循环卡住程序

### 11.2 兼容多模型平台

通过 OpenAI 兼容接口，项目可以轻松切换不同模型供应商：

- OpenAI
- DeepSeek
- 阿里云 DashScope
- 其他 OpenAI-compatible API

### 11.3 多轮上下文记忆

`ConversationMemory` 使用固定窗口策略：

- 保留最近的多个对话轮次
- 丢弃更早的历史

这样既保留上下文，又控制 token 消耗。

---

## 12. 常见问题与排查

### 12.1 API Key 不可用

报错示例：

```text
API Key无效或已过期
```

常见原因：

- Key 错误
- Key 已过期
- 账号被停用
- 账号欠费
- Base URL 和模型与服务商不一致

### 12.2 模型名错误

例如：

- DeepSeek 使用 `deepseek-chat`
- DashScope 使用 `qwen-plus`

如果混用，可能出现请求失败。

### 12.3 旧环境变量残留

有时终端中残留旧环境变量，会导致程序继续读取旧值。

可以在新终端中重新设置：

```powershell
Remove-Item Env:DASHSCOPE_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:OPENAI_API_KEY -ErrorAction SilentlyContinue
Remove-Item Env:DASHSCOPE_API_BASE -ErrorAction SilentlyContinue
Remove-Item Env:OPENAI_API_BASE -ErrorAction SilentlyContinue
```

### 12.4 模型供应商混用

例如：

- DeepSeek key + DashScope base URL
- DashScope key + OpenAI / DeepSeek base URL

这会导致服务端拒绝请求。

---

## 13. 推荐用例

以下是几个最典型的测试用例：

### 13.1 解释类

```text
请解释这段代码：

def fib(n):
    if n <= 1:
        return n
    return fib(n - 1) + fib(n - 2)
```

### 13.2 生成类

```text
/generate 生成一个 Python 函数，筛选列表中的偶数并返回新列表
```

### 13.3 测试类

```text
/testgen
def is_palindrome(s):
    return s == s[::-1]
```

### 13.4 审查类

```text
/review
class A:
    def foo(self, x):
        if x is None:
            return 0
        return x * 2
```

### 13.5 重构类

```text
/refactor
def total_prices(items):
    total = 0
    for item in items:
        if item['active']:
            total += item['price']
    return total
```

---

## 14. 典型输出示例

启动后输出类似：

```text
--- 配置信息 ---
API Key: sk-ws-***
模型: qwen-plus
Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
----------------
[LLM] 正在初始化客户端...
[检测] 正在测试API连接...
[检测] API连接正常!
============================================================
  AI Programming Assistant - 编程助手
  功能: 解释代码、生成代码、修复Bug、代码审查、优化重构、测试生成、重构建议
============================================================

>
```

如果运行正常，后续可以直接输入各种命令和需求。 

---

## 15. 扩展方向

这个项目非常适合继续扩展成更成熟的编码助手。下一步可以考虑：

### 15.1 项目级代码分析

扩展命令：

```text
/analyze src/
```

功能：

- 扫描整个项目目录
- 读取多个文件
- 提供全局代码审查

### 15.2 文件自动改写

增加支持：

- 自动改代码
- 生成修复 patch
- 将建议直接写回文件

### 15.3 更强的工程集成

例如：

- 测试文件自动生成
- CI/CD 配置生成
- 文档自动生成
- 代码风格检查器集成

### 15.4 多文件上下文理解

让 Agent 能基于更大范围的项目上下文进行决策，而不是只看单段代码。

---

## 16. 总结

这个项目是一个轻量且可扩展的 AI 编程助手，适合：

- 学习大型语言模型 Agent 的基础实现
- 掌握代码解释/代码生成/代码审查等核心能力
- 探索 AI 编程助手的工程实现方式
- 作为开发者自己的本地 AI 编程工具

它的本质并不是“聊天机器人”，而是：

> 一个能够结合 LLM、工具、执行环境和上下文记忆的编程协作助手。

如果继续扩展下去，它很容易发展成为一个更接近 IDE 辅助工具的项目。

---

## 17. 结语

这个项目已经具备了完整的基础能力：

- 解释代码
- 生成代码
- 修复 Bug
- 审查代码
- 生成测试
- 提出重构建议

---

## 18. 一句话说明

这是一个“面向开发者的 AI 编程助手”，目标是让大模型不仅能回答问题，还能参与到代码理解、代码生成、代码审查、测试生成和重构决策中。