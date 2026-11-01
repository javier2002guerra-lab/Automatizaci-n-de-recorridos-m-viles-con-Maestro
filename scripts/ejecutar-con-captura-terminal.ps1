<#
.SYNOPSIS
  Abre una consola PowerShell visible, ejecuta allí scripts\ejecutar-pruebas.ps1 y, al terminar,
  captura una imagen PNG solo de esa ventana (no del resto del escritorio).
.DESCRIPTION
  La captura muestra la sesión real de terminal donde corrió Maestro. Se guarda en
  evidencias\<carpeta>\terminal-<escenario>.png
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\ejecutar-con-captura-terminal.ps1 -Escenario 01
#>
param(
  [Parameter(Mandatory = $true)][ValidateSet('01', '02', '03', 'conjunta')][string]$Escenario,
  [int]$TiempoMaximoSeg = 900
)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$carpeta = if ($Escenario -eq 'conjunta') { 'ejecucion-conjunta' } else { "escenario-$Escenario" }
$dirEvid = Join-Path $raiz "evidencias\$carpeta"
New-Item -ItemType Directory -Force $dirEvid | Out-Null
$marcaFin = Join-Path $env:TEMP "taskflow-fin-$Escenario.txt"
Remove-Item $marcaFin -ErrorAction SilentlyContinue
$titulo = "TaskFlow Maestro - $carpeta"

Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class Win {
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll", CharSet = CharSet.Unicode)] public static extern IntPtr FindWindow(string c, string t);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
  [DllImport("user32.dll")] public static extern bool MoveWindow(IntPtr h, int x, int y, int w, int hh, bool r);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("dwmapi.dll")] public static extern int DwmGetWindowAttribute(IntPtr h, int a, out RECT r, int s);
}
'@
[Win]::SetProcessDPIAware() | Out-Null
Add-Type -AssemblyName System.Drawing

$cmd = @"
`$Host.UI.RawUI.WindowTitle = '$titulo'
try { `$Host.UI.RawUI.BufferSize = New-Object Management.Automation.Host.Size(170, 3000) } catch {}
Set-Location '$raiz'
Write-Host 'PS $raiz> .\scripts\ejecutar-pruebas.ps1 -Escenario $Escenario' -ForegroundColor Yellow
& '$raiz\scripts\ejecutar-pruebas.ps1' -Escenario $Escenario
`$c = `$LASTEXITCODE
Write-Host "`nexit code del script: `$c" -ForegroundColor Cyan
Set-Content '$marcaFin' `$c
"@
$enc = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($cmd))
# conhost garantiza una ventana de consola clásica aunque Windows Terminal sea el predeterminado
$proc = Start-Process conhost.exe -ArgumentList "powershell.exe -NoProfile -ExecutionPolicy Bypass -NoExit -EncodedCommand $enc" -PassThru

$t0 = Get-Date
while (-not (Test-Path $marcaFin)) {
  if (((Get-Date) - $t0).TotalSeconds -gt $TiempoMaximoSeg) { throw 'Tiempo de espera agotado' }
  Start-Sleep -Seconds 2
}
$codigo = [int](Get-Content $marcaFin)
Start-Sleep -Seconds 2

$h = [Win]::FindWindow($null, $titulo)
if ($h -eq [IntPtr]::Zero) { throw "No se encontró la ventana '$titulo'" }
[Win]::ShowWindow($h, 9) | Out-Null   # SW_RESTORE
[Win]::MoveWindow($h, 0, 0, 1400, 1000, $true) | Out-Null
Start-Sleep -Milliseconds 600
[Win]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 900
$r = New-Object Win+RECT
# Límites reales de la ventana sin la sombra (DWMWA_EXTENDED_FRAME_BOUNDS = 9)
if ([Win]::DwmGetWindowAttribute($h, 9, [ref]$r, 16) -ne 0) { [Win]::GetWindowRect($h, [ref]$r) | Out-Null }
$w = $r.Right - $r.Left; $hh = $r.Bottom - $r.Top
$bmp = New-Object Drawing.Bitmap $w, $hh
$g = [Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.Left, $r.Top, 0, 0, $bmp.Size)
$png = Join-Path $dirEvid "terminal-$carpeta.png"
$bmp.Save($png, [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "Captura de terminal: $png ($w x $hh)"
Write-Host "Código de salida de la ejecución: $codigo"
# Cerrar la consola de la ejecución
Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue
exit $codigo
