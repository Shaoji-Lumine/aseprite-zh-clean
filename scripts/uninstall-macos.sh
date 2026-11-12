#!/usr/bin/env bash
#
# 还原 Aseprite 原版资源（卸载汉化）
#
# 用法：
#   ./scripts/uninstall-macos.sh [Aseprite.app 路径]
#
# 会从 ~/Library/Application Support/Aseprite-zh-clean/ 里最近一次备份还原。
#
set -euo pipefail

APP="${1:-/Applications/Aseprite.app}"
DATA="$APP/Contents/Resources/data"
ROOT="$HOME/Library/Application Support/Aseprite-zh-clean"

info()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
die()   { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[ -d "$APP" ] || die "找不到 $APP"
[ -d "$DATA/strings" ] || die "这不是 Aseprite.app"
[ -d "$ROOT" ] || die "没有找到汉化备份目录：$ROOT"

BACKUP="$(ls -1d "$ROOT"/backup-* 2>/dev/null | sort | tail -1 || true)"
[ -n "$BACKUP" ] || die "没有可用备份"

info "使用备份：$BACKUP"
for rel in "fonts/fonts.xml" "extensions/aseprite-theme/theme.xml" \
           "extensions/aseprite-theme/dark/theme.xml" "pref.xml"; do
  [ -f "$BACKUP/$rel" ] && cp "$BACKUP/$rel" "$DATA/$rel"
done

rm -f "$DATA/strings/zh_CN.ini"
rm -f "$DATA/fonts/FusionPixel-10px-zh_hans.ttf" \
      "$DATA/fonts/FusionPixel-8px-zh_hans.ttf" \
      "$DATA/fonts/FusionPixel-OFL.txt"
rm -rf "$DATA/fonts/FusionPixel-LICENSES"

if command -v codesign >/dev/null 2>&1; then
  codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || true
fi

info "已还原 Aseprite 原版。重新打开 Aseprite 即可（如语言仍残留，首选项里切回 English）。"
