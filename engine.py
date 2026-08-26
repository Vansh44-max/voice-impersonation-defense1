import io
import os
import numpy as np
import librosa
import soundfile as sf
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None


def extract_audio_features(audio_bytes: bytes):
    """
    Extracts basic acoustic features from the uploaded audio.

    NOTE:
    These are prototype/demo estimates.
    They are NOT a trained deepfake detection model.
    """

    audio_buffer = io.BytesIO(audio_bytes)

    # Read audio
    y, sr = sf.read(audio_buffer)

    # Convert stereo audio to mono
    if len(y.shape) > 1:
        y = np.mean(y, axis=1)

    # Convert sample rate to 16 kHz
    if sr != 16000:
        y = librosa.resample(
            y,
            orig_sr=sr,
            target_sr=16000
        )
        sr = 16000

    # Basic acoustic features
    spec_cent = float(
        np.mean(
            librosa.feature.spectral_centroid(
                y=y,
                sr=sr
            )
        )
    )

    zcr = float(
        np.mean(
            librosa.feature.zero_crossing_rate(y)
        )
    )

    flatness = float(
        np.mean(
            librosa.feature.spectral_flatness(y=y)
        )
    )

    duration = float(
        librosa.get_duration(
            y=y,
            sr=sr
        )
    )

    # Prototype synthetic speech estimate
    synthetic_prob = min(
        98.0,
        max(
            4.0,
            (flatness * 1200) + (zcr * 180)
        )
    )

    # Prototype speaker similarity estimate
    speaker_similarity = min(
        96.0,
        max(
            20.0,
            100.0 - (synthetic_prob * 0.65)
        )
    )

    # IMPORTANT:
    # Return all values that the frontend expects.
    return {
        "duration": round(duration, 2),
        "synthetic_prob": round(synthetic_prob, 1),
        "speaker_similarity": round(speaker_similarity, 1),
        "spec_cent": round(spec_cent, 2),
        "flatness": round(flatness, 4)
    }


def transcribe_audio(audio_bytes: bytes):
    """
    Transcribes audio using OpenAI.
    Falls back to demo text if the API is unavailable.
    """

    if client:

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "sample.wav"

            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )

            return transcript.text

        except Exception as e:

            print("Transcription error:", e)

    # Prototype fallback
    return (
        "Urgent: Send the bank verification OTP immediately "
        "to my backup phone."
    )


def analyze_context_and_recommend(
    transcript: str,
    synthetic_score: float,
    speaker_sim: float
):
    """
    Evaluates threat risk and generates recommended action.
    """

    # Use OpenAI API if available
    if client:

        prompt = f"""
You are an AI Voice Impersonation and Fraud Prevention Engine.

Analyze the following transcribed call:

"{transcript}"

Extracted Signals:

Synthetic Speech Probability:
{synthetic_score}%

Speaker Similarity:
{speaker_sim}%

Respond in this exact format:

CONTEXT_RISK: [LOW / MEDIUM / HIGH / CRITICAL]
RISK_SCORE: [Integer between 0 and 100]
KEY_TRIGGERS: [Comma-separated triggers]
RECOMMENDED_ACTION: [2 concise sentences detailing defense actions]
"""

        try:

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )

            content = response.choices[0].message.content

            parsed = {}

            for line in content.split("\n"):

                if ":" in line:

                    key, value = line.split(":", 1)

                    parsed[key.strip()] = value.strip()

            # Safely convert risk score
            try:
                risk_score = int(
                    parsed.get(
                        "RISK_SCORE",
                        int(
                            (
                                synthetic_score
                                + (100 - speaker_sim)
                            ) / 2
                        )
                    )
                )

            except ValueError:

                risk_score = int(
                    (
                        synthetic_score
                        + (100 - speaker_sim)
                    ) / 2
                )

            return {
                "context_risk": parsed.get(
                    "CONTEXT_RISK",
                    "HIGH"
                ),

                "risk_score": risk_score,

                "triggers": parsed.get(
                    "KEY_TRIGGERS",
                    "Urgency indicators detected"
                ),

                "recommendation": parsed.get(
                    "RECOMMENDED_ACTION",
                    "Halt sensitive transfer. "
                    "Initiate out-of-band verification."
                )
            }

        except Exception as e:

            print("OpenAI analysis error:", e)

    # Prototype fallback risk engine
    calculated_risk = int(
        (synthetic_score * 0.5)
        + ((100 - speaker_sim) * 0.3)
        + 20
    )

    calculated_risk = min(
        98,
        max(15, calculated_risk)
    )

    if calculated_risk > 70:
        context_risk = "HIGH"

    elif calculated_risk > 40:
        context_risk = "MEDIUM"

    else:
        context_risk = "LOW"

    return {
        "context_risk": context_risk,
        "risk_score": calculated_risk,
        "triggers": (
            "Acoustic anomaly, "
            "Unverified voice profile, "
            "High urgency phrase pattern"
        ),
        "recommendation": (
            "Secondary verification mandatory. "
            "Initiate an out-of-band callback and hold "
            "any sensitive credential or transaction requests."
        )
    }
    
