# URL Ultimate Filter - Changelog

## V44.93 - 2026-03-17
- [Privacy] 精準攔截 Slack 事件日誌 API (`/api/eventlog.history`)，採用 204 DROP 靜默拋棄避免企業軟體錯誤重試。
- [AdBlock] 新增 L1 Script Root `gad_script.` 精準狙殺 Google Ad (GAD) 廣告腳本，不受 `/js/` 靜態豁免影響。
- [Audit] 驗證 BusinessToday Google News 品牌圖片 (.jpg) 不被誤殺，確認靜態資源豁免正常。

## V44.92 - 2026-03-17
- [Anti-Tampering] iframe 沙箱防護：攔截 createElement('iframe') + MutationObserver 同步 patch 所有同源 iframe 的 sendBeacon/fetch，杜絕乾淨 contentWindow 繞過攻擊。
- [Performance] ACScanner → CompiledScanner：SSOT 編譯階段預建置 3 組 RegExp 字面量取代 641 次逐一 String.includes() 線性掃描。pathScanner 加速 69.9x (11.5µs→0.16µs/URL)。

## V44.91 - 2026-03-17
- [Anti-Tampering] navigator.sendBeacon 反篡改防護：偵測 Object.defineProperty 鎖定狀態，自動降級為 Proxy 代理攔截，封堵廣告腳本屬性鎖定攻擊向量。
- [Privacy] 新增 CSS background-image No-JS 追蹤攔截：MutationObserver 即時偵測 inline style url() 指向追蹤域名並清除。
- [Privacy] `<a ping>` 物理剝離升級為雙層防護：DOM 插入時主動巡邏 + 點擊時捕獲階段最後防線，杜絕瀏覽器競態條件。
- [Performance] Delayed Drop 記憶體安全閥 (MAX_PENDING_DROPS=64)：防止高頻遙測場景下 pending Promise/setTimeout 累積造成低階設備 GC 壓力。
- [Compatibility] 驗證 iOS Safari「阻擋所有 Cookie」模式下全部 204 Mock 機制零 Cookie 依賴，完全不受影響。

## V44.89 - 2026-03-17
- [Architecture] XHR 204 Mock 機制完美適配 Axios，補足 `getAllResponseHeaders` 與 `responseURL` 偽造，防止前端框架解析崩潰。
- [Architecture] 導入 `navigator.sendBeacon` 原生攔截，完美防堵背景遙測外洩，針對 DROP 權重直接回傳 `true` 以靜默欺騙客戶端。
- [Strategy] 擴展 204 DROP 應用範圍至 Microsoft Teams (`*.events.data.microsoft.com`) 與 Discord (`/api/v*/science`)。
- [UI] 實裝獨立的「Dropped」監控面板（紫色視覺），精準區分惡意阻擋與效能拋棄。

## V44.88 - 2026-03-17
- [Architecture] 升級 Tampermonkey 前端攔截器。針對 Fetch API 與 XMLHttpRequest 實作 204 (No Content) 完美偽造機制。當觸發 DROP 權重時，不再拋出網路錯誤，而是回傳虛擬的 204 成功狀態，欺騙 Slack 等具備 Exponential Backoff 重試機制的 SPA 客戶端，節省設備資源並避免 Console 紅字污染。
- [Audit] 驗證 Slack `/clog/track/` 在雙平台下的動作路由均能穩定輸出 204 靜默拋棄。

## V44.87 - 2026-03-16
- [Privacy] 針對 Yahoo! JAPAN 跨站點身份解析端點實施精準防護。將 `/acookie/` 與 `/cookie-sync/` 納入 L1 啟發式掃描 (`CRITICAL_PATH_GENERIC`)，並於 `CRITICAL_PATH_MAP` 綁定 `yahooapis.jp` 網域。此舉成功阻斷廣告商在背景執行的 Audience Cookie 匹配，且完全保障地圖、天氣等正常 API 運作。
- [Test] 擴展動態測試矩陣，新增 `Privacy: Audience Cookie Sync` 與 `Edge: Yahoo API Safe Harbor` 案例，確保規則具備嚴謹的向下相容性與防誤殺能力。

