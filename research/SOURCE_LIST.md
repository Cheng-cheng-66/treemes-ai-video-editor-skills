# 来源清单

> 调研日期：2026-07-23。  
> 可信度：A = 官方文档/官方仓库/原始论文；B = 项目作者技术文章、可核验社区案例；C = 二手内容，仅用于发现线索或观察市场，不能单独支撑关键结论。  
> 日期列按“首次发布；最近更新/本次快照”记录。页面未分别显示两个日期时写“未明确显示”，不推测。

## 1. Codex 与 OpenAI

| ID | 标题 | URL | 类型 | 发布时间；最近更新时间 | 可信度 | 关键发现 |
|---|---|---|---|---|---|---|
| S01 | OpenAI Codex CLI – Getting Started | https://help.openai.com/en/articles/11096431 | 官方文档 | 页面显示更新于约 3 个月前 | A | Codex CLI 可读写本地文件、运行命令，有审批/沙箱模式 |
| S02 | Introducing Codex | https://openai.com/index/introducing-codex/ | 官方发布 | 2025-05-16，后续有更新 | A | Codex 是软件工程智能体，可在隔离环境运行命令和测试；结果仍需人工审查 |
| S03 | Codex is now generally available | https://openai.com/index/codex-now-generally-available/ | 官方发布 | 2025-10-06 | A | Codex SDK 可嵌入工作流、工具和应用 |
| S04 | Introducing the Codex app | https://openai.com/index/introducing-the-codex-app/ | 官方发布 | 2026-02-02；2026-03-04 更新 Windows | A | Codex App 有 Skills、Automations、多任务；官方定位从写代码扩展到用代码完成工作 |
| S05 | Codex use cases | https://developers.openai.com/codex/use-cases?category=automation | 官方文档 | 本次访问 2026-07-23 | A | 官方强调可验证操作、创建 CLI、保存可重复工作流 |
| S06 | Audio API reference | https://platform.openai.com/docs/api-reference/audio/ | 官方 API | 本次访问 2026-07-23 | A | 转写端点、可用模型、词/段时间戳能力 |
| S07 | OpenAI model comparison/pricing | https://developers.openai.com/api/docs/models/compare | 官方价格 | 本次访问 2026-07-23 | A | 模型按输入/输出 Token 计费，价格随模型变化 |

## 2. 确定性媒体处理与程序化视频

| ID | 标题 | URL | 类型 | 发布时间；最近更新时间 | 可信度 | 关键发现 |
|---|---|---|---|---|---|---|
| S08 | ffprobe Documentation | https://ffmpeg.org/ffprobe.html | 官方文档 | 2026-07 页面快照 | A | 机器可读输出格式/流/元数据，适合素材清点 |
| S09 | FFmpeg Filters Documentation | https://ffmpeg.org/ffmpeg-filters.html | 官方文档 | 本次访问 2026-07-23 | A | silencedetect、silenceremove、loudnorm、overlay、crop、drawtext、blurdetect 等 |
| S10 | Remotion official | https://www.remotion.dev/ | 官方文档 | 本次访问 2026-07-23 | A | React 程序化视频、Studio 预览、本地/云/浏览器渲染 |
| S11 | remotion-dev/remotion | https://github.com/remotion-dev/remotion | 官方仓库 | v4.0.477，2026-06-13；约 50.1k Star | A | 高活跃程序化视频框架；特殊许可需核对 |
| S12 | Remotion agent skill | https://github.com/remotion-dev/skills/blob/main/skills/remotion/SKILL.md | 官方仓库 | 本次访问 2026-07-23 | A | 官方 Skill 指出静音检测/裁切等应使用 FFmpeg |
| S13 | MoviePy documentation | https://zulko.github.io/moviepy/ | 官方文档 | v2 文档，本次访问 2026-07-23 | A | Python 拼接、合成、效果；v2 有破坏性 API 变化 |
| S14 | Zulko/moviepy | https://github.com/Zulko/moviepy | 官方仓库 | v2.2.1，2025-05-21；约 14.6k Star | A | 可运行、跨平台；维护者带宽和 v2 迁移是现实风险 |
| S15 | mifi/editly | https://github.com/mifi/editly | 官方仓库 | v0.15.0-rc.1，2025-01-19；约 5.4k Star | A | Node + FFmpeg 声明式 JSON 时间线，支持字幕/B-roll/混音 |

