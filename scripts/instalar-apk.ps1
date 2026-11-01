<#
.SYNOPSIS
  Instala el APK de TaskFlow Mobile con ADB y verifica paquete y versión instalada.
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\instalar-apk.ps1 -Apk build\TaskFlowMobile-1.0.0.apk
#>
param(
  [string]$Apk = (Join-Path (Split-Path -Parent $PSScriptRoot) 'build\TaskFlowMobile-1.0.0.apk'),
  [string]$Dispositivo
)
$ErrorActionPreference = 'Stop'
$sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
$adb = Join-Path $sdk 'platform-tools\adb.exe'
if (-not (Test-Path $Apk)) { throw "No existe el APK: $Apk" }
$sel = if ($Dispositivo) { @('-s', $Dispositivo) } else { @() }

& $adb @sel devices -l
& $adb @sel install -r $Apk
if ($LASTEXITCODE -ne 0) { throw 'adb install falló' }
Write-Host '--- Paquete instalado ---'
& $adb @sel shell pm list packages gt.edu.umg.taskflow
& $adb @sel shell dumpsys package gt.edu.umg.taskflow | Select-String 'versionCode=|versionName='
