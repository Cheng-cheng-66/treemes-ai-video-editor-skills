# 基于 Codex 的自动剪辑方法全网调研报告

> 调研日期：2026-07-23（Asia/Shanghai）  
> 研究口径：以当天可访问的官方文档、官方仓库、Release、Issue、论文及社区案例为证据。GitHub Star、价格和产品能力会变化，均按本次页面快照记录。  
> 重要限制：本次是技术与项目决策调研，没有下载模型、克隆全部仓库或用公司真实素材跑基准；“可运行”表示有代码、安装说明或 Release，不能等同于已通过本公司生产验收。

## 中间发现

1. 已找到真正可由 Codex/编码智能体使用的公开视频编辑案例：`video-use`、Codex + Remotion 社区案例、`VideoAgent` 等。但它们大多仍是快速演进的开源框架或个人工作流，没有形成“安装后即可稳定替代专业剪辑师”的成熟产品。
2. 官方资料确认 Codex 能读写文件、运行命令、使用 Skills、SDK 和 Automations；因此它能编写、调用和维护视频管线。但“镜头审美”和“业务事实判断”不是 Codex 的内建视频剪辑能力。
3. 最稳妥的分层是：FFmpeg/ffprobe 做确定性媒体处理，Python 做分析与编排，ASR + LLM 生成可审核的剪辑决策清单，Remotion 只负责模板化包装，人工在审核页或专业时间线中做最终确认。
4. 中文口播的 V1 不应默认押注 WhisperX。FunClip/FunASR 对中文热词、字符时间戳和说话人裁剪很有参考价值；faster-whisper/WhisperX 仍适合作为可替换后端和长访谈/说话人对齐方案。
5. 剪映/CapCut 的社区自动化主要依赖逆向草稿 JSON 或桌面点击。未找到可靠证据证明其桌面剪辑器存在面向一般开发者、稳定、公开、长期兼容的完整编辑 API。

## 1. 执行摘要

### 这件事能不能做

能做，但要把目标定义为“自动生成可恢复、可审核、可修改的粗剪和包装”，而不是“AI 无人监督地剪出导演级成片”。

当前最成熟的自动化部分是：

- 探测素材、抽取音频、转码、切片、拼接、字幕、Logo、片头片尾、音乐混音、横竖版和批量导出；
- 中文口播转写、静音/长停顿候选、口头填充词和重复表达候选；
- 长访谈按主题和观点生成短视频候选；
- 按固定品牌模板生成字幕与包装；
- 生成 EDL/OTIO/FCP XML 等可继续编辑的时间线数据。

当前不应完全自动化的是：

- 事实敏感的口误判断；
- 工厂画面是否符合安全、客户保密和品牌要求；
- B-roll 是否真正支持口播论点；
- 情绪、节奏、幽默、叙事转折和音乐版权；
- 客户案例中的数据、承诺与敏感信息；
- 最终发布。

### Codex 究竟扮演什么角色

Codex 更适合做“方案工程师 + 管线编排器 + 故障处理员”，而不是逐帧承担解码、特效和渲染：

- 它编写与维护 Python、FFmpeg、Remotion 代码；
- 读取素材清单、转写、检测结果和缩略图；
- 调用工具生成 EDL/剪辑计划；
- 执行渲染、读取日志、抽帧质检并修复失败；
- 把重复工作固化为 CLI、服务、Skill 或 Automation。

