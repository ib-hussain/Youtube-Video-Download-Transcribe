@echo off
echo ================================================
echo    Building Portable YouTube Transcription Tool
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    
    exit /b 1
)

REM Install/upgrade required packages
echo Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt

REM Check if vosk_model exists
if not exist "vosk_model" (
    echo Error: vosk_model folder not found!
    echo Please download the Vosk model and place it in the vosk_model folder
    echo Download from: https://alphacephei.com/vosk/models
    
    exit /b 1
)

REM Download latest yt-dlp.exe
echo Downloading latest yt-dlp.exe...
if not exist "yt-dlp.exe" (
    echo Downloading yt-dlp.exe from GitHub...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile 'yt-dlp.exe'}"
    if errorlevel 1 (
        echo Failed to download yt-dlp.exe
        echo Please download manually from: https://github.com/yt-dlp/yt-dlp/releases/latest
        
        exit /b 1
    )
    echo yt-dlp.exe downloaded successfully!
) else (
    echo yt-dlp.exe already exists, skipping download
)

REM Clean previous builds
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del *.spec

echo Building executable...

REM Build with all necessary dependencies including yt-dlp.exe
pyinstaller ^
    --onefile ^
    --name "YouTube_Transcriber" ^
    --add-data "vosk_model;vosk_model" ^
    --add-data "audio.py;." ^
    --add-binary "yt-dlp.exe;." ^
    --hidden-import=vosk ^
    --hidden-import=imageio_ffmpeg ^
    --hidden-import=wave ^
    --hidden-import=json ^
    --hidden-import=subprocess ^
    --collect-all=vosk ^
    --collect-all=imageio_ffmpeg ^
    --console ^
    download.py

if errorlevel 1 (
    echo Build failed!
    
    exit /b 1
)

echo.
echo ================================================
echo Build completed successfully!
echo ================================================
echo.
echo Your executable is located at: dist\YouTube_Transcriber.exe
echo.
echo Creating portable distribution...
if not exist "portable_dist" mkdir portable_dist
copy "dist\YouTube_Transcriber.exe" "portable_dist\"

REM Create a simple README for users
echo Creating README.txt...
(
echo YouTube Transcriber - Portable Version
echo =====================================
echo.
echo This is a fully portable YouTube transcription tool that works on any Windows 10+ computer.
echo.
echo HOW TO USE:
echo 1. Double-click YouTube_Transcriber.exe
echo 2. Enter a YouTube video ID when prompted ^(the part after "v=" in the URL^)
echo    Example: For https://www.youtube.com/watch?v=dQw4w9WgXcQ
echo    Enter: dQw4w9WgXcQ
echo 3. Wait for download, conversion, and transcription
echo 4. Your files will be created:
echo    - transcript_[VIDEO_ID].srt ^(for browser extensions^)
echo    - transcript_[VIDEO_ID].vtt ^(for web players^)
echo.
echo FEATURES:
echo - No internet required for transcription ^(after download^)
echo - Works without Python installation
echo - Includes all necessary dependencies
echo - Generates subtitles compatible with browser extensions
echo.
echo BROWSER EXTENSIONS:
echo Use the generated .srt files with extensions like:
echo - Substital ^(Chrome/Firefox^)
echo - YouTube Custom Subtitles
echo - +Sub
echo.
echo REQUIREMENTS:
echo - Windows 10 or later
echo - Internet connection for video download
echo - ~100MB free space for temporary files
echo.
echo Created with yt-dlp, Vosk, and Python
) > "portable_dist\README.txt"

echo.
echo ================================================
echo Portable distribution created in 'portable_dist' folder!
echo ================================================
echo.
echo The executable is now completely portable and includes:
echo ✓ yt-dlp.exe for downloading videos
echo ✓ Vosk model for speech recognition
echo ✓ FFmpeg for audio conversion
echo ✓ All Python dependencies
echo.
echo You can copy the 'portable_dist' folder to any Windows 10+ computer and it will work!
echo File size: ~200MB ^(includes AI model^)
echo.
exit
