"""
API 连接测试
============

测试 302.ai API 是否能正常连接。

使用方法：
    python tests/test_api_connection.py
"""

import os
import http.client
import json
import sys

# 添加父目录到路径，以便导入 config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def test_api_connection():
    """测试 API 连接"""
    print("=" * 60)
    print("测试 302.ai API 连接")
    print("=" * 60)

    try:
        conn = http.client.HTTPSConnection("api.302.ai")
        payload = json.dumps(
            {
                "model": "gemini-2.5-flash",
                "stream": False,
                "messages": [
                    {
                        "role": "user",
                        "content": "你好！请回复：连接成功。",
                    }
                ],
            }
        )
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {os.getenv('API_KEY')}",
            "Content-Type": "application/json",
        }
        conn.request("POST", "/v1/chat/completions", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_json = json.loads(data.decode("utf-8"))

        # 解析响应
        if "choices" in response_json and len(response_json["choices"]) > 0:
            reply = response_json["choices"][0]["message"]["content"]
            print(f"Gemini 回复：{reply}")
            print("\n[成功] API 连接测试通过！")
            return True
        else:
            error_msg = response_json.get("error", {}).get("message", "未知错误")
            print(f"[错误] API 返回：{error_msg}")
            return False

    except Exception as e:
        print(f"[错误] 调试信息：{e}")
        return False
    finally:
        print("=" * 60)


if __name__ == "__main__":
    test_api_connection()
