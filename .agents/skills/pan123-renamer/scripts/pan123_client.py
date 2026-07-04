# -*- coding: utf-8 -*-
"""123云盘开放平台 API 客户端

鉴权、按接口 QPS 节流、429/401 自动重试。
凭证从项目根目录 .env 读取：PAN123_CLIENT_ID / PAN123_CLIENT_SECRET
access_token 缓存到本目录 .token_cache.json（已 gitignore）。

直接运行做自测：python pan123_client.py  → 打印用户信息 + 根目录列表
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

# Windows 控制台默认 GBK，统一切到 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

API_BASE = "https://open-api.123pan.com"
SCRIPT_DIR = Path(__file__).resolve().parent
TOKEN_CACHE = SCRIPT_DIR / ".token_cache.json"

# 各接口 QPS 上限（参考开放平台文档）→ 换算为最小请求间隔（秒）
QPS = {
    "/api/v1/user/info": 1,
    "/api/v2/file/list": 3,
    "/api/v1/file/name": 1,
    "/api/v1/file/move": 1,
    "/upload/v1/file/mkdir": 2,
    "/api/v1/file/trash": 2,
}


def load_env():
    """从当前目录向上查找 .env 并读入环境变量（不覆盖已有值）"""
    d = Path.cwd()
    for p in [d, *d.parents, SCRIPT_DIR.parents[3]]:
        env = p / ".env"
        if env.is_file():
            for line in env.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
            return


class Pan123Client:
    def __init__(self):
        load_env()
        self.client_id = os.environ.get("PAN123_CLIENT_ID", "")
        self.client_secret = os.environ.get("PAN123_CLIENT_SECRET", "")
        if not self.client_id or not self.client_secret:
            sys.exit("缺少 PAN123_CLIENT_ID / PAN123_CLIENT_SECRET，请在 .env 中配置")
        self.session = requests.Session()
        self._last_call = {}  # path -> 上次请求时间戳
        self._token = None

    # ---------- 鉴权 ----------
    def get_token(self, force=False):
        if not force:
            if self._token:
                return self._token
            if TOKEN_CACHE.is_file():
                try:
                    cache = json.loads(TOKEN_CACHE.read_text(encoding="utf-8"))
                    if cache.get("expireTs", 0) > time.time() + 3600:
                        self._token = cache["accessToken"]
                        return self._token
                except (json.JSONDecodeError, KeyError):
                    pass
        r = self.session.post(
            API_BASE + "/api/v1/access_token",
            json={"clientID": self.client_id, "clientSecret": self.client_secret},
            headers={"Platform": "open_platform"},
            timeout=30,
        )
        data = r.json()
        if data.get("code") != 0:
            sys.exit(f"获取 access_token 失败: {data.get('message')}")
        self._token = data["data"]["accessToken"]
        # expiredAt 形如 2026-08-01T12:00:00+08:00，保守按 25 天缓存
        TOKEN_CACHE.write_text(
            json.dumps({"accessToken": self._token, "expireTs": time.time() + 25 * 86400}),
            encoding="utf-8",
        )
        return self._token

    # ---------- 通用请求（节流 + 重试） ----------
    def request(self, method, path, **kwargs):
        interval = 1.0 / QPS.get(path, 1)
        for attempt in range(8):
            wait = self._last_call.get(path, 0) + interval - time.time()
            if wait > 0:
                time.sleep(wait)
            self._last_call[path] = time.time()

            headers = {
                "Authorization": "Bearer " + self.get_token(),
                "Platform": "open_platform",
            }
            r = self.session.request(method, API_BASE + path, headers=headers, timeout=60, **kwargs)
            try:
                data = r.json()
            except json.JSONDecodeError:
                raise RuntimeError(f"{path} 返回非 JSON: HTTP {r.status_code}")
            code = data.get("code")
            if code == 0:
                return data.get("data")
            if code == 401:
                self.get_token(force=True)
                continue
            if code == 429:
                time.sleep(1 + attempt)
                continue
            raise RuntimeError(f"{path} 失败(code={code}): {data.get('message')}")
        raise RuntimeError(f"{path} 重试次数用尽")

    # ---------- 业务接口 ----------
    def user_info(self):
        return self.request("GET", "/api/v1/user/info")

    def list_dir(self, parent_file_id=0):
        """列出目录下全部条目（自动翻页，过滤回收站文件）"""
        items, last_id = [], 0
        while last_id != -1:
            data = self.request(
                "GET", "/api/v2/file/list",
                params={"parentFileId": parent_file_id, "limit": 100, "lastFileId": last_id},
            )
            for f in data.get("fileList", []):
                if f.get("trashed") == 0:
                    items.append(f)
            last_id = data.get("lastFileId", -1)
        return items

    def rename(self, file_id, new_name):
        self.request("PUT", "/api/v1/file/name", json={"fileId": file_id, "fileName": new_name})

    def move(self, file_ids, to_parent_id):
        if isinstance(file_ids, int):
            file_ids = [file_ids]
        self.request("POST", "/api/v1/file/move",
                     json={"fileIDs": file_ids, "toParentFileID": to_parent_id})

    def mkdir(self, parent_id, name):
        """创建目录，返回新目录 fileId"""
        data = self.request("POST", "/upload/v1/file/mkdir",
                            json={"parentID": str(parent_id), "name": name})
        return data["dirID"]

    def find_child_dir(self, parent_id, name):
        """在 parent 下查找同名目录，返回 fileId 或 None"""
        for f in self.list_dir(parent_id):
            if f.get("type") == 1 and f.get("filename") == name:
                return f["fileId"]
        return None

    def ensure_dir(self, parent_id, name):
        """存在则复用，不存在则创建"""
        fid = self.find_child_dir(parent_id, name)
        return fid if fid is not None else self.mkdir(parent_id, name)


if __name__ == "__main__":
    c = Pan123Client()
    info = c.user_info()
    print(f"登录成功：{info.get('nickname')} (uid={info.get('uid')})，"
          f"已用空间 {info.get('spaceUsed', 0) / 2**30:.1f} GB")
    print("根目录：")
    for f in c.list_dir(0):
        kind = "📁" if f.get("type") == 1 else "📄"
        print(f"  {kind} [{f['fileId']}] {f['filename']}")
