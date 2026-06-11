# ================================================================
#  setup_iis.ps1  —  Instalación automática en IIS
#  Quiniela Deportiva
#
#  Ejecutar como Administrador en el servidor Windows:
#      .\setup_iis.ps1
#
#  Parámetros opcionales (los valores por defecto sirven en la
#  mayoría de los casos):
#      -AppPath   Carpeta donde copiaste los archivos de la app
#      -AppPool   Nombre del Application Pool a crear
#      -SiteName  Nombre del sitio en IIS
#      -Port      Puerto HTTP del sitio
# ================================================================
param(
    [string]$AppPath  = "C:\inetpub\wwwroot\quiniela",
    [string]$AppPool  = "QuinielaPool",
    [string]$SiteName = "Quiniela",
    [int]   $Port     = 80
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$msg) {
    Write-Host ""
    Write-Host "==> $msg" -ForegroundColor Cyan
}

# ----------------------------------------------------------------
# 0. Verificar que se ejecuta como Administrador
# ----------------------------------------------------------------
$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "ERROR: ejecuta este script como Administrador." -ForegroundColor Red
    exit 1
}

# ----------------------------------------------------------------
# 1. Habilitar IIS + FastCGI
# ----------------------------------------------------------------
Write-Step "Habilitando IIS y FastCGI..."

$isServer = (Get-WmiObject Win32_OperatingSystem).ProductType -ne 1
if ($isServer) {
    # Windows Server: usar Install-WindowsFeature
    $features = @('Web-Server','Web-CGI','Web-ISAPI-Ext','Web-ISAPI-Filter',
                   'Web-Static-Content','Web-Default-Doc','Web-Http-Errors')
    foreach ($f in $features) {
        $state = (Get-WindowsFeature -Name $f).InstallState
        if ($state -ne 'Installed') {
            Write-Host "  Instalando feature: $f"
            Install-WindowsFeature -Name $f -IncludeManagementTools | Out-Null
        } else {
            Write-Host "  OK (ya instalado): $f"
        }
    }
} else {
    # Windows 10/11: usar Enable-WindowsOptionalFeature
    $features = @('IIS-WebServerRole','IIS-WebServer','IIS-CGI',
                   'IIS-ISAPIExtensions','IIS-ISAPIFilter','IIS-StaticContent')
    foreach ($f in $features) {
        $state = (Get-WindowsOptionalFeature -Online -FeatureName $f).State
        if ($state -ne 'Enabled') {
            Write-Host "  Habilitando: $f"
            Enable-WindowsOptionalFeature -Online -FeatureName $f -All -NoRestart | Out-Null
        } else {
            Write-Host "  OK (ya habilitado): $f"
        }
    }
}

# ----------------------------------------------------------------
# 2. Detectar Python
# ----------------------------------------------------------------
Write-Step "Detectando instalación de Python..."

$pythonExe = $null

# Buscar en PATH primero
$fromPath = Get-Command python.exe -ErrorAction SilentlyContinue
if ($fromPath) { $pythonExe = $fromPath.Source }

# Si no está en PATH, buscar en rutas comunes
if (-not $pythonExe) {
    $candidates = @(
        "C:\Python313\python.exe",
        "C:\Python312\python.exe",
        "C:\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:ProgramFiles\Python313\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:ProgramFiles\Python311\python.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $pythonExe = $c; break }
    }
}

if (-not $pythonExe) {
    Write-Host "ERROR: Python no encontrado." -ForegroundColor Red
    Write-Host "Instalá Python 3.11+ desde https://python.org y volvé a ejecutar." -ForegroundColor Yellow
    exit 1
}

$pyVersion = & $pythonExe --version 2>&1
Write-Host "  Encontrado: $pyVersion en $pythonExe"

# ----------------------------------------------------------------
# 3. Instalar dependencias
# ----------------------------------------------------------------
Write-Step "Instalando dependencias Python..."
& $pythonExe -m pip install --upgrade pip --quiet
& $pythonExe -m pip install -r "$AppPath\requirements.txt" --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR al instalar dependencias." -ForegroundColor Red; exit 1
}
Write-Host "  Dependencias instaladas OK"

# ----------------------------------------------------------------
# 4. Obtener path de wfastcgi.py
# ----------------------------------------------------------------
Write-Step "Configurando wfastcgi..."
$wfastcgiPy = (& $pythonExe -c "import wfastcgi, os; print(os.path.abspath(wfastcgi.__file__))" 2>&1).Trim()
if (-not $wfastcgiPy -or $wfastcgiPy -like "*Error*") {
    Write-Host "ERROR: wfastcgi no encontrado. Revisá que esté en requirements.txt." -ForegroundColor Red
    exit 1
}
$scriptProcessor = "$pythonExe|$wfastcgiPy"
Write-Host "  ScriptProcessor: $scriptProcessor"

