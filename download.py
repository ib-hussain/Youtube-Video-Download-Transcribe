import os
import sys
import subprocess
import re
from audio import transcribe_audio as transcript, convert_to_wav as convert

def get_bundled_ytdlp_path():
    """Get path to bundled yt-dlp.exe"""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    ytdlp_path = os.path.join(base_path, 'yt-dlp.exe')
    if os.path.exists(ytdlp_path):
        return ytdlp_path
    else:
        # Fallback to system yt-dlp
        return 'yt-dlp'

def extract_video_id(input_str):
    """Extract video ID from YouTube URL or return the input if it's already a video ID"""
    # Pattern for YouTube URLs
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
    ]
    
    for pattern in youtube_patterns:
        match = re.search(pattern, input_str.strip())
        if match:
            return match.group(1)
    
    return None

def main():
    try:
        print("=" * 60)
        print("      YouTube Video Transcription Tool")
        print("=" * 60)
        
        # Get user choice
        while True:
            print("\nChoose an option:")
            print("a) Transcribe an existing MP4 file")
            print("b) Download and transcribe from YouTube")
            
            choice = input("\nEnter your choice (a or b): ").strip().lower()
            if choice in ['a', 'b']:
                break
            print("Error: Please enter 'a' or 'b'")
        
        if choice == 'a':
            # Option A: Existing MP4 file
            while True:
                file_path = input("Enter the path to your MP4 file: ").strip()
                if file_path and os.path.exists(file_path):
                    if file_path.lower().endswith('.mp4'):
                        break
                    else:
                        print("Error: Please provide a valid MP4 file")
                else:
                    print("Error: File not found. Please enter a valid file path")
            
            # Extract filename without extension for output naming
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_base_name = f"transcript_{base_name}"
            
            print(f"Processing file: {file_path}")
            
            # Convert to WAV
            print("Converting to WAV format...")
            try:
                convert(input_path=file_path)
                print("Conversion completed!")
            except Exception as e:
                print(f"Conversion failed: {e}")
                input("Press Enter to exit...")
                return
            
            # Generate transcript and subtitles
            print("Generating transcript and subtitles...")
            try:
                trans = transcript(
                    generate_subtitles=True, 
                    subtitle_format="both",
                    output_base_name=output_base_name
                )
                print("Transcription completed!")
            except Exception as e:
                print(f"Transcription failed: {e}")
                print("Make sure the vosk_model folder is present")
                input("Press Enter to exit...")
                return
            
            # Show generated files
            srt_file = f"{output_base_name}.srt"
            vtt_file = f"{output_base_name}.vtt"
            wav_file = "temp_audio1.wav"
            
        else:
            # Option B: YouTube download
            while True:
                user_input = input("Enter YouTube URL or video ID: ").strip()
                if user_input:
                    video_id = extract_video_id(user_input)
                    if video_id:
                        break
                    else:
                        print("Error: Invalid YouTube URL or video ID format")
                        print("Examples:")
                        print("  - https://www.youtube.com/watch?v=bKgf5PaBzyg")
                        print("  - https://youtu.be/bKgf5PaBzyg")
                        print("  - bKgf5PaBzyg")
                else:
                    print("Error: Please enter a valid input")
            
            output_path = f"temp_audio_{video_id}.mp4"
            ytdlp_cmd = get_bundled_ytdlp_path()
            
            # Check if file already exists
            if not os.path.exists(output_path):
                print(f"Downloading {output_path}...")
                command = f'"{ytdlp_cmd}" -f mp4 -o "{output_path}" --force-overwrites https://www.youtube.com/watch?v={video_id}'
                
                print("Running download command...")
                result = subprocess.run(command, shell=True)
                if result.returncode != 0:
                    print("Download failed. Please check:")
                    print("  - Your internet connection")
                    print("  - The video ID is correct")
                    print("  - Video is available")
                    input("Press Enter to exit...")
                    return
                print("Download completed successfully!")
            else:
                print(f"File {output_path} already exists, skipping download.")
            
            # Convert to WAV
            print("Converting to WAV format...")
            try:
                convert(input_path=output_path)
                print("Conversion completed!")
            except Exception as e:
                print(f"Conversion failed: {e}")
                input("Press Enter to exit...")
                return
            
            # Generate transcript and subtitles
            print("Generating transcript and subtitles...")
            try:
                trans = transcript(
                    generate_subtitles=True, 
                    subtitle_format="both",
                    output_base_name=f"transcript_{video_id}"
                )
                print("Transcription completed!")
            except Exception as e:
                print(f"Transcription failed: {e}")
                print("Make sure the vosk_model folder is present")
                input("Press Enter to exit...")
                return
            
            # Show generated files
            srt_file = f"transcript_{video_id}.srt"
            vtt_file = f"transcript_{video_id}.vtt"
            wav_file = "temp_audio1.wav"
            output_base_name = f"transcript_{video_id}"
        
        print("\n" + "=" * 60)
        print("TRANSCRIPT:")
        print("=" * 60)
        print(trans)
        print("\n" + "=" * 60)
        
        print("Files generated:")
        files_created = []
        
        if choice == 'b' and os.path.exists(output_path):
            files_created.append(f"  {output_path} (Original audio)")
        if os.path.exists(wav_file):
            files_created.append(f"  {wav_file} (Processed audio)")
        if os.path.exists(srt_file):
            files_created.append(f"  {srt_file} (SRT subtitles)")
        if os.path.exists(vtt_file):
            files_created.append(f"  {vtt_file} (VTT subtitles)")
        
        for file in files_created:
            print(file)
        
        print(f"\n✓ All done! You can use the subtitle files with browser extensions.")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("\nPlease ensure:")
        print("  - Internet connection is working (for YouTube downloads)")
        print("  - vosk_model folder is in the same directory")
        print("  - File paths are correct")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()