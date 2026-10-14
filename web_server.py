#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web网页后端，复用agent.py全部Agent&Workflow逻辑
浏览器网页交互，替代PowerShell终端
"""
import os
import asyncio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# 导入你原有agent.py中全部类与函数
from agent import (
    LLMClient, CodeExplanationAgent,
    WorkflowState, BaseWorkflowAgent, CodeAnalyzeAgent, DocWriterAgent, RiskScanAgent,
    SimpleWorkflowEngine, run_document_generation_workflow,
    NodeType, WorkflowNode, AdvancedWorkflowEngine, run_adv_workflow
)

app = FastAPI(title="Homework2 Agent WebUI")

# 全局单例（作业开发MVP，生产不要全局）
api_key = os.getenv("DASHSCOPE_API_KEY", "")
model_name = os.getenv("AGENT_MODEL", "qwen-plus")
base_url = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

agent = CodeExplanationAgent(api_key=api_key, model=model_name, base_url=base_url)

class ChatReq(BaseModel):
    user_text: str

@app.get("/", response_class=HTMLResponse)
async def get_index():
    """返回网页前端index.html内容"""
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
    return html

@app.post("/api/chat")
async def api_chat(req: ChatReq):
    """✅【修复】统一入口，调用agent.handle_command()"""
    user_input = req.user_text.strip()
    print(f"[WEB收到输入] {user_input}")
    try:
        # run是同步阻塞函数，放到线程池，不要卡死fastapi事件循环
        loop = asyncio.get_running_loop()
        reply = await loop.run_in_executor(None, agent.handle_command, user_input)
        return {"ok": True, "reply": reply}
    except Exception as e:
        import traceback
        err_info = traceback.format_exc()
        print("[WEB后端异常]", err_info)
        return {"ok": False, "msg": f"后端异常：{str(e)}"}


class WorkflowRunReq(BaseModel):
    code_text: str
    mode: str # base / adv

@app.post("/api/workflow_run")
async def api_workflow_run(req:WorkflowRunReq):
    code_str = req.code_text
    mode = req.mode
    try:
        if mode == "base":
            state = run_document_generation_workflow(api_key, model_name, base_url, code_str)
            log_text = state.dump_log()
            doc = state.doc_output
            err = state.error
            risk_report = ""
            summary_text = getattr(state, "summary_result", "")
        else:
            state = await run_adv_workflow(api_key, model_name, base_url, code_str, max_loop=2)
            log_text = state.dump_log()
            doc = state.doc_output
            err = state.error
            risk_report = getattr(state, "risk_scan_result", "")
            summary_text = getattr(state, "summary_result", "")
        return {
            "ok": True,
            "error": err,
            "log": log_text,
            "document": doc,
            "risk_scan": risk_report,
            "summary": summary_text
        }
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return {"ok":False,"error":str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