## 3. 自动剪辑、ASR、场景与智能体项目

| ID | 标题 | URL | 类型 | 发布时间；最近更新时间 | 可信度 | 关键发现 |
|---|---|---|---|---|---|---|
| S16 | browser-use/video-use | https://github.com/browser-use/video-use | 官方仓库 | 无 Release；本次约 17.5k Star、18 commits | A | 明确支持 Codex；转写→LLM→EDL→FFmpeg→切点自检；项目新 |
| S17 | modelscope/FunClip | https://github.com/modelscope/FunClip | 官方仓库 | README 2026-05-20 更新；约 6k Star | A | 中文 Paraformer、热词、说话人、文本剪辑、LLM 辅助；Nano 时间戳不适合精剪 |
| S18 | FunClip Hugging Face Space | https://huggingface.co/spaces/FunAudioLLM/FunClip | 官方演示 | 2026-07 仍运行 | A | 有公开可交互演示，证明项目不是仅 README 概念 |
| S19 | Huanshere/VideoLingo | https://github.com/Huanshere/VideoLingo | 官方仓库 | v3.0.1，2026-02-28；约 17.8k Star | A | WhisperX、字幕、翻译、配音、断点续跑、批量；明确列出噪声/数字/多人限制 |
| S20 | HKUDS/VideoAgent | https://github.com/HKUDS/VideoAgent | 官方仓库/研究 | 2026；约 1.5k Star；无 Release | A | 工具图式视频理解/编辑/重制；安装链复杂、需多模型/多 API |
| S21 | VideoAgent paper | https://arxiv.org/abs/2606.23327 | 论文 | 2026-06 | A | 研究级 agentic video understanding/editing 框架；实验不等于生产 SLA |
| S22 | WyattBlue/auto-editor | https://github.com/WyattBlue/auto-editor | 官方仓库 | 30.3.0，2026-05-27；约 4.3k Star | A | 成熟静音/响度驱动自动粗剪；不理解语义 |
| S23 | SYSTRAN/faster-whisper | https://github.com/SYSTRAN/faster-whisper | 官方仓库 | 1.2.1，2025-10-31；约 23.2k Star | A | CTranslate2 加速、量化、批处理 ASR；仍需平台和中文样本实测 |
| S24 | m-bain/whisperX | https://github.com/m-bain/whisperX | 官方仓库 | v3.8.6，2026-05-25；约 23.1k Star | A | 逐词时间戳与说话人；Issue 显示数字/符号、CUDA、模型访问问题 |
| S25 | WhisperX paper | https://arxiv.org/abs/2303.00747 | 论文 | 2023-03 | A | 长音频时间对齐方法的原始证据 |
| S26 | Breakthrough/PySceneDetect | https://github.com/Breakthrough/PySceneDetect | 官方仓库 | v0.7，2026-05-03；约 5k Star | A | 场景检测、VFR 改进、EDL/OTIO/FCP 输出 |
| S27 | PySceneDetect docs | https://www.scenedetect.com/docs/latest/ | 官方文档 | v0.7 | A | API、CLI、检测器、split、EDL/OTIO |
| S28 | OpenAI Whisper | https://github.com/openai/whisper | 官方仓库 | v20250625；约 105k Star | A | 多语 ASR 原始模型和许可；本身不做完整剪辑 |

## 4. 专业剪辑软件与交换格式

