# 修復Git路徑問題的腳本

Write-Host "🔧 修復Git路徑問題..." -ForegroundColor Green

# 常見的Git安裝路徑
$gitPaths = @(
    "C:\Program Files\Git\bin",
    "C:\Program Files (x86)\Git\bin",
    "$env:LOCALAPPDATA\Programs\Git\bin",
    "$env:USERPROFILE\AppData\Local\Programs\Git\bin"
)

Write-Host "🔍 搜尋Git安裝位置..." -ForegroundColor Blue

$foundGit = $false
foreach ($path in $gitPaths) {
    if (Test-Path $path) {
        Write-Host "✅ 找到Git在: $path" -ForegroundColor Green
        $gitExe = Join-Path $path "git.exe"
        if (Test-Path $gitExe) {
            Write-Host "✅ Git可執行文件存在: $gitExe" -ForegroundColor Green
            $foundGit = $true
            
            # 臨時添加到PATH
            $env:PATH = "$path;$env:PATH"
            Write-Host "📝 已臨時添加Git到PATH" -ForegroundColor Yellow
            
            # 測試Git
            try {
                $version = & $gitExe --version
                Write-Host "✅ Git版本: $version" -ForegroundColor Green
                break
            } catch {
                Write-Host "❌ Git執行失敗" -ForegroundColor Red
            }
        }
    }
}

if (-not $foundGit) {
    Write-Host "❌ 未找到Git安裝" -ForegroundColor Red
    Write-Host "請重新安裝Git for Windows:" -ForegroundColor Yellow
    Write-Host "https://git-scm.com/download/win" -ForegroundColor Cyan
    exit 1
}

Write-Host "🚀 現在可以執行Git命令了！" -ForegroundColor Green
Write-Host "嘗試運行: git --version" -ForegroundColor Cyan 