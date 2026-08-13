# V1.0.0 发布验收目录

本目录只用于 `release/v1.0.0` 的发布验收准备，不改变剪辑算法、视觉模板或场景启用状态。

```text
acceptance/
├── standard/              标准真实样片登记
├── complex/               复杂真实样片要求和候选登记
├── abnormal/              异常真实样片/故障注入要求
├── reports/               自动检查原始日志与汇总
├── ACCEPTANCE_MATRIX.md   自动与人工验收矩阵
└── acceptance_schema.json 机器可校验的结果 Schema
```

## 证据原则

- 合成技术样片只能证明渲染链可运行，不能替代真实发布验收。
- 未执行的人工检查一律使用 `NOT_REVIEWED`，不得写成 `PASS` 或 `0`。
- 原素材未挂载时，SHA-256、ffprobe、只读状态和真实回归均保持 `BLOCKED`/空值。
- `standard`、`complex`、`abnormal` 三类真实样片和全部人工审核完成前，不允许创建 `v1.0.0-rc.1`。
- 本目录不得存放原始视频、客户私密素材、密钥或大型模型。

## 执行

```bash
python3 acceptance/run_acceptance_checks.py
```

命令会保存 bootstrap、严格 doctor、12 项自动测试、合成技术样片、现有基线回归、更新预演和回滚列表日志。标准原素材未挂载时，只生成明确的阻断记录。
