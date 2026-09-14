$ErrorActionPreference = 'Stop'

$Target = Join-Path $env:USERPROFILE 'quantdinger-taiwan'
$Base = 'https://raw.githubusercontent.com/b01510/QuantDinger/taiwan-custom/taiwan_dashboard'

Write-Host 'QuantDinger Taiwan Edition installer' -ForegroundColor Cyan
Write-Host "Install directory: $Target"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw '找不到 Docker。請先啟動 Docker Desktop。'
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Desktop 尚未啟動，請先開啟 Docker Desktop。'
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null

Write-Host '下載台股版檔案...'
Invoke-WebRequest "$Base/app.py" -OutFile (Join-Path $Target 'app.py')
Invoke-WebRequest "$Base/requirements.txt" -OutFile (Join-Path $Target 'requirements.txt')
Invoke-WebRequest "$Base/Dockerfile" -OutFile (Join-Path $Target 'Dockerfile')

Write-Host '建立 Docker image（第一次會需要幾分鐘）...'
docker build -t quantdinger-taiwan-dashboard $Target
if ($LASTEXITCODE -ne 0) { throw 'Docker build 失敗。' }

$existing = docker ps -a --filter 'name=^quantdinger-taiwan-dashboard$' --format '{{.Names}}'
if ($existing -eq 'quantdinger-taiwan-dashboard') {
    Write-Host '更新既有台股版容器...'
    docker rm -f quantdinger-taiwan-dashboard | Out-Null
}

Write-Host '啟動台股版...'
docker run -d `
  --name quantdinger-taiwan-dashboard `
  --restart unless-stopped `
  -p 127.0.0.1:8890:8890 `
  quantdinger-taiwan-dashboard | Out-Null

Start-Sleep -Seconds 3
Write-Host ''
Write-Host '完成。' -ForegroundColor Green
Write-Host '台股版：http://127.0.0.1:8890'
Write-Host '官方原版：http://127.0.0.1:8888'
Write-Host ''
Write-Host '可先測試：2330、2317、0050、3017、2368'
