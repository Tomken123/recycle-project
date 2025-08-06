# GitHub推送腳本
# 使用方法: .\push_to_github.ps1

Write-Host "🚀 開始推送專案到GitHub..." -ForegroundColor Green

# 檢查Git是否安裝
try {
    $gitVersion = git --version
    Write-Host "✅ Git已安裝: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Git未安裝，請先安裝Git for Windows" -ForegroundColor Red
    Write-Host "下載地址: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

# 檢查Git配置
Write-Host "📋 檢查Git配置..." -ForegroundColor Blue
$userName = git config --global user.name
$userEmail = git config --global user.email

if (-not $userName -or -not $userEmail) {
    Write-Host "⚠️ 請先配置Git用戶信息:" -ForegroundColor Yellow
    Write-Host "git config --global user.name '您的GitHub用戶名'" -ForegroundColor Cyan
    Write-Host "git config --global user.email '您的GitHub郵箱'" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Git配置完成: $userName <$userEmail>" -ForegroundColor Green

# 檢查是否在Git倉庫中
if (-not (Test-Path ".git")) {
    Write-Host "📁 初始化Git倉庫..." -ForegroundColor Blue
    git init
}

# 檢查遠程倉庫
$remoteUrl = git remote get-url origin 2>$null
if (-not $remoteUrl) {
    Write-Host "🔗 添加遠程倉庫..." -ForegroundColor Blue
    git remote add origin https://github.com/Tomken123/recycle-project.git
}

# 添加文件到暫存區
Write-Host "📦 添加文件到暫存區..." -ForegroundColor Blue
git add .

# 檢查暫存區狀態
$stagedFiles = git diff --cached --name-only
if ($stagedFiles) {
    Write-Host "✅ 已暫存以下文件:" -ForegroundColor Green
    $stagedFiles | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }
} else {
    Write-Host "ℹ️ 沒有新文件需要提交" -ForegroundColor Yellow
}

# 提交更改
Write-Host "💾 提交更改..." -ForegroundColor Blue
$commitMessage = "Initial commit: 資源回收物分類檢測系統 v1.0"
git commit -m $commitMessage

# 設置主分支
Write-Host "🌿 設置主分支..." -ForegroundColor Blue
git branch -M main

# 推送到GitHub
Write-Host "🚀 推送到GitHub..." -ForegroundColor Blue
Write-Host "⚠️ 如果要求認證，請使用您的GitHub用戶名和Personal Access Token" -ForegroundColor Yellow
git push -u origin main

Write-Host "✅ 推送完成！" -ForegroundColor Green
Write-Host "🌐 查看您的專案: https://github.com/Tomken123/recycle-project" -ForegroundColor Cyan 