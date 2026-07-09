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

順序如下：

1. 確認變更內容
2. 暫存必要檔案
3. commit
4. fetch / rebase 最新 `main`
5. push
6. PR / review / merge

## 7. 一頁版最短流程

```text
1. 收 URL / 預期行為 / 實際現象
2. 依現行 processRequest() 決策鏈判定
3. 確認是否真的需要改規則
4. 只改 SSOT_Compiler.py
5. 補測試、版本號、日期與摘要
6. 執行 python3 SSOT_Compiler.py
7. 確認 failed = 0
8. 才做 git / push / PR
```
