@echo off
chcp 65001 >nul
title 猫耳女友桌宠
cd /d "%~dp0"
set "PYTHONW=C:\ProgramData\anaconda3\pythonw.exe"
set "TCL_LIBRARY=C:\ProgramData\anaconda3\tcl\tcl8.6"
set "TK_LIBRARY=C:\ProgramData\anaconda3\tcl\tk8.6"
start "" "%PYTHONW%" pet.pyw
