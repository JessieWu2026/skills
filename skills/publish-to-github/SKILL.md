---
name: publish-to-github
description: 把本地文件或文件夹（技能、文档、代码）发布到 GitHub 仓库。当用户说"把这个传到 GitHub""推到我的仓库""保存到 GitHub""打包上传到 GitHub"时使用。包含本机已验证的可行链路（Fine-grained PAT + api.github.com REST）、连接器与 gh CLI 的已知限制、现成的上传脚本，以及推送后必须检查的事项（仓库可见性、Token 作废）。
agent_created: true
---

# 发布到 GitHub（本地 → 仓库）

## 结论先行：本机唯一可靠的路径

**Fine-grained PAT + `api.github.com` REST**，配脚本 `{SKILL_ROOT}/scripts/push_to_github.py`。

另外两条路在本机都走不通，**不要再浪费轮次去试**：

| 路径 | 本机实测结果 | 说明 |
|---|---|---|
| WorkBuddy **github 连接器** | ❌ **只读** | 读成功（`get_file_contents` 能拿到文件）；写一律 `403 Resource not accessible by integration` —— `push_files`、`create_or_update_file`、`create_repository` 全部失败。这是连接器本身只申请了读权限，用户在授权页怎么调都没用。 |
| **gh** CLI | ❌ **网络不通** | 本机 `github.com` = HTTP 000；而设备码申请（`/login/device/code`）与 token 交换（`/login/oauth/access_token`）都必须走 github.com → `unexpected EOF` / `i/o timeout`。 |
| **PAT + api.github.com** | ✅ **可用** | `api.github.com` 实测 HTTP 200 稳定可达（401 = 未带凭据但通道通）。 |

## 标准流程

### 第 1 步 · 先测通道
```bash
curl -sS -o /dev/null -w "api.github.com -> %{http_code}\n" -m 12 https://api.github.com   # 期望 401（=通）
curl -sS -o /dev/null -w "github.com     -> %{http_code}\n" -m 12 https://github.com       # 常为 000（不通，属正常）
```

### 第 2 步 · 让用户提供最小权限凭据
引导用户生成 **Fine-grained PAT**（不要用经典 token，也不要 `repo` 全量权限）：

1. 打开 https://github.com/settings/personal-access-tokens/new
2. **Token name** 任填；**Expiration** 选 7 days（用完自动失效）
3. **Repository access** → *Only select repositories* → 只勾选目标仓库
4. **Permissions** → *Repository permissions* → 只需把 **Contents** 设为 **Read and write**
5. **Metadata** 保持默认 **Read-only** —— 它是 Mandatory、被系统锁死为只读，改不了也不用改
6. Generate token → 复制 `github_pat_...`

> 必须告知用户：① Token 会明文出现在对话中；② 它只对指定仓库有内容读写权；③ **推送完成后请到 https://github.com/settings/personal-access-tokens 点 Revoke 作废**。

### 第 3 步 · 整理要上传的目录
把文件收拢到一个目录。脚本递归遍历，自动跳过 `.git` / `__pycache__` / `.venv` / `.idea` / `.vscode` / `.DS_Store`。

### 第 4 步 · 推送
```bash
GH_TOKEN=github_pat_xxx \
/Users/JessieWu/.workbuddy/binaries/python/envs/default/bin/python \
{SKILL_ROOT}/scripts/push_to_github.py <owner>/<repo> <本地目录> [目标子目录]
```
脚本行为：`GET /user` 校验凭据 → `GET /repos/{repo}` 校验仓库 → 逐文件 `PUT /contents/{path}`
（已存在的文件自动先取 sha 再更新）→ 打印每个文件的"新增/更新"与最终成功/失败计数、仓库地址。
退出码：全部成功为 0。

### 第 5 步 · 验证
```bash
GH_TOKEN=xxx python3 - <<'PY'
import json,os,urllib.request
op=urllib.request.build_opener(); t=os.environ["GH_TOKEN"]
def g(p):
    r=urllib.request.Request("https://api.github.com"+p)
    r.add_header("Authorization","Bearer "+t); r.add_header("User-Agent","wb")
    return json.load(op.open(r,timeout=60))
print("可见性:", "private" if g("/repos/OWNER/REPO")["private"] else "⚠️ PUBLIC")
for it in g("/repos/OWNER/REPO/git/trees/main?recursive=1")["tree"]:
    if it["type"]=="blob": print(f"  {it['size']:>7,} B  {it['path']}")
PY
```

