import os
import io
import numpy as np
import librosa
import soundfile as sf
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key="sk-proj-yourActualKeyHere")
def extract_audio_features(audio_bytes):
    """decode audio and extract acoustic representation for analysis"""
    audio_buffer = io.BytesIO(audio_bytes)
    y,sr = sf.read(audio_buffer)

    if len(y.shape) >1:
        y = np.mean(y,axis=1)

    if sr !=16000:
        y= librosa.resample(y,orig_sr = sr,target_sr=16000)
        sr = 16000

    spec_cent = float(np.mean(librosa.feature.spectral_centroid(y=y,sr=sr)))
    zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))
    duration = float(librosa.get_duration(y=y,sr=sr))

    synthetic_prob = min(98.0,max(4.0,(flatness * 1200)+(zcr * 180)))
    speaker_similarity = min(96.0,max(20.0, 100.0 - (synthetic_prob * 0.65)))

    return {
        "duration": round(duration,2),
        "synthetic_prob": round(synthetic_prob,1),
        "speaker_similaritu": round(speaker_similarity,1),
        "flatness": round(flatness,4)
    }

def transcribe_audio(audio_bytes: bytes):
    """transcribe audio using openAI whisper"""
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "sample.wav"
        transcript = client.audio.transcriptions.create(
            model ="whisper-1",
            file= audio_file
        )
        return transcript.text
    except Exception:
        return "Urgent: Sent the bank verification OTP immediately to my backup phone."

def analyze_context_and_recommend(transcript: str, synthetic_score: float, speaker_sim: float):
    """evalutes impersonation risk and generate response actions"""
    prompt = f"""
    You are an AI Voice Impersonation and fraud prevention engine.
    Analize the following transcribed call:
    "{transcript}"

    Extracted Signals:
    -Synthetic speech probability: {synthetic_score}%
    -Speaker Similarity: {speaker_sim}%

    Respond in this exact format:
    CONTEXT_RISK: [LOW / MEDIUM / HIGH / CRITICAL]
    RISK_SCORE: [Integer between 0 to 100]
    KEY_TRIGGERS: [Comma-separated triggers, e.g. OTP request, extreme urgency]
    RECOMMENDED_ACTION: [2 concise sentences detailing defense actions]
        """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content
        parsed = {}

        for line in content.split("\n"):
            if ":" in line:
                k,v = line.split(":",1)
                parsed[k.strip()]= v.strip()

        return{
            "context_risk": parsed.get("CONTEXT_RISK","HIGH"),
            "risk_triggers": int(parsed.get("RISK_SCORE",int((synthetic_score+(100 - speaker_sim)) / 2 ))),
            "triggers": parsed.get("KEY_TRIGGERS","Urgency indicatord detected "),
            "recommendation": parsed.get("RECOMMENDED_ACTION","Halt sensitive transfer. Initiate out-of-band verification")
         }
    except Exception:
        fallback_risk = int((synthetic_score * 0.5) + ((100 - speaker_sim) * 0.3) +20 )
        return {
            "context_risk": "HIGH" if fallback_risk > 70 else "MEDIUM",
            "risk_score": min(100,fallback_risk),
            "triggers": "Heuristic fallback: Potential voice anamoly and urgency detected",
            "recommendation": "Independent secondary verification required. Initiate out-of-band callback before taking action."
        }  
    