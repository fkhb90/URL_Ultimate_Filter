# URL Ultimate Filter — AI Workflow Quickstart

> 本文件是快速入口，不是正式規範。
> Operator 實際先讀入口已移到 Obsidian：`C:/Users/fkhb9/Documents/Obsidian/Hermes-Knowledge-Base/09-SOP/URL Ultimate Filter — AI Workflow Quickstart.md`
> 需要完整流程時再讀 Obsidian：`C:/Users/fkhb9/Documents/Obsidian/Hermes-Knowledge-Base/09-SOP/URL Ultimate Filter — 完整工作流程說明.md`
> 完整流程、決策鏈、規則語意與 Git／PR 細節，一律以 `docs/workflow.md` 為準。

## 1. 先收最小必要資訊

開始前先確認：

- URL
- 預期行為（`ALLOW` / `BLOCK` / `DROP` / `CLEAN`）
- 實際現象
- 網站功能上下文（登入、播放器、API、跳轉、追蹤、廣告、靜態資源等）

資訊不足時先補缺口，不得猜測。

## 2. 先判定，再決定是否修改

依目前 Surge JavaScript `processRequest()` 的現行決策鏈順序判定。
不要只看網域名稱、單一關鍵字或直覺決定結果。

判定輸出至少包含：

- URL
- 命中的 gate／規則
- 預期結果
- 判定理由

## 2.5 判定輔助：Jev verdict pipeline（v0.2.0）

> 判定階段可用 skill `url-filter-jev-verdict` 自動蒐證＋判定，**它不改規則**；一旦結論是需要改規則，就回到第 3 步走 SSOT。
> 腳本：`C:\Users\fkhb9\AppData\Local\hermes\skills\software-development\url-filter-jev-verdict\scripts\jev_url_verdict.py`

```bash
python3 "C:\Users\fkhb9\AppData\Local\hermes\skills\software-development\url-filter-jev-verdict\scripts\jev_url_verdict.py" <URL> [<URL> ...] --json-out receipts.json
```

五段（證據在前、判定在後）：

1. **runtime probe** — 對 generated runtime 實跑，取得 `ALLOW` / `403 BLOCK` / `204 DROP` / `302 REWRITE`。
2. **SSOT 先例** — 掃 `SSOT_Compiler.py` 的 host／registrable domain／path 段落與命中 token。
3. **origin 證據** — 單次未帶身分的 **GET**（不送 POST、不帶認證），記錄 status／Content-Type／body 前 200 字／`Allow`／`Via`。
4. **端點用途證據**（v0.2.0 新增）— 自動辨識 Sentry 形 ingestion ack、`/envelope/`／`/minidump/`、`sentry_key=`、`405`+`Allow`、結構化 401 JSON 等。
5. **Jev 判定** — 第一輪偏弱（`needs_evidence`、confidence < 0.60、或前兩名差距 < 0.05）且第 4 段有事實時，自動補證據跑第二輪；兩輪都進 receipts。

輸出與判讀：

- `deciding_rule` 會寫出關鍵字層歸因，例如 `Blocked by Keyword: PATH_BLOCK keyword 'sentry' index 203/389`。**`Blocked by Keyword` 的來源是 SSOT 的 `RULES_DB["PATH_BLOCK"]` 字串清單（leftmost 命中優先），不是 runtime 裡那個巨型 regex 層**（後者是晚一步的 `Blocked by Regex`）。
- 每條 URL 附 `policy` / `needs_review`：`correct` → 不動規則；`false_positive` → PATH_EXEMPTIONS 提案；`false_negative` → DROP_RE 提案；`needs_review` → **不輸出結論**，補證據或升級人工。
- **信心值只是分數，不是機率，且會漂移**（同一 URL 實測單輪 0.23 ↔ 0.25 連方向都不同）；判讀看方向與 `functional_traffic`，必要時用 `--drift` 再問一次比對。

常用旗標：`--reask-below`、`--margin`、`--no-reask`、`--purpose-hint FILE`、`--drift`、`--no-origin`、`--json-out`。

實測基準（2026-09-22，4 條 URL）：8.15 秒、5 次 Jev 呼叫；`slack.com/apps/sentryproxy/api/<id>/envelope/` 全自動得到 `correct`（needs_review=False），取代原本需要人工 grep + curl + 手寫 state 的 4 個步驟。

## 3. 確認需要改規則時，只改 SSOT

- 唯一規則來源：`SSOT_Compiler.py`
- 不得直接修改 generated files：
  - `URL-Ultimate-Filter-Surge.js`
  - `URL-Ultimate-Filter-Tampermonkey.user.js`
  - `CHANGELOG.md`

先確認最小且正確的修改位置，避免擴大豁免或封鎖範圍。

## 4. 每次行為變更都要補測試與版本

- 新增對應測試案例
- 版本號 `+0.01`
- 同步更新版本日期與近期摘要

## 5. 驗證指令

```bash
python3 SSOT_Compiler.py
```

只有在下列條件成立時，才可往下：

```text
失敗錯誤     : 0 CASES
```

未完成驗證前，不得宣告成功、建立 commit 或推送。

## 6. 驗證通過後才進 Git／PR 流程

本 repo 預設採用 **source-only commit**：只提交 `SSOT_Compiler.py`，由 GitHub Actions 重新編譯並提交生成檔案；`public/index.html` 只作為 GitHub Pages artifact，不進 Git。

順序如下：

1. 確認變更內容
2. 只暫存 `SSOT_Compiler.py`
3. commit
4. fetch / rebase 最新 `main`
5. push 到 `main`（功能分支則在合併到 `main` 後觸發 CI）
6. 等待 GitHub Actions 產出 Surge、Tampermonkey 與 `CHANGELOG.md`
7. 確認 Actions 與 Pages 部署結果，再進行 PR / review / merge

只有在 CI 不可用且明確採離線交付時，才可在本機一併提交生成檔案；`public/index.html` 仍不進 Git。

## 7. 一頁版最短流程

```text
1. 收 URL / 預期行為 / 實際現象
2. 依現行 processRequest() 決策鏈判定
3. 確認是否真的需要改規則
4. 只改 SSOT_Compiler.py
5. 補測試、版本號、日期與摘要
6. 執行 python3 SSOT_Compiler.py
7. 確認 failed = 0
8. 只 commit SSOT_Compiler.py
9. push 到 main，等待 GitHub Actions 產出其他檔案
10. 確認 Actions / Pages 結果後再進 PR / review / merge
```
