# URL Ultimate Filter — 完整工作流程說明

---

> Operator 入口已移到 Obsidian。
> 每次執行 URL_Ultimate_Filter 任務時，先讀 `C:/Users/fkhb9/Documents/Obsidian/Hermes-Knowledge-Base/09-SOP/URL Ultimate Filter — AI Workflow Quickstart.md`；
> 需要完整 phase / 決策鏈 / Git 細節時，再讀 `C:/Users/fkhb9/Documents/Obsidian/Hermes-Knowledge-Base/09-SOP/URL Ultimate Filter — 完整工作流程說明.md`。
> 本 repo `docs/workflow.md` 保留為 source mirror / 對照來源。

## 0、AI 執行契約

AI 執行本流程時，必須遵守以下約束：

1. 先取得待判定 URL、預期網站功能，以及問題現象；資訊不足時先提出缺口，不得猜測。
2. 以 `SSOT_Compiler.py` 為唯一規則來源；不得直接修改生成檔案。
3. 嚴格依照目前 Surge JavaScript 的 `processRequest()` 執行順序判定；不得沿用過時的白皮書 Step 編號推測優先級。
4. 某一閘門產生最終動作時立即停止判定；狀態或標籤計算則保留結果並繼續。
5. 修改前先確認最小且正確的規則位置，避免擴大豁免或封鎖範圍。
6. 每次行為變更都必須新增對應測試，且編譯器測試失敗數必須為 `0`。
7. 未完成驗證前，不得宣告成功、建立 commit 或推送。

### 每階段必要輸出

| 階段 | AI 必須輸出 |
|------|-------------|
| 判定 | URL、命中的順序與閘門、規則、預期結果、判定理由 |
| 修改前 | 預計修改位置、最小變更範圍、可能影響 |
| 修改後 | 實際變更、加入的測試案例、版本號 |
| 驗證後 | 測試總數、成功數、失敗數 |
| Git / PR | commit、分支、PR 與 CI 狀態 |

## 1、收到 URL → 完整搜索並判斷應該封鎖或放行

先確認 URL 的實際用途與必要功能，再依目前 Surge JavaScript 的現行決策鏈進行判定。不得只依網域名稱、單一關鍵字或直覺決定結果。

### 主要判定結果

| 結果 | HTTP 狀態 | 適用情境 |
|------|-----------|----------|
| ALLOW | 放行 | 功能性請求，正常通過 |
| BLOCK | 403 | 廣告、追蹤端點，硬封鎖 |
| DROP | 204 | 遙測、日誌端點，靜默丟棄（網站感知不到失敗） |
| CLEAN | 302 / REWRITE | 放行請求，但先移除追蹤參數 |


## 2、確認如需修改 → 只更新 SSOT_Compiler.py（現行決策鏈）


按照目前 Surge JavaScript `processRequest()` 的順序逐步判斷適合以何種方式增加規則。產生最終動作時立即提早退出；狀態或標籤計算則保留結果並繼續。

### 現行決策鏈（依 V46.35 原始碼順序）

