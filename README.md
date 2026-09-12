# Skills

Jessie 的 AI 技能库（WorkBuddy / CodeBuddy Agent Skills）。

## 技能清单

| 技能 | 作用 |
|---|---|
| [`private-domain-data-asset-prompt`](skills/private-domain-data-asset-prompt/) | 生成并执行「企业私域数据资产积累」主题的专业提示词。含完整提示词模板（角色 / 任务 / 背景 / 8 步思维链 / 输出规范 / 约束 / 自检清单）、**换行业变量表**（通用 → 手袋箱包等）与 Word 产出链路 |
| [`ima-prompt-to-word`](skills/ima-prompt-to-word/) | 通用工作流：从 IMA 知识库提炼提示词方法论 → 生成专业提示词 → 执行 → 输出企业级 Word 文档。含 ima-mcp 调用链路、检索技巧与踩坑记录 |
| [`publish-to-github`](skills/publish-to-github/) | 把本地文件/文件夹发布到 GitHub 仓库。含本机已验证的可行链路（Fine-grained PAT + `api.github.com` REST）、连接器与 gh CLI 的已知限制、现成上传脚本，以及推送后必须检查的事项 |

## 目录结构

```
.
├── skills/                              # 技能（每个文件夹一个 SKILL.md）
│   ├── private-domain-data-asset-prompt/
│   │   └── SKILL.md
│   ├── ima-prompt-to-word/
│   │   └── SKILL.md
│   └── publish-to-github/
│       └── SKILL.md
├── prompts/                             # 提示词成品
│   └── 企业私域数据资产_专业提示词.md
└── scripts/                             # 配套脚本
    ├── build_docx.py                    # python-docx 企业级 Word 生成器
    └── push_to_github.py                # 走 api.github.com 的一键上传脚本
```

## 安装到本地

WorkBuddy 的技能目录是 `~/.workbuddy/skills/`（CodeBuddy 是 `~/.codebuddy/skills/`）。
把技能的整个文件夹复制进去即可，重启会话后生效：

```bash
cp -r skills/private-domain-data-asset-prompt ~/.workbuddy/skills/
cp -r skills/ima-prompt-to-word ~/.workbuddy/skills/
cp -r skills/publish-to-github ~/.workbuddy/skills/
```

> 注意：`publish-to-github` 依赖 `scripts/push_to_github.py`，安装时需一并放进
> `~/.workbuddy/skills/publish-to-github/scripts/`，技能内的引用写作 `{SKILL_ROOT}/scripts/push_to_github.py`。

## 如何生成 Word 文档

```bash
python -m venv .venv && source .venv/bin/activate
pip install python-docx
python scripts/build_docx.py
```

脚本输出一份企业级 `.docx`：封面页 + 目录域（TOC）+ 页眉页脚页码 + 分级标题 + 品牌配色表格。

> 打开文档后，在目录处右键选择「更新域」即可生成页码与目录。

## 如何推送到 GitHub

本机 `github.com` 不可达、WorkBuddy 的 GitHub 连接器只有读权限，因此**统一走 `api.github.com` REST**：

```bash
GH_TOKEN=github_pat_xxx python3 scripts/push_to_github.py <owner>/<repo> <本地目录>
```

需要用户提供一个 **Fine-grained PAT**（Repository access 只勾目标仓库，Permissions → Contents: Read and write）。
详见 [`skills/publish-to-github/SKILL.md`](skills/publish-to-github/SKILL.md)。

## 说明

- 所有技能均为自建（`agent_created: true`），可自由修改。
- 文档中的企业数据一律为示例，不涉及真实经营数据；涉及个人信息的章节均附有合规边界说明。
- 配图 / 视频等生成内容不得直接复刻他人商标、Logo 或完整产品外观。
