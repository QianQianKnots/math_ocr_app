"""
图片识别测试
============

测试 API 是否能正确识别图片内容。

使用方法：
    python tests/test_image_recognition.py
"""

import http.client
import json
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


def test_image_recognition():
    """测试图片识别功能"""
    print("=" * 60)
    print("测试图片识别功能")
    print("=" * 60)

    conn = http.client.HTTPSConnection("api.302.ai")
    payload = json.dumps(
        {
            "model": "gemini-2.5-flash",
            "stream": False,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "这张图片有什么？请简短描述。"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "https://s2.loli.net/2024/02/01/QSWVdw9bX56gj7O.jpg"
                            },
                        },
                    ],
                }
            ],
        }
    )
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {os.getenv('API_KEY')}",
        "Content-Type": "application/json",
    }

    try:
        conn.request("POST", "/v1/chat/completions", payload, headers)
        res = conn.getresponse()
        data = res.read()
        response_json = json.loads(data.decode("utf-8"))

        if "choices" in response_json and len(response_json["choices"]) > 0:
            reply = response_json["choices"][0]["message"]["content"]
            print(f"识别结果：{reply}")
            print("\n[成功] 图片识别测试通过！")
            return True
        else:
            error_msg = response_json.get("error", {}).get("message", "未知错误")
            print(f"[错误] {error_msg}")
            return False

    except Exception as e:
        print(f"[错误] {e}")
        return False
    finally:
        print("=" * 60)


if __name__ == "__main__":
    test_image_recognition()
