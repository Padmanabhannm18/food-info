@echo off
rem Rebuild index.html and the QR from business.json, then push to GitHub Pages.
rem Usage: edit business.json, then double-click this file (or run: publish)
cd /d "%~dp0"
python make_qr.py --url https://padmanabhannm18.github.io/food-info/ || goto :error
git add -A || goto :error
git diff --cached --quiet && (echo Nothing changed. & goto :end)
git commit -m "Update business details" || goto :error
git push origin main || goto :error
echo.
echo Published. The page updates in 1-2 minutes: https://padmanabhannm18.github.io/food-info/
goto :end
:error
echo.
echo Publishing FAILED - see the message above.
:end
pause
