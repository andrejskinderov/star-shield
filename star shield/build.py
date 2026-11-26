"""Сборка игры в готовое приложение (Windows .exe / macOS / Linux).

    pip install -r requirements-dev.txt
    python build.py

Результат: папка dist/StarShield. Именно её содержимое загружают в Steam (через SteamPipe).
Сборку нужно делать на той системе, для которой выпускаете (exe собирается только на Windows).
"""
import os
import subprocess
import sys

sep = os.pathsep
cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed",
       "--onedir", "--name", "StarShield", "--add-data", f"assets{sep}assets", "main.py"]
if os.path.exists(os.path.join("assets", "icon.ico")):
    cmd += ["--icon", os.path.join("assets", "icon.ico")]
print(" ".join(cmd))
sys.exit(subprocess.call(cmd))