| 順序 | 閘門 | 現行判定方式 | 動作或後續行為 |
|------|------|--------------|----------------|
| 0 | 輸入與 URL 解析 | 無 URL 時直接放行；提取 hostname 並建立 `hostProfile`；移除 fragment；保留 path 與 query；支援最多兩次 URL decode | 建立後續判定資料 |
| 1 | CheckConnection | `pathLower` 包含 `/accounts/checkconnection` | 回傳 `204`，立即退出 |
| 2 | P0 優先封鎖網域 | `hostProfile.isPriorityBlocked` 為真時，先檢查該網域的 `CRITICAL_PATH_MAP`；若命中 DROP 規則則回傳 `204`，否則回傳 P0 `403` | `204` 或 `BLOCK 403`，立即退出 |
| 3 | 安全轉址抽取 | 命中 `REDIRECT_EXTRACT_HOSTS`；從路徑或精確的 `url=` 參數抽取 `http://` 或 `https://` 目標 | 成功抽取則 `302` 至目標；否則 `BLOCK 403`，立即退出 |
| 4 | 惡意重新導向 | 命中 `REDIRECTOR_HOSTS` | `BLOCK 403`，立即退出 |
| 5 | 特定網域路徑攔截 | 取得 `CRITICAL_PATH_MAP`，使用 `matchCriticalMapRule` 判定 | DROP 規則回傳 `204`；其他規則回傳 `BLOCK 403`，立即退出 |
| 6 | OAuth 安全港 | hostname 精確命中 `OAUTH_SAFE_HARBOR.DOMAINS`，且不是 `accounts.youtube.com` | `ALLOW`，立即退出 |
| 7 | 絕對豁免網域 | 命中 `ABSOLUTE_BYPASS_DOMAINS` | `ALLOW`，立即退出 |
| 8 | 硬性白名單 | 命中 `HARD_WHITELIST` | 執行 `_performCleaning`；有追蹤參數時清理，否則直接放行；立即退出 |
| 9 | 標準網域攔截 | 命中 `BLOCK_DOMAINS`、`BLOCK_DOMAINS_WILDCARDS` 或 `BLOCK_DOMAINS_REGEX`，且未被前述 Allow 規則處理 | `BLOCK 403`，立即退出 |
| 10 | 路徑豁免 | 命中對應 hostname 的 `PATH_EXEMPTIONS` | 執行 `_performCleaning`；有追蹤參數時清理，否則直接放行；立即退出 |
| 11 | 後續掃描標籤 | 讀取 `isSoftWhitelisted`，並計算 `isExplicitlyAllowed` 與 `isStatic` | 保留三個標籤，繼續 |
| 12 | 優先捨棄 | 非 `isExplicitlyAllowed`、非 `isStatic`，且命中 `PRIORITY_DROP` | `DROP 204`，立即退出 |
| 13 | 高置信度攔截 | 非 `isExplicitlyAllowed`，且命中 `highConfidenceScanner` | `BLOCK 403`，立即退出 |
| 14 | 關鍵路徑掃描器 | 命中 `criticalPathScanner` | `BLOCK 403`，立即退出 |
| 15 | Coupang 專用攔截 | hostname 為 `cmapi.tw.coupang.com`，且 path 命中 `/\/.*-ads\//` | `BLOCK 403`，立即退出 |
| 16 | 路徑深度掃描 | 符合 `!(isSoftWhitelisted && isStatic) && !isExplicitlyAllowed && !isStatic`，再依序執行 `pathScanner` 與 `COMBINED_PATH_SCANNER` | 命中關鍵字或正則時 `BLOCK 403`，立即退出 |
| 17 | 常規捨棄 | 非 `isExplicitlyAllowed`、非 `isStatic`，且命中 `DROP` | `DROP 204`，立即退出 |
| 18 | 參數清理兜底 | 所有前述閘門皆未產生最終動作 | 執行 `_performCleaning`；回傳 `CLEAN_302`、`REWRITE` 或直接放行 |

### 不可變更的決策語意

- 上表順序是目前 V46.35 的實際執行優先級，不得套用舊白皮書的 Step 0~19 順序。
- P0 網域不是一律先回傳 `403`；若同網域 `CRITICAL_PATH_MAP` 命中 DROP 規則，會先回傳 `204`。
- `REDIRECT_EXTRACT_HOSTS` 先於一般 `REDIRECTOR_HOSTS`，允許抽取安全目標並回傳 `302`。
- OAuth、絕對豁免與硬白名單先於標準網域攔截；這是 V45.36 起的 allow-before-block 順序。
- 軟性白名單不再先於網域攔截執行；它只在後續路徑深度掃描階段作為標籤使用。
- `criticalPathScanner` 是後續掃描區唯一不受 `isExplicitlyAllowed` 或 `isStatic` 標籤保護的掃描器。
- 參數清理是最終兜底；只有未被前述閘門處理的流量才會抵達。
- `processRequest()` 發生例外時會記錄 Debug 訊息（僅限 DEBUG 模式）並採 fail-open 放行。


### 修改位置參考對照表（非完整，僅參考）

| 情境 | 修改位置 | 說明 |
|------|----------|------|
| P0 零容忍網域 | PRIORITY_BLOCK_DOMAINS | 先檢查同網域的 CRITICAL_PATH_MAP DROP 規則；未命中則直接 403 |
| 可抽取安全目標的轉址網域 | REDIRECT_EXTRACT_HOSTS | 成功抽取 HTTP(S) 目標時回傳 302，否則 403 |
| 惡意轉址網域 | REDIRECTOR_HOSTS | 直接 403 |
| 特定域名的特定路徑要封鎖或捨棄 | CRITICAL_PATH_MAP | 支援 `DROP:`、`DROP_RE:`、`RE:` 與普通路徑 |
| 跨域名通用封鎖（BLOCK） | PATH_BLOCK | substring 匹配，命中即 403 |
| 跨域名通用靜默丟棄 | DROP | substring 匹配，命中即 204 |
| 誤封的功能性路徑 | PATH_EXEMPTIONS | 支援路徑子字串與 `RE:` 正則；在標準網域攔截之後、所有路徑掃描之前放行並執行參數清理 |
| 整個域名應完全放行 | HARD_WHITELIST | 優先於標準網域攔截；放行並執行參數清理 |
| 域名為可信平台（靜態資源豁免） | SOFT_WHITELIST | 作為後續路徑深度掃描的標籤，不會略過前面的標準網域攔截 |
| 一般廣告或追蹤網域 | BLOCK_DOMAINS | 在 OAuth、絕對豁免與硬白名單之後執行，命中即 403 |

### CRITICAL_PATH_MAP 四種規則語法

```python
'<example.com>': [
    'DROP:/path/to/block',           # 路徑包含此字串 → DROP 204
    'DROP_RE:^/path/regex(\\?|$)',   # 路徑符合正規表示式 → DROP 204
    'RE:^/path/regex(\\?|$)',        # 路徑符合正規表示式 → BLOCK 403
    '/path/to/hard-block',           # 路徑包含此字串 → BLOCK 403
]
```

### PATH_EXEMPTIONS 現行比對語意

- 網域鍵值可命中相同 hostname 或其子網域；特定數字前綴格式則以 hostname 前綴比對。
- 普通路徑規則會對解碼後且移除 query 的 `pathOnly` 執行子字串比對。
- `RE:` 規則會以不區分大小寫的正則，對未解碼、移除 query 且轉小寫的 `rawPathOnlyLower` 比對。
- 路徑豁免命中後會執行 `_performCleaning`；有可移除參數時回傳 `302` 或 `REWRITE`，否則直接放行。

### 參數清理現行順序

`_performCleaning()` 會呼叫 `cleanTrackingParams()`，並依目前 Surge JavaScript 採取下列順序：

1. URL 沒有 query 時，不執行清理。
2. URL 含 `signature`、`sig` 或 `hmac` 參數時，不執行清理。
3. hostname 位於 OAuth 安全港、路徑命中 OAuth 路徑正則，或網域位於參數清理豁免清單時，不執行清理。
4. hostname 以 `api.`、`appapi.` 開頭、命中 API 簽章 bypass 正則，或位於 `SILENT_REWRITE_DOMAINS` 時，清理結果使用 `REWRITE`；其餘使用 `302`。
5. 每個參數先檢查 `PARAMS.WHITELIST` 與網域專屬 `SCOPED_EXEMPTIONS`，命中時保留。
6. 再依序移除命中 `PARAMS.GLOBAL`、`PARAMS.COSMETIC`、前綴 bucket、`GLOBAL_REGEX` 或 `PREFIXES_REGEX` 的參數。
7. 沒有參數被移除時直接放行；有變更時才回傳清理後 URL。

### 版本號規則

- 每次修改 → 版號 +0.01（例：V46.09 → V46.10）
- `VERSION`、`RELEASE_DATE` 同步更新
- Header docstring 保留最近 5 版摘要，舊版自動追加至 `CHANGELOG.md`


### 重要注意事項

- `pathLower` 為完整 URL-decoded 路徑**含 query string**，關鍵字掃描會對整段字串比對
- `PATH_EXEMPTIONS` 在標準網域攔截之後、所有路徑掃描之前執行，是修正路徑誤封的主要手段；它無法豁免已命中的標準網域攔截
- `CRITICAL_PATH_MAP` 在所有 Allow 與標準網域攔截之前執行
- P0 網域會先檢查同網域 `CRITICAL_PATH_MAP` 的 DROP 規則，再決定回傳 `204` 或 P0 `403`
- `REDIRECT_EXTRACT_HOSTS` 的抽取只接受以 `http://` 或 `https://` 開頭的目標
- OAuth 安全港在 `processRequest()` 中是 hostname 精確比對，並明確排除 `accounts.youtube.com`
- `cleanTrackingParams()` 會另外對 OAuth 路徑正則、簽章參數與參數清理豁免網域採取不清理策略


---


## 3、執行編譯器 → 確認測試通過

### 執行前檢查

- 已依目前 Surge JavaScript 的現行決策鏈確認修改位置與預期結果。
- 已更新版本號、發佈日期與近期版本摘要。
- 已在對應版本區塊新增測試案例。

### 新增測試案例規範

每次修改規則，必須在對應版本區塊新增測試案例：

```python
# --- V46.XX 修改說明 ---
cases.append(TestCase(
    "類型: 簡短名稱",
    "<https://example.com/path>",
    RES_ALLOW / RES_BLOCK_403 / RES_DROP_204,
    "V46.XX 詳細說明；命中規則說明"
))
```

### 執行編譯器

