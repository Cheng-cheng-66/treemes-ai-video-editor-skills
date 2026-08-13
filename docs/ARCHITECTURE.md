# 架构

## 总体结构

```text
core/                         共用编排底座
skills/
  video_diary/                视频日记专属规则与兼容渲染器
  factory_shoot/              工厂实拍边界（未启用）
  case_study/                 客户案例 Beta 分析入口
presets/                      可版本化场景规则
configs/default.json          可版本化默认配置
configs/local.json            本机配置，不进入 Git
scripts/                      安装、诊断、运行、回归、更新、回滚
tests/                        单元、边界与兼容测试
var/                          默认本机数据根目录，不进入 Git
```

## Core 职责

- `core.config`：合并默认、本机和环境变量配置；把输入、输出、缓存、日志、模型目录解析到本机数据根。
- `core.skills`：发现 manifest、加载入口、检测跨 Skill 导入。
- `core.process`：外部命令探测与受控执行。
- `core.qc`：统一 `PASS`、`FAIL`、`MANUAL_REVIEW_REQUIRED` 结果和媒体探测。
- `core.release`：版本通道校验、Git 状态、更新历史。

Core 不包含视频日记标题规则、工厂镜头分类或客户案例叙事规则。

## 数据流

```text
本机配置/环境变量
        ↓
Python CLI → Skill manifest → video_diary runner
        ↓                       ↓
路径/依赖校验             V5 兼容渲染器
                                ↓
                         FFmpeg / ffprobe
                                ↓
                    成片 + 日志 + QC/回归报告
```

`edit_plan.json` 继续作为可复核的剪辑时间线来源；逐字字幕是独立输入。原素材只读，输出进入本机数据目录。

## 依赖方向

- `scripts → core + 单个目标 Skill`
- `skills/* → core`
- `skills/video_diary → 自己的 legacy renderer`
- 禁止 `skills/A → skills/B`
- 禁止 Core 反向导入任何 Skill

## 兼容策略

当前接受的 Node/FFmpeg V5 渲染算法被收进 `skills/video_diary/legacy/`。Python 只参数化日期、Day、字体、工作目录和报告目录；默认值保持旧版。macOS 封面和正文顶部模板的回归哈希与迁移前一致。

全量 Python 重写必须作为独立 feature，在同一固定测试集上证明输出差异可接受后才能替换 legacy。
