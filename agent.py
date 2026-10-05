
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码解释Agent (Code Explanation Agent)
=======================================
方向: 代码解释Agent - 解释代码逻辑、生成注释、回答代码问题

核心能力:
1. 接收代码片段或代码文件
2. 调用LLM解释代码的逻辑和功能
3. 为代码生成自然语言注释
4. 回答关于代码行为的问题
5. 支持多轮对话上下文记忆
6. 支持手动执行代码验证(输入 /exec 命令)
"""

import os
import sys
import subprocess
import traceback
import time
from datetime import datetime
from typing import List, Dict, Optional


# ============================================================
# 1. 工具模块 (Tools)
# ============================================================

class Tool:
    """工具基类 - 所有工具都继承此类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def execute(self, argument: str) -> str:
        """执行工具操作，返回结果字符串"""
        raise NotImplementedError


class CodeExecutionTool(Tool):
    """代码执行工具
    功能: 执行Python代码并返回stdout/stderr输出
    用途: 用户输入 /exec 命令时，让Agent运行代码来验证解释是否正确
    """

    def __init__(self):
        super().__init__(
            name="code_executor",
            description="执行Python代码并返回输出结果。参数是一个Python代码字符串。"
                        "适用于验证代码行为、测试代码逻辑、观察运行输出。"
        )
        self.executed_code = ""

    def execute(self, argument: str) -> str:
        self.executed_code = argument
        try:
            # 使用subprocess运行代码，设置30秒超时防止无限循环
            result = subprocess.run(
                [sys.executable, "-c", argument],
                capture_output=True,
                text=True,
                timeout=30
            )
            output = ""
            if result.stdout:
                output += "[STDOUT]\n" + result.stdout
            if result.stderr:
                output += "[STDERR]\n" + result.stderr
            if result.returncode != 0 and not result.stderr:
                output += "\n[执行失败, 返回码: " + str(result.returncode) + "]"
            return output if output else "[代码执行完成, 无输出]"
        except subprocess.TimeoutExpired:
            return "[错误] 代码执行超时(超过30秒)，可能包含无限循环"
        except Exception as e:
            return "[错误] " + str(e)


class FileReadTool(Tool):
    """文件读取工具
    功能: 读取指定路径的文件内容
    用途: 用户输入 /read 命令时，让Agent读取项目中的代码文件进行分析解释
    """

    def __init__(self, base_dir: str = "."):
        super().__init__(
            name="file_reader",
            description="读取指定路径的文件内容。参数是文件路径字符串。"
                        "适用于读取项目代码文件进行分析。"
        )
        # 获取基础目录的绝对路径，用于安全检查
        self.base_dir = os.path.abspath(base_dir)

    def execute(self, argument: str) -> str:
        # 转换为绝对路径
        filepath = os.path.abspath(argument)
        # 安全检查: 防止目录遍历攻击 (如 ../../etc/passwd)
        if not filepath.startswith(self.base_dir):
            return "[错误] 不允许访问项目目录之外的文件"
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return "[文件: " + argument + "]\n" + content
        except FileNotFoundError:
            return "[错误] 文件未找到: " + argument
        except PermissionError:
            return "[错误] 无权限读取文件: " + argument
        except Exception as e:
            return "[错误] " + str(e)


class CodeSearchTool(Tool):
    """代码搜索工具
    功能: 搜索代码相关知识或文档
    用途: 当Agent需要查找某个API的用法或某个概念的解释时使用
    """

    def __init__(self):
        super().__init__(
            name="code_search",
            description="搜索代码相关知识或文档。参数是搜索关键词。"
                        "适用于查找Python标准库文档、第三方库用法等。"
        )

    def execute(self, argument: str) -> str:
        # 当前为模拟实现，实际可接入DuckDuckGo/Bing API
        # 这里返回提示信息，用户可替换为真实API调用
        return "[搜索结果] 关于 '" + argument + "' 的搜索结果(请接入真实搜索API以获取实际数据)"


# ============================================================
# 2. 记忆模块 (Memory) - 对话上下文管理
# ============================================================