# Registrar aplicación FastCGI en IIS (global)
$appcmd = "$env:windir\system32\inetsrv\appcmd.exe"
if (Test-Path $appcmd) {
    & $appcmd set config /section:system.webServer/fastCGI `
        "/+[fullPath='$pythonExe',arguments='$wfastcgiPy',instanceMaxRequests='10000']" 2>$null
    Write-Host "  FastCGI registrado en IIS"
}

# ----------------------------------------------------------------
# 5. Generar SECRET_KEY aleatoria
# ----------------------------------------------------------------
$rng   = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$bytes = New-Object byte[] 48
$rng.GetBytes($bytes)
$secretKey = [Convert]::ToBase64String($bytes)

# ----------------------------------------------------------------
# 6. Escribir web.config definitivo
# ----------------------------------------------------------------
Write-Step "Generando web.config..."
$webConfigContent = @"
<?xml version="1.0" encoding="utf-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="Python FastCGI"
           path="*"
           verb="*"
           modules="FastCgiModule"
           scriptProcessor="$scriptProcessor"
           resourceType="Unspecified"
           requireAccess="Script" />
    </handlers>
    <staticContent>
      <mimeMap fileExtension=".ico"   mimeType="image/x-icon" />
      <mimeMap fileExtension=".woff"  mimeType="font/woff" />
      <mimeMap fileExtension=".woff2" mimeType="font/woff2" />
    </staticContent>
  </system.webServer>
  <appSettings>
    <add key="WSGI_HANDLER"  value="wsgi.app" />
    <add key="PYTHONPATH"    value="$AppPath" />
    <add key="FLASK_CONFIG"  value="production" />
    <add key="SECRET_KEY"    value="$secretKey" />
  </appSettings>
</configuration>
"@
$webConfigContent | Out-File -FilePath "$AppPath\web.config" -Encoding utf8
Write-Host "  web.config generado con SECRET_KEY aleatoria"

# ----------------------------------------------------------------
# 7. Crear Application Pool
# ----------------------------------------------------------------
Write-Step "Configurando Application Pool '$AppPool'..."
Import-Module WebAdministration
if (!(Test-Path "IIS:\AppPools\$AppPool")) {
    New-WebAppPool -Name $AppPool | Out-Null
    Write-Host "  Pool creado"
} else {
    Write-Host "  Pool ya existe, actualizando..."
}
Set-ItemProperty "IIS:\AppPools\$AppPool" managedRuntimeVersion ""
Set-ItemProperty "IIS:\AppPools\$AppPool" processModel.identityType "ApplicationPoolIdentity"
Set-ItemProperty "IIS:\AppPools\$AppPool" startMode "AlwaysRunning"

# ----------------------------------------------------------------
# 8. Crear o actualizar sitio IIS
# ----------------------------------------------------------------
Write-Step "Configurando sitio IIS '$SiteName'..."
if (!(Test-Path "IIS:\Sites\$SiteName")) {
    New-WebSite -Name $SiteName -Port $Port -PhysicalPath $AppPath -ApplicationPool $AppPool | Out-Null
    Write-Host "  Sitio '$SiteName' creado en puerto $Port"
} else {
    Set-ItemProperty "IIS:\Sites\$SiteName" physicalPath $AppPath
    Set-ItemProperty "IIS:\Sites\$SiteName" applicationPool $AppPool
    Write-Host "  Sitio existente actualizado"
}

# ----------------------------------------------------------------
# 9. Permisos de carpeta
# ----------------------------------------------------------------
Write-Step "Configurando permisos de carpeta..."
$iisIdentity = "IIS AppPool\$AppPool"

# Lectura + ejecución en toda la app
$acl = Get-Acl $AppPath
$readRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $iisIdentity,
    [System.Security.AccessControl.FileSystemRights]"ReadAndExecute",
    [System.Security.AccessControl.InheritanceFlags]"ContainerInherit,ObjectInherit",
    [System.Security.AccessControl.PropagationFlags]::None,
    [System.Security.AccessControl.AccessControlType]::Allow
)
$acl.AddAccessRule($readRule)
Set-Acl $AppPath $acl

# Escritura en instance/ (SQLite necesita escribir ahí)
$instancePath = Join-Path $AppPath "instance"
New-Item -ItemType Directory -Force -Path $instancePath | Out-Null
$acl2 = Get-Acl $instancePath
$writeRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $iisIdentity,
    [System.Security.AccessControl.FileSystemRights]"Modify",
    [System.Security.AccessControl.InheritanceFlags]"ContainerInherit,ObjectInherit",
    [System.Security.AccessControl.PropagationFlags]::None,
    [System.Security.AccessControl.AccessControlType]::Allow
)
$acl2.AddAccessRule($writeRule)
Set-Acl $instancePath $acl2
Write-Host "  Permisos asignados a: $iisIdentity"

# ----------------------------------------------------------------
# 10. Inicializar base de datos
# ----------------------------------------------------------------
Write-Step "Inicializando base de datos..."
$env:FLASK_CONFIG = "production"
& $pythonExe "$AppPath\init_db.py"

# ----------------------------------------------------------------
# 11. Reiniciar IIS
# ----------------------------------------------------------------
Write-Step "Reiniciando IIS..."
iisreset /noforce | Out-Null
Write-Host "  IIS reiniciado"

# ----------------------------------------------------------------
# Resumen final
# ----------------------------------------------------------------
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  INSTALACION COMPLETADA EXITOSAMENTE" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "  URL del sitio : http://localhost:$Port"
Write-Host "  Admin usuario : admin"
Write-Host "  Admin clave   : admin123"
Write-Host ""
Write-Host "  IMPORTANTE:" -ForegroundColor Yellow
Write-Host "  - Cambia la contraseña del admin luego del" -ForegroundColor Yellow
Write-Host "    primer inicio de sesion." -ForegroundColor Yellow
Write-Host "  - La SECRET_KEY fue generada aleatoriamente" -ForegroundColor Yellow
Write-Host "    y guardada en web.config." -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Green