```powershell
python3 SSOT_Compiler.py
```

編譯器會產出或更新：

- `URL-Ultimate-Filter-Surge.js`
- `URL-Ultimate-Filter-Tampermonkey.user.js`
- `CHANGELOG.md`
- `public/index.html`（由 CI artifact 部署至 GitHub Pages，不進 Git）

### 測試通過標準

```text
總共測試案例 : XXXX CASES
成功通過     : XXXX CASES
失敗錯誤     : 0 CASES
```

**Checkpoint：失敗數不是 `0` 時立即停止。不得進入 Git、PR 或合併流程。**

## 4、Git 操作流程

只有在編譯器測試全部通過後，才依下列順序執行。

### 標準流程

```powershell
# A. 丟棄不追蹤的測試報告（由 .gitignore 管理）
git restore public/index.html

# B. 暫存四個產出檔案
git add SSOT_Compiler.py `
        URL-Ultimate-Filter-Surge.js `
        URL-Ultimate-Filter-Tampermonkey.user.js `
        CHANGELOG.md

# C. 建立 commit
git commit -m "feat(V46.XX): 簡短說明"

# D. 拉取最新 main 並變基整合
git fetch origin main
git rebase origin/main

# E. 推送
git push -u origin claude/review-version-updates-2NEC0
```

### 遇到 `public/index.html` 衝突時

```powershell
# CI auto-build 又把此檔案提交到 main，與分支的刪除記錄衝突
git rm public/index.html      # 保留刪除意圖，解決衝突
git rebase --continue
git push --force-with-lease   # 功能分支可安全強制推送
```

### Commit 訊息格式

```text
feat(V46.XX): Privacy/BugFix — 一句話說明
```

詳細說明可包含：

- 問題根源
- 修正方式

**Checkpoint：rebase 或 push 失敗時立即停止並回報錯誤，不得宣告完成。**

## 5、建立 PR → 等待 Codex Review → 合併

### PR 規範

- 分支：`claude/review-version-updates-2NEC0` → `main`
- 標題：`V46.XX — [Privacy/BugFix/chore]: 簡短說明`
- 內文：問題描述、修正方式、測試結果統計

### Codex Review 處理原則

- 只處理有明確風險且實際可能發生的問題。
- 優先檢查 `SSOT_Compiler.py` 的手動修改 diff。
- 不全文 review `CHANGELOG.md` 與 generated JS。
- 一次只處理單點問題。
- 避免在同一輪混合處理 PR、rebase、review、規則判讀與 changelog 文案。
- 長串 review comment 分開處理。
- Review 後若修改行為，版號加 `0.01`，重新測試後再 commit 與 push。
- 理論風險但實際可忽略時，在 PR 說明理由，不修改規則。
- 合併後才收到的建議，依必要性決定是否建立新 PR。

**Checkpoint：Review 導致任何行為變更時，必須回到第 2、3 節重新判定與驗證。**

## 6、後台 CI 自動機制

PR 合併後，CI 自動執行以下既定流程：

```text
PR 合併到 main
  └─→ GitHub Actions (build-and-test.yml) 觸發
        │
        ├─→ python SSOT_Compiler.py
        │     └─→ 自動重新編譯 Surge.js + Tampermonkey.js
        │         更新 CHANGELOG.md
        │         自動生成 public/index.html（測試報告）
        │
        ├─→ git add Surge.js + Tampermonkey.js + CHANGELOG.md
        ├─→ git rm --cached public/index.html（自我修復殘留追蹤）
        ├─→ git commit "Auto-build [skip ci]"
        ├─→ git pull --rebase origin main
        ├─→ git push → main
        │
        ├─→ upload-pages-artifact（上傳 ./public 目錄）
        └─→ deploy-pages → GitHub Pages 部署測試報告
```

CI 任一步驟失敗時，視為流程未完成；必須先定位失敗步驟，再決定是否修正或重新執行。

## 7、工作準則

- 手術式修正：只改必要位置，不引入無關變更。
- 最小豁免面積：`PATH_EXEMPTIONS` 路徑盡量精確，避免前綴過寬。
- 先驗證再推送：編譯器測試全數通過後才能 commit。
- Git sync 優先：修改前先 fetch + rebase，確保基於最新 `main`。
- 每版都有測試案例：新增規則必須附對應測試，防止未來退化。
- 近期摘要只保留 5 版：Header docstring 保留最新 5 版，完整歷史寫入 `CHANGELOG.md`。
- 明確暴露失敗：任何指令、測試、rebase、push、Review 或 CI 失敗，都必須回報實際錯誤與停止位置。
