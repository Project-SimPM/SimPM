@echo off
setlocal

echo [SimPM] Building Sphinx HTML docs...

rem Set PYTHONPATH to the src folder next to this script
set "PYTHONPATH=%~dp0src"

rem Run Sphinx: source = docs/source, output = docs/_build/html
python -m sphinx -b html "%~dp0docs\source" "%~dp0docs\_build\html"
if errorlevel 1 (
    echo [SimPM] Error: Sphinx build failed.
    exit /b %errorlevel%
)

echo [SimPM] Done. Docs built in docs\_build\html
echo [SimPM] Open docs\_build\html\index.html in your browser.

endlocal
