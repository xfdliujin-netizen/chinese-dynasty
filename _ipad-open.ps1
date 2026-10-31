$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$port = 8080
$page = 'chinese-dynasty.html'

Write-Host ''
Write-Host '  ============================================' -ForegroundColor DarkGray

if (-not (Test-Path (Join-Path $root $page))) {
  Write-Host '  [X] 当前文件夹里找不到 chinese-dynasty.html' -ForegroundColor Red
  Write-Host '      请把本工具和两个 html 文件放在同一个文件夹里。' -ForegroundColor Gray
  Write-Host ''
  Read-Host '  按回车关闭'
  exit 1
}

# 自动探测可用的 Python（跳过 Microsoft Store 的占位 stub）
$py = $null
$cands = @()
$cands += Get-ChildItem "$env:USERPROFILE\.workbuddy\binaries\python\versions" -Directory -ErrorAction SilentlyContinue | ForEach-Object { Join-Path $_.FullName 'python.exe' }
$cands += Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Directory -ErrorAction SilentlyContinue | ForEach-Object { Join-Path $_.FullName 'python.exe' }
$cands += 'C:\Python313\python.exe','C:\Python312\python.exe','C:\Python311\python.exe','C:\Python310\python.exe'
foreach ($c in $cands) { if (Test-Path $c) { $py = $c; break } }
if (-not $py) {
  $where = & where.exe python 2>$null
  if ($where) { $py = $where | Where-Object { $_ -notlike '*WindowsApps*' } | Select-Object -First 1 }
}
if (-not $py -or -not (Test-Path $py)) {
  Write-Host '  [X] 没有检测到 Python' -ForegroundColor Red
  Write-Host '      请先安装 Python，或在「Microsoft Store」搜索 Python 安装。' -ForegroundColor Gray
  Write-Host ''
  Read-Host '  按回车关闭'
  exit 1
}

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
  Select-Object -First 1).IPAddress

if (-not $ip) {
  Write-Host '  [!] 没找到局域网地址，请确认电脑已连上 Wi-Fi' -ForegroundColor Yellow
  $ip = '127.0.0.1'
}

Write-Host '  历史长卷 · iPad 访问服务已启动' -ForegroundColor Green
Write-Host '  ============================================' -ForegroundColor DarkGray
Write-Host ''
Write-Host '  1) 让 iPad 连上同一个 Wi-Fi' -ForegroundColor Gray
Write-Host '  2) 在 iPad 的 Safari 地址栏输入：' -ForegroundColor Gray
Write-Host ''
Write-Host ('       http://' + $ip + ':' + $port + '/' + $page) -ForegroundColor Cyan
Write-Host ''
Write-Host '  3) 打开后点「分享 → 添加到主屏幕」，' -ForegroundColor Gray
Write-Host '     以后从桌面图标进入即为全屏无地址栏。' -ForegroundColor Gray
Write-Host ''
Write-Host '  * 首次运行如弹出防火墙提示，请点「允许访问」。' -ForegroundColor DarkYellow
Write-Host '  * 此窗口不要关闭；用完按 Ctrl + C 停止。' -ForegroundColor DarkYellow
Write-Host ''
Write-Host '  ============================================' -ForegroundColor DarkGray
Write-Host ''

& $py -m http.server $port --bind 0.0.0.0
