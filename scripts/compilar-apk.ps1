<#
.SYNOPSIS
  Compila el APK release de TaskFlow Mobile (JS empaquetado dentro del APK, sin Metro).
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File scripts\compilar-apk.ps1
#>
param(
  [string]$Arquitecturas = 'arm64-v8a,x86_64'
)
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$app = Join-Path $raiz 'app'

if (-not $env:JAVA_HOME) { $env:JAVA_HOME = 'C:\Program Files\Java\jdk-21' }
if (-not $env:ANDROID_HOME) { $env:ANDROID_HOME = Join-Path $env:LOCALAPPDATA 'Android\Sdk' }
# Expo SDK 58 exige Node >= 22.13. Si existe una copia portable en C:\tools\node22 se usa primero.
if (Test-Path 'C:\tools\node22\node.exe') { $env:Path = "C:\tools\node22;$env:Path" }
Write-Host "Node usado: $(node -v)"
$env:NODE_ENV = 'production'
$env:CI = '1'

Push-Location $app
try {
  if (-not (Test-Path 'node_modules')) { npm ci; if ($LASTEXITCODE -ne 0) { throw 'npm ci falló' } }
  # android/ se genera a partir de app.json (Expo Continuous Native Generation)
  npx expo prebuild --platform android --clean
  if ($LASTEXITCODE -ne 0) { throw 'expo prebuild falló' }

  # El ninja de CMake 3.22.1 (1.10) no admite rutas > 260 caracteres en Windows y falla con el código
  # generado de react-native-safe-area-context. CMake 3.31.6 trae ninja 1.12.1, que sí las admite
  # (requiere LongPathsEnabled=1 en Windows). Se indica a Gradle mediante local.properties.
  $cmakeDir = Join-Path $env:ANDROID_HOME 'cmake\3.31.6'
  if (-not (Test-Path $cmakeDir)) { throw "Falta CMake 3.31.6: sdkmanager --install `"cmake;3.31.6`"" }
  $esc = { param($p) $p.Replace('\', '\\').Replace(':', '\:') }
  @("sdk.dir=$(& $esc $env:ANDROID_HOME)", "cmake.dir=$(& $esc $cmakeDir)") |
    Set-Content (Join-Path $app 'android\local.properties') -Encoding ascii

  Push-Location 'android'
  try {
    & .\gradlew.bat assembleRelease "-PreactNativeArchitectures=$Arquitecturas" --no-daemon
    if ($LASTEXITCODE -ne 0) { throw "gradlew assembleRelease falló (código $LASTEXITCODE)" }
  } finally { Pop-Location }

  $apk = Join-Path $app 'android\app\build\outputs\apk\release\app-release.apk'
  if (-not (Test-Path $apk)) { throw "No se encontró el APK en $apk" }
  $salida = Join-Path $raiz 'build'
  New-Item -ItemType Directory -Force $salida | Out-Null
  $destino = Join-Path $salida 'TaskFlowMobile-1.0.0.apk'
  Copy-Item $apk $destino -Force
  $hash = (Get-FileHash $destino -Algorithm SHA256).Hash
  Write-Host "APK generado: $destino"
  Write-Host "Tamaño: $([math]::Round((Get-Item $destino).Length / 1MB, 2)) MB"
  Write-Host "SHA-256: $hash"
} finally { Pop-Location }
