# -*- coding: utf-8 -*-
"""
log_server.py
Flask 日志收集 + SSE 实时查看（前端 /stream） + 静态页面 (/)
- 采用以脚本目录为基准的绝对路径，避免跨目录运行找不到文件/静态资源
- 默认追踪 log.txt（可用环境变量 LOG_PATH 覆盖，或在前端输入绝对路径）
- SSE 为最简 tail -f 实现，不自动跟随日志轮转（需要可后续加 inode 监测）
"""

import os
import time
from typing import Generator

from flask import (
    Flask,
    request,
    jsonify,
    Response,
    stream_with_context,
    send_from_directory,
    make_response,
)

# ---------------- 路径初始化 ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # 脚本所在目录
STATIC_DIR = os.path.join(BASE_DIR, "static")                # 静态目录
DEFAULT_LOG_PATH = os.path.join(BASE_DIR, "log.txt")         # 默认日志文件（绝对路径）

# 环境变量可覆盖默认日志文件
LOG_PATH_DEFAULT = os.environ.get("LOG_PATH", DEFAULT_LOG_PATH)

# ---------------- Flask 实例 ----------------
app = Flask(__name__, static_folder=STATIC_DIR)


# ---------------- 基础接口 ----------------
@app.get("/health")
def health():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.post("/log")
def ingest_log():
    """
    接收日志：POST /log  {json}
    将原样附加写入 LOG_PATH_DEFAULT
    """
    data = request.json or {}
    print(f"✅ 收到日志：{data}")

    # 确保日志目录存在
    os.makedirs(os.path.dirname(LOG_PATH_DEFAULT), exist_ok=True)

    with open(LOG_PATH_DEFAULT, "a", encoding="utf-8") as f:
        f.write(str(data) + "\n")

    return jsonify({"message": "log saved", "path": os.path.abspath(LOG_PATH_DEFAULT)}), 200


@app.get("/")
def index():
    """前端首页，返回 static/index.html"""
    return send_from_directory(STATIC_DIR, "index.html")


# ---------------- SSE 实时流 ----------------
def _sse_format(line: str) -> str:
    """
    SSE 每个事件以 'data: ...\\n\\n' 发送
    可按需添加 event/id/retry 字段，这里保持最简
    """
    return f"data: {line.rstrip()}\n\n"


def tail_generator(filepath: str, from_beginning: bool = False, poll: float = 0.25) -> Generator[str, None, None]:
    """
    简易版 tail -f：轮询文件，发现新行就通过 SSE 推送
    - 跨平台，无需额外依赖
    - 不跟随日志轮转（仅跟随当前打开的文件描述符）
    """
    if not os.path.isabs(filepath):
        # 若传入的是相对路径，则基于脚本目录解析，避免工作目录变化导致找不到
        filepath = os.path.join(BASE_DIR, filepath)

    if not os.path.isfile(filepath):
        yield _sse_format(f"[error] file not found: {filepath}")
        return

    # 发送响应头中的 no-cache，尽量避免中间代理缓存
    yield ""  # 占位（部分代理需要至少有输出才会立刻刷新）

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        if not from_beginning:
            f.seek(0, os.SEEK_END)

        buffer = ""
        while True:
            chunk = f.read()
            if chunk:
                buffer += chunk
                while True:
                    nl = buffer.find("\n")
                    if nl == -1:
                        break
                    line, buffer = buffer[:nl], buffer[nl + 1 :]
                    yield _sse_format(line)
            else:
                time.sleep(poll)


@app.get("/stream")
def stream():
    """
    SSE 实时流：
      GET /stream                      -> 追踪默认 LOG_PATH_DEFAULT，从末尾开始
      GET /stream?from=1               -> 从头开始
      GET /stream?path=/abs/xxx.log    -> 指定日志文件绝对路径
    """
    filepath = request.args.get("path", LOG_PATH_DEFAULT)
    from_beginning = request.args.get("from", "0") in ("1", "true", "True")

    gen = tail_generator(filepath, from_beginning=from_beginning)

    # 组装 SSE 响应，并尽量关闭缓存
    resp = Response(stream_with_context(gen), mimetype="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"  # 对 Nginx 友好：关闭缓冲
    return resp


# ---------------- 静态资源兜底（可选） ----------------
@app.get("/static/<path:filename>")
def static_files(filename: str):
    """静态资源路由"""
    return send_from_directory(STATIC_DIR, filename)


# ---------------- 入口 ----------------
if __name__ == "__main__":
    print("🌐 Flask 日志服务 + SSE 实时查看： http://0.0.0.0:8888")
    # threaded=True 允许并发处理 SSE 与 /log 写入
    app.run(host="0.0.0.0", port=8888, threaded=True)
