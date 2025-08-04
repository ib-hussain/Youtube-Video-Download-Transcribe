@echo off
echo ================================================
echo     YouTube Transcriber - Complete Setup
echo ================================================
echo.
echo This script will:
echo 1. Download the Vosk model
echo 2. Download yt-dlp.exe
echo 3. Install Python dependencies
echo 4. Build the portable executable
echo.


REM Create requirements.txt if it doesn't exist
if not exist "requirements.txt" (
    echo Creating requirements.txt...
    (
    echo vosk^>=0.3.42
    echo imageio-ffmpeg^>=0.4.7
    echo yt-dlp^>=2023.1.6
    echo pyinstaller^>=5.0
    ) > requirements.txt
)

REM Install Python packages
echo Installing Python packages...
pip install --upgrade pip
pip install -r requirements.txt

REM Download Vosk model if not exists
if not exist "vosk_model" (
    echo.
    echo Downloading Vosk speech recognition model...
    echo This is a one-time download ^(~39MB^)
    echo.
    powershell -Command "& {Invoke-WebRequest -Uri 'https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip' -OutFile 'vosk-model.zip'}"
    
    if exist "vosk-model.zip" (
        echo Extracting Vosk model...
        powershell -Command "& {Expand-Archive -Path 'vosk-model.zip' -DestinationPath '.' -Force}"
        ren "vosk-model-small-en-us-0.15" "vosk_model"
        del "vosk-model.zip"
        echo ✓ Vosk model installed successfully!
    ) else (
        echo Failed to download Vosk model
        echo Please download manually from: https://alphacephei.com/vosk/models
        
        exit /b 1
    )
) else (
    echo ✓ Vosk model already exists
)

REM Download yt-dlp.exe if not exists
if not exist "yt-dlp.exe" (
    echo.
    echo Downloading yt-dlp.exe...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile 'yt-dlp.exe'}"
    
    if exist "yt-dlp.exe" (
        echo ✓ yt-dlp.exe downloaded successfully!
    ) else (
        echo Failed to download yt-dlp.exe
        
        exit /b 1
    )
) else (
    echo ✓ yt-dlp.exe already exists
)

REM Check if download.py exists
if not exist "download.py" (
    echo Error: download.py not found!
    echo Please ensure your main Python script is named 'download.py'
    
    exit /b 1
)

REM Check if audio.py exists
if not exist "audio.py" (
    echo Error: audio.py not found!
    echo Please ensure your audio processing script exists
    
    exit /b 1
)

echo.
echo ================================================
echo All dependencies ready! Building executable...
echo ================================================

REM Run the build script
call build_portable_exe.bat

echo.
echo ================================================
echo Setup Complete!
echo ================================================
echo.
echo Your portable YouTube Transcriber is ready in the 'portable_dist' folder.
echo The executable works on any Windows 10+ computer without requiring Python.
echo.
echo Total package size: ~200MB ^(includes AI model and all dependencies^)
echo.
exit
