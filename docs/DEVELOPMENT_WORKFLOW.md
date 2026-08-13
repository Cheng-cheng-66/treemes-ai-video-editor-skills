# 开发流程

## 分支

- `main`：只包含已满足 Release 门禁的版本。
- `develop`：集成已验证的开发变更。
- `feature/video-diary-*`
- `feature/factory-shoot-*`
- `feature/case-study-*`

生产电脑默认只使用 `main` 和 stable tag，不自动跟随 `develop`。

## 每次变更

1. 从 `develop` 建场景对应 feature。
2. 先写失败测试，再做最小实现。
3. Core 或视频日记变更必须执行：

   ```bash
   python3 scripts/doctor.py
   python3 -m unittest discover -s tests -v
   python3 scripts/smoke_test.py
   python3 scripts/regression.py
   ```

4. 报告中的 `FAIL` 必须清零；`MANUAL_REVIEW_REQUIRED` 必须由指定人员完成并记录证据。
5. 合并到 `develop` 前检查 Skill 边界、无密钥、无媒体、无本机绝对路径。

## 合并到 main 的条件

- standard、complex、abnormal 固定测试集齐全。
- 自动检查全部 PASS。
- 逐字字幕、音画同步、误删人声、降噪损伤、BGM、人眼标题检查完成。
- 原素材哈希前后不变。
- CHANGELOG/Release notes、迁移说明、回滚目标齐全。
- 至少一次在干净环境执行 bootstrap、doctor、技术样片和真实标准样片。
- 无未说明的高风险项。

未达到上述条件的提交只能停留在 feature/develop 或 beta。