class ConversationMemory:
    """对话记忆管理器
    功能: 存储多轮对话历史，实现上下文记忆
    策略: 固定窗口大小(默认20轮)，超出后丢弃最早的对话
    """

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.history: List[Dict[str, str]] = []

    def add_turn(self, role: str, content: str):
        """添加一轮对话记录
        role: 'user'(用户) 或 'assistant'(Agent)
        content: 对话内容
        """
        self.history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # 固定窗口策略: 保留最近 max_turns * 2 条(每轮2条: user+assistant)
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-self.max_turns * 2:]

    def get_context(self) -> List[Dict[str, str]]:
        """获取当前对话上下文(去除timestamp)"""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.history
        ]

    def clear(self):
        """清空记忆"""
        self.history = []

    def __len__(self):
        return len(self.history)


# ============================================================
# 3. LLM调用模块 - 封装大模型API (已修复)
# ============================================================

class LLMClient:
    """LLM客户端
    功能: 封装大语言模型的API调用
    兼容性: 支持LangChain OpenAI和原生OpenAI SDK两种方式
    配置: 支持自定义API Key / Model / Base URL

    修复内容:
    - 默认base_url设为阿里云DashScope端点
    - 增加自动重试机制(最多3次)
    - 增加连接健康检查
    - 更清晰的错误提示
    """

    # 阿里云DashScope默认端点(兼容OpenAI协议)
    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(self, api_key: str, model: str = "qwen-plus", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        # 如果没有指定base_url，默认使用阿里云DashScope端点
        self.base_url = base_url if base_url else self.DEFAULT_BASE_URL
        self._llm = None
        self._llm_type = None
        self._init_llm()

    def _init_llm(self):
        """初始化LLM客户端，尝试多种后端"""
        print("[LLM] 正在初始化客户端...")
        print("[LLM] 模型: " + self.model)
        print("[LLM] Base URL: " + self.base_url)

        try:
            # 方式1: 使用LangChain
            from langchain_openai import ChatOpenAI
            llm_kwargs = {
                "model": self.model,
                "api_key": self.api_key,
                "temperature": 0.3,
            }
            if self.base_url:
                llm_kwargs["openai_api_base"] = self.base_url
            self._llm = ChatOpenAI(**llm_kwargs)
            self._llm_type = "langchain"
            print("[LLM] 使用 LangChain 后端")
        except ImportError:
            try:
                # 方式2: 使用原生OpenAI SDK
                from openai import OpenAI
                client_kwargs = {"api_key": self.api_key, "timeout": 120}
                if self.base_url:
                    client_kwargs["base_url"] = self.base_url
                self._llm = OpenAI(**client_kwargs)
                self._llm_type = "openai_native"
                print("[LLM] 使用 OpenAI SDK 原生后端")
            except ImportError:
                raise ImportError(
                    "请安装LLM客户端库: pip install openai -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn"
                )

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """发送对话请求并获取LLM回复
        messages: 消息列表，每条包含 role 和 content
        返回: LLM的回复文本

        修复: 增加了重试机制(最多3次)，网络波动时自动重试
        """
        max_retries = 3
        last_error = ""

        for attempt in range(max_retries):
            try:
                if self._llm_type == "openai_native":
                    # 原生OpenAI SDK调用
                    response = self._llm.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=0.3,
                        timeout=120
                    )
                    return response.choices[0].message.content
                else:
                    # LangChain调用
                    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
                    langchain_messages = []
                    for msg in messages:
                        if msg["role"] == "system":
                            langchain_messages.append(SystemMessage(content=msg["content"]))
                        elif msg["role"] == "user":
                            langchain_messages.append(HumanMessage(content=msg["content"]))
                        elif msg["role"] == "assistant":
                            langchain_messages.append(AIMessage(content=msg["content"]))
                    response = self._llm.invoke(langchain_messages)
                    return response.content
            except Exception as e:
                last_error = str(e)
                error_str = str(e)

                # 判断是否是超时错误
                if "timed out" in error_str.lower() or "timeout" in error_str.lower() or "timeout" in type(e).__name__.lower():
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 5秒、10秒、15秒
                        print("[LLM] 请求超时 (第" + str(attempt + 1) + "次尝试)，" + str(wait_time) + "秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return "[LLM调用错误] 请求超时，已重试" + str(max_retries) + "次。请检查网络连接或API Key是否有效。"
                elif "401" in error_str or "unauthorized" in error_str.lower() or "auth" in error_str.lower():
                    return "[LLM调用错误] API Key无效或已过期，请检查你的DASHSCOPE_API_KEY环境变量是否正确设置。"
                elif "403" in error_str or "forbidden" in error_str.lower():
                    return "[LLM调用错误] 权限不足(403)，请检查API Key是否有调用该模型的权限。"
                elif "429" in error_str or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10
                        print("[LLM] 请求过于频繁 (第" + str(attempt + 1) + "次尝试)，" + str(wait_time) + "秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return "[LLM调用错误] 请求频率限制(429)，请稍后再试。"
                elif "404" in error_str or "not found" in error_str.lower():
                    return "[LLM调用错误] 模型不存在(404)，请检查AGENT_MODEL环境变量设置的模型名称是否正确。可用模型: qwen-turbo, qwen-plus, qwen-max"
                else:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print("[LLM] 请求失败 (第" + str(attempt + 1) + "次尝试): " + error_str[:100] + "，" + str(wait_time) + "秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return "[LLM调用错误] " + error_str[:500] + "\n[提示] 请检查: 1)网络连接 2)API Key是否正确 3)模型名称是否正确 4)是否设置了正确的Base URL"

        return "[LLM调用错误] 未知错误，已重试" + str(max_retries) + "次。"

    def health_check(self) -> tuple:
        """健康检查: 测试API连接是否正常
        返回: (是否成功, 错误信息)
        """
        try:
            test_messages = [
                {"role": "system", "content": "你是一个测试助手。"},
                {"role": "user", "content": "请回复OK"}
            ]
            result = self.chat(test_messages)
            if "ok" in result.lower():
                return True, "连接正常"
            else:
                return False, "响应异常: " + result[:200]
        except Exception as e:
            return False, str(e)


