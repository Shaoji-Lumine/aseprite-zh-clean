#!/usr/bin/env bash
#
# Aseprite 简体中文汉化 · 干净整洁版 —— macOS 一键安装脚本
#
# 用法：
#   ./scripts/install-macos.sh [Aseprite.app 路径]
#
# 默认目标是 /Applications/Aseprite.app。
# 本脚本只修改你的 Aseprite.app 内的资源文件（语言文件、字体、主题配置），
# 不包含、也不会下载 Aseprite 本体；请先自行合法获取 Aseprite。
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
APP="${1:-/Applications/Aseprite.app}"
DATA="$APP/Contents/Resources/data"

info()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn()  { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()   { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

[ -d "$APP" ] || die "找不到 $APP，请把 Aseprite.app 放到 /Applications，或用参数指定路径。"
[ -d "$DATA/strings" ] || die "这不是 Aseprite.app（缺少 Contents/Resources/data/strings）。"
[ -w "$DATA/fonts" ] || die "$APP 不可写。请把 Aseprite.app 拖到「应用程序」后重试，或用 sudo 运行本脚本。"

TS="$(date +%Y%m%d-%H%M%S)"
BACKUP="$HOME/Library/Application Support/Aseprite-zh-clean/backup-$TS"
mkdir -p "$BACKUP"

info "备份原文件到：$BACKUP"
for rel in "fonts/fonts.xml" "extensions/aseprite-theme/theme.xml" \
           "extensions/aseprite-theme/dark/theme.xml" "pref.xml"; do
  mkdir -p "$BACKUP/$(dirname "$rel")"
  cp "$DATA/$rel" "$BACKUP/$rel"
done
[ -f "$DATA/strings/zh_CN.ini" ] && cp "$DATA/strings/zh_CN.ini" "$BACKUP/strings_zh_CN.ini.bak" || true
printf '%s\n' "$APP" > "$BACKUP/app_path.txt"

info "安装语言文件 zh_CN.ini"
cp "$HERE/i18n/zh_CN.ini" "$DATA/strings/zh_CN.ini"

info "安装中文像素字体"
cp "$HERE/fonts/FusionPixel-10px-zh_hans.ttf" "$DATA/fonts/"
cp "$HERE/fonts/FusionPixel-8px-zh_hans.ttf"  "$DATA/fonts/"
cp "$HERE/fonts/OFL.txt" "$DATA/fonts/FusionPixel-OFL.txt"
[ -d "$HERE/fonts/LICENSES" ] && cp -R "$HERE/fonts/LICENSES" "$DATA/fonts/FusionPixel-LICENSES"

# ---- 注册字体 -------------------------------------------------------------
if ! grep -q 'FusionPixel-10px' "$DATA/fonts/fonts.xml"; then
  info "在 fonts.xml 中注册 Fusion Pixel 字体"
  TMPBLOCK="$(mktemp)"
  cat > "$TMPBLOCK" <<'FONT_BLOCK'
  <font name="FusionPixel-8px"
        type="truetype"
        file="FusionPixel-8px-zh_hans.ttf"
        antialias="false"
        hinting="false" />

  <font name="FusionPixel-10px"
        type="truetype"
        file="FusionPixel-10px-zh_hans.ttf"
        antialias="false"
        hinting="false" />

FONT_BLOCK
  awk -v addfile="$TMPBLOCK" '
    BEGIN { while ((getline line < addfile) > 0) add = add line "\n" }
    /<\/fonts>/ { printf "%s", add }
    { print }
  ' "$DATA/fonts/fonts.xml" > "$DATA/fonts/fonts.xml.new"
  mv "$DATA/fonts/fonts.xml.new" "$DATA/fonts/fonts.xml"
  rm -f "$TMPBLOCK"
else
  info "fonts.xml 已包含 Fusion Pixel，跳过"
fi

# ---- 主题字体：中文像素字体 / 迷你字体 ------------------------------------
info "替换主题字体（浅色 + 深色）"
for theme in "$DATA/extensions/aseprite-theme/theme.xml" \
             "$DATA/extensions/aseprite-theme/dark/theme.xml"; do
  sed -i '' -E 's#<font id="default" font="[^"]*"[^/]*/>#<font id="default" font="FusionPixel-10px" />#' "$theme"
  sed -i '' -E 's#<font id="mini" font="[^"]*"[^/]*/>#<font id="mini" font="FusionPixel-8px" size="8" mnemonics="off" />#' "$theme"
done

# ---- 默认语言 = 简体中文 --------------------------------------------------
info "设置默认语言为简体中文"
TMPPREF="$(mktemp)"
awk '
  /id="language"/ {
    match($0, /^[ \t]*/)
    indent = substr($0, 1, RLENGTH)
    printf "%s<option id=\"language\" type=\"std::string\" default=\"&quot;zh_CN&quot;\" />\n", indent
    next
  }
  { print }
' "$DATA/pref.xml" > "$TMPPREF"
mv "$TMPPREF" "$DATA/pref.xml"

# ---- 重新签名（ad-hoc），避免修改资源后签名失效 ---------------------------
if command -v codesign >/dev/null 2>&1; then
  info "重新签名（ad-hoc）"
  codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || \
    warn "重新签名失败（不影响本地运行，可稍后手动 codesign）"
fi

cat <<EOF

$(printf '\033[1;32m✓ 安装完成！\033[0m')

  1. 如果 Aseprite 正在运行，请退出并重新打开。
  2. 菜单 / 首选项 / 对话框应显示为简体中文。
  3. 若界面仍是英文：编辑 → 首选项 → 常规 → 语言 → 简体中文。

  备份目录：$BACKUP
  卸载/还原：./scripts/uninstall-macos.sh "$APP"
EOF
