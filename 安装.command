#!/bin/zsh
set -eu

SOURCE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
CODEX_BASE=${CODEX_HOME:-"$HOME/.codex"}
DEST_PARENT="$CODEX_BASE/skills"
DEST="$DEST_PARENT/ai-video-editing-skills"
SKILL_NAME="ai-video-editing-skills"
BACKUP=""
STAGING_ROOT=""

pause_before_exit() {
  if [ "${AI_VIDEO_SKILL_NONINTERACTIVE:-0}" != "1" ]; then
    printf "\n按回车键关闭窗口..."
    read -r _answer
  fi
}

fail() {
  printf "\n安装失败：%s\n" "$1" >&2
  pause_before_exit
  exit 1
}

cleanup() {
  if [ -n "$STAGING_ROOT" ] && [ -d "$STAGING_ROOT" ]; then
    case "$STAGING_ROOT" in
      "$DEST_PARENT"/.ai-video-editing-skills.install.*)
        rm -rf -- "$STAGING_ROOT"
        ;;
    esac
  fi
}
trap cleanup EXIT HUP INT TERM

for required in SKILL.md VERSION core presets scripts agents/openai.yaml; do
  if [ ! -e "$SOURCE_DIR/$required" ]; then
    fail "安装包不完整，缺少 $required。请重新下载完整 ZIP。"
  fi
done

if [ "$(basename -- "$DEST_PARENT")" != "skills" ]; then
  fail "目标目录校验失败：$DEST_PARENT"
fi
if [ "$(basename -- "$DEST")" != "$SKILL_NAME" ]; then
  fail "目标 Skill 名称校验失败：$DEST"
fi
if [ -L "$DEST" ]; then
  fail "目标路径是符号链接，为避免覆盖错误目录，已停止安装。"
fi

mkdir -p -- "$DEST_PARENT"
STAGING_ROOT=$(mktemp -d "$DEST_PARENT/.ai-video-editing-skills.install.XXXXXX")
STAGED_SKILL="$STAGING_ROOT/$SKILL_NAME"

printf "正在安装 AI 视频剪辑 Skill...\n"
if command -v ditto >/dev/null 2>&1; then
  ditto --norsrc "$SOURCE_DIR" "$STAGED_SKILL"
else
  cp -R "$SOURCE_DIR" "$STAGED_SKILL"
fi
chmod +x "$STAGED_SKILL/安装.command" "$STAGED_SKILL/scripts/install_macos.sh"

if [ -e "$DEST" ]; then
  timestamp=$(date +%Y%m%d-%H%M%S)
  BACKUP="${DEST}.backup-${timestamp}"
  counter=1
  while [ -e "$BACKUP" ]; do
    BACKUP="${DEST}.backup-${timestamp}-${counter}"
    counter=$((counter + 1))
  done
  mv -- "$DEST" "$BACKUP"
fi

if ! mv -- "$STAGED_SKILL" "$DEST"; then
  if [ -n "$BACKUP" ] && [ -e "$BACKUP" ] && [ ! -e "$DEST" ]; then
    mv -- "$BACKUP" "$DEST"
  fi
  fail "无法启用新 Skill，旧版本已尝试恢复。"
fi

printf "\n安装成功。\n"
printf "安装位置：%s\n" "$DEST"
if [ -n "$BACKUP" ]; then
  printf "旧版本备份：%s\n" "$BACKUP"
fi

if [ "${AI_VIDEO_SKILL_SKIP_DOCTOR:-0}" = "1" ]; then
  printf "环境检查：已跳过（测试模式）。\n"
elif command -v python3 >/dev/null 2>&1; then
  printf "\n正在检查剪辑环境...\n"
  if python3 "$DEST/scripts/doctor.py" --strict; then
    printf "环境检查：通过。\n"
  else
    printf "\n提示：Skill 已安装，但本机剪辑依赖尚未全部就绪。\n"
    printf "重新打开 Codex 后，它会根据检查结果继续配置。\n"
  fi
else
  printf "环境检查：未找到 Python 3；Skill 已安装，后续由 Codex 完成配置。\n"
fi

printf "\n下一步：重新打开 Codex，上传原素材并说明“视频日记”“工厂实拍”或“客户案例”。\n"
pause_before_exit
