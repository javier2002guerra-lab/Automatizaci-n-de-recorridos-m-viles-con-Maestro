<#
.SYNOPSIS
  Borra los datos locales de TaskFlow Mobile en el dispositivo/emulador de pruebas.
.DESCRIPTION
  Equivale a "Ajustes > Apps > TaskFlow Mobile > Borrar datos". Solo afecta al paquete
  gt.edu.umg.taskflow del dispositivo indicado; no toca otras apps ni datos del usuario.
  Los escenarios de Maestro ya hacen esta limpieza con launchApp + clearState: true,
  así que este script solo es necesario para dejar el emulador limpio de forma manual.
#>
param([string]$Dispositivo)
$sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
$adb = Join-Path $sdk 'platform-tools\adb.exe'
$sel = if ($Dispositivo) { @('-s', $Dispositivo) } else { @() }
& $adb @sel shell pm clear gt.edu.umg.taskflow
exit $LASTEXITCODE
