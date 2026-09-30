@echo off
rem Backtest collection, ~35 h. Resumable: if the PC restarts, run this file again.
cd /d "%~dp0.."
set PYTHONUTF8=1
python backtest\collect.py counts >> data\backtest\collect.log 2>&1
python backtest\collect.py reviews >> data\backtest\collect.log 2>&1
echo DONE %date% %time% >> data\backtest\collect.log