## V44.86 - 2026-03-16
- [Audit] 全量邏輯驗證 (2296 Cases × 19-Step Decision Chain)：以 3 個平行審計代理人逐行追蹤每條測試的引擎判定路徑，確認 expected 值零邏輯錯誤、原有手動案例零衝突 (向下相容)、核心防護功能零影響。
- [Fix] 修正 10 條測試描述的封鎖機制精準度：sentry.io 衝突描述 (非 Soft WL 衝突，Step 6 直接封鎖)、Coupang 3 條 (MAP Step 4 而非 Regex Step 16)、Mutation tracker (criticalPathScanner Step 15 而非 PATH_BLOCK)、Regex 類別 6 條 (標注實際觸發 Step 14/15/17)。描述現與引擎判定路徑完全對齊。
- [Architecture] 完整保留前述所有隱私防護與動作路由 (Action Routing) 策略。

## V44.84 - 2026-03-16
- [HotFix] 修復 V44.83 編譯器中的 RULES_DB 字典截斷錯誤 (KeyError: 'BLOCK_DOMAINS')，完整還原黑名單陣列以確保 GitHub Actions CI/CD 流程正常執行。
- [Architecture] 完整保留前述所有隱私防護與動作路由 (Action Routing) 策略。

## V44.82 - 2026-03-13
- [BugFix] 針對 Uber Eats 網頁版/WebView 新增路徑豁免 /go/_events，修復因 GraphQL 批次請求與遙測事件深度耦合，導致商品圖片無法顯示 (破圖) 之異常陷阱。

## V44.81 - 2026-03-13
- [HotFix] 修復 V44.80 編譯器中的 RULES_DB 字典截斷錯誤 (KeyError: 'REDIRECTOR_HOSTS')，確保 CI/CD 流程正常執行。
- [Architecture] 完整繼承 V44.79 的反向排除機制與 V44.80 的風傳媒 Nuxt 防崩潰策略。

## V44.79 - 2026-03-13
- [Architecture] 於 SCOPED_PARAM_EXEMPTIONS 導入「反向排除 (Negative Exclusion)」雙層校驗機制 (支援 `!` 前綴)。
- [Privacy] 針對 104 APP (v3.30.0) 實施寬鬆放行 /2.0/ 目錄，並透過 !/2.0/ad/ 精準狙擊內部廣告模組，徹底根除 API 變更引發的白名單疲勞現象。

## V44.78 - 2026-03-12
- [BugFix & Strategy] 針對 104 APP 導入「防禦性預測擴充策略」。除修復 /2.0/recommend/ 外，預先豁免 /job/, /apply/, /resume/ 等潛在核心業務路徑的 device_id，以預防後續的白名單疲勞與未知的斷線破圖。

## V44.77 - 2026-03-12
- [BugFix] 針對 104 工作快找 APP (v3.30.0) 新增局部參數豁免，精準放行 /2.0/notify/、/2.0/user/ 與 /2.0/company/ 路徑下的 device_id，修復 APP 啟動時報錯「必傳參數遺失」之異常。

## V44.76 - 2026-03-12
- [Architecture] 升級 CRITICAL_PATH_MAP 支援 Action Routing (動作路由) 標籤。
- [Privacy] 針對 Slack 遙測端點 (/clog/track/) 實作 DROP 權重 (HTTP 204)，防範客戶端重試風暴 (Retry Storm)。

## V44.75 - 2026-03-11
- [Privacy] 精準狙擊蝦皮 A/B 測試與流量分配遙測端點 (/abtest/traffic/)，防止設備特徵分群。

V44.74 - 202X-XX-XX

[Architecture] 策略回退與重構：回退至 V44.68 狀態，恢復腳本對蝦皮遙測的精準控管；將 FINANCE_SAFE_HARBOR 語意升級為 ABSOLUTE_BYPASS_DOMAINS。

[Feature] 透過 PATH_EXEMPTIONS 精準豁免蝦皮 PDP 商品 API (/api/v4/pdp/get)，解決 ads_id 參數觸發正則掃描器的誤殺問題。

