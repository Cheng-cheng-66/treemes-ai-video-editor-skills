# 当前状态

## 本次任务目标

系统、真实、可验证地调研如何以 OpenAI Codex 为主要开发、执行或编排工具搭建自动视频剪辑系统，并为老板口播、工厂现场、客户案例和 Vlog 给出技术决策、V1 范围与验收标准。

## 已完成内容

- [x] 完整读取任务与禁止事项；
- [x] 建立中英文关键词与来源分级；
- [x] 搜索 Codex 官方资料、FFmpeg/Remotion/MoviePy/PySceneDetect 官方资料；
- [x] 检查 10+ 开源项目的仓库、安装、Release/Issue/限制；
- [x] 检查 Premiere UXP、DaVinci、剪映/CapCut 自动化证据；
- [x] 对比 5+ 商业 AI 剪辑产品；
- [x] 区分 A 类 Codex 核心、B 类 Codex 搭建后独立运行、C 类普通 AI 工具；
- [x] 形成 3 套完整架构；
- [x] 针对四类公司场景给出自动化边界；
- [x] 形成 V1 功能、不做项、20 条可判定验收标准；
- [x] 生成要求的 5 个 Markdown 文件。

## 未完成内容

- [ ] 未克隆并本地运行全部开源项目；
- [ ] 未用公司真实视频执行 FunASR vs faster-whisper A/B；
- [ ] 未测试当前公司 Mac 的 10 分钟素材处理耗时；
- [ ] 未验证当前安装版本的剪映草稿兼容性；
- [ ] 未验证 Premiere/DaVinci 的公司许可证和实际版本；
- [ ] 未建立工厂设备/MES/三色灯镜头标注集；
- [ ] 未开发任何完整自动剪辑系统（符合本次“先调研、不立即开发”的要求）。

## 调研日期

2026-07-23（Asia/Shanghai）

## 搜索过的平台

- 官方：OpenAI、FFmpeg、Remotion、MoviePy、PySceneDetect、Adobe、Blackmagic Design、CapCut；
- 代码与模型：GitHub、Hugging Face；
- 英文社区：Reddit、Hacker News、DEV、Medium、YouTube；
- 中文平台：Bilibili、知乎、抖音、掘金、CSDN；
- 学术：arXiv。

说明：YouTube、Medium、CSDN 本轮没有筛出优于官方文档/官方仓库的关键原始证据，未用于支撑核心结论。

## 找到的有效来源数量

- 纳入 `SOURCE_LIST.md`：54 条；
- A 级官方/原始来源：40 条；
- 深入比较的开源项目：11 个；
- 商业产品/专业产品：6 个以上；
- 可被 Codex 调用的成熟底层工具：FFmpeg/ffprobe、faster-whisper/FunASR、PySceneDetect、Remotion、MoviePy 等。

## 当前推荐结论

1. 没有发现成熟、通用、开箱即用、能稳定替代人工导演/剪辑师的“Codex 自动剪辑”方案。
2. Codex 最适合搭建、维护和诊断独立运行的自动剪辑系统，不适合成为每个生产任务不可替代的唯一运行时。
3. V1 以 Python + FFmpeg/ffprobe 为底座。
4. 中文 ASR 不预设赢家：FunASR/Paraformer 与 faster-whisper 必须用公司真实口播 A/B。
5. 所有语义删除默认是可恢复候选；人工审核是硬门。
6. V1 只做老板口播可解释粗剪；V1.1 加客户案例长转短与 Remotion；V2 做工厂 B-roll 检索；V3 才做数字员工。
7. 剪映/CapCut 只作为可选人工精修/适配层，不作为核心时间线真相源。

## 仍需验证的问题

1. 公司术语在 FunASR/Paraformer 与 faster-whisper 上的字错率、时间码和速度；
2. 8GB Mac 的模型/FFmpeg 并发和代理文件策略；
3. 老板说话习惯中“重复强调”与“重录”能否被稳定区分；
4. 运营人员愿意接受的审核交互和单条耗时；
5. 品牌字幕、Logo、安全区、片头片尾的正式规范；
6. 音乐、字体、客户画面授权台账；
7. 专业续编最终选 Premiere 还是 DaVinci；
8. 若坚持剪映交接，需要固定版本矩阵和每次升级回归；
9. 工厂 B-roll 的标签体系、敏感区和至少 200–500 个镜头的标注集；
10. 云 API 数据是否允许上传客户/工厂内容。

## 下一步建议

### 立即执行（第 1 周）

1. 选 10 条真实老板口播，总时长不少于 60 分钟；
2. 复制到独立测试目录并计算哈希，不在原素材上操作；
3. 人工标注术语、静音、重录、保留/删除；
4. A/B 测试 FunASR/Paraformer 与 faster-whisper；
5. 冻结 20 条代表性回归片段和验收标准；
6. 只实现 ingest、ffprobe、转写、静音候选、EDL JSON、最小 FFmpeg 预览；
7. 一周末做 Go/No-Go 评审，不提前扩展到 B-roll、Remotion 或发布。

### 决策门

- 如果术语/时间码和人工节省不达标：先修数据/ASR/审核，不扩功能；
- 如果通过：进入 V1 第二周，补恢复、字幕、品牌包装、日志和中断重试；
- 只有 20 条回归与 5 条完整片对照达标，才批准 V1.1。