# ============================================================
# 4. Agent核心 - 代码解释Agent (已修复)
# ============================================================

class CodeExplanationAgent:
    """代码解释Agent - 核心Agent循环
    方向: 代码解释Agent
    核心功能:
      - 解释代码逻辑(用自然语言描述代码做了什么)
      - 为代码生成注释
      - 回答关于代码的问题
      - 分析代码执行流程

    修复内容:
    - 移除了自动从LLM回复中解析代码块并执行的功能(之前会导致无限循环)
    - 改为纯对话模式: 用户输入 -> LLM回复 -> 输出
    - 代码执行改为手动触发(输入 /exec 命令)
    - 文件读取改为手动触发(输入 /read 命令)
    """

    # 系统提示词 - 定义Agent的角色和能力
    SYSTEM_PROMPT = """你是一个专业的 AI 编程助手(Programming Assistant)，擅长:
1. 解释代码逻辑、功能和执行流程
2. 生成高质量代码、函数、类和脚本
3. 修复代码中的Bug和兼容性问题
4. 为代码添加清晰注释和重构建议
5. 代码审查、性能优化、复杂度分析
6. 根据需求直接给出可运行的实现方案
7. 自动生成单元测试、边界测试和异常测试用例
8. 识别代码坏味道（重复代码、长函数、过度耦合、神秘命名等）并给出重构方案

你的工作流程:
- 当用户给出需求时，优先给出可执行代码和必要说明
- 当用户给出代码片段时，先解释再提出改进方案
- 当需要验证代码行为时，可以建议用户使用 /exec 命令
- 当需要查看文件内容时，可以建议用户使用 /read 命令
- 当需要查找某个API用法时，可以建议用户使用 /search 命令
- 当用户需要修复错误时，先定位问题，再给出修复代码
- 当用户请求生成测试时，优先产出 pytest 或 unittest 风格的测试代码，并包含正常路径、边界条件和异常场景
- 当用户请求重构建议时，优先识别代码坏味道，给出重构目标、重构步骤和重构后示例

你不是一个简单的解释器，而是一个帮助开发者编程、调试、重构和学习的协作助手。
请优先用中文回答，但代码和函数示例可以直接给出，保持简洁且实用。

输出时请遵循：
- 先回答核心问题
- 再给出关键代码
- 最后给出注意事项或优化建议
"""

    # 工具描述 - 告诉LLM有哪些工具可用(仅供参考, 实际由用户手动触发)
    TOOL_DESCRIPTION = """用户可以使用以下命令:
- /exec <代码> : 执行Python代码并返回输出结果，用于验证代码行为。
- /read <文件路径> : 读取指定路径文件内容，用于查看代码文件。
- /search <关键词> : 搜索代码相关知识，用于查找API用法或文档。
- /generate <需求> : 根据需求直接生成代码方案。
- /fix <问题描述或代码> : 帮助定位并修复代码问题。
- /review <代码> : 审查代码质量并给出改进建议。
- /testgen <代码或功能描述> : 根据代码/需求自动生成测试用例（pytest/unittest）。
- /refactor <代码或需求> : 分析代码坏味道并给出重构建议和重构示例。
- /help : 显示帮助信息
- /clear : 清空对话记忆
- /status : 显示Agent状态
- exit : 退出程序"""

    def __init__(self, api_key: str, model: str = "qwen-plus", base_url: Optional[str] = None):
        """初始化Agent
        api_key: LLM API密钥
        model: 使用的模型名称
        base_url: API基础URL(用于兼容非OpenAI的接口)
        """
        self.llm = LLMClient(api_key, model, base_url)
        self.memory = ConversationMemory(max_turns=20)
        # 注册工具(供用户手动触发)
        self.tools = {
            "code_executor": CodeExecutionTool(),
            "file_reader": FileReadTool(),
            "code_search": CodeSearchTool(),
        }
        self.turn_count = 0

    def _execute_tool(self, tool_name: str, argument: str) -> str:
        """执行工具调用"""
        if tool_name in self.tools:
            try:
                return self.tools[tool_name].execute(argument)
            except Exception as e:
                return "[工具执行错误] " + tool_name + ": " + str(e)
        return "[错误] 未知工具: " + tool_name

    def _build_messages(self, user_input: str) -> List[Dict[str, str]]:
        """构建LLM请求消息
        消息组成:
          1. System消息: Agent角色定义 + 工具描述
          2. 历史对话: 多轮上下文
          3. 当前用户输入
        """
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "system", "content": self.TOOL_DESCRIPTION},
        ]
        # 添加历史对话(上下文记忆)
        messages.extend(self.memory.get_context())
        # 添加当前用户输入
        messages.append({"role": "user", "content": user_input})
        return messages

    def _process(self, messages: List[Dict[str, str]]) -> str:
        """处理用户输入: 调用LLM生成回复
        修复: 不再自动解析工具调用, 直接返回LLM回复
        """
        # 调用LLM生成回复
        llm_response = self.llm.chat(messages)
        return llm_response

    def run(self, user_input: str) -> str:
        """运行Agent主循环: 输入 -> 推理 -> 输出"""
        self.turn_count += 1
        print("\n" + "=" * 50)
        print("用户 (第" + str(self.turn_count) + "轮): " + user_input)
        print("=" * 50)

        try:
            # 构建消息
            messages = self._build_messages(user_input)
            # 调用LLM
            response = self._process(messages)
            # 保存到记忆
            self.memory.add_turn("user", user_input)
            self.memory.add_turn("assistant", response)

            print("\nAgent: " + response)
            return response
        except Exception as e:
            error_msg = "[Agent错误] " + str(e) + "\n" + traceback.format_exc()
            print("\nAgent: " + error_msg)
            self.memory.add_turn("assistant", error_msg)
            return error_msg

    def run_tool(self, tool_command: str) -> str:
        """处理工具命令
        支持执行代码、读取文件、搜索知识，以及更像编程助手的生成/修复/评审命令。
        """
        self.turn_count += 1
        print("\n" + "=" * 50)
        print("用户 (第" + str(self.turn_count) + "轮): " + tool_command)
        print("=" * 50)

        try:
            # 解析命令
            if tool_command.startswith("/exec "):
                code = tool_command[6:].strip()
                if not code:
                    result = "[错误] 请提供要执行的代码"
                else:
                    result = self._execute_tool("code_executor", code)
            elif tool_command.startswith("/read "):
                filepath = tool_command[6:].strip()
                if not filepath:
                    result = "[错误] 请提供文件路径"
                else:
                    result = self._execute_tool("file_reader", filepath)
            elif tool_command.startswith("/search "):
                keyword = tool_command[8:].strip()
                if not keyword:
                    result = "[错误] 请提供搜索关键词"
                else:
                    result = self._execute_tool("code_search", keyword)
            elif tool_command.startswith("/generate "):
                requirement = tool_command[10:].strip()
                if not requirement:
                    result = "[错误] 请提供生成代码的需求描述"
                else:
                    prompt = (
                        "你是一个资深程序员和代码助手。请根据下面需求直接生成高质量代码，"
                        "并给出简短说明。\n\n需求：" + requirement +
                        "\n\n要求：\n1. 代码要可直接运行\n2. 说明输入输出和关键逻辑\n3. 若有边界情况，说明清楚"
                    )
                    result = self._process(self._build_messages(prompt))
            elif tool_command.startswith("/fix "):
                content = tool_command[5:].strip()
                if not content:
                    result = "[错误] 请提供需要修复的问题描述或代码"
                else:
                    prompt = (
                        "你是一个程序调试助手。请分析并修复下面的问题，并给出修复后的代码。\n\n问题/代码：\n" + content +
                        "\n\n要求：\n1. 说明根因\n2. 给出修复方案\n3. 提供修复后的代码示例"
                    )
                    result = self._process(self._build_messages(prompt))
            elif tool_command.startswith("/review "):
                code = tool_command[8:].strip()
                if not code:
                    result = "[错误] 请提供要评审的代码"
                else:
                    prompt = (
                        "你是一个资深代码审查员。请审查下面代码的优点、潜在问题和改进建议。\n\n代码：\n" + code +
                        "\n\n要求：\n1. 说明主要问题\n2. 给出优化建议\n3. 给出重构示例（如有必要）"
                    )
                    result = self._process(self._build_messages(prompt))
            elif tool_command.startswith("/testgen "):
                content = tool_command[9:].strip()
                if not content:
                    result = "[错误] 请提供要生成测试的代码或功能描述"
                else:
                    prompt = (
                        "你是一个资深测试工程师。请根据下面的代码或需求生成高质量的 Python 单元测试。\n\n输入：\n" + content +
                        "\n\n要求：\n1. 使用 pytest 或 unittest 形式编写测试代码\n2. 覆盖正常路径、边界条件和异常情况\n3. 生成清晰的断言和测试名称\n4. 若代码中有依赖，明确假设和测试方式\n5. 输出可直接运行的测试代码"
                    )
                    result = self._process(self._build_messages(prompt))
            elif tool_command.startswith("/refactor "):
                content = tool_command[10:].strip()
                if not content:
                    result = "[错误] 请提供要重构分析的代码或需求"
                else:
                    prompt = (
                        "你是一个资深软件架构师和代码重构顾问。请分析下面的代码，识别坏味道，并给出重构建议。\n\n代码/需求：\n" + content +
                        "\n\n要求：\n1. 识别重复代码、长函数、耦合过高、命名不清、职责不单一等问题\n2. 说明重构目标和重构理由\n3. 给出具体重构步骤\n4. 提供重构后的示例代码\n5. 说明重构后的收益与注意事项"
                    )
                    result = self._process(self._build_messages(prompt))
            else:
                result = "[错误] 未知命令: " + tool_command

            # 保存到记忆
            self.memory.add_turn("user", tool_command)
            self.memory.add_turn("assistant", result)

            print("\nAgent: " + result)
            return result
        except Exception as e:
            error_msg = "[Agent错误] " + str(e) + "\n" + traceback.format_exc()
            print("\nAgent: " + error_msg)
            self.memory.add_turn("assistant", error_msg)
            return error_msg

    def status(self):
        """显示Agent状态"""
        print("\n--- Agent状态 ---")
        print("对话轮数: " + str(self.turn_count))
        print("记忆条数: " + str(len(self.memory)))
        print("可用工具: " + str(list(self.tools.keys())))
        print("-----------------")