OpenAI 官方说明 Codex 可读写文件、运行命令，并可通过 SDK 嵌入工作流；Codex App 也支持 Skills 和 Automations。来源：[Codex CLI](https://help.openai.com/en/articles/11096431)、[Codex GA 与 SDK](https://openai.com/index/codex-now-generally-available/)、[Codex App](https://openai.com/index/introducing-the-codex-app/)。

### 最值得采用的路线

推荐组合：

```text
Codex（开发、调试、人工反馈编排）
+ Python 3.11（业务逻辑、任务状态、适配器）
+ FFmpeg / ffprobe（确定性剪切、合成、混音、导出、媒体探测）
+ FunASR/Paraformer 或 faster-whisper（可插拔中文 ASR）
+ WhisperX（V1.1 后用于逐词对齐/说话人；非 V1 必需）
+ SQLite（任务、素材、片段、决策、审核、日志）
+ LLM Structured Output（删除/保留候选及理由，不直接删素材）
+ 简单 Web 审核页（接受、拒绝、恢复、试听、预览）
+ Remotion（V1.1 后的字幕动画与品牌模板）
+ OTIO/FCP XML/EDL 导出（V1.1 后保留专业人工编辑）
```

### 最大风险

最大风险不是“FFmpeg 不会剪”，而是语义判断错误造成误删、断句生硬、事实失真和错误 B-roll。第二风险是把剪映草稿逆向或桌面自动化当作长期稳定核心。第三风险是模型、字体、音乐、素材和客户画面的版权/合规问题。

### 最小版本

V1.0 只做“中文老板口播 3–10 分钟原片 → 可审核粗剪 + 中文字幕 + Logo/片头片尾 + 9:16 预览”。不做自动工厂 B-roll、不做一键发布、不做复杂动效、不做无人审核的口误删除。

## 2. “基于 Codex 自动剪辑”的准确含义

### A 类：真正以 Codex 为核心

每个任务都由 Codex 读取转写/缩略图、生成或修改 EDL、调用渲染、检查结果并迭代。`video-use` 是当前最贴近此定义的公开项目之一：其 README 明确支持 Codex，采用“转写 → 压缩语义视图 → LLM 决策 → EDL → 渲染 → 自检”的链路，并要求策略确认后再执行。它仍是快速演进项目，当前无正式 Release，不应直接视为企业稳定产品。[项目](https://github.com/browser-use/video-use)

### B 类：Codex 负责搭建，系统后续独立运行

这是最适合公司的定义。Codex 开发和维护服务，真正的生产任务由固定版本的 Python Worker、队列、FFmpeg、ASR 和审核页面完成。优点是可测试、可追踪、可批量、可限制权限；即使 Codex 不在线也能运行。

### C 类：普通 AI 剪辑工具

OpusClip、Descript、Wisecut、CapCut AI、Captions 等是竞品或能力标杆。除非 Codex 通过公开 API 调用它们，或为它们搭建明确适配层，否则不能称为“基于 Codex”。

结论：生产系统应以 B 类为主，A 类用于研发、例外处理和人工反馈迭代，C 类用于做效果基准和应急工具。

## 3. 当前主要技术路线地图

| 路线 | 核心价值 | 自动化上限 | 主要短板 | 定位 |
|---|---|---:|---|---|
| Codex + FFmpeg | 确定、可审计、跨平台、批量 | 高（执行层） | 不理解语义与审美 | 必选底座 |
| Codex + Python 视频库 | 易组合 ASR/CV/业务规则 | 高（分析/编排） | 依赖与性能复杂 | 必选编排层 |
| Codex + Remotion | 字幕动画、模板、批量变体 | 高（包装层） | React/浏览器渲染成本、许可 | V1.1 后加入 |
| Codex + 剪映/CapCut | 运营熟悉、可人工接手 | 中 | 公共编辑 API 证据不足；草稿逆向易失效 | 非核心适配层 |
| Codex + Premiere | 专业时间线、人工可编辑、UXP | 高 | 订阅、版本兼容、插件开发 | 专业团队方案 |
| Codex + DaVinci | 编辑/调色/音频/交付一体化 | 高 | 学习和自动化运维较重；高级/远程能力偏 Studio | 企业长期方案 |
| Codex + VLM | 语义检索、B-roll 候选、质量评估 | 中 | 成本、误判、时间定位 | V2 重点 |
| 桌面/浏览器自动化 | 可操作无 API 软件 | 低到中 | 脆弱、慢、账号与弹窗风险 | 最后手段 |

## 4. 全网发现的开源项目与案例

以下数据按 2026-07-23 页面快照；“可运行判断”来自代码、安装步骤、Release/Issue/依赖检查，本次未对所有项目执行真实素材测试。

| 项目 | 快照与活跃度 | 解决的问题与主要技术 | 平台/中文/批量 | 可运行性、缺点与参考价值 |
|---|---|---|---|---|
| [browser-use/video-use](https://github.com/browser-use/video-use) | 约 17.5k Star；18 commits；14 issues；无 Release | 编码智能体剪真实素材；FFmpeg、转写、EDL、抽帧自检、Remotion/Manim/PIL 可选 | 文档有 macOS 安装；Windows 未明确；中文取决于转写服务；可按目录工作 | 代码和安装说明存在，支持 Codex；默认依赖 ElevenLabs，项目很新、无 Release。最值得借鉴“文字视图 + 按需视觉 + 审批 + 自检”，不建议原样投产 |
| [modelscope/FunClip](https://github.com/modelscope/FunClip) | 约 6k Star；255 commits；README 2026-05-20 更新；未见稳定 Release 列表 | FunASR/Paraformer 中文识别、热词、说话人、文本选段、LLM 辅助剪辑、Gradio、SRT | Python；macOS/Windows 理论可用但模型依赖需实测；中文强；有 CLI | 安装与 CLI 示例完整；官方说明 Nano 时间戳不适合精确文本剪辑，应使用 Paraformer。V1 中文 ASR/文本剪辑首要参考 |
| [Huanshere/VideoLingo](https://github.com/Huanshere/VideoLingo) | 约 17.8k Star；975 commits；177 issues；v3.0.1（2026-02-28） | WhisperX、LLM 翻译、字幕切分、配音、Streamlit、断点续跑 | macOS/Windows/Linux；中文支持；文档有 batch | 可运行资料成熟，但目标是本地化/配音而非内容删选；README 明确列出噪声、数字对齐、多说话人限制。参考其任务恢复和字幕工程 |
| [HKUDS/VideoAgent](https://github.com/HKUDS/VideoAgent) | 约 1.5k Star；无 Release | Agentic graph、Whisper、ImageBind、多 LLM、视频理解/重制 | README 明示 Linux/Windows、8GB GPU；未声明 macOS；中文示例有；批量不清晰 | 安装链长、模型多、Claude 路由依赖明显；更像研究框架。适合参考工具图和反思，不适合作为 V1 |
| [WyattBlue/auto-editor](https://github.com/WyattBlue/auto-editor) | 约 4.3k Star；142 Releases；30.3.0（2026-05-27） | 以音频响度为主自动删除静默，CLI，导出编辑工程 | macOS/Windows/Linux；与语言无关；批量可脚本化 | 成熟可运行，适合做静音候选或效果基准；不理解口误/重复/内容价值。可作为可替换检测器，不应直接决定删除 |
| [SYSTRAN/faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 约 23.2k Star；1.2.1（2025-10-31）；约 281 issues | CTranslate2 加速 Whisper、量化、批处理 ASR | macOS/Windows/Linux；多语含中文；批量强 | 成熟底层库；中文专有词需热词/后处理；Apple Silicon 性能与 CUDA 路线不同。推荐作为通用 ASR 适配器 |
| [m-bain/whisperX](https://github.com/m-bain/whisperX) | 约 23.1k Star；v3.8.6（2026-05-25）；约 171 issues | 逐词时间戳、强制对齐、说话人分离 | 主要 Python/GPU；跨平台依赖复杂；中文可用但需样本验证；批量可开发 | 论文与活跃 Release 支持真实性；Issue 显示数字/符号对齐、CUDA/模型访问等现实问题。V1.1 可选，不是 V1 必需 |
| [Breakthrough/PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 约 5k Star；v0.7（2026-05-03） | 快切/转场/淡入淡出检测，CSV/EDL/OTIO/FCP 输出，FFmpeg 分段 | macOS/Windows/Linux；与语言无关；批量强 | 成熟可用；只发现镜头边界，不知道镜头好坏。工厂素材切镜和时间线交换必备候选 |
| [Zulko/moviepy](https://github.com/Zulko/moviepy) | 约 14.6k Star；v2.2.1（2025-05-21）；63 issues | Python 剪切、拼接、合成、特效封装 | macOS/Windows/Linux；与语言无关；批量可写 | 可运行且易开发，但 v2 有破坏性 API 变化，复杂/大批量性能与稳定性通常不如直接 FFmpeg。适合原型和少量合成 |
| [remotion-dev/remotion](https://github.com/remotion-dev/remotion) | 约 50.1k Star；33,788 commits；v4.0.477（2026-06-13） | React 程序化视频、Studio 预览、字幕/图形动画、本地/云渲染 | macOS/Windows/Linux；中文取决于字体；批量强 | 高度活跃、生态成熟；有特殊许可，企业使用须核对。适合品牌模板，不适合替代 FFmpeg 的静音分析与基础转码 |
| [mifi/editly](https://github.com/mifi/editly) | 约 5.4k Star；v0.15.0-rc.1（2025-01-19） | Node + FFmpeg 声明式 JSON NLE、标题、字幕、B-roll、转场 | macOS/Windows/Linux；中文取决于字体；批量强 | 可运行，规范简单，适合作为“JSON 时间线”参考；维护规模较小，OpenGL/headless 依赖可能带来部署问题 |

二次开发说明：上述 11 个项目均提供源代码，技术上可二次开发；实际商用还必须分别核对代码许可证、模型权重许可证、字体/素材许可和第三方 API 条款。Remotion 使用特殊许可，不能仅凭“GitHub 可见源码”推断企业免费；FunClip 等项目的模型权重也有独立条款。表中的 macOS/Windows“可用”只代表文档或跨平台依赖支持，不代表已在本公司的具体硬件上通过安装与性能验收。

补充案例：

- Reddit 出现多条“100% 用 Codex 剪视频”的流程分享，通常组合 Remotion、FFmpeg、分割模型和抽帧反馈；其中一位作者明确说某次流程比人工剪辑更慢。这证明“已有人实现”，不证明“稳定更省钱”。[案例](https://www.reddit.com/r/ClaudeCode/comments/1r0btpu/i_edited_this_video_100_with_codex_workflow/)
- 抖音/B站已出现 Codex + HyperFrames 教程，但创作者也明确提示 Token 消耗大、动效有限、需要反复反馈。[抖音案例](https://jingxuan.douyin.com/m/video/7637087594219687210)
- DEV 社区的 LangGraph + Whisper + FFmpeg 案例将节点拆成转写、选段、人物居中和渲染，并指出 B-roll 重、多人构图仍差。这与本次推荐的可重试分层架构一致。[案例](https://dev.to/abhisek_mishra/how-i-built-an-ai-video-clipping-pipeline-with-langgraph-whisper-and-ffmpeg-4nfh)

## 5. 商业 AI 剪辑产品对比

| 产品 | 主要能力 | 价格快照/计费 | 适合作为 | 局限 |
|---|---|---|---|---|
| OpusClip | 长视频找高光、重构短视频、字幕、社媒 | 以处理分钟/积分为核心；官方帮助页显示 Pro 300 分钟/月；价格随计划变化 | 客户案例长转短效果基准 | 云端黑箱、审美不可控、不是 Codex 系统 |
| Descript | 文本式剪辑、填充词/重复词删除、字幕、音质、AI co-editor | 官方 2026 页面：免费；Hobbyist 年付折算约 US$16/月；Creator 约 US$24/月；Business 约 US$50/月 | 英文/访谈文本剪辑标杆 | 中文和本地部署不是其核心；额度/AI credits；项目格式被平台绑定 |
| Wisecut | 自动静音、字幕、音乐、长转短、Autopilot | 官方年付折算 Starter+ 约 US$23.25/月；Professional+ 约 US$83.25/月；Autopilot US$49/月起 | 无人值守发布链参考 | 云端、按分钟、可解释性和人工恢复有限 |
| CapCut/剪映 AI | 模板、自动字幕、一键成片、AI 功能、人工时间线 | 地区/平台/订阅差异大，本次未找到统一可靠的人民币 API 计价 | 运营团队人工精修与竞品效果 | 未确认公开通用桌面编辑 API；草稿逆向和 UI 自动化易失效；账号/条款/素材合规 |
| Captions | 自动字幕、AI Edit、配音、B-roll/生成资产 | 官方采用计划 + AI credits；不同地区价格不同 | 移动端口播包装基准 | 云端黑箱，生成素材版权和成本需逐项核对 |
| DaVinci Resolve Studio（专业产品基准） | 文本剪辑、智能重构、调色、音频、交付、脚本/工作流 | 官方一次性 US$295；免费版存在但高级 AI、远程脚本、专业格式有差异 | 长期企业人工精修底座 | 学习/部署较重，不是开箱即用 AI 自动剪辑 SaaS |

商业工具用于回答“市场已经做到什么”，不能作为“基于 Codex”的证据。

## 6. 各技术方案详细分析

### 6.1 Codex + FFmpeg

FFmpeg 是最合适的 V1 执行底座。`ffprobe` 能以 JSON 等机器可读格式输出容器、视频流、音轨、分辨率、时长、码率和元数据。FFmpeg 官方过滤器包含 `silencedetect`、`silenceremove`、`loudnorm`、`overlay`、`subtitles/ass`、`crop`、`drawtext`、`blurdetect`、`freezedetect`、`deshake` 等。[ffprobe](https://ffmpeg.org/ffprobe.html) / [filters](https://ffmpeg.org/ffmpeg-filters.html)

能稳定完成：

- 媒体探测和标准化；
- 按明确时间码切片、拼接、转码；
- 静音候选检测和阈值删除；
- SRT/ASS 字幕烧录、Logo/贴纸/进度条/片头片尾；
- BGM 混音、响度标准化、旁白侧链压缩；
- 16:9/9:16/1:1 画布、固定/跟踪裁切结果；
- 多平台编码预设和批处理。

不能单独完成：

- 判断一句话是不是口误；
- 判断重复是否是修辞；
- 判断哪个观点最有价值；
- 判断工厂镜头是否与口播语义匹配；
- 产生品牌级审美。

建议：FFmpeg 命令不由 LLM 每次自由生成并直接执行。把它封装成参数化、白名单化函数，先产出命令/manifest，再执行；输出与原始素材分目录，禁止覆盖输入。

### 6.2 Codex + Python 视频库

| 组件 | 最适合的任务 | V1 状态 |
|---|---|---|
| MoviePy | 快速原型、Python 内拼接/合成 | 可替换；不作为核心渲染 |
| OpenCV | 抽帧、清晰度/曝光/运动、跟踪、缩略图 | V1 可选；V2 必需 |
| PyAV | 精细解码、帧/时间基、性能与 FFmpeg 库级访问 | 后期性能优化 |
| librosa / pydub | 音频特征、能量、节奏、便捷分段 | 可替换；简单静音优先 FFmpeg |
| PySceneDetect | 镜头边界、缩略图、EDL/OTIO | V1.1/V2 |
| auto-editor | 静音粗剪基准/可替换引擎 | V1 可选 |
| faster-whisper | 跨语种本地 ASR | V1 候选 |
| FunASR/Paraformer | 中文字符时间戳、热词、说话人生态 | V1 中文首选候选，需 A/B |
| WhisperX | 逐词对齐、说话人 | V1.1 |
| YOLO | 人/设备/屏幕/安全帽等对象检测 | V2；需自有标注或定制 |
| MediaPipe | 人脸/姿态/关键点和轻量追踪 | V1.1 自动居中 |

关键设计：所有模型输出都写成带 `model_version`、`confidence`、`source_interval` 的结构化证据；LLM 只能引用这些证据生成决策，不能凭空编时间码。

### 6.3 Codex + Remotion

Remotion 适合：

- 程序化字幕动画、关键词强调、图表和品牌卡片；
- 同一内容批量生成横版/竖版、多品牌、多 CTA；
- React Studio 预览和模板组件化；
- 营销、知识类、口播包装。

Remotion 不适合替代：

- ffprobe/转码；
- 静音和场景检测；
- 大量原始素材理解；
- 专业剪辑师的自由时间线。

成本包括 Node/Chromium 渲染资源、字体与浏览器一致性、模板开发、云渲染费用，以及需要核对的商业许可。V1 先用 FFmpeg + ASS 完成字幕；V1.1 再用 Remotion 提升包装，避免一开始同时调通两个渲染栈。

### 6.4 Codex + 剪映或 CapCut

本次发现：

- 社区项目能写 `draft_info.json`/`draft_content.json` 并生成可被桌面端打开的草稿；
- macOS 和 Windows 文件名、路径、枚举及版本存在差异；
- 有第三方“剪映小助手 API”和 `capcut-cli`，但这些不是已确认的剪映桌面官方通用编辑 API；
- UI/桌面自动化可点击导入、套模板、导出，但容易受登录、弹窗、版本和坐标变化影响。

结论：

- 技术上可行：生成草稿/控制 UI；
- 已有人实现：是；
- 可稳定生产：未经本公司版本矩阵和回归测试前，否；
- 风险：草稿结构变化、素材路径、云草稿加密、账号风控、版权/条款、无人值守弹窗；
- 建议：只做“导出可导入草稿”的可选适配器，核心 EDL 和素材数据库必须独立于剪映。

### 6.5 Codex + Premiere Pro

Adobe 官方 UXP 是当前扩展标准。Premiere DOM 可访问项目、序列、轨道、剪辑、标记、效果和导出；UXP 还能做文件、网络和 UI。[官方 UXP](https://developer.adobe.com/premiere-pro/uxp/) / [Premiere API](https://developer.adobe.com/premiere-pro/uxp/ppro_reference/)

路线优先级：

1. V1.1：生成 FCP XML/EDL/OTIO，由 Premiere 导入；
2. V2：做 UXP 面板，读取审核结果、创建/修改序列；
3. 兼容旧系统时才考虑 ExtendScript/CEP；新项目优先 UXP。

优点是人工可继续编辑、专业生态成熟；缺点是订阅成本、插件开发和 Premiere/UXP 版本兼容。Adobe 官方列出 AAF、EDL、FCP XML 等直接导出格式，说明时间线交换是可靠的人工交接方式。[格式](https://helpx.adobe.com/premiere/desktop/render-and-export/export-files/supported-export-file-formats.html)

### 6.6 Codex + DaVinci Resolve

DaVinci 适合企业长期底座：

- Python/Lua 脚本可管理项目、媒体池、时间线和渲染队列；
- 编辑、Fusion、调色、Fairlight、Deliver 在同一系统；
- 可通过 EDL/XML/AAF/OTIO 类交换格式保留人工精修；
- Studio 有 Neural Engine、Smart Reframe、场景检测、语音隔离等高级能力。

官方当前页面显示：免费版支持最高 Ultra HD 3840×2160/60fps 的大量 8-bit 工作；Studio 为 US$295，增加 AI Neural Engine、10-bit/高帧率/更高分辨率、远程脚本 API、工作流和编码集成。[官方比较](https://www.blackmagicdesign.com/products/davinciresolve/studio)

局限：V1 开发和运维复杂度高；版本/API 环境要固定；部分外部/远程脚本能力受 Studio 限制。建议 V2 后把它作为专业精修/交付端，而不是 V1 唯一渲染器。

### 6.7 Codex + AI 视频理解模型

#### 语音层

- VAD 找说话段；
- ASR 生成带时间码文本；
- 对齐模型细化到词/字；
- 说话人分离标注谁在说；
- LLM 根据转写标记填充词、重复、逻辑断裂、重点观点。

#### 视觉层

- PySceneDetect 切成镜头；
- 每镜头抽开头/中间/结尾帧；
- OpenCV 计算模糊、曝光、抖动、黑帧/冻结帧；
- 人脸/人体追踪判断出镜、看镜头与裁切中心；
- YOLO/定制分类器识别设备、产线、工人、看板、三色灯、MES 屏幕；
- VLM 为镜头生成受控标签与短描述；
- 文本与镜头描述嵌入后做 B-roll 候选检索。

#### 决策层

```json
{
  "source_id": "A001",
  "start_ms": 8120,
  "end_ms": 12640,
  "action": "review_delete",
  "reason_code": "LONG_PAUSE_AFTER_RETAKE",
  "evidence": {
    "silence_ms": 1820,
    "transcript_before": "我们系统可以...",
    "transcript_after": "重新来，我们的MES系统可以..."
  },
  "confidence": 0.87,
  "reversible": true
}
```

LLM 输出必须通过 JSON Schema，时间码必须来自 ASR/镜头边界，动作默认是 `review_delete` 而不是物理删除。

## 7. 方案横向对比表

详表见 `SOLUTION_COMPARISON.md`。核心结论：

| 底座 | 开发 | 自动化 | 稳定 | 中文 | 批量 | 人工编辑 | 推荐 |
|---|---:|---:|---:|---:|---:|---:|---|
| FFmpeg + Python | 中 | 高 | 高 | 取决于 ASR | 强 | 需导出时间线/审核页 | V1 首选 |
| Remotion | 中高 | 高 | 中高 | 字体可控 | 强 | React/Studio，不是传统 NLE | 包装层 |
| 剪映草稿/UI | 中 | 中 | 低 | 强 | 中 | 强 | 可选适配 |
| Premiere UXP | 高 | 高 | 高 | 强 | 中高 | 很强 | 专业团队 |
| DaVinci API | 高 | 高 | 高 | 强 | 高 | 很强 | 长期企业 |

## 8. 针对公司场景分析

### 老板口播

- 现在适合自动化：转写、静音/长停顿候选、明显重复候选、粗剪、字幕、Logo、片头片尾、9:16、响度；
- 只能自动粗剪：口误、修辞重复、节奏、关键词强调；
- 必须复核：产品承诺、数字、客户名、专业术语、删句后的逻辑；
- 自动化成熟度：高；
- V1 优先级：第一。

### 工厂现场

- 现在适合自动化：镜头切分、模糊/曝光/抖动评分、物体/场景标签、相似镜头去重、检索候选；
- 只能自动粗剪：根据口播匹配设备/产线/MES/B-roll；
- 必须复核：安全违规、客户保密、工人肖像、屏幕数据、镜头是否真实支持论点；
- 自动化成熟度：中；
- V1 优先级：不做自动匹配，先建素材标签库。

### 客户案例

- 现在适合自动化：长访谈转写、说话人、章节、观点/数据候选、短视频候选、字幕；
- 只能自动粗剪：7–20 分钟长片结构、证言和 B-roll 组合；
- 必须复核：案例数据、授权、语境完整性、客户审批；
- 自动化成熟度：中高（长转短）/中（完整长片）；
- V1 优先级：V1.1。

### 视频日记/Vlog

- 现在适合自动化：镜头分类、质量评分、节拍分析、初步顺序候选、字幕/包装；
- 只能自动粗剪：叙事弧线、情绪节奏、笑点、音乐卡点；
- 必须复核：创作者风格和故事意义；
- 自动化成熟度：低到中；
- V1 优先级：最后。

综合排序：老板口播 V1 → 客户案例长转短 V1.1 → 工厂素材检索与 B-roll 候选 V2 → Vlog 叙事 V3。

## 9. 推荐的三套落地方案

### 方案 A：最低成本快速验证

```text
Codex
→ Python CLI
→ ffprobe + FFmpeg
→ FunASR/Paraformer 与 faster-whisper 二选一 A/B
→ 规则 + LLM JSON 剪辑清单
→ 静态 HTML 审核报告
→ FFmpeg 预览/正式导出
```

- 难度：中；1 名工程师约 1–2 周做可验收样机；
- 运行成本：本地 CPU/GPU + 可选 LLM API；无专业剪辑软件订阅；
- 优点：快、可审计、跨平台、核心风险可验证；
- 缺点：审核体验和字幕动效有限；
- 阶段：V1。

### 方案 B：稳定可持续的推荐方案

```text
Codex（研发维护）
→ FastAPI
→ SQLite/PostgreSQL + 本地任务队列
→ Worker：ffprobe/FFmpeg + 可插拔 ASR + PySceneDetect/OpenCV
→ LLM 结构化决策
→ Web 审核页（波形、文本、缩略图、恢复）
→ Remotion 品牌模板
→ MP4 + SRT + EDL/OTIO/FCP XML
```

- 难度：中高；4–8 周形成稳定内测；
- 运行成本：本地/单机 Worker；LLM 按文本 Token，VLM 按需调用；
- 优点：任务可恢复、人工可控、可扩展到四类场景；
- 缺点：需要前后端、队列、模型和模板工程；
- 阶段：V1.1–V2；
- 本报告最终推荐此方案，但必须从方案 A 的口播闭环起步。

### 方案 C：长期数字员工终局方案

```text
素材入口/监控目录
→ 不可变原始素材库 + 哈希
→ 素材/镜头/人物/设备/文本索引
→ 持久任务编排与 Worker 池
→ ASR/CV/VLM/LLM 决策
→ 多版本粗剪
→ Web 审核/批注/差异
→ Remotion + DaVinci/Premiere 适配
→ 自动质检
→ 审批后导出
→ 发布系统（独立审批）
→ 反馈回流评测集
```

- 难度：高；3–9 个月渐进建设；
- 成本：GPU/对象存储/数据库/API/专业软件/运维；
- 优点：可批量、可学习、可审计、可接专业后期；
- 缺点：系统复杂，模型漂移与数据治理要求高；
- 阶段：V2–V3。

## 10. V1.0 最小可行版本建议

核心场景：单人中文老板口播，输入 3–10 分钟，输出 9:16 可审核粗剪。

V1 最重要的问题不是“自动生成酷炫视频”，而是：

> 系统能否在不破坏原片的前提下，把明显停顿、重录和重复表达转化为可解释、可恢复的剪辑决策，并稳定输出同步中文字幕。

ASR 选型必须用公司真实样本 A/B：

- 10 条、总计至少 60 分钟；
- 包含 MES、三色灯、安灯、工位、OEE、设备名、客户名等词；
- 比较 FunASR/Paraformer 与 faster-whisper；
- 指标包括字错率、专有词命中、时间码偏差、处理时长和资源占用；
- 不能根据通用排行榜直接决定。

## 11. V1.0 功能清单

必须：

- 素材只读接入、SHA-256、任务 ID、输出隔离；
- ffprobe 媒体清单；
- 音频提取、中文转写、SRT/JSON；
- 静音与长停顿候选；
- 填充词、明显重复、重录候选；
- 结构化 EDL/剪辑决策清单和原因；
- 人工接受/拒绝/恢复；
- FFmpeg 粗剪、ASS/SRT 字幕、Logo、片头片尾、9:16；
- 前后时长、删除清单、命令、日志、模型版本；
- 失败可重试，不重跑已成功阶段。

可替换：

- FunASR ↔ faster-whisper；
- 本地 LLM ↔ OpenAI/其他兼容 API；
- 静态 HTML 审核 ↔ 简单 Web 服务。

暂不需要：

- WhisperX、YOLO、MediaPipe、PySceneDetect、Remotion；
- 专业 NLE 插件；
- 云队列和多机 GPU。

## 12. V1.0 不做什么

- 不自动发布；
- 不覆盖或删除原始素材；
- 不把所有低音量都删掉；
- 不自动确认事实性口误；
- 不自动选工厂 B-roll；
- 不做 Vlog 叙事；
- 不做复杂转场、生成式特效、数字人、配音克隆；
- 不直接写剪映私有草稿作为唯一工程格式；
- 不承诺“零人工”或“替代剪辑师”；
- 不用未经授权的音乐、字体、客户画面或生成素材。

## 13. V1.0 验收标准

| 编号 | 测试 | 通过标准 |
|---|---|---|
| A01 | 输入 | 可选择一条 3–10 分钟中文单人 MP4/MOV；任务创建成功并生成唯一 ID |
| A02 | 原片保护 | 输入文件 SHA-256 在任务前后完全一致；程序对输入目录无写权限或无写操作 |
| A03 | 媒体探测 | `media.json` 含时长、分辨率、帧率、视频/音频编码、采样率；字段非空且可被 JSON 解析 |
| A04 | 转写 | 生成 UTF-8 `transcript.json` 和 SRT；每段均有 `start_ms < end_ms`，区间不越过原片 |
| A05 | 专有词 | 在预先标注测试集中，指定的 20 个公司术语命中率 ≥ 90%；未达标不得进入正式试用 |
| A06 | 时间码 | 随机抽查 30 个词/句边界，人工标注与系统边界绝对误差中位数 ≤ 300ms，P95 ≤ 800ms |
| A07 | 静音 | 对预置 10 个 ≥1.2s 静音样本，检出 ≥9 个；不得自动删除 <400ms 的自然语气间隔 |
| A08 | 候选决策 | 每个删除候选含来源、起止、原因码、证据、置信度；Schema 校验 100% 通过 |
| A09 | 人工审核 | 用户可逐条接受/拒绝；拒绝后重新渲染，相关原片区间必须恢复 |
| A10 | 粗剪 | 接受的区间全部不出现在成片；拒绝的区间全部保留；允许边界容差 ±2 帧 |
| A11 | 音频切点 | 30 个切点中无爆音/明显断裂的切点 ≥ 29；用 20–50ms 淡化并人工听检 |
| A12 | 字幕 | 生成中文字幕；抽查 30 条，字幕显示区间与语音重叠率 ≥ 95%，无越界/乱码 |
| A13 | 品牌包装 | Logo、片头、片尾均出现；Logo 不超安全区；素材文件哈希与配置记录在 manifest |
| A14 | 竖屏导出 | 输出 MP4 为 1080×1920、H.264 + AAC、可由 macOS QuickTime 和指定发布测试端播放 |
| A15 | 日志 | 生成输入/输出时长、保留/删除区间、命令、退出码、版本、耗时；不记录密钥 |
| A16 | 失败恢复 | 人为终止渲染后重启，同一任务可从最近成功阶段继续；不重复 ASR |
| A17 | 性能 | 在指定验收 Mac 上，10 分钟 1080p 素材从任务开始到预览完成 ≤ 30 分钟；硬件型号写入报告 |
| A18 | 人工效率 | 5 条测试片，审核与修正平均 ≤ 原人工粗剪时间的 50%；用计时记录，不凭主观评价 |
| A19 | 回归集 | 至少 20 条代表性片段，所有确定性测试连续运行 3 次结果一致 |
| A20 | 发布隔离 | V1 无任何抖音、视频号、小红书发布凭证或自动发布调用 |

## 14. 后续版本路线图

### V1.1

- 客户案例长访谈章节/高价值观点候选；
- WhisperX 逐词对齐与说话人 A/B；
- Remotion 品牌字幕模板；
- PySceneDetect、缩略图和 OTIO/FCP XML；
- Web 波形审核与批注；
- 20–50 条回归样本和效果指标。

### V2.0

- 工厂素材库、镜头级标签/向量检索；
- 模糊/曝光/抖动/重复镜头评分；
- 人物居中与多主体裁切；
- MES/设备/看板/三色灯定制标签；
- B-roll Top-5 候选，人工选择；
- Premiere UXP 或 DaVinci 脚本适配；
- PostgreSQL/对象存储/持久队列。

### V3.0

- 目录/上传/业务系统事件触发；
- 多 Worker、资源配额、自动扩缩；
- 多版本自动生成和质检；
- 反馈学习、按栏目/人物/平台维护风格配置；
- 审批后发布（独立权限、双人确认、回滚）；
- SLA、监控、成本预算和审计。

## 15. 风险与限制

| 风险 | 后果 | 控制 |
|---|---|---|
| ASR 专有词错误 | 字幕错误、删错内容 | 公司词表、双引擎 A/B、低置信度复核 |
| 静音阈值过激 | 语气被剪碎 | 只产候选、保留 margin、听检 |
| LLM 编造时间码 | 剪错区间 | 时间码只能引用上游 ID；Schema + 区间校验 |
| 重复/口误误判 | 语义改变 | 默认 review；事实类句子强制人工 |
| B-roll 误配 | 宣传失真 | Top-K 候选 + 证据标签 + 人工确认 |
| 客户/工厂隐私 | 泄密/合规 | 本地优先、权限、脱敏、授权清单 |
| 音乐/字体/素材版权 | 下架/索赔 | 许可台账、禁用未知来源 |
| 剪映草稿变更 | 流程中断 | 非核心适配、版本固定、回归矩阵 |
| 专业软件版本升级 | 插件/API 失效 | 固定版本、兼容层、交换格式兜底 |
| 模型/API 价格变化 | 成本失控 | 可插拔 provider、预算上限、缓存 |
| 8GB Mac 资源压力 | 任务失败/卡顿 | 低并发、代理文件、分阶段处理、资源监控 |
| Codex 自主执行过宽 | 误删/越权 | 沙箱、只读输入、白名单命令、审批点 |

自动剪辑质量上限：对规则明确、语音主导、品牌模板稳定的口播，能接近“可用粗剪 + 标准包装”；对视觉叙事、品牌调性和复杂情绪，当前上限仍是“智能助理/副剪辑师”，不是导演。

## 16. 必须问题的明确答案与最终结论

1. **有没有真正成熟的 Codex 自动剪辑方案？** 没有发现能开箱稳定替代人工导演/剪辑师的成熟通用方案；有真实可运行的组件、早期框架和个人案例。
2. **Codex 直接剪还是搭系统？** 搭建并维护独立运行的系统更合适；Codex 每次直接剪适合研发和例外任务。
3. **哪个底座最好？** V1 是 FFmpeg + Python；包装用 Remotion；专业可编辑交接用 Premiere/DaVinci；剪映不做核心。
4. **如何判断删除？** 静音/VAD/ASR/重复检测产生证据，LLM 只生成候选和理由，人工确认。
5. **如何判断保留？** 信息完整度、业务关键词、观点价值、视听质量、独立可理解性、上下文依赖和人工规则联合评分。
6. **如何删除停顿、口误、重复？** 停顿可规则检测；口误和重复需 ASR + 对齐 + 语义比较 + 重录模式识别，默认可恢复候选。
7. **如何识别工厂 B-roll？** 先镜头切分和标签/向量索引，再用口播句检索 Top-K，结合对象、质量和合规过滤，由人选。
8. **如何继续人工修改？** 保存不可变原片、EDL/OTIO/FCP XML、字幕和全部决策；导入 Premiere/DaVinci 或在审核页恢复。
9. **如何批量运行？** 固定 CLI/API、任务队列、幂等阶段、内容哈希、并发配额、失败重试、缓存和 manifest。
10. **如何成为数字员工？** 常驻入口 + 持久任务状态 + Worker + 审核/升级机制 + 监控 + 可追溯日志；不是让一个聊天窗口无限运行。
11. **质量上限？** 规则化口播可高；长访谈中高；B-roll 叙事中；Vlog/品牌导演低到中。
12. **不能交给 AI 的判断？** 事实、保密、授权、品牌审美、情绪叙事、最终发布。
13. **V1 先解决什么？** 中文口播的可解释、可恢复粗剪。
14. **第一周做什么？** 收集并标注 10 条真实口播；冻结验收集；完成 ffprobe、ASR A/B、静音候选、EDL Schema 和最小 FFmpeg 渲染。
15. **最终组合？** Codex + Python + FFmpeg/ffprobe + FunASR/faster-whisper 可插拔 + SQLite + LLM JSON 决策 + Web 审核；V1.1 加 PySceneDetect、WhisperX（验证后）、Remotion、OTIO/FCP XML。

最终建议：立即批准一个“只做老板口播粗剪”的 1–2 周验证，不批准“大而全数字员工”一次性开发。只有当 20 条代表性样本通过 A01–A20，才进入方案 B。

## 17. 参考资料

完整来源元数据见 [SOURCE_LIST.md](./SOURCE_LIST.md)。最关键的原始来源：

1. [OpenAI Codex CLI](https://help.openai.com/en/articles/11096431)
2. [OpenAI Codex SDK / GA](https://openai.com/index/codex-now-generally-available/)
3. [FFmpeg Filters](https://ffmpeg.org/ffmpeg-filters.html)
4. [ffprobe](https://ffmpeg.org/ffprobe.html)
5. [Remotion](https://www.remotion.dev/)
6. [video-use](https://github.com/browser-use/video-use)
7. [FunClip](https://github.com/modelscope/FunClip)
8. [PySceneDetect](https://www.scenedetect.com/docs/latest/)
9. [Premiere UXP](https://developer.adobe.com/premiere-pro/uxp/)
10. [DaVinci Resolve Studio](https://www.blackmagicdesign.com/products/davinciresolve/studio)
