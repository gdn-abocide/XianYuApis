import asyncio
import json
import threading
import time
import sys
from datetime import datetime

import websockets

from goofish_live import XianyuLive
from utils.goofish_utils import decrypt, generate_mid, get_session_cookies_str

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


COOKIE_STR = (
    "cna=21FCIsebDnQCAXj2AoZoP+uz; t=9370e0f1d65e875b4993d5fbc8919ba2; "
    "tracknick=you748812; mtop_partitioned_detect=1; "
    "_m_h5_tk=5a52969adbcf8cd88da4d7dd054e3230_1779273753073; "
    "_m_h5_tk_enc=e61a99b1336c33cc6858ad242029d9fc; xlly_s=1; unb=3286898822; "
    "cookie2=23e1178f9ef50eaa02dddd1380f93b2c; _samesite_flag_=true; "
    "_tb_token_=ef659fb3e7b38; sdkSilent=1779352581116; "
    "sgcookie=E100yDv4tFdSFxR5dE5Hm6lXfexVANPpN0XpzKsjI7dHDhSWFNIfWom5bv5aI4zOYdz6DyjKgUuqIbEUjteT2VttBKvwvqysfo9DpKNaIcjozjY%3D; "
    "csg=2f959a1e; "
    "havana_lgc2_77=eyJoaWQiOjMyODY4OTg4MjIsInNnIjoiMjc0MTM1ZDNiNjI3ODNlMzgzNTcwYjQ0OTQyZWIxNTciLCJzaXRlIjo3NywidG9rZW4iOiIxaHJJYm9tMFRkZ3B1V1NnNzBkaWdkQSJ9; "
    "_hvn_lgc_=77; havana_lgc_exp=1781858328293; "
    "tfstk=gqmqhmXErnKquMAnLvqw8c3PatEYflRB7cN_IADghSVcci1izXc8GVgbGOursbUbiS9YbPciifz9H5Ng_fMilLtBAxHYXlVwOHtQ4TqHSVygIZvgr-Zan_3sudMYXlA5FGYBYxh44i_0SlvzqRy0nl2gSYvzCRQgjS4GZa23Z5qisrDkqJecn5VcjuvzB7VgjlcgqLy_Z5qgjfDoMhoicgP4oKwktq3OM6a0txVPjMWLnrvthNsOX0y4ucD0a-yq4-z4tP8B6xmmNAmjDzLdRlHS8fuiZ3Sq_x0nsSiktGPsJ7aomfxdL7mqQ0zxPsb0LoP4-m4l3ikzS4ozcmAOJYMziyrSPUdb5olqJWUDyQhZUSGi0zf2N5gIFm4rtQsr6Pumg8qh4y5TEK3SXq5G7r28UW9yUUa0sCkEkoTNWNUze8PBLp7OWroRfZoEvNQTrOyzOKih."
)


class PrintOnlyXianyuLive(XianyuLive):
    async def connect(self, headers):
        try:
            return await websockets.connect(self.base_url, additional_headers=headers)
        except TypeError:
            return await websockets.connect(self.base_url, extra_headers=headers)

    async def main(self):
        headers = {
            "Cookie": get_session_cookies_str(self.xianyu.session),
            "Host": "wss-goofish.dingtalk.com",
            "Connection": "Upgrade",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "Origin": "https://www.goofish.com",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        threading.Thread(target=self.user_alive, daemon=True).start()
        async with await self.connect(headers) as websocket:
            asyncio.create_task(self.init(websocket))
            asyncio.create_task(self.heart_beat(websocket))
            print("WebSocket 已连接，等待消息...", flush=True)
            async for raw_message in websocket:
                message = json.loads(raw_message)
                ack = {
                    "code": 200,
                    "headers": {
                        "mid": message["headers"]["mid"] if "mid" in message["headers"] else generate_mid(),
                        "sid": message["headers"]["sid"] if "sid" in message["headers"] else "",
                    }
                }
                if "app-key" in message["headers"]:
                    ack["headers"]["app-key"] = message["headers"]["app-key"]
                if "ua" in message["headers"]:
                    ack["headers"]["ua"] = message["headers"]["ua"]
                if "dt" in message["headers"]:
                    ack["headers"]["dt"] = message["headers"]["dt"]
                await websocket.send(json.dumps(ack))
                await self.handle_message(message, websocket)

    async def handle_message(self, message, websocket):
        parsed = self.parse_sync_message(message)
        if not parsed:
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("\n" + "=" * 80)
        print(f"[{now}] 收到闲鱼消息")
        print(f"发送人: {parsed.get('sender_name') or '-'} ({parsed.get('sender_id') or '-'})")
        print(f"会话ID: {parsed.get('cid') or '-'}")
        print(f"内容: {parsed.get('content') or '-'}")
        print("原始消息:")
        print(json.dumps(parsed.get("raw"), ensure_ascii=False, indent=2))
        print("=" * 80, flush=True)

    def parse_sync_message(self, message):
        payload = self.extract_payload(message)
        if payload is None:
            return None

        decoded = self.decode_payload(payload)
        if not isinstance(decoded, dict):
            return None

        return {
            "sender_name": self.pick(decoded, ["1", "10", "reminderTitle"]),
            "sender_id": self.pick(decoded, ["1", "10", "senderUserId"]),
            "content": self.pick(decoded, ["1", "10", "reminderContent"]),
            "cid": self.clean_cid(self.pick(decoded, ["1", "2"])),
            "raw": decoded,
        }

    @staticmethod
    def extract_payload(message):
        try:
            return message["body"]["syncPushPackage"]["data"][0]["data"]
        except Exception:
            return None

    @staticmethod
    def decode_payload(payload):
        try:
            return json.loads(payload)
        except Exception:
            pass

        try:
            decrypted = decrypt(payload)
            return json.loads(decrypted)
        except Exception:
            return None

    @staticmethod
    def pick(data, path):
        current = data
        for key in path:
            if not isinstance(current, dict) or key not in current:
                return ""
            current = current[key]
        return current

    @staticmethod
    def clean_cid(cid):
        return cid.split("@", 1)[0] if isinstance(cid, str) else ""


if __name__ == "__main__":
    if not COOKIE_STR.strip():
        raise SystemExit("请先在 local_message_listener.py 中配置 COOKIE_STR")

    print("开始监听闲鱼消息，按 Ctrl+C 停止。")
    asyncio.run(PrintOnlyXianyuLive(COOKIE_STR).main())
