#!/bin/sh
# ============================================================
#  华夏千年历史长卷 · iPad 本机离线服务（a-Shell 用）
# ------------------------------------------------------------
#  用法（a-Shell 内，只需两步）：
#    1) cd ~/Documents             # 进入放了本脚本和两个 html 的目录
#    2) sh 启动.sh                  # 启动服务
#  然后切到 Safari 打开：http://localhost:8080/chinese-dynasty.html
#
#  提示：
#   · a-Shell 请用「侧拉」缩成右侧小窗，与 Safari 同屏，服务就不会被系统挂起
#   · 两个 html 必须与本脚本在同一目录（jiangshan-atlas.html 不能少）
#   · 完全不需要联网，脚本只做一件事：把本地文件夹变成 http 地址
# ============================================================

DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR" || exit 1

PORT=8080
PAGE=chinese-dynasty.html

if [ ! -f "$PAGE" ]; then
  echo ""
  echo "  [X] 当前目录找不到 $PAGE"
  echo "      当前目录：$DIR"
  echo "      请把本脚本和两个 html 放在同一个文件夹里。"
  echo ""
  exit 1
fi

if [ ! -f "jiangshan-atlas.html" ]; then
  echo ""
  echo "  [!] 缺少 jiangshan-atlas.html —— 长卷能看，但「疆域图谱」页会打不开。"
  echo ""
fi

echo ""
echo "  ============================================"
echo "   历史长卷 · 离线服务已启动"
echo "  ============================================"
echo "   目录：$DIR"
echo "   地址：http://localhost:$PORT/$PAGE"
echo ""
echo "   在 Safari 打开上面的地址，"
echo "   再点「分享 → 添加到主屏幕」即可全屏使用。"
echo "   停止服务：按 Ctrl + C（或关闭 a-Shell）"
echo "  ============================================"
echo ""

exec python3 -m http.server "$PORT" --bind 127.0.0.1
