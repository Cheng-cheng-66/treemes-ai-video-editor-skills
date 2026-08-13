# 跨电脑迁移指南

## 原电脑准备

1. 确认工作分支和状态：

   ```bash
   git status
   git branch --show-current
   python3 scripts/doctor.py
   python3 -m unittest discover -s tests -v
   python3 scripts/smoke_test.py
   python3 scripts/regression.py
   ```

2. 只把源码、规则、测试和文档推送到有权限的私有仓库。当前任务只建立本地 Git，没有擅自创建远程仓库。
3. 单独盘点并复制以下非 Git 数据：

   - 原始素材
   - 已批准成片和 QC 证据
   - 需要的模型
   - 合法字体或替代字体
   - `configs/local.json`

4. 对复制包生成 SHA-256 清单。大型资源使用外接盘、受控文件服务器或对象存储，不放普通 Git。
5. 外接盘开始长任务前先验证挂载和源文件可读；具体挂载路径只能写入本机配置或环境变量。

## 新电脑安装

1. 安装 Git、Python 3.11+、Node.js、FFmpeg/ffprobe。
2. 从私有仓库只克隆 `main` 或明确的正式 Release；不要默认使用 `develop`。
3. macOS 执行：

   ```bash
   ./scripts/install_macos.sh
   ```

   Windows PowerShell 执行：

   ```powershell
   .\scripts\install_windows.ps1
   ```

4. 编辑未跟踪的 `configs/local.json`，至少确认 `data_root`。
5. 将素材和模型放进数据根下的 `inputs/`、`models/`，或用环境变量指向受控位置。
6. 执行：

   ```bash
   python3 scripts/doctor.py --strict
   python3 scripts/smoke_test.py
   ```

## 全量验收

设置标准样片原素材：

```bash
export VIDEO_DIARY_STANDARD_SOURCE=/mounted/read-only/source.mov
python3 scripts/regression.py
```

新电脑还必须补齐复杂样片和异常样片，人工复核逐字字幕、音画同步、有效人声、降噪损伤、封面/正文标题状态后，才能在 `docs/NEW_COMPUTER_ACCEPTANCE.md` 中判定为生产可用。

## 常见错误

- `source media not found`：检查挂载点和 `edit_plan.json` 的本机源路径。
- `missing configured fonts`：在 `configs/local.json` 选择/覆盖新电脑字体，不要改业务代码。
- `ffmpeg/node not available`：安装系统依赖并重开终端。
- 字幕超宽：调整字幕事件切分，不允许自动缩小、双行或改写。
- 磁盘空间不足：先扩容或更换数据根，不删除现有素材/成片来“通过”检查。
