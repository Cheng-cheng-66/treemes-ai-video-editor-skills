# 案例视频自动剪辑工作流

## 当前定位

`case_study` 是长案例视频工作流，主成片为5至20分钟。它不修改或继承视频日记、工厂实拍预设。

当前状态：分析与计划层 Beta 可运行；正式渲染必须经过素材选择、编辑计划和逐句字幕审核。第一条九沣开关端到端成片尚待用户确认原素材。

## 环境检查

```bash
python3 scripts/doctor_case_study.py --json
```

必须通过：

- FFmpeg、ffprobe；
- whisper.cpp `whisper-cli`；
- 本地 `ggml-small-q5_1.bin`；
- OpenCV、NumPy、SciPy、Pillow；
- OpenCV YuNet 人脸检测模型；
- `case_study` 技能发现、启用和入口检查。

## 分析一条新原素材

```bash
python3 scripts/run_case_study.py analyze \
  --job-id case_customer_001 \
  --source "/absolute/path/source.mp4" \
  --output-dir "runs/case_customer_001"
```

默认只使用本地语音识别，不把客户音频发送到外部服务。

输出：

- `job.json`：任务合同和人工审核状态；
- `reports/source_manifest.json`：来源路径、哈希和媒体身份；
- `reports/transcript.machine.json`：机器转写，不是发布字幕；
- `reports/transcript.review.csv`：逐句人工听审表；
- `reports/story_analysis.json`：七个故事单元及证据；
- `reports/visual_analysis.json`：接触表和镜头估算；
- `reports/sync_zones.json`：同步区域候选；
- `reports/quality_report.json`：当前阶段质量门槛；
- `source_contact_sheet.jpg`：20帧快速视觉预览。

## 人工成片反向学习

当同一案例存在人工标准版时：

```bash
python3 scripts/analyze_case_pair.py \
  --source "/absolute/path/long_source.mp4" \
  --reference "/absolute/path/human_reference.mp4" \
  --source-asr "runs/job/asr/source.json" \
  --reference-asr "runs/job/asr/reference.json" \
  --output-dir "runs/job"
```

再使用：

```bash
python3 scripts/align_case_audio.py \
  --source-wav "runs/job/audio/source.wav" \
  --reference-wav "runs/job/audio/reference.wav" \
  --transcript-alignment "runs/job/reports/reference_alignment.json" \
  --output "runs/job/reports/audio_alignment_dense.json" \
  --anchor-step 2 \
  --downsample-factor 2
```

这一步只学习章节重排、真实音频切点和节奏，不把人工字幕当作自动准确答案。

## 正式渲染门槛

编辑计划中的每个动作必须包含：

- 原素材入点和出点；
- 操作类型；
- 故事单元；
- 同步区域；
- 剪辑原因；
- 证据；
- 风险；
- 置信度。

未批准计划或未通过逐句字幕听审时，默认禁止正式渲染。仅调试时可以显式使用 `--draft`：

```bash
python3 scripts/run_case_study.py render \
  --plan "runs/job/edit_plan.json" \
  --output "runs/job/draft.mp4" \
  --draft
```

草稿导出不代表人工验收、发布通过或工作流 V1.0 Go。

## 字幕硬规则

- 以最终保留人声为唯一依据；
- 不总结、不改写、不润色、不替换近义词；
- 客户名、MES、三色灯、安灯、计件工资等专业词逐句复核；
- 专业词提示词只改善识别候选，不能自动替换人物原话；
- 人物说错而音频保留时，字幕仍应忠实呈现；
- 删除文字必须同步删除对应音频与画面。

## 当前九沣校准结果

- 原长版：644.447秒；
- 人工标准版：374.150秒；
- 人工版改变了章节顺序，不是单纯删停顿；
- 175个密集音频锚点中126个高置信、38个中置信、11个低置信；
- 原长版词间停顿候选214处、84.43秒；
- 人工版停顿候选85处、34.66秒；
- 工厂底噪使简单静音检测失效，因此不能用“检测到静音就剪画面”的机械规则。