## ⚠️ 推送后必须检查的两件事（最容易漏）

1. **仓库可见性**：用户说"私有库"未必真是私有。**必须查 `private` 字段**；若为 `false` 立即提醒：
   打开 `https://github.com/<owner>/<repo>/settings` → 拉到底 **Danger Zone** → **Change visibility** → **Make private**。
   注意：只有 Contents 权限的 PAT **改不了可见性**，必须用户自己点。
2. **提醒作废 Token**：https://github.com/settings/personal-access-tokens

## 网络注意事项

- 沙箱出网**必须经环境代理**（`http_proxy` / `https_proxy`，形如 `http://127.0.0.1:<port>`）。
  `push_to_github.py` 默认**尊重环境代理**；若某次代理异常，用 `GH_NO_PROXY=1` 强制直连兜底。
- **不要用 `git push` 或 `gh`** —— 它们走 `github.com`，本机不通。
- 只需要 `api.github.com` 这一个域名，它稳定可达。

## 报文错误对照表

| 报错 | 含义 | 处理 |
|---|---|---|
| `403 Resource not accessible by integration` | 连接器/integration 无写权限 | 放弃连接器，改用 PAT |
| `404 Not Found`（读仓库时） | 仓库名或账号不符，或 App 未授权该库 | 让用户提供仓库完整 URL 核对 |
| `404` 但用户确信库存在 | 可能是另一个 GitHub 账号建的库 | 用 `get_me` 确认连接器授权的账号 |
| `CONNECT tunnel failed, response 502` | 代理不放行该域名 | 换到 `api.github.com` 或重试 |
| `dial tcp ...: i/o timeout` | 直连被墙 | 走环境代理，不要 `--noproxy` |
| `Search.q (invalid)` | 新账号/私有库不在搜索索引 | 别用 search，直接 get repo |

## 附：gh CLI 的安装与陷阱（备查，通常不需要走这条路）

**安装（本机 macOS 15.5 / arm64，无 Homebrew）**：不装 brew（太重且要 sudo），下官方二进制：
`gh_<version>_macOS_arm64.zip` → 解压取 `bin/gh` → 拷入 `~/.local/bin/` → `chmod +x` →
`xattr -dr com.apple.quarantine ~/.local/bin/gh`。使用前 `export PATH="$HOME/.local/bin:$PATH"`。

**陷阱（实测）**：
- `gh auth login` 的 `? Authenticate Git with your GitHub credentials? (Y/n)` **不接受管道输入**：
  `printf '\n' |` 会卡住；`yes '' |` 刷屏看不到验证码；`expect`（含 `stty_init "rows 40 columns 120"`）**也驱动不动**。
- **解法**：先配置 credential helper 即可跳过该提问，直接进入设备码流程：
  ```bash
  git config --global --add credential.https://github.com.helper '!gh auth git-credential'
  git config --global --add credential.https://github.com.helper ''
  printf '\n' | gh auth login --hostname github.com --git-protocol https --web --skip-ssh-key
  ```
  此时会打印 `one-time code: XXXX-XXXX` 与 `https://github.com/login/device`，`printf '\n'` 正好应答
  "Press Enter to open"，**可非交互跑通到设备码环节**。
- **但**：即便跑通设备码，只要 `github.com` 不通，token 交换仍会 `unexpected EOF` 失败。
  所以**先测通道再决定是否走 gh**——大概率应该直接走 PAT。

## 定位说明

本技能只覆盖「本地 → GitHub 仓库」的发布动作。若要发布的是**技能**，通常还应同时：
① 把技能装到 `~/.workbuddy/skills/<name>/`（含其依赖脚本）；② 保持仓库副本与本地安装副本一致
（脚本引用建议写成 `{SKILL_ROOT}/scripts/xxx` 这种自包含形式）。
