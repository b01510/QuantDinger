# QuantDinger Taiwan Stock Extension

This custom layer adds a `TWStock` market to QuantDinger while keeping the official image as the base.

## What it adds

- Taiwan market entry: `TWStock`
- Symbol aliases: `TWStock`, `taiwan`, `twse`, `tpex`
- Yahoo Finance data adapter for Taiwan listed / OTC stocks and ETFs
- Bare Taiwan symbols such as `2330`, `0050`, `2317`, `6488`
- Yahoo suffix resolution: `.TW` first, then `.TWO`
- Yahoo symbol search restricted to Taiwan `.TW` / `.TWO` results
- K-line and ticker support through yfinance

## Files

- `tw_stock.py`: Taiwan stock market-data adapter
- `patch_backend.py`: patches the official backend registry/factory/search code
- `Dockerfile`: builds `quantdinger-backend-tw:local` from the official backend image
- `docker-compose.override.yml`: points all backend worker services at the custom image

## Install on the existing Windows deployment

Your official install currently lives at:

```text
C:\Users\b01510\quantdinger
```

Copy this `taiwan_patch` directory into that folder so the result is:

```text
C:\Users\b01510\quantdinger\taiwan_patch\Dockerfile
C:\Users\b01510\quantdinger\taiwan_patch\patch_backend.py
C:\Users\b01510\quantdinger\taiwan_patch\tw_stock.py
C:\Users\b01510\quantdinger\taiwan_patch\docker-compose.override.yml
```

Then run from PowerShell:

```powershell
cd C:\Users\b01510\quantdinger
docker compose -f .\docker-compose.yml -f .\taiwan_patch\docker-compose.override.yml build
docker compose -f .\docker-compose.yml -f .\taiwan_patch\docker-compose.override.yml up -d
```

Open `http://127.0.0.1:8888`, select **Taiwan Stocks**, then search for symbols such as `2330`, `0050`, `2317`, or `6488`.

## Important

This first stage provides market selection, symbol search, quotes, and K-lines. It does not yet add Taiwan broker live-order routing, TWSE/TPEX official fundamental data, institutional flows, margin trading statistics, or corporate-action normalization.