V44.73 - 202X-XX-XX

[Architecture] 規則語意學重構：將 FINANCE_SAFE_HARBOR 升級為 ABSOLUTE_BYPASS_DOMAINS (絕對豁免網域)；並將 shopee.tw 等蝦皮核心網域納入 WILDCARDS，徹底解決零信任架構下的正則誤殺悖論。

V44.72 - 202X-XX-XX

[Architecture] 全面解耦蝦皮 (Shopee) 相關規則，徹底移除其專屬網域、路徑與測試案例，將遙測阻擋與放行主導權移交 Surge Rule-Set 核心接管，提升系統靈活性與效能。

V44.71 - 202X-XX-XX

[Refine] 移除 CRITICAL_PATH_MAP 中對蝦皮 patronus.idata.shopeemobile.com 的精準狙擊，修復 App 內部活動與獎勵功能。

V44.70 - 202X-XX-XX

[Architecture] 實作字首匹配法 (Prefix Matching) 以支援蝦皮 143.92.x.x 等動態 HTTPDNS IP 網段豁免。

V44.69 - 202X-XX-XX

[Feature] 擴充 PATH_EXEMPTIONS 支援蝦皮 HTTPDNS 直連 IP (143.92.88.1) 局部放行，修復 App 核心連線。

V44.68 - 202X-XX-XX

[Feature] 擴充 PATH_EXEMPTIONS 支援 Google Favicon API，防止因目標網域夾帶廣告關鍵字 (如 hubspot) 而遭 L2 掃描器誤殺。

V44.67 - 202X-XX-XX

[Feature] 擴充 PATH_EXEMPTIONS 支援 Coupang CDN 新舊目錄雙軌豁免 (ccm & cmg/oms)。

V44.66 - 202X-XX-XX

[Security] PRIORITY_BLOCK_DOMAINS 全面重構與擴充 (131→168 條)：修復 15 個因 SOFT_WHITELIST 通配覆蓋而完全失效的 BLOCK_DOMAINS 條目。

V44.65 - 202X-XX-XX

[Feature] REDIRECTOR_HOSTS 大規模擴充 (77→137 條)：新增六大家族共 60 個活躍廣告短網址網域。

V44.64 - 202X-XX-XX

[Refine] disqus.com 防護策略精修：採「保功能、斬遙測」架構，精準狙擊 /api/3.0/users/events、/j/、/tracking_pixel/。

[Audit] addthis.com 確認為 Oracle 2023 年已終止的殭屍服務，還原至 BLOCK_DOMAINS 全域封殺。

V44.63 - 202X-XX-XX

[Audit] 全面規則矩陣安全審查：移除 FINANCE_SAFE_HARBOR 中的高危 org.tw 通配；清理 27 個失效 REDIRECTOR_HOSTS 等。

V44.62 - 202X-XX-XX

[BugFix] 修正 Matrix Test Suite 中 OAUTH_SAFE_HARBOR 碰撞問題；升級 OAuth 路徑比對為嚴格 Regex 邊界防護。

V44.61 - 202X-XX-XX

[Architecture] 將 shopee.tw 移至 PARAM_CLEANING_EXEMPTED_DOMAINS 通配符；實作 HMAC 簽章防護與分號參數分隔符解析。

V44.60 - 202X-XX-XX

[Feature] 擴增 Google ODM (On-Device Measurement) 系統級備援遙測端點，並將 15 家主流 MMP 移入 WILDCARDS 進行通配符封殺。

V44.59 - 202X-XX-XX

[BugFix] 修正執行流優先級衝突導致 iadsdk.apple.com 測試失敗，還原白名單層級，並將 app-ads-services 升級至 WILDCARDS 徹底封殺。

V44.58 - 202X-XX-XX

[BugFix] Surge 引擎執行流重大修復：強制提升 BLOCK_DOMAINS 優先級，解決惡意網域遭 Surge FINAL 規則穿透放行的漏洞。

V44.57 - 202X-XX-XX

[Feature] Tampermonkey UX 最佳化：實作「點擊面板外部任意處自動收合」功能，提升操作直覺性。

