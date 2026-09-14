$ErrorActionPreference = 'Stop'

$Target = Join-Path $env:USERPROFILE 'quantdinger-taiwan'
$Base = 'https://raw.githubusercontent.com/b01510/QuantDinger/taiwan-custom/taiwan_dashboard'
$Image = 'quantdinger-taiwan'
$Container = 'quantdinger-taiwan'
$Volume = 'quantdinger-taiwan-data'

Write-Host 'QuantDinger Taiwan Edition v0.7 updater' -ForegroundColor Cyan
Write-Host "Install directory: $Target"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw '找不到 Docker。請先啟動 Docker Desktop。'
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Desktop 尚未啟動，請先開啟 Docker Desktop。'
}

New-Item -ItemType Directory -Force -Path $Target | Out-Null

$Files = @(
    'app.py',
    'requirements.txt',
    'cache_store.py',
    'patch_chart.py',
    'patch_v04_backend.py',
    'patch_v04_frontend.py',
    'patch_v05_filters.py',
    'patch_v06_backend.py',
    'patch_v06_frontend.py',
    'patch_v07_cache.py',
    'patch_v07_fix.py',
    'patch_v07_frontend.py',
    'Dockerfile.v07'
)

Write-Host '下載最新版台股工作台...'
foreach ($file in $Files) {
    Invoke-WebRequest "$Base/$file" -OutFile (Join-Path $Target $file)
}

Write-Host '建立 v0.7 Docker image（第一次可能需要幾分鐘）...'
docker build --no-cache -f (Join-Path $Target 'Dockerfile.v07') -t $Image $Target
if ($LASTEXITCODE -ne 0) { throw 'Docker build 失敗。' }

# Remove both current and legacy container names so port 8890 cannot remain occupied.
foreach ($name in @('quantdinger-taiwan','quantdinger-taiwan-dashboard')) {
    $existing = docker ps -a --filter "name=^${name}$" --format '{{.Names}}'
    if ($existing -eq $name) {
        Write-Host "移除舊容器：$name"
        docker rm -f $name | Out-Null
    }
}

# Keep the SQLite database across container rebuilds.
docker volume inspect $Volume *> $null
if ($LASTEXITCODE -ne 0) {
    docker volume create $Volume | Out-Null
}

Write-Host '啟動台股版 v0.7...'
docker run -d `
  --name $Container `
  --restart unless-stopped `
  -p 127.0.0.1:8890:8890 `
  -v "${Volume}:/app/data" `
  $Image | Out-Null

Start-Sleep -Seconds 4

$status = docker ps --filter "name=^${Container}$" --format '{{.Status}}'
if (-not $status.StartsWith('Up')) {
    Write-Host '容器沒有正常啟動，以下是最後 80 行紀錄：' -ForegroundColor Yellow
    docker logs $Container --tail 80
    throw 'QuantDinger Taiwan v0.7 啟動失敗。'
}

Write-Host ''
Write-Host '完成。' -ForegroundColor Green
Write-Host '台股工作台：http://127.0.0.1:8890'
Write-Host 'SQLite：Docker volume quantdinger-taiwan-data'
Write-Host '第一次全市場掃描會建立快取；之後掃描會大量改讀本機 SQLite。'
Write-Host ''
Write-Host '快取統計：http://127.0.0.1:8890/api/cache/stats'
