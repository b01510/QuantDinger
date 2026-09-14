# QuantDinger Workspace

這個 repository 現在明確分成兩個互不混用的版本。

## 1. official-original

用途：保存 OpenByteInc/QuantDinger 官方原版。

- 不加入個人台股策略
- 不修改官方功能
- 目標是與官方 upstream main 保持一致
- 官方來源：https://github.com/OpenByteInc/QuantDinger

GitHub Actions 同步器位於 `.github/workflows/sync-official.yml`，用來把官方 main 鏡像到 `official-original`。

## 2. taiwan-custom

用途：以 QuantDinger 的概念與架構為基礎，加入個人台股功能。

規劃包含：

- 台股資料源
- 爆量上漲掃描
- 第一次回測 20MA
- 成交量與技術面排名
- CSV / Excel 輸出
- 回測模組
- AI 個股分析
- 未來接 QuantDinger UI / Agent / MCP

## main

`main` 只作為入口、安裝輔助與版本管理，不直接混入兩個版本的核心程式。

> 實盤交易涉及真實資金風險。開發及測試階段應優先使用 paper trading，且不要把券商 API Key、密碼或 `.env` 上傳 GitHub。
