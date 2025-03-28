@echo off
start ngrok http 5000
python F:\telegram\server.py
pause
