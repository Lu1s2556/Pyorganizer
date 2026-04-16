# setup.ps1 - Instalador Automático para Windows
Write-Host "🎯 INSTALADOR ORGANIZADOR INTELIGENTE" -ForegroundColor Green
Write-Host "=============================================="

# 1. VERIFICAR PYTHON 3.12
Write-Host "`n1. 🔍 Verificando Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -like "*3.12*") {
        Write-Host "   ✅ Python 3.12 encontrado: $pythonVersion" -ForegroundColor Green
    }
    else {
        Write-Host "   ❌ Se requiere Python 3.12.7" -ForegroundColor Red
        Write-Host "   📥 Descargar: https://python.org/downloads" -ForegroundColor Cyan
        Write-Host "   💡 Asegúrate de marcar 'Add Python to PATH'" -ForegroundColor Yellow
        timeout /t 5
        Start-Process "https://www.python.org/downloads/"
        exit 1
    }
}
catch {
    Write-Host "   ❌ Python no encontrado" -ForegroundColor Red
    Write-Host "   📥 Descargar Python 3.12.7 desde python.org" -ForegroundColor Cyan
    timeout /t 5
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

# 2. CREAR ENTORNO VIRTUAL
Write-Host "`n2. 🐍 Creando entorno virtual..." -ForegroundColor Yellow

if (Test-Path "venv") {
    Write-Host "   ⚠️  Eliminando entorno virtual existente..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

try {
    python -m venv venv
    Write-Host "   ✅ Entorno virtual creado" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Error creando entorno virtual: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. ACTIVAR ENTORNO
Write-Host "`n3. 🔧 Activando entorno..." -ForegroundColor Yellow

try {
    & .\venv\Scripts\activate
    Write-Host "   ✅ Entorno virtual activado" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Error activando entorno: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. ACTUALIZAR PIP
Write-Host "`n4. 📦 Actualizando pip..." -ForegroundColor Yellow

try {
    python -m pip install --upgrade pip
    Write-Host "   ✅ pip actualizado" -ForegroundColor Green
}
catch {
    Write-Host "   ⚠️  Error actualizando pip, continuando..." -ForegroundColor Yellow
}

# 5. INSTALAR DEPENDENCIAS
Write-Host "`n5. 📦 Instalando dependencias..." -ForegroundColor Yellow

$dependencies = @(
    "PySide6==6.10.0",
    "watchdog==4.0.0", 
    "python-dateutil==2.9.0",
    "scikit-learn==1.5.2",
    "nltk==3.8.1",
    "textblob==0.17.1",
    "pywin32==306"
)

$successCount = 0
$errorCount = 0

foreach ($dep in $dependencies) {
    try {
        Write-Host "   📦 Instalando: $dep" -ForegroundColor Cyan
        python -m pip install $dep
        $successCount++
        Write-Host "   ✅ Instalado" -ForegroundColor Green
    }
    catch {
        Write-Host "   ❌ Error instalando $dep : $($_.Exception.Message)" -ForegroundColor Red
        $errorCount++
    }
    Start-Sleep -Milliseconds 500
}

# 6. VERIFICAR INSTALACIÓN
Write-Host "`n6. ✅ Verificando instalación..." -ForegroundColor Yellow

try {
    python -c "
print('🔍 Verificando importaciones...')
import PySide6.QtWidgets
import watchdog
import sklearn
import nltk
import textblob
print('✅ Todas las dependencias importan correctamente')
"
    Write-Host "   ✅ Verificación exitosa" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Error en verificación: $($_.Exception.Message)" -ForegroundColor Red
    $errorCount++
}

# 7. DESCARGAR DATOS NLTK (opcional)
Write-Host "`n7. 🧠 Configurando NLP..." -ForegroundColor Yellow

try {
    python -c "
import nltk
nltk.download('punkt', quiet=True)
print('✅ Recursos NLP descargados')
"
    Write-Host "   ✅ NLP configurado" -ForegroundColor Green
}
catch {
    Write-Host "   ⚠️  Error descargando recursos NLP (no crítico)" -ForegroundColor Yellow
}

# 8. RESULTADO FINAL
Write-Host "`n🎉 INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "=============================================="
Write-Host "✅ Dependencias instaladas: $successCount" -ForegroundColor Green

if ($errorCount -gt 0) {
    Write-Host "⚠️  Errores durante instalación: $errorCount" -ForegroundColor Yellow
}

Write-Host "`n🚀 PARA EJECUTAR LA APLICACIÓN:" -ForegroundColor Cyan
Write-Host "   .\venv\Scripts\activate" -ForegroundColor White
Write-Host "   python src\main.py" -ForegroundColor White

Write-Host "`n📝 O ejecuta directamente:" -ForegroundColor Cyan
Write-Host "   .\run.ps1" -ForegroundColor White

Write-Host "`n💡 Si hay problemas, ejecuta: .\troubleshoot.ps1" -ForegroundColor Yellow

# 9. CREAR SCRIPTS ADICIONALES
Write-Host "`n9. 🔧 Creando scripts de utilidad..." -ForegroundColor Yellow

# Crear script de ejecución rápida
$runScript = @'
# run.ps1 - Ejecutar aplicación
& .\venv\Scripts\activate
python src/main.py
'@
$runScript | Out-File -FilePath "run.ps1" -Encoding UTF8

# Crear script de troubleshooting
$troubleshootScript = @'
# troubleshoot.ps1 - Solucionar problemas
Write-Host "🔧 SOLUCIONADOR DE PROBLEMAS" -ForegroundColor Yellow

# Verificar Python
Write-Host "`n1. Verificando Python..." -ForegroundColor Cyan
python --version

# Verificar entorno
Write-Host "`n2. Verificando entorno virtual..." -ForegroundColor Cyan
if (Test-Path "venv") {
    Write-Host "   ✅ Entorno virtual existe" -ForegroundColor Green
} else {
    Write-Host "   ❌ Entorno virtual no encontrado" -ForegroundColor Red
}

# Verificar dependencias
Write-Host "`n3. Verificando dependencias..." -ForegroundColor Cyan
python -m pip list | Select-String "PySide6|watchdog|scikit-learn|nltk|textblob"

# Reinstalar si hay problemas
Write-Host "`n4. Para reinstalar dependencias:" -ForegroundColor Cyan
Write-Host "   pip install --force-reinstall PySide6==6.10.0 watchdog==4.0.0 scikit-learn==1.5.2 nltk==3.8.1 textblob==0.17.1 pywin32==306" -ForegroundColor White

pause
'@
$troubleshootScript | Out-File -FilePath "troubleshoot.ps1" -Encoding UTF8

Write-Host "   ✅ Scripts de utilidad creados" -ForegroundColor Green

# 10. MENSAJE FINAL
Write-Host "`n🎯 ¡TODO LISTO!" -ForegroundColor Green
Write-Host "=============================================="
Write-Host "✅ Entorno virtual configurado" -ForegroundColor Cyan
Write-Host "✅ Dependencias instaladas" -ForegroundColor Cyan
Write-Host "✅ Scripts de utilidad creados" -ForegroundColor Cyan

Write-Host "`n📞 Si tienes problemas:" -ForegroundColor Yellow
Write-Host "   1. Ejecuta .\troubleshoot.ps1" -ForegroundColor White
Write-Host "   2. Revisa que Python 3.12 esté instalado" -ForegroundColor White
Write-Host "   3. Verifica que 'Python' esté en el PATH" -ForegroundColor White

Write-Host "`n🚀 Para empezar: .\run.ps1" -ForegroundColor Green

# Esperar para que no se cierre
timeout /t 10
