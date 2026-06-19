@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 相見積もり比較アプリ

echo ============================================
echo    相見積もり比較アプリ を起動します
echo ============================================
echo.

REM --- Python を探す ---
set "PY="
where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py"
if not defined PY (
  echo [エラー] Python が見つかりません。
  echo.
  echo  1. https://www.python.org/downloads/ を開く
  echo  2. 「Download Python」でインストーラを入手
  echo  3. インストール画面の一番下「Add Python to PATH」に必ずチェック
  echo  4. インストール後、このファイルをもう一度ダブルクリック
  echo.
  pause
  exit /b 1
)

REM --- 初回だけ仮想環境を作成 ---
if not exist ".venv" (
  echo 初回セットアップ中です。数分かかることがあります...
  %PY% -m venv .venv
)

call ".venv\Scripts\activate.bat"

REM --- 必要なライブラリを用意（2回目以降はすぐ終わります） ---
echo 必要な部品を確認しています...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo.
  echo [エラー] ライブラリのインストールに失敗しました。
  echo インターネットに接続されているか確認して、もう一度お試しください。
  echo.
  pause
  exit /b 1
)

REM --- 3秒後にブラウザを自動で開く ---
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5000"

echo.
echo ============================================
echo   起動しました。ブラウザが自動で開きます。
echo   開かない場合は、ブラウザで次を開いてください:
echo       http://127.0.0.1:5000
echo.
echo   ※ この黒い画面は閉じないでください
echo     （閉じるとアプリが止まります）
echo   ※ 終わるときは、この画面で Ctrl + C を押すか
echo     画面の×ボタンで閉じてください
echo ============================================
echo.

python app.py
pause