# ============================================================
# 5. 命令行交互界面
# ============================================================

def print_welcome():
    """打印欢迎信息"""
    print("=" * 60)
    print("  AI Programming Assistant - 编程助手")
    print("  功能: 解释代码、生成代码、修复Bug、代码审查、优化重构、测试生成、重构建议")
    print("  支持命令: help, clear, status, exit, /exec, /read, /search, /generate, /fix, /review, /testgen, /refactor")
    print("=" * 60)


def main():
    """主函数 - 程序入口"""
    # 从环境变量读取API密钥
    api_key = os.getenv("DASHSCOPE_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    model = os.getenv("AGENT_MODEL", "qwen-plus")
    base_url = os.getenv("DASHSCOPE_API_BASE", os.getenv("OPENAI_API_BASE", None))

    # 打印配置信息
    masked_key = api_key[:10] + "..." + api_key[-6:] if len(api_key) > 16 else "未设置"
    print("\n--- 配置信息 ---")
    print("API Key: " + masked_key)
    print("模型: " + model)
    print("Base URL: " + (base_url if base_url else "https://dashscope.aliyuncs.com/compatible-mode/v1"))
    print("----------------")

    if not api_key:
        print("\n[警告] 未设置API密钥环境变量")
        print("请运行: export DASHSCOPE_API_KEY=你的密钥")
        print("或使用兼容API: export OPENAI_API_BASE=https://your-api.com/v1")
        # 启动演示模式
        demo_mode = input("是否启动演示模式(无需API Key)? [y/N]: ").strip().lower()
        if demo_mode != "y":
            print("请设置API Key后重试。")
            sys.exit(1)
        api_key = "demo"

    # 初始化Agent
    agent = CodeExplanationAgent(api_key=api_key, model=model, base_url=base_url)

    # 健康检查
    print("\n[检测] 正在测试API连接...")
    success, msg = agent.llm.health_check()
    if success:
        print("[检测] API连接正常!")
    else:
        print("[检测] API连接异常: " + msg)
        print("[警告] Agent可能无法正常工作, 请检查API配置")

    print_welcome()

    # 主交互循环
    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见!")
            break

        if not user_input:
            continue

        # 内置命令
        if user_input.lower() in ("exit", "quit", "bye"):
            print("再见!")
            break
        elif user_input.lower() == "help":
            print("""可用命令:
  help            - 显示帮助信息
  status          - 显示Agent状态
  clear           - 清空对话记忆
  exit/quit       - 退出程序
  /exec <代码>    - 执行Python代码(用于验证代码行为)
  /read <路径>    - 读取文件内容(用于分析代码文件)
  /search <关键词> - 搜索代码知识
  /generate <需求> - 根据需求直接生成代码
  /fix <问题>     - 帮助修复代码错误
  /review <代码>  - 审查代码并给出改进建议
  /testgen <代码/需求> - 根据代码或需求生成单元测试
  /refactor <代码/需求> - 分析坏味道并给出重构建议
  其他输入        - 作为问题发送给Agent(例如解释代码、写代码、修Bug、生成测试、重构代码)""")
        elif user_input.lower() == "status":
            agent.status()
        elif user_input.lower() == "clear":
            agent.memory.clear()
            agent.turn_count = 0
            print("对话记忆已清空。")
        elif user_input.startswith("/exec ") or user_input == "/exec":
            agent.run_tool(user_input)
        elif user_input.startswith("/read ") or user_input == "/read":
            agent.run_tool(user_input)
        elif user_input.startswith("/search ") or user_input == "/search":
            agent.run_tool(user_input)
        elif user_input.startswith("/generate ") or user_input == "/generate":
            agent.run_tool(user_input)
        elif user_input.startswith("/fix ") or user_input == "/fix":
            agent.run_tool(user_input)
        elif user_input.startswith("/review ") or user_input == "/review":
            agent.run_tool(user_input)
        elif user_input.startswith("/testgen ") or user_input == "/testgen":
            agent.run_tool(user_input)
        elif user_input.startswith("/refactor ") or user_input == "/refactor":
            agent.run_tool(user_input)
        else:
            try:
                agent.run(user_input)
            except Exception as e:
                print("[错误] " + str(e))


if __name__ == "__main__":
    main()