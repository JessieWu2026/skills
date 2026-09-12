---
name: ima-prompt-to-word
description: 基于 IMA 知识库提炼方法论 → 生成专业提示词 → 执行 → 输出企业级 Word 文档的完整工作流。当用户说"基于某个 IMA 知识库生成专业提示词""从知识库提取提示词方法论""执行生成的提示词并输出 Word/企业文档"时使用。包含 ima-mcp 工具调用链路、常用提示词方法论清单、python-docx 企业级文档模板。
agent_created: true
---

# IMA 知识库 → 专业提示词 → 企业级 Word 文档

## 适用场景
用户要求：① 基于某个 IMA 知识库（如「ai提示词宝库」）生成针对某主题的专业提示词；② 执行该提示词；③ 把执行结果保存为企业专业格式的 Word 文件。

## 前置：连接器
- `ima-mcp` 必须在 WorkBuddy 右上角「连接器管理」里 **connected**，否则工具不可见（`ToolSearch` 只能搜到通用工具）。
- 不要尝试直连 ima.qq.com 网页或猜测 HTTP API 绕行；连接失败就引导用户去设置页重新连接。

## 工具调用链路（ima-mcp，顺序不可跳）
1. **定位知识库** `mcp__ima-mcp__search_knowledge_base`（参数 query、limit、cursor=""）
   或 `mcp__ima-mcp__get_knowledge_base_list`（params 数组，每项含 limit + type：KBT_MINE_KB / KBT_SHARED_KB / KBT_SUBSCRIBED_CREATE_KB / KBT_SUBSCRIBED_JOIN_KB）→ 拿到 `knowledge_base_id`
2. **列举或检索库内条目**
   - `mcp__ima-mcp__get_knowledge_list`（knowledge_base_id、limit、cursor、sort_type、filters）
   - `mcp__ima-mcp__search_knowledge`（knowledge_base_id、query、cursor、filters）
   - ⚠️ **`limit` 必须在 (0, 50]，传 100 会报 `code:51 invalid GetKnowledgeListReq.Limit`**。
   - ⚠️ 参数结构不对称：`get_knowledge_base_list` 用 `params:[{limit,type,cursor}]`，`get_knowledge_list` 用**顶层** `limit`/`cursor`。
   - 建议 filters 叠加：`MEDIA_STATE_FILTER_TYPE`(只要 MEDIA_PARSE_SUCCESS) + `MEDIA_TYPE_FILTER_OUT_TYPE`(排除 FOLDER)，否则结果混入读不出正文的条目。
3. **读正文** `mcp__ima-mcp__fetch_media_content`（media_id）→ 拿到正文，提炼方法论
   - 只有 `can_fetch_content: true` 的条目能读；PDF 类常为 false。
   - 别逐条拉全文，先用 introduction 摘要筛出 3~5 篇高相关再读。

## 检索技巧（踩过的坑，务必遵守）
- **`search_knowledge` 是模糊检索**：多个关键词会返回大量弱相关结果（常 100 条 / >100KB），工具会把结果落盘到
  `~/.workbuddy/projects/<项目>/<会话>/tool-results/*.txt` 并报 "exceeds maximum allowed tokens"。
  → **不要读整个文件**。用 python 解析：
  `json.loads(re.search(r'\{.*\}', open(f,encoding='utf-8').read(), re.S).group(0))`，
  然后只抽 `title / media_id / parent_folder_name / media_type_info.name / highlight_content`，
  再按关键词白名单过滤，输出精简清单。
- **单关键词更准**：搜「手袋」命中 1 条有效；搜「手袋 包袋 女包 皮具 箱包」返回 100 条噪音。
  先试单关键词，不够再加。
- **过滤条件**：`filters` 用 `MEDIA_STATE_FILTER_TYPE` + `media_states:["MEDIA_PARSE_SUCCESS"]`；
  列举时再加 `MEDIA_TYPE_FILTER_OUT_TYPE` + `media_type:["FOLDER"]`。
  单查文件夹时反过来用 `MEDIA_TYPE_FILTER_TYPE` + `media_type:["FOLDER"]`。
- **两个大库没有真实顶层文件夹**（`folder_number=0`，条目平铺在 root）：`parent_folder_name` 只是虚拟分组名，
  **不能当 folder_id 传**。
- `media_type`：1=PDF 2=WEB 3=WORD 6=公众号文章 7=MARKDOWN；公众号文章通常可读全文，PDF 往往读不了正文。
- 关键词找不到时应如实说"库里没有相关内容"，**不要用模型知识补足并冒充检索结果**；可给替代建议。

