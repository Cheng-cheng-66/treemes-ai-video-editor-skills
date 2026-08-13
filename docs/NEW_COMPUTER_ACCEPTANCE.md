# 新电脑生产验收

结果只能填写 `PASS`、`FAIL` 或 `MANUAL_REVIEW_REQUIRED`。

| 验收项 | 当前结果 | 证据/阻断 |
|---|---|---|
| 从正式 stable Release 安装 | FAIL | 尚未创建 v1.0.0 |
| Python/Node/FFmpeg/ffprobe | MANUAL_REVIEW_REQUIRED | 必须在新电脑运行 doctor |
| 本机配置与数据目录 | MANUAL_REVIEW_REQUIRED | 必须在新电脑确认 |
| 字体 | MANUAL_REVIEW_REQUIRED | Windows/macOS 字体需实机验证 |
| 模型路径 | PASS | 当前视频日记不要求外部模型 |
| Skill 可加载 | MANUAL_REVIEW_REQUIRED | 原电脑 doctor PASS；新电脑待测 |
| 合成技术样片 | MANUAL_REVIEW_REQUIRED | 原电脑 PASS；新电脑待测 |
| 标准真实样片 | MANUAL_REVIEW_REQUIRED | 原素材未挂载 |
| 复杂样片 | FAIL | 固定样片缺失 |
| 异常样片 | FAIL | 固定样片缺失 |
| 逐字字幕 | MANUAL_REVIEW_REQUIRED | 需听审 |
| 字幕安全区 | MANUAL_REVIEW_REQUIRED | 自动结构 PASS，实机成片需看帧 |
| 封面/正文顶部状态 | MANUAL_REVIEW_REQUIRED | 模板哈希一致，实机播放待审 |
| 音画同步/误删人声 | MANUAL_REVIEW_REQUIRED | 需实机播放 |
| 日志和 QC | MANUAL_REVIEW_REQUIRED | 新电脑任务待生成 |
| 原素材不变 | MANUAL_REVIEW_REQUIRED | 需记录前后 SHA-256 |
| 更新与回滚演练 | MANUAL_REVIEW_REQUIRED | stable tag 后执行 |

当前结论：**FAIL — 不具备宣布正式生产迁移成功的证据**。
