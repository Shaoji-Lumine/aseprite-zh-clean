#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把「Aseprite 简体中文汉化 · 干净整洁版」应用到 Aseprite 官方源码。

用法：
    python3 scripts/apply-to-source.py /path/to/aseprite-source

脚本会：
  1. 复制 zh_CN.ini 与中文像素字体到 data/
  2. 修改 data/fonts/fonts.xml、主题 theme.xml、data/pref.xml
  3. 汉化 macOS 原生菜单与几处硬编码报错文案
然后按官方 INSTALL.md 编译即可。

注意：本脚本只修改你自己的源码副本，不包含 Aseprite 本体。
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = sys.argv[1] if len(sys.argv) > 1 else None
if not SRC or not os.path.isdir(SRC):
    print("用法: python3 scripts/apply-to-source.py /path/to/aseprite-source")
    sys.exit(2)

DATA = os.path.join(SRC, "data")
if not os.path.isdir(os.path.join(DATA, "strings")):
    print(f"[x] {SRC} 看起来不是 Aseprite 源码目录（缺少 data/strings）")
    sys.exit(2)


def log(msg):
    print(f"\033[1;32m==>\033[0m {msg}")


def replace_once(path, old, new, required=True):
    if not os.path.isfile(path):
        if required:
            print(f"[!] 找不到文件: {path}")
        return False
    s = open(path, encoding="utf-8").read()
    if old in s:
        open(path, "w", encoding="utf-8").write(s.replace(old, new, 1))
        return True
    if new in s:
        return True
    if required:
        print(f"[!] 未匹配到内容: {path}")
    return False


# ---------------------------------------------------------------- 资源文件
log("复制语言文件与字体")
shutil.copy2(os.path.join(HERE, "i18n/zh_CN.ini"), os.path.join(DATA, "strings/zh_CN.ini"))
fonts_dir = os.path.join(DATA, "fonts")
for fn in ("FusionPixel-10px-zh_hans.ttf", "FusionPixel-8px-zh_hans.ttf"):
    shutil.copy2(os.path.join(HERE, "fonts", fn), os.path.join(fonts_dir, fn))
shutil.copy2(os.path.join(HERE, "fonts/OFL.txt"), os.path.join(fonts_dir, "FusionPixel-OFL.txt"))
if os.path.isdir(os.path.join(HERE, "fonts/LICENSES")):
    shutil.copytree(os.path.join(HERE, "fonts/LICENSES"),
                    os.path.join(fonts_dir, "FusionPixel-LICENSES"), dirs_exist_ok=True)

# ---------------------------------------------------------------- fonts.xml
log("注册 Fusion Pixel 字体 (fonts.xml)")
fonts_xml = os.path.join(fonts_dir, "fonts.xml")
s = open(fonts_xml, encoding="utf-8").read()
if "FusionPixel-10px" not in s:
    block = """
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

"""
    s = s.replace("</fonts>", block + "</fonts>")
    open(fonts_xml, "w", encoding="utf-8").write(s)

# ---------------------------------------------------------------- 主题字体
for theme in ("data/extensions/aseprite-theme/theme.xml",
              "data/extensions/aseprite-theme/dark/theme.xml"):
    p = os.path.join(SRC, theme)
    s = open(p, encoding="utf-8").read()
    s = re.sub(r'<font id="default" font="[^"]*"[^/]*/>',
               '<font id="default" font="FusionPixel-10px" />', s)
    s = re.sub(r'<font id="mini" font="[^"]*"[^/]*/>',
               '<font id="mini" font="FusionPixel-8px" size="8" mnemonics="off" />', s)
    open(p, "w", encoding="utf-8").write(s)
log("替换主题字体（浅色 + 深色）")

# ---------------------------------------------------------------- 默认语言
log("设置 data/pref.xml 默认语言为 zh_CN")
replace_once(os.path.join(DATA, "pref.xml"),
             '<option id="language" type="std::string" default="&quot;en&quot;" />',
             '<option id="language" type="std::string" default="&quot;zh_CN&quot;" />')

# ---------------------------------------------------------------- macOS 菜单
log("汉化 macOS 原生菜单")
app_menus = os.path.join(SRC, "src/app/app_menus.cpp")
menu_map = [
    ('fmt::format("About {}", get_app_name())', 'fmt::format("关于 {}", get_app_name())'),
    ('os::MenuItemInfo preferences("Preferences...")', 'os::MenuItemInfo preferences("设置…")'),
    ('fmt::format("Hide {}", get_app_name())', 'fmt::format("隐藏 {}", get_app_name())'),
    ('fmt::format("Quit {}", get_app_name())', 'fmt::format("退出 {}", get_app_name())'),
    ('os::MenuItemInfo("Hide Others", os::MenuItemInfo::HideOthers)', 'os::MenuItemInfo("隐藏其他", os::MenuItemInfo::HideOthers)'),
    ('os::MenuItemInfo("Show All", os::MenuItemInfo::ShowAll)', 'os::MenuItemInfo("全部显示", os::MenuItemInfo::ShowAll)'),
    ('os::MenuItemInfo minimize("Minimize", os::MenuItemInfo::Minimize)', 'os::MenuItemInfo minimize("最小化", os::MenuItemInfo::Minimize)'),
    ('os::MenuItemInfo("Zoom", os::MenuItemInfo::Zoom)', 'os::MenuItemInfo("缩放", os::MenuItemInfo::Zoom)'),
    ('os::MenuItemInfo("Window")', 'os::MenuItemInfo("窗口")'),
]
for old, new in menu_map:
    replace_once(app_menus, old, new, required=False)

# ---------------------------------------------------------------- 报错文案
log("汉化控制台报错文案")
replace_once(os.path.join(SRC, "src/app/console.cpp"),
             'text = "There is not enough memory to complete the action.";',
             'text = "内存不足，无法完成该操作。";', required=False)
replace_once(os.path.join(SRC, "src/app/console.cpp"),
             'fmt::format("A problem has occurred.\\n\\nDetails:\\n{}\\n", e.what())',
             'fmt::format("出现问题。\\n\\n详细信息：\\n{}\\n", e.what())', required=False)
replace_once(os.path.join(SRC, "src/app/commands/filters/filter_worker.cpp"),
             '"A problem has occurred.\\n\\nDetails:\\n%s"',
             '"出现问题。\\n\\n详细信息：\\n%s"', required=False)
replace_once(os.path.join(SRC, "src/app/cli/default_cli_delegate.cpp"),
             '"Error executing script %s"', '"执行脚本时出错：%s"', required=False)

print("""
\033[1;32m✓ 源码汉化应用完成！\033[0m

接下来按官方 INSTALL.md 编译（需要 Skia）：
  export SKIA_DIR=~/deps/skia
  cd <source>
  cmake -B build -S . -G Ninja -DCMAKE_BUILD_TYPE=Release \\
        -DLAF_BACKEND=skia -DSKIA_DIR="$SKIA_DIR" \\
        -DSKIA_LIBRARY_DIR="$SKIA_DIR/out/Release-arm64"
  cmake --build build --target aseprite -j 8

Skia 预编译包：https://github.com/aseprite/skia/releases
""")