V44.56 - 202X-XX-XX

[Feature] Tampermonkey UI 再進化：縮小預設盾牌、修正重複請求計數 (採用 Map 狀態機 xN 次數標記)。

V44.54 - 202X-XX-XX

[Feature] Tampermonkey 前端 UI 重構：導入分頁 (Tab) 切換展收清單，整合 TM 原生選單開關。

V44.52 - 202X-XX-XX

[Architecture] 實作「雙軌目標發佈」，同時生成 Surge 版與具備獨立防護 UI 的 Tampermonkey 版本。

V44.51 - 202X-XX-XX

[Feature] 擴充 Matrix Test Suite 支援 E2E (End-to-End) 鏈式測試與 Hash 截斷物理模擬。

V44.50 - 202X-XX-XX

[BugFix] 修復 Python f-string 反斜線編譯錯誤 (SyntaxError)，確保完全相容 CI/CD (Python < 3.12) 環境。

V44.49 - 202X-XX-XX

[BugFix] 修正 P0 子網域繼承失效 (px.ads.linkedin.com) 與還原 URL 雙重編碼解譯引擎。

V44.48 - 202X-XX-XX

[BugFix] 完整還原 Matrix Test Suite 的動態生成迴圈，恢復 800+ 條全方位回歸測試案例。

V44.47 - 202X-XX-XX

[BugFix] 修正 HTML_TEMPLATE 格式化 KeyError 錯誤，還原高階圖表測試報表儀表板。

V44.46 - 202X-XX-XX

[Architecture] 將 PATH_EXEMPTIONS 納入 SSOT，並精準放行 Coupang CDN /banner/ 靜態資源。

V44.45 - 202X-XX-XX

[Architecture] 導入模組化「路徑感知參數豁免 (SCOPED_PARAM_EXEMPTIONS)」。

[Feature] 擴增 12 項國際級數位簽章 API 至豁免清單 (AWS S3, GCS, Azure, Stripe 等)。

V44.44 - 202X-XX-XX

[BugFix] 將 feedly.com 納入 PARAM_CLEANING_EXEMPTED_DOMAINS，防止 API 斷線。

V44.43 - 202X-XX-XX

[Optimize] 實作 PARAMS_PREFIX_BUCKETS (前綴分桶)，O(1) 查找提升效能。

V44.42 - 202X-XX-XX

[BugFix] 修復 cleanTrackingParams 中 Set 結構的效能 Bug。

V44.41 - 202X-XX-XX

[Optimize] 統一重構 isDomainMatch 為「後綴剝離 Set 查找」演算法。

V44.40 - 202X-XX-XX

[Optimize] 重構 isPriorityDomain 為「後綴剝離 Set 查找」演算法。

V44.39 - 202X-XX-XX

[Optimize] 重構 BLOCK_DOMAINS_REGEX 為混合式三層架構。

V44.38 - 202X-XX-XX

[BugFix] 將 browserleaks.com 納入 HARD_WHITELIST。

V44.37 - 202X-XX-XX

[BugFix] 分離 PRIORITY_DROP 與常規 DROP 處理層級。

V44.36 - 202X-XX-XX

[Privacy] 新增 OpenTelemetry (OTLP) 標準遙測端點防護。

V44.35 - 202X-XX-XX

[Compatibility] Surge JSC 引擎相容性修復。

V44.34 - 202X-XX-XX

[BugFix] 擴充 SOFT_WHITELIST 與 PATH_EXEMPTIONS，精準放行 threads。

V44.33 - 202X-XX-XX

[BugFix] 修復 Matrix Test Suite 引擎中的陣列截斷問題。

V44.32 - 202X-XX-XX

[BugFix] 拔除 L1 掃描器中危險的無邊界特徵 '/api/log' 等，解決 104 登入失敗。

V44.31 - 202X-XX-XX

[Architecture] 建立「網域特化參數白名單」，豁免 104 API 嚴格校驗的 device_id。

V44.27 - 202X-XX-XX

[Architecture] 導入雙軌淨化機制「靜默網址重寫 (Silent URL Rewrite)」。
