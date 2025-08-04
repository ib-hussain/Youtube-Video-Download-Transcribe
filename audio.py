import wave
import json
import subprocess
import os
from imageio_ffmpeg import get_ffmpeg_exe

debug = True

# Convert the video/audio files into audio(.wav) only
# Involves Pre-Processing on the audio files before conversion, to normalise all of them
ffmpeg_path = get_ffmpeg_exe()

def convert_to_wav(input_path: str = "temp_audio.mp4", output_path: str = "temp_audio1.wav"):
    """
    Convert audio file to WAV format with normalization.
    
    Args:
        input_path (str): Path to input audio file
        output_path (str): Path for output WAV file
    """
    # Check if input file exists
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Add audio normalization for better preprocessing
    cmd = [
        ffmpeg_path,
        "-y",                    # force overwrite without asking
        "-i", input_path,
        "-ac", "1",           # mono channel
        "-ar", "16000",       # 16 kHz sample rate
        "-acodec", "pcm_s16le",  # 16-bit PCM encoding (standard for WAV)
        "-loglevel", "error",    # suppress verbose output
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        if debug: print(f"Successfully converted {input_path} to {output_path}")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"FFmpeg conversion failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Conversion error: {e}")

def format_timestamp_srt(seconds):
    """Convert seconds to SRT timestamp format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

def format_timestamp_vtt(seconds):
    """Convert seconds to VTT timestamp format HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millisecs = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"

def create_srt_file(segments, output_path):
    """Create SRT subtitle file from segments"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(segments, 1):
            start_time = format_timestamp_srt(segment['start'])
            end_time = format_timestamp_srt(segment['end'])
            text = segment['text'].strip()
            
            if text:  # Only write non-empty segments
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

def create_vtt_file(segments, output_path):
    """Create VTT subtitle file from segments"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        
        for segment in segments:
            start_time = format_timestamp_vtt(segment['start'])
            end_time = format_timestamp_vtt(segment['end'])
            text = segment['text'].strip()
            
            if text:  # Only write non-empty segments
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

def group_words_into_segments(words, max_duration=5.0, max_words=10):
    """Group words into subtitle segments based on duration and word count"""
    if not words:
        return []
    
    segments = []
    current_segment = {
        'start': words[0]['start'],
        'end': words[0]['end'],
        'words': [words[0]]
    }
    
    for word in words[1:]:
        # Check if we should start a new segment
        segment_duration = word['end'] - current_segment['start']
        word_count = len(current_segment['words'])
        
        if segment_duration > max_duration or word_count >= max_words:
            # Finalize current segment
            current_segment['text'] = ' '.join([w['word'] for w in current_segment['words']])
            segments.append(current_segment)
            
            # Start new segment
            current_segment = {
                'start': word['start'],
                'end': word['end'],
                'words': [word]
            }
        else:
            # Add word to current segment
            current_segment['end'] = word['end']
            current_segment['words'].append(word)
    
    # Don't forget the last segment
    if current_segment['words']:
        current_segment['text'] = ' '.join([w['word'] for w in current_segment['words']])
        segments.append(current_segment)
    
    return segments

def transcribe_audio(audio_file_path: str = "temp_audio1.wav", 
                    generate_subtitles: bool = True,
                    subtitle_format: str = "both",  # "srt", "vtt", or "both"
                    output_base_name: str = None):
    """
    Transcribe audio and optionally generate subtitle files.
    
    Args:
        audio_file_path (str): Path to the audio file
        generate_subtitles (bool): Whether to generate subtitle files
        subtitle_format (str): Format for subtitles - "srt", "vtt", or "both"
        output_base_name (str): Base name for output files (without extension)
    
    Returns:
        str: Full transcript text
    """
    from vosk import Model, KaldiRecognizer
    
    # Check if audio file exists
    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
    
    model_path = "vosk_model"  # vosk-model-small-en-us-0.15
    
    # Check if model directory exists
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Vosk model not found at: {model_path}. Please download the model first.")
    
    wf = wave.open(audio_file_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
        raise ValueError(f"{audio_file_path} must be mono, 16-bit, 16kHz WAV file")
    
    model = Model(model_path)
    # Enable word-level timestamps
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)  # This enables word-level timing information
    
    results = []
    all_words = []
    
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            result = json.loads(rec.Result())
            results.append(result)
            # Extract words with timestamps
            if 'result' in result:
                all_words.extend(result['result'])
    
    # Get final result
    final_result = json.loads(rec.FinalResult())
    results.append(final_result)
    if 'result' in final_result:
        all_words.extend(final_result['result'])
    
    # Generate full transcript
    transcript = " ".join(r.get("text", "") for r in results)
    
    # Generate subtitle files if requested
    if generate_subtitles and all_words:
        if output_base_name is None:
            output_base_name = os.path.splitext(audio_file_path)[0]
        
        # Group words into subtitle segments
        segments = group_words_into_segments(all_words)
        
        if subtitle_format in ["srt", "both"]:
            srt_path = f"{output_base_name}.srt"
            create_srt_file(segments, srt_path)
            if debug: print(f"Generated SRT file: {srt_path}")
        
        if subtitle_format in ["vtt", "both"]:
            vtt_path = f"{output_base_name}.vtt"
            create_vtt_file(segments, vtt_path)
            if debug: print(f"Generated VTT file: {vtt_path}")
    
    wf.close()  # Close the wave file
    return transcript
