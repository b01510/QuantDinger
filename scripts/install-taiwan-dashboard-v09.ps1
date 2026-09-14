$ErrorActionPreference = 'Stop'
$Target = Join-Path $env:USERPROFILE 'quantdinger-taiwan'
$Base = 'https://raw.githubusercontent.com/b01510/QuantDinger/taiwan-custom/taiwan_dashboard'
$Image = 'quantdinger-taiwan'
$Container = 'quantdinger-taiwan'
$Volume = 'quantdinger-taiwan-data'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw '找不到 Docker。請先啟動 Docker Desktop。' }
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop 尚未啟動。' }
New-Item -ItemType Directory -Force -Path $Target | Out-Null

$Files = @('app.py','requirements.txt','cache_store.py','patch_chart.py','patch_v04_backend.py','patch_v04_frontend.py','patch_v05_filters.py','patch_v06_backend.py','patch_v06_frontend.py','patch_v07_cache.py','patch_v07_fix.py','patch_v07_frontend.py','patch_v08_progress_backend.py','patch_v08_progress_view.py','patch_v08_progress_embed.py','patch_v081_ui.py','patch_v09_signal_quality.py','patch_v09_frontend.py','Dockerfile.v09')
foreach ($file in $Files) { Invoke-WebRequest "$Base/$file" -OutFile (Join-Path $Target $file) }

docker build --no-cache -f (Join-Path $Target 'Dockerfile.v09') -t $Image $Target
if ($LASTEXITCODE -ne 0) { throw 'Docker build 失敗。' }

foreach ($name in @('quantdinger-taiwan','quantdinger-taiwan-dashboard')) {
  $existing = docker ps -a --filter "name=^${name}$" --format '{{.Names}}'
  if ($existing -eq $name) { docker rm -f $name | Out-Null }
}

$volumeExists = docker volume ls --filter "name=^${Volume}$" --format '{{.Name}}'
if ($volumeExists -ne $Volume) { docker volume create $Volume | Out-Null }

docker run -d --name $Container --restart unless-stopped -p 127.0.0.1:8890:8890 -v "${Volume}:/app/data" $Image | Out-Null
Start-Sleep -Seconds 4
$status = docker ps --filter "name=^${Container}$" --format '{{.Status}}'
if (-not $status -or -not $status.StartsWith('Up')) { docker logs $Container --tail 80; throw 'QuantDinger Taiwan v0.9 啟動失敗。' }
Write-Host 'QuantDinger Taiwan v0.9 更新完成' -ForegroundColor Green
Write-Host 'http://127.0.0.1:8890'
