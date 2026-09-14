# QuantDinger Taiwan Custom

這是台股客製版分支，與 `official-original` 完全分開。

## 目標

建立一套可以實際每天使用的台股 AI 選股與策略研究工作台，而不是單純複製官方功能。

## 第一階段

1. 台股日 K / 成交量資料取得
2. 近期爆量上漲掃描
3. 第一次回測 20MA 判定
4. 成交量、趨勢、距離均線與動能評分
5. 產生排名結果
6. 輸出 CSV / Excel
7. 保留 CLI，可獨立執行

## 第二階段

- 策略回測
- 個股 AI 摘要與 Bear Case
- 族群 / 產業強弱
- 自選股追蹤
- 每日盤後掃描
- GitHub Actions 自動執行

## 第三階段

- 串 QuantDinger UI
- 串 Agent / MCP
- Paper Trading
- 風控與部位管理

## 分支規則

- 官方乾淨版：`official-original`
- 台股開發版：`taiwan-custom`
- 專案入口：`main`

此分支未來可以吸收 `b01510/TaiwanStockScanner` 中已經驗證過的邏輯，但會重新整理成模組化架構，而不是直接把舊程式整包貼進來。

> 預設只做研究、篩選與 paper trading。任何 live trading 功能都必須額外啟用。
