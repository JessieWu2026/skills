#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把本地 workbuddy-skills/ 目录推送到 GitHub 仓库。
走 api.github.com REST（本机该端点稳定可达，绕开不通的 github.com）。

用法：
    GH_TOKEN=ghp_xxx python3 push_to_github.py <owner>/<repo> [本地目录] [目标子目录]

例：
    GH_TOKEN=ghp_xxx python3 push_to_github.py jessiewu/skills
    GH_TOKEN=ghp_xxx python3 push_to_github.py jessiewu/skills ./workbuddy-skills skills

依赖：仅标准库。
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
SKIP_DIRS = {".git", "__pycache__", ".venv", ".idea", ".vscode"}
SKIP_FILES = {".DS_Store"}

# api.github.com 是本机唯一稳定可达的 GitHub 端点（github.com 不通）。
# 沙箱需要通过环境里的 http(s)_proxy 出网，因此这里尊重环境代理；
# 若某次代理异常，可用环境变量 GH_NO_PROXY=1 强制直连兜底。
if os.environ.get("GH_NO_PROXY"):
    OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
else:
    OPENER = urllib.request.build_opener()


def api(method, path, token, payload=None):
    url = API + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "workbuddy-push")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with OPENER.open(req, timeout=60) as r:
            body = r.read().decode()
            return r.status, (json.loads(body) if body.strip() else {})
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}


def collect_files(root):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in SKIP_FILES:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            out.append((rel, full))
    return sorted(out)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("✗ 缺少凭据：请设置 GH_TOKEN 环境变量")
        sys.exit(1)

    repo = sys.argv[1].strip().strip("/")
    root = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..")
    prefix = sys.argv[3].strip("/") if len(sys.argv) > 3 else ""

    if not os.path.isdir(root):
        print("✗ 本地目录不存在:", root)
        sys.exit(1)

    status, me = api("GET", "/user", token)
    if status != 200:
        print("✗ 凭据校验失败 HTTP", status, me)
        sys.exit(1)
    login = me.get("login")
    print("✓ 已认证为:", login)

    status, info = api("GET", "/repos/" + repo, token)
    if status == 200:
        print("✓ 仓库存在:", info.get("full_name"),
              "| 私有:", info.get("private"))
    else:
        print("✗ 仓库不可访问 HTTP", status, info)
        sys.exit(1)

    files = collect_files(root)
    print("准备上传 %d 个文件 → %s%s\n" % (
        len(files), repo, ("/" + prefix) if prefix else ""))

    ok = fail = 0
    for rel, full in files:
        target = (prefix + "/" + rel) if prefix else rel
        with open(full, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        # 已存在则需带 sha 更新
        q = urllib.parse.quote(target)
        st, existing = api("GET", "/repos/%s/contents/%s" % (repo, q), token)
        payload = {
            "message": "feat: add %s" % target,
            "content": content,
        }
        if st == 200 and isinstance(existing, dict) and existing.get("sha"):
            payload["sha"] = existing["sha"]
            action = "更新"
        else:
            action = "新增"

        st, res = api("PUT", "/repos/%s/contents/%s" % (repo, q), token, payload)
        if st in (200, 201):
            print("  ✓ %s %s" % (action, target))
            ok += 1
        else:
            print("  ✗ %s %s → HTTP %s %s" % (action, target, st, res))
            fail += 1

    print("\n完成：成功 %d，失败 %d" % (ok, fail))
    print("仓库地址: https://github.com/%s" % repo)
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
