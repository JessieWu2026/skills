# WorkBuddy Skills

Jessie 的 AI 技能库（WorkBuddy / CodeBuddy Agent Skills）。

## 包含的技能

| 技能 | 作用 |
|---|---|
| [`private-domain-data-asset-prompt`](skills/private-domain-data-asset-prompt/) | 生成并执行「企业私域数据资产积累」主题的专业提示词（含完整提示词模板 + 换行业变量表 + Word 产出链路） |
| [`ima-prompt-to-word`](skills/ima-prompt-to-word/) | 通用工作流：从 IMA 知识库提炼提示词方法论 → 生成专业提示词 → 执行 → 输出企业级 Word 文档（含 ima-mcp 调用链路与踩坑记录） |

## 目录结构

```
.
├── skills/                              # 技能（每个文件夹一个 SKILL.md）
│   ├── private-domain-data-asset-prompt/
│   │   └── SKILL.md
│   └── ima-prompt-to-word/
│       └── SKILL.md
├── prompts/                             # 提示词成品
│   └── 企业私域数据资产_专业提示词.md
└── scripts/                             # 配套脚本
    └── build_docx.py                    # python-docx 企业级 Word 生成器
```

## 如何安装到本地

WorkBuddy 的技能目录是 `~/.workbuddy/skills/`（CodeBuddy 是 `~/.codebuddy/skills/`）。
把技能的整个文件夹复制进去即可，重启会话后生效：

```bash
cp -r skills/private-domain-data-asset-prompt ~/.workbuddy/skills/
cp -r skills/ima-prompt-to-word ~/.workbuddy/skills/
```

## 如何生成 Word 文档

```bash
python -m venv .venv && source .venv/bin/activate
pip install python-docx
python scripts/build_docx.py
```

脚本会输出一份企业级 `.docx`：封面页 + 目录域（TOC）+ 页眉页脚页码 + 分级标题 + 品牌配色表格。
> 打开文档后，在目录处右键选择「更新域」即可生成页码与目录。

## 说明

- 所有技能均为自建（`agent_created: true`），可自由修改。
- 文档中的企业数据一律为示例，不涉及真实经营数据；涉及个人信息的章节均附有合规边界说明。
