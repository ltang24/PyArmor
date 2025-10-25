import json
import platform
import requests
from datetime import datetime
import os

# 加载合法 token
with open("active_tokens.json", "r") as f:
    valid_tokens = json.load(f)

def upload_log(token: str):
    try:
        log_data = {
            "token": token,
            "os": platform.platform(),
            "python_version": platform.python_version(),
            "time": datetime.utcnow().isoformat()
        }
        response = requests.post(
            "http://localhost:8888/log",
            json=log_data,
            timeout=5
        )
        if response.status_code == 200:
            print(f"🟢 log upload success: {response.json()}")
        else:
            print(f"🟠 log upload failed: {response.status_code} {response.text}")
    except Exception as e:
        print(f"🔴 log upload exception: {e}")

def verify_hello_txt():
    path = "hello.txt"
    if not os.path.exists(path):
        print("📛 文件不存在：hello.txt")
        return

    with open(path, "r") as f:
        content = f.read().strip()

    if content == "hello world":
        print("✅ 文件内容正确：hello world")
    else:
        print(f"❌ 文件内容错误：{content}")

def main():
    token = input("Enter your token: ").strip()

    if token in valid_tokens:
        print("🎉 Authorized user. Running main logic...")
        upload_log(token)

        # 简单的 hello.txt 校验
        verify_hello_txt()
    else:
        print("🚫 Unauthorized token.")

if __name__ == "__main__":
    main()
