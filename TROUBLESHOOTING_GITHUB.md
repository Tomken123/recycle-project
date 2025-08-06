# 🔧 GitHub推送故障排除指南

## 🚨 常見問題及解決方案

### 1. Git未安裝
**問題**: `git : 無法辨識 'git' 詞彙是否為 Cmdlet、函數、指令檔或可執行程式的名稱`

**解決方案**:
1. 下載並安裝 [Git for Windows](https://git-scm.com/download/win)
2. 安裝時選擇預設設定
3. 重新開啟PowerShell
4. 驗證安裝: `git --version`

### 2. 認證問題
**問題**: 推送時要求輸入用戶名和密碼

**解決方案**:
1. **使用Personal Access Token**:
   - 前往 GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 點擊 "Generate new token (classic)"
   - 選擇權限: `repo`, `workflow`
   - 複製生成的token
   - 推送時使用GitHub用戶名和token作為密碼

2. **使用GitHub CLI**:
   ```powershell
   # 安裝GitHub CLI
   winget install GitHub.cli
   
   # 登錄
   gh auth login
   ```

### 3. 大文件推送失敗
**問題**: 模型文件太大無法推送

**解決方案**:
1. 確保`.gitignore`文件正確配置
2. 從Git歷史中移除大文件:
   ```powershell
   git rm --cached yolov8n.pt yolov8s.pt
   git commit -m "Remove large model files"
   ```

### 4. 遠程倉庫錯誤
**問題**: `fatal: remote origin already exists`

**解決方案**:
```powershell
# 移除現有遠程倉庫
git remote remove origin

# 添加新的遠程倉庫
git remote add origin https://github.com/Tomken123/recycle-project.git
```

### 5. 分支名稱問題
**問題**: `fatal: The current branch main has no upstream branch`

**解決方案**:
```powershell
# 設置上游分支
git push -u origin main
```

## 📋 完整推送流程

### 步驟1: 安裝Git
```powershell
# 檢查Git是否已安裝
git --version

# 如果未安裝，下載並安裝Git for Windows
# 下載地址: https://git-scm.com/download/win
```

### 步驟2: 配置Git
```powershell
# 設置用戶名和郵箱
git config --global user.name "Tomken123"
git config --global user.email "您的GitHub郵箱"

# 驗證配置
git config --list
```

### 步驟3: 初始化倉庫
```powershell
# 初始化Git倉庫
git init

# 添加遠程倉庫
git remote add origin https://github.com/Tomken123/recycle-project.git
```

### 步驟4: 添加和提交文件
```powershell
# 添加所有文件（除了.gitignore中排除的）
git add .

# 提交更改
git commit -m "Initial commit: 資源回收物分類檢測系統 v1.0"
```

### 步驟5: 推送到GitHub
```powershell
# 設置主分支
git branch -M main

# 推送到GitHub
git push -u origin main
```

## 🔍 檢查清單

推送前請確認:

- [ ] Git已正確安裝 (`git --version`)
- [ ] Git用戶配置完成 (`git config --list`)
- [ ] GitHub倉庫已創建 (https://github.com/Tomken123/recycle-project)
- [ ] `.gitignore`文件正確配置
- [ ] 大文件已被排除
- [ ] 有GitHub Personal Access Token

## 🆘 緊急救援

如果推送完全失敗，可以重新開始:

```powershell
# 刪除現有Git倉庫
Remove-Item -Recurse -Force .git

# 重新初始化
git init
git remote add origin https://github.com/Tomken123/recycle-project.git
git add .
git commit -m "Initial commit: 資源回收物分類檢測系統 v1.0"
git branch -M main
git push -u origin main
```

## 📞 需要幫助？

如果以上方法都無法解決問題，請:

1. 檢查錯誤訊息
2. 確認GitHub倉庫權限
3. 驗證Personal Access Token是否有效
4. 嘗試使用GitHub Desktop作為替代方案

---

**提示**: 使用提供的 `push_to_github.ps1` 腳本可以自動化大部分流程！ 