# 发布流程

## 版本号

- `v1.0.0`：视频日记首个生产稳定版。
- `v1.0.1`：兼容、不改变输出规则的缺陷修复。
- `v1.1.0`：向后兼容的视频日记能力增加。
- `v1.2.0`：工厂实拍达到可用门禁。
- `v2.0.0`：破坏性架构升级或客户案例正式上线。
- 预发布使用 `vX.Y.Z-beta.N`。

当前代码版本为 `0.10.0-beta.5`，不是 stable Release。

## stable

- 只能由 `main` 上的 `vX.Y.Z` tag 产生。
- 自动、真实样片和人工门禁全部通过。
- 必须有版本说明、已知风险、校验值和明确回滚目标。
- 生产电脑更新时必须显式指定 tag。

## beta

- 可使用 `vX.Y.Z-beta.N`。
- 允许带已记录的人工/素材门禁，但不允许隐瞒失败。
- 不作为生产电脑默认通道。

## Release 内容

- Git tag 对应源码
- macOS 双击安装 ZIP 及 SHA-256 校验文件
- `VERSION`
- `CHANGELOG.md` 对应章节
- 依赖锁、默认配置、`.env.example`
- doctor/smoke/update/rollback
- 回归 JSON/Markdown 报告
- 不包含原素材、客户素材、密钥、大模型或本机配置

## 查看更新内容

```bash
git fetch --tags origin
git log --oneline CURRENT_TAG..TARGET_TAG
git diff --stat CURRENT_TAG..TARGET_TAG
git show TARGET_TAG:CHANGELOG.md
```
