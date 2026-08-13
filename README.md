# AI Video Editing Skills

可迁移的 AI 自动剪辑底座与三个相互隔离的场景 Skill。当前版本为
`0.10.0-beta.1`，只发布代码、配置、合成示例和质量规则，不包含任何真实素材。

## 当前支持与真实成熟度

| Skill | 状态 | Enabled | 当前边界 |
|---|---|---:|---|
| `video_diary` | Beta | 是 | 可运行；自动技术检查通过不等于人工听看通过 |
| `factory_shoot` | Planned / Experimental | 否 | 产品宣发归入此类型；混合路线预设和规则可读，暂无生产入口 |
| `case_study` | Beta analysis | 是 | 分析、同步区和故事计划可运行；正式渲染仍需首条案例验收 |

`factory_demo`、工厂实拍和产品宣发是同一业务类别。仓库保留实际目录名
`factory_shoot`，不重复创建同义 Skill。

## 架构

```text
core/                 公共配置、进程、QC、Skill发现和发布策略
skills/               场景Skill；禁止相互导入
presets/              场景预设与质量规则
schemas/              可机读任务与manifest约束
scripts/              安装、doctor、运行、更新和回滚
tests/                单元、边界、兼容和发布包测试
templates/            不含媒体的模板说明
```

原素材始终只读。运行输入、输出、缓存、日志和模型默认进入 `var/`，全部位于
Git 之外。

## 安装

需要 Python 3.11+、Node.js、FFmpeg 和 ffprobe。macOS：

```bash
./scripts/install_macos.sh
./.venv/bin/python scripts/doctor.py --strict
```

Windows PowerShell：

```powershell
.\scripts\install_windows.ps1
.\.venv\Scripts\python.exe scripts\doctor.py --strict
```

`bootstrap` 会安装 `requirements.lock`、建立本机运行目录并执行测试。模型、
剪映、BGM权益和客户素材不会随仓库安装。

## 使用

视频日记：

```bash
./.venv/bin/python scripts/run_video_diary.py \
  --plan skills/video_diary/examples/edit_plan.json \
  --captions skills/video_diary/examples/verbatim_captions.json \
  --output var/outputs/video_diary.mp4 \
  --date 2026/08/06 \
  --day Day18
```

未显式指定画幅时继承源素材：横屏输出16:9，竖屏输出9:16；跨画幅转换需要
明确授权。

客户案例分析：

```bash
./.venv/bin/python scripts/run_case_study.py analyze \
  --job skills/case_study/examples/job.json
```

工厂实拍当前 `enabled=false`，不得绕过 manifest 强行当作无人值守生产入口。
同步区、四轨资产和剪映混合路线见
[`skills/factory_shoot/SKILL.md`](skills/factory_shoot/SKILL.md)。

## 三类工作流

### 视频日记

素材探测 → 源画幅继承 → 气口判断 → 封面 → 正文常驻标题 → 逐字字幕 →
渲染 → 自动QC → 人工听看。字幕禁止总结、润色或替换人物原话。剪映音频
规范为仅保留人声、`+10 dB`，固定BGM初始音量 `-8 dB`；实际使用前仍需
确认账号权益、峰值和人工听感。

### 工厂实拍／产品宣发

长素材主题拆分和完整叙事优先。使用 `A_SYNC_LOCKED`、`B_SYNC_FLEX`、
`C_AUDIO_FREE`、`D_ACTION_LOCKED` 区分口型、画外音和操作动作。当前可发布
的是规则、预设与质量门禁；可执行入口仍为 disabled，不宣称生产就绪。

### 客户案例

按问题—方案—实施—结果拆解长视频，保留客户事实和数字证据；支持同步区、
停顿和章节计划、中英文字幕及MES术语表。授权、事实、故事完整性、英文语境
和最终导演判断必须人工审核。

## 质量与人工门禁

```bash
./.venv/bin/python scripts/doctor.py --strict
./.venv/bin/python -m unittest discover -s tests -v
./.venv/bin/python scripts/smoke_test.py
```

自动检查覆盖依赖、manifest、边界、画幅、字幕安全区、合成渲染和完整解码。
以下内容不能由自动测试伪造为通过：逐句人声/字幕一致、专业词、口型、吞字、
BGM听感、工厂连续性、客户事实、授权和最终叙事。未审核字段必须保持 `null`、
`NOT_REVIEWED` 或 `MANUAL_REVIEW_REQUIRED`。

## 输入与输出

- 输入：通过命令参数、本机配置或环境变量提供；禁止写进仓库。
- 输出：默认 `var/outputs/`；`outputs/`、`runs/`、`logs/` 也被Git忽略。
- 示例：只允许合成JSON/文本，不包含客户、人物或正式媒体。

## 更新与回滚

```bash
./.venv/bin/python scripts/update.py --help
./.venv/bin/python scripts/rollback.py --help
```

生产电脑必须显式选择版本。Beta 不作为 stable 自动更新目标；更新失败应保留
旧版本并执行回滚检查。详见
[`docs/UPDATE_AND_ROLLBACK.md`](docs/UPDATE_AND_ROLLBACK.md)。

## 已知限制

- `video_diary` 仍需每条成片人工完整听看。
- `factory_shoot` manifest 为 `planned + disabled`。
- `case_study` 尚未完成首条正式渲染验收。
- 剪映GUI、版本、登录、会员和素材可用性无法由纯代码仓库保证。
- 真实模型与测试素材不随仓库分发。

## 隐私与安全

禁止提交原素材、成片、音频、客户图片、客户名称、剪映草稿、模型、缓存、
日志、Cookie、Token、密钥、本机配置和用户绝对路径。发布前运行
`scripts/validate_github_release.py`，并对暂存清单再次人工复核。

## 版本策略

- `vX.Y.Z-beta.N`：允许已记录的人工门禁，但不得隐藏自动测试失败。
- `vX.Y.Z`：仅在自动、真实样片和人工门禁全部通过后使用。
- 当前版本：`0.10.0-beta.1`，GitHub Release 必须标记 Pre-release。

本仓库的授权状态见 [`LICENSE_STATUS.md`](LICENSE_STATUS.md)。
