# 视频剪辑完整移植包说明

## 目标

将当前仓库中可迁移的视频剪辑程序、视频日记正式预设、工厂实拍混合路线
代码和预设、安装入口、自动测试及文档打成一个不含客户素材和登录凭证的
Mac 移植包。

## 当前固定规格

- 视频日记人声分离：开启；
- 分离方式：仅保留人声；
- 人声音量：`+10.0dB`；
- 固定 BGM：`Global Technology Background`；
- 剪映素材 ID：`7377866594003568681`；
- BGM 音量：`-8.0dB`；
- BGM 淡入、淡出：各 1 秒；
- 同步字幕必须忠实匹配最终人声，不允许总结或改写。

## 构建

```bash
./.venv/bin/python scripts/build_video_editing_full_migration_package.py
```

默认产物位于：

```text
outputs/migration/ai-video-editor-full-migration-20260728.zip
outputs/migration/ai-video-editor-full-migration-20260728.zip.sha256
```

## 新 Mac 部署

```bash
brew install python node ffmpeg
unzip ai-video-editor-full-migration-20260728.zip
cd ai-video-editor-full-migration-20260728
chmod +x DEPLOY_MACOS.sh scripts/install_macos.sh
./DEPLOY_MACOS.sh
```

部署脚本会创建本机虚拟环境、运行全部可迁移测试、严格环境检查和合成
技术样片。执行完成后还要登录剪映专业版 7.9.0，重新下载固定 BGM，并用
一条真实素材做影子测试和人工听审。

## 安全边界

移植包不会包含：

- 原素材、客户视频、成片、音频和剪映草稿；
- 剪映 BGM 缓存、账号、会员信息、Cookie、密钥或登录状态；
- `configs/local.json`、`.git`、`.venv`、`var/`、`runs/`、`outputs/`
  和大体积实验证据。

这些内容不能通过复制包代替目标电脑上的授权、素材绑定和真人验收。

## 验收边界

本机独立目录解压部署通过，只能证明包的完整性、依赖检查、程序自检和
合成渲染链路可用。另一台电脑上的真实素材播放、字幕、人声、BGM、剪映
导出和人工观感仍必须实测，未实测前保持 `NOT_REVIEWED`。