| ID | 标题 | URL | 类型 | 发布时间；最近更新时间 | 可信度 | 关键发现 |
|---|---|---|---|---|---|---|
| S29 | Premiere UXP API | https://developer.adobe.com/premiere-pro/uxp/ | 官方文档 | 本次访问 2026-07-23 | A | Premiere 当前扩展平台，可构建面板和自动化 |
| S30 | Premiere DOM API | https://developer.adobe.com/premiere-pro/uxp/ppro_reference/ | 官方 API | 本次访问 2026-07-23 | A | 可访问项目、序列、轨道、剪辑、标记与导出 |
| S31 | Understanding UXP APIs | https://developer.adobe.com/premiere-pro/uxp/resources/fundamentals/apis/ | 官方文档 | 本次访问 2026-07-23 | A | UXP/Premiere API 分工及版本兼容风险 |
| S32 | Premiere supported export formats | https://helpx.adobe.com/premiere/desktop/render-and-export/export-files/supported-export-file-formats.html | 官方文档 | 2026-04-02 | A | AAF、EDL、FCP XML 等交换格式 |
| S33 | DaVinci Resolve Studio | https://www.blackmagicdesign.com/products/davinciresolve/studio | 官方产品/价格 | 本次访问 2026-07-23 | A | 免费/Studio 差异，Studio US$295，AI/远程脚本/专业交付能力 |
| S34 | DaVinci Resolve product | https://www.blackmagicdesign.com/products/davinciresolve | 官方产品 | 本次访问 2026-07-23 | A | Mac/Windows/Linux、工作流/编码 API 和专业后期能力 |

## 5. 剪映/CapCut 自动化

| ID | 标题 | URL | 类型 | 发布时间；最近更新时间 | 可信度 | 关键发现 |
|---|---|---|---|---|---|---|
| S35 | capcut-cli draft schema | https://app.unpkg.com/capcut-cli@0.12.0/files/docs/draft-schema/00-overview.md | 第三方项目文档 | 2026-07 页面快照 | B | 草稿 JSON 结构、轨道/素材分离；属于逆向/实践文档，不是官方 API |
| S36 | capcut-cli version differences | https://app.unpkg.com/capcut-cli@0.12.0/files/docs/draft-schema/05-version-differences.md | 第三方项目文档 | 2026-07 页面快照 | B | macOS/Windows、CapCut/剪映文件名和枚举差异 |
| S37 | renqingfei/CapCutAPI | https://github.com/renqingfei/CapCutAPI | 第三方仓库 | 本次访问 2026-07-23 | B | 生成/修改草稿的社区方案；不是官方桌面编辑 API |
| S38 | CapCut AI Video Editor | https://www.capcut.com/tools/ai-video-editor | 官方产品 | 本次访问 2026-07-23 | A | 模板、字幕、生成能力；部分功能按地区提供 |
| S39 | 掘金：剪映草稿与 FFmpeg 导出 | https://juejin.cn/post/7341288829684318260 | 技术文章 | 2024-03-02 | B | 显示 macOS/Windows 草稿路径及 JSON 实践，佐证逆向可行但版本敏感 |

## 6. 商业产品

| ID | 标题 | URL | 类型 | 发布时间；最近更新时间 | 可信度 | 关键发现 |
|---|---|---|---|---|---|---|
| S40 | Descript Pricing | https://www.descript.com/pricing | 官方价格 | 本次访问 2026-07-23 | A | 免费与 Hobbyist/Creator/Business 计划、媒体小时和 AI credits |
| S41 | Wisecut Pricing | https://www.wisecut.ai/pricing | 官方价格 | 本次访问 2026-07-23 | A | 按处理分钟/分辨率计费，Autopilot 监控频道并切片 |
| S42 | OpusClip plans and credits | https://help.opus.pro/docs/article/plans-and-credits | 官方帮助 | 2026 页面快照 | A | Pro 处理分钟额度，长转短定位 |
| S43 | Captions plans | https://www.captions.ai/plans | 官方价格 | 本次访问 2026-07-23 | A | AI 视频编辑按计划/credits；地区价格可能不同 |

