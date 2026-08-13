# 更新与回滚

## 更新

生产电脑不使用“自动最新”。每次由管理员指定已审核 tag：

```bash
python3 scripts/update.py --target v1.0.1 --channel stable --fetch --dry-run
python3 scripts/update.py --target v1.0.1 --channel stable --fetch
```

更新脚本会：

1. 拒绝脏工作区。
2. 验证目标是当前通道允许的语义化 tag。
3. 记录当前 commit。
4. 备份 `configs/local.json` 到数据根 `backups/`。
5. 切换目标 commit。
6. 恢复本机配置。
7. 运行严格 doctor、完整单元测试和合成技术样片。
8. 失败时切回旧 commit 并记录原因。

素材、成片、缓存、日志和模型位于 Git 外，不随代码更新切换。

## 回滚

查看记录：

```bash
python3 scripts/rollback.py --list
```

预演和执行：

```bash
python3 scripts/rollback.py --reason "v1.0.1 subtitle timing regression" --dry-run
python3 scripts/rollback.py --reason "v1.0.1 subtitle timing regression"
```

脚本从 `release_history.json` 选择上一成功版本，切换后执行严格 doctor。失败会恢复回滚前 commit。本机配置和数据不删除。

## 限制

首个 stable 发布前没有可用的生产更新/回滚链。当前本地的 `pre-modularization-20260725` 是开发迁移安全标签，不是生产 Release。
