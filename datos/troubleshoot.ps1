# troubleshoot.ps1 - Diagnosticar y solucionar problemas
Write-Host "🔧 SOLUCIONADOR DE PROBLEMAS" -ForegroundColor Yellow
Write-Host "=========================================="

# 1. Verificar Python
Write-Host "`n1. 🐍 Verificando Python..." -ForegroundColor Cyan
$pythonVersion = python --version 2>&1
if ($pythonVersion -like "*3.12*") {
    Write-Host "   ✅ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ $pythonVersion - Se requiere 3.12" -ForegroundColor Red
}

# 2. Verificar entorno
Write-Host "`n2. 📁 Verificando entorno virtual..." -ForegroundColor Cyan
if (Test-Path "venv") {
    Write-Host "   ✅ Entorno virtual existe" -ForegroundColor Green
} else {
    Write-Host "   ❌ Entorno virtual no encontrado" -ForegroundColor Red
    Write-Host "   💡 Ejecuta: .\setup.ps1" -ForegroundColor Yellow
}

# 3. Verificar dependencias
Write-Host "`n3. 📦 Verificando dependencias..." -ForegroundColor Cyan
$deps = @("PySide6", "watchdog", "scikit-learn", "nltk", "textblob", "pywin32")

foreach ($dep in $deps) {
    $result = python -c "try: import $dep; print('OK'); except: print('MISSING')" 2>$null
    if ($result -eq "OK") {
        Write-Host "   ✅ $dep" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $dep - Faltante" -ForegroundColor Red
    }
}

# 4. Soluciones
Write-Host "`n4. 🛠️ Soluciones:" -ForegroundColor Cyan

if (Test-Path "venv") {
    Write-Host "   💡 Reactivar entorno: .\venv\Scripts\activate" -ForegroundColor White
}

Write-Host "   💡 Reinstalar dependencias: pip install --force-reinstall PySide6==6.10.0 watchdog==4.0.0 scikit-learn==1.5.2 nltk==3.8.1 textblob==0.17.1 pywin32==306" -ForegroundColor White

Write-Host "   💡 Recrear entorno: Borrar carpeta 'venv' y ejecutar .\setup.ps1" -ForegroundColor White

Write-Host "`n5. 🔍 Verificar PATH de Python:" -ForegroundColor Cyan
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path
if ($pythonPath) {
    Write-Host "   ✅ Python en: $pythonPath" -ForegroundColor Green
} else {
    Write-Host "   ❌ Python no encontrado en PATH" -ForegroundColor Red
}

pause