## 7. 视频理解、社区案例与中文平台

| ID | 标题 | URL | 类型 | 发布时间；最近更新时间 | 可信度 | 关键发现 |
|---|---|---|---|---|---|---|
| S44 | Gemini 2.5 video understanding | https://developers.googleblog.com/gemini-2-5-video-understanding/ | 官方技术博客 | 2025-05-09 | A | 视频理解、长视频低分辨率输入、时序定位；适合 VLM 候选 |
| S45 | Reddit: Codex video editing workflow | https://www.reddit.com/r/ClaudeCode/comments/1r0btpu/i_edited_this_video_100_with_codex_workflow/ | 作者案例/讨论 | 2026 页面快照 | B | Codex + Remotion + 抽帧反馈真实案例；作者称某次比人工慢 |
| S46 | DEV: LangGraph + Whisper + FFmpeg | https://dev.to/abhisek_mishra/how-i-built-an-ai-video-clipping-pipeline-with-langgraph-whisper-and-ffmpeg-4nfh | 作者技术文章 | 2026-05-24，2026-06-13 编辑 | B | 节点化重试；单人焦点较好，B-roll/多人仍难 |
| S47 | HN: LLM powered FFmpeg pipeline | https://news.ycombinator.com/item?id=39044405 | 社区案例 | 2024-01-18 | B | 已有人用 LLM 生成并执行 FFmpeg 处理管线 |
| S48 | 抖音：Codex + HyperFrames | https://jingxuan.douyin.com/m/video/7637087594219687210 | 创作者案例 | 2026-05-07 | C | 真实市场用法；创作者明确提到 Token 消耗和动效限制 |
| S49 | 抖音：Codex 视频系列流程 | https://jingxuan.douyin.com/m/video/7640105180394602575 | 创作者案例 | 2026-05-15 | C | 找素材、字幕、音乐、动效的工作流展示，不足以证明稳定生产 |
| S50 | Bilibili：Whisper 本地字幕教程 | https://www.bilibili.com/video/BV1Vte8zLEmw/ | 教程 | 2025-08-22 | C | 中文用户部署需求、硬件/安装现实；关键事实以官方仓库复核 |
| S51 | Bilibili：FunClip 教程 | https://www.bilibili.com/opus/973229238442262544 | 教程 | 2024-09-04 | C | 展示中文文本/说话人裁剪，能力以官方仓库复核 |
| S52 | 知乎：VideoLingo 使用说明 | https://www.zhihu.com/question/590449168/answer/78191687588 | 使用文章 | 2026 页面快照 | C | 使用过程和 API/TTS 依赖；能力以官方仓库复核 |
| S53 | 掘金：FunClip 介绍 | https://juejin.cn/post/7404777076090044426 | 教程/二手 | 2024-08-20 | C | 国内用户场景线索；不用于独立支撑质量结论 |
| S54 | DEV: Text-to-Clip serverless engine | https://dev.to/aws-builders/text-to-clip-building-a-serverless-ai-engine-that-edits-video-from-descriptions-2fbf | 作者技术文章 | 2026-01-08 | B | 镜头识别 + 转写 + 向量检索 + FFmpeg 的 B-roll/片段检索架构 |

## 搜索平台覆盖与未采用结果

- 已搜索并找到有效来源：OpenAI/FFmpeg/Remotion/Adobe/Blackmagic 官方站、GitHub、Hugging Face、Reddit、Hacker News、DEV、Bilibili、知乎、抖音、掘金。
- 已搜索但本次没有进入关键证据：YouTube、Medium、CSDN。原因是结果缺乏原始代码/技术细节，或可由官方文档/仓库替代。
- “未找到可靠证据”：剪映/CapCut 面向普通开发者的官方、完整、稳定桌面时间线编辑 API；成熟开箱即用的通用 Codex 自动剪辑产品；AI 在无人复核下稳定完成工厂 B-roll 语义与合规判断。
