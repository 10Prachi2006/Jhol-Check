import os
import math
from pydub import AudioSegment
from transformers import pipeline

# Define a class to handle voice processing, including audio preprocessing and speech recognition
class VoiceProcessor:
    def __init__(self, model_name="openai/whisper-small"):
        self.device = -1 
        self.asr_pipeline = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device=self.device
        )

        # Define a method to preprocess audio files, converting them to mono and resampling to 16kHz

    def preprocess_audio(self, input_path, output_path="/tmp/clean_st.wav"):
        audio = AudioSegment.from_file(input_path)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(output_path, format="wav")
        return output_path

        # Define a method to process large audio files by splitting them into chunks, transcribing each chunk, and combining the results

    def process_large_audio(self, audio_path, chunk_length_ms=30000):
        clean_path = self.preprocess_audio(audio_path)
        audio = AudioSegment.from_file(clean_path)
        total_duration = len(audio)
        chunks_count = math.ceil(total_duration / chunk_length_ms)
        
        full_transcript = []
        for i in range(chunks_count):
            start = i * chunk_length_ms
            end = min(start + chunk_length_ms, total_duration)
            chunk = audio[start:end]
            
            chunk_filename = f"/tmp/chunk_st_{i}.wav"
            chunk.export(chunk_filename, format="wav")
            
            try:
                result = self.asr_pipeline(chunk_filename)
                full_transcript.append(result["text"])
            except Exception:
                pass
            finally:
                if os.path.exists(chunk_filename):
                    os.remove(chunk_filename)
                    
        if os.path.exists(clean_path):
            os.remove(clean_path)
            
        return " ".join(full_transcript).strip()
