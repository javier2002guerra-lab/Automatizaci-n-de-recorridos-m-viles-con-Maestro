<#
.SYNOPSIS
  Ejecuta los escenarios de Maestro sobre TaskFlow Mobile y guarda registros, reportes JUnit y capturas.
.PARAMETER Escenario
  01, 02, 03 (individual) o "conjunta" (los tres en una sola ejecución de Maestro).
.PARAMETER Dispositivo
  Serial de ADB. Si se omite se usa el primer dispositivo conectado.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\ejecutar-pruebas.ps1 -Escenario 01
  powershell -ExecutionPolicy Bypass -File scripts\ejecutar-pruebas.ps1 -Escenario conjunta
#>
param(
  [Parameter(Mandatory = $true)][ValidateSet('01', '02', '03', 'conjunta')][string]$Escenario,
  [string]$Dispositivo
)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
if (-not $env:JAVA_HOME) { $env:JAVA_HOME = 'C:\Program Files\Java\jdk-21' }
$sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
$adb = Join-Path $sdk 'platform-tools\adb.exe'
$maestro = Join-Path $env:USERPROFILE '.maestro\maestro\bin\maestro.bat'
$env:MAESTRO_CLI_NO_ANALYTICS = '1'
$env:MAESTRO_CLI_ANALYSIS_NOTIFICATION_DISABLED = 'true'
$appId = 'gt.edu.umg.taskflow'

$flujos = @{
  '01'       = @{ Archivos = @('maestro/01-registro-exitoso.yaml'); Carpeta = 'escenario-01'; Nombre = 'escenario-01' }
  '02'       = @{ Archivos = @('maestro/02-validacion-entrada.yaml'); Carpeta = 'escenario-02'; Nombre = 'escenario-02' }
  '03'       = @{ Archivos = @('maestro/03-persistencia-reapertura.yaml'); Carpeta = 'escenario-03'; Nombre = 'escenario-03' }
  'conjunta' = @{ Archivos = @('maestro'); Carpeta = 'ejecucion-conjunta'; Nombre = 'ejecucion-conjunta' }
}[$Escenario]

# 1. Dispositivo disponible
if (-not $Dispositivo) {
  $Dispositivo = (& $adb devices | Select-String "`tdevice$" | Select-Object -First 1).ToString().Split("`t")[0]
}
if (-not $Dispositivo) { throw 'No hay ningún dispositivo Android conectado (adb devices).' }
$modelo = (& $adb -s $Dispositivo shell getprop ro.product.model).Trim()
$android = (& $adb -s $Dispositivo shell getprop ro.build.version.release).Trim()
$api = (& $adb -s $Dispositivo shell getprop ro.build.version.sdk).Trim()
$version = ((& $adb -s $Dispositivo shell dumpsys package $appId) | Select-String 'versionName=' | Select-Object -First 1).ToString().Trim()
if (-not $version) { throw "La app $appId no está instalada en $Dispositivo." }

# 2. Carpetas de salida
$marca = Get-Date -Format 'yyyyMMdd-HHmmss'
$dirEjec = Join-Path $raiz "resultados\ejecuciones\$($flujos.Nombre)-$marca"
$dirRep = Join-Path $raiz 'resultados\reportes'
$dirEvid = Join-Path $raiz "evidencias\$($flujos.Carpeta)"
New-Item -ItemType Directory -Force $dirEjec, $dirRep, $dirEvid | Out-Null
$log = Join-Path $dirEjec 'salida-terminal.log'
$junit = Join-Path $dirRep "$($flujos.Nombre)-junit.xml"

$inicio = Get-Date
$cabecera = @(
  "=== TaskFlow Mobile - Ejecución Maestro: $($flujos.Nombre) ===",
  "Fecha inicio : $($inicio.ToString('yyyy-MM-dd HH:mm:ss zzz'))",
  "Dispositivo  : $Dispositivo ($modelo, Android $android, API $api)",
  "Aplicación   : $appId $version",
  "Comando      : maestro test $($flujos.Archivos -join ' ') --format JUNIT --output $junit --test-output-dir $dirEjec\maestro --udid $Dispositivo",
  ''
)
$cabecera | Set-Content $log -Encoding utf8
$cabecera | Write-Host

# 3. Ejecución real de Maestro
Push-Location $raiz
try {
  $argsMaestro = @('test') + $flujos.Archivos + @('--format', 'JUNIT', '--output', $junit, '--test-output-dir', (Join-Path $dirEjec 'maestro'), '--udid', $Dispositivo, '--no-ansi')
  $ErrorActionPreference = 'Continue'
  & $maestro @argsMaestro 2>&1 | ForEach-Object { "$_" } | Tee-Object -FilePath $log -Append
  $codigo = $LASTEXITCODE
  $ErrorActionPreference = 'Stop'
} finally { Pop-Location }
$fin = Get-Date

# 4. Copiar capturas generadas por takeScreenshot a evidencias/
$capturas = Get-ChildItem (Join-Path $dirEjec 'maestro') -Recurse -Filter '*.png' -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -like 'escenario-*' }
foreach ($c in $capturas) { Copy-Item $c.FullName (Join-Path $dirEvid $c.Name) -Force }

$resultado = if ($codigo -eq 0) { 'APROBADO' } else { 'FALLIDO' }
$pie = @(
  '',
  "Fecha fin    : $($fin.ToString('yyyy-MM-dd HH:mm:ss zzz'))",
  "Duración     : $([math]::Round(($fin - $inicio).TotalSeconds, 1)) s",
  "Código salida: $codigo",
  "Resultado    : $resultado",
  "Capturas     : $($capturas.Count) copiadas a evidencias\$($flujos.Carpeta)"
)
$pie | Add-Content $log -Encoding utf8
$pie | Write-Host

[ordered]@{
  ejecucion     = $flujos.Nombre
  flujos        = $flujos.Archivos
  inicio        = $inicio.ToString('o')
  fin           = $fin.ToString('o')
  dispositivo   = $Dispositivo
  modelo        = $modelo
  android       = $android
  api           = $api
  app           = "$appId $version"
  maestro       = '2.12.0'
  codigoSalida  = $codigo
  resultado     = $resultado
  reporteJUnit  = (Resolve-Path $junit -ErrorAction SilentlyContinue | ForEach-Object { $_.Path.Replace("$raiz\", '') })
  capturas      = @($capturas | ForEach-Object { "evidencias/$($flujos.Carpeta)/$($_.Name)" })
} | ConvertTo-Json | Set-Content (Join-Path $dirEjec 'resumen.json') -Encoding utf8

exit $codigo