## 常用提示词方法论速查（「ai提示词宝库」常见内容）
| 框架 | 结构 |
|---|---|
| 万能公式 | 角色 + 任务 + 背景 + 要求(1/2/3) + 参考 |
| 4 步提问法 | 明确身份 + 具体任务 + 细节约束 + 输出格式 |
| ICIO | Instruction 指令 / Context 背景 / Input Data 输入数据 / Output Indicator 输出引导 |
| 结构化 Markdown 提示词 | # 目标 / # 步骤要求 / # 规范（设计/排版/技术栈）/ # 其他要求（内容必须完整不得省略） |
| 三层提示 | System（全局规则）+ Role（人设风格）+ Context（即时信息） |
| 进阶技法 | 零/单/少样本、CoT 思维链、Self-consistency 自洽、ToT 思维树、Step-back 后退提示、ReAct |
| 最佳实践 | 正向指令优先、明确具体输出要求、变量占位符、指令放在上下文前后重复、用 Markdown/XML/JSON 分隔 |
| 分隔符选择 | Markdown 标题（首选）/ 三反引号（代码）/ XML（嵌套与元数据）/ JSON（程序消费）|

## 生成的专业提示词应包含
角色（System Prompt，可给多重身份）→ 任务 → 背景 → 输入数据 → 执行步骤（思维链，8 步左右，含一次后退提示）→ 输出规范（分级标题+表格化）→ 约束与禁忌 → 质量标准自检清单。

## 企业级 Word 生成（python-docx）
- 解释器：`/Users/JessieWu/.workbuddy/binaries/python/envs/default/bin/python`（已装 python-docx 1.2.0）。
- 参考实现：`/Users/JessieWu/WorkBuddy/9.12 AI 培训空间/scripts/build_docx.py`（封面+目录域+页眉页脚+品牌配色表格）。
- 必备要素：
  - 封面页：大标题（微软雅黑 28pt 深蓝 #1F3A5F）+ 副标题 + 元信息表（文档类型/适用对象/版本/日期/密级）
  - 目录：插入 TOC 域 `TOC \o "1-3" \h \z \u`，占位文字提示"右键更新域"
  - 页眉（章节名/内部资料）+ 页脚（PAGE 域页码）；`sec.different_first_page_header_footer = True` 让封面无页眉页脚
  - 样式：Normal=宋体 11pt/1.5 倍行距；Heading 1/2/3=微软雅黑 17/14/12pt 粗体深蓝
  - 表格：`Table Grid` + 表头深蓝底(#1F3A5F)白字 + 隔行浅蓝底(#EEF3F9)
  - 中文字体必须设 `w:eastAsia`，否则中文回退默认字体
- 交付前用 python-docx 回读校验：标题数、表格数、总字数。

## 执行边界
- 生成文件放工作区 `outputs/`，脚本放 `scripts/`。
- 只交付用户要的成果文件；提示词可作为 Word 附录一并给出（用户往往会复用）。

## 附：把提示词真正跑成图/视频（ImageGen / VideoGen）
当用户要求"跑一条出来看效果"时，先告知积分消耗（图片约 5–10／条，视频约 50–100／5 秒），再执行。
- **VidMuse CLI 通常未安装**——IMA 文章里说的 WorkBuddy + VidMuse 链路不代表本机可用；先 `command -v vidmuse` 确认，没有就走 ImageGen + VideoGen。
- **推荐链路**：ImageGen 出产品主图 → VideoGen 图生视频。这样产品一致性最好，也最贴近"上传主图直出广告"的真实工作流。
- **VideoGen 坑**：`aspect_ratio: "9:16"` 会报 `code:14407 unsupported video aspect_ratio`。
  → **不要传 aspect_ratio**，画面比例跟随输入图（用竖版主图即得竖版视频）。
- VideoGen 可用参数：`image`（本地路径）+ `prompt`（中文分镜，按秒分段写）+ `negative_prompt`（禁文字/logo/产品漂移/肢体畸变）+ `resolution:"1080P"` + `seconds` + `watermark:false` + `output_dir`。
- **奢侈品/箱包类生图必须显式禁止品牌元素**：提示词里写"五金为纯素面几何形，无字母、无花纹、无 logo 图案"。
  否则模型会自动补一个酷似大牌的五金，产生商标风险。出图后**务必 Read 图片肉眼复核**再用。
