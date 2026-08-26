import streamlit as st
import plotly.graph_objects as go

from engine import (
    extract_audio_features,
    transcribe_audio,
    analyze_context_and_recommend
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="VoiceGuard | AI Impersonation Defense",
    page_icon="🛡️",
    layout="wide"
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🛡️ VoiceGuard: AI Voice Impersonation Defense")

st.caption(
    "SIH Prototype: Deepfake Detection, Speaker Verification "
    "& Contextual Risk Engine"
)


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("Claimed Identity Profile")

    claimed_user = st.selectbox(
        "Claimed Speaker",
        [
            "Manager / Executive",
            "Family Member",
            "Bank Official",
            "Unknown"
        ]
    )

    st.divider()

    st.info(
        "The prototype evaluates acoustic signals, "
        "speaker similarity and NLP-based urgency cues."
    )


# --------------------------------------------------
# MAIN COLUMNS
# --------------------------------------------------

col_left, col_right = st.columns([1, 1])

audio_bytes = None


# --------------------------------------------------
# AUDIO CAPTURE
# --------------------------------------------------

with col_left:

    st.subheader("1. Audio Capture")

    input_method = st.radio(
        "Select Input Mode",
        [
            "Upload Audio File",
            "Record Microphone"
        ],
        horizontal=True
    )


    # -------------------------
    # UPLOAD
    # -------------------------

    if input_method == "Upload Audio File":

        uploaded_file = st.file_uploader(
            "Upload audio (WAV, MP3, M4A)",
            type=[
                "wav",
                "mp3",
                "m4a"
            ]
        )

        if uploaded_file is not None:

            audio_bytes = uploaded_file.read()

            st.audio(audio_bytes)


    # -------------------------
    # RECORD
    # -------------------------

    else:

        recorded_audio = st.audio_input(
            "Record voice sample"
        )

        if recorded_audio is not None:

            audio_bytes = recorded_audio.read()

            st.audio(audio_bytes)


# --------------------------------------------------
# THREAT ANALYSIS
# --------------------------------------------------

with col_right:

    st.subheader("2. Threat Analysis")

    if audio_bytes is not None:

        if st.button(
            "Run Full Impersonation Scan",
            type="primary",
            use_container_width=True
        ):

            with st.spinner(
                "Processing acoustic features, "
                "transcription and threat risk..."
            ):

                # -------------------------
                # AUDIO ANALYSIS
                # -------------------------

                audio_data = extract_audio_features(
                    audio_bytes
                )


                # -------------------------
                # TRANSCRIPTION
                # -------------------------

                transcript = transcribe_audio(
                    audio_bytes
                )


                # -------------------------
                # RISK ANALYSIS
                # -------------------------

                analysis = analyze_context_and_recommend(

                    transcript,

                    audio_data.get(
                        "synthetic_prob",
                        50.0
                    ),

                    audio_data.get(
                        "speaker_similarity",
                        50.0
                    )
                )


                # -------------------------
                # SAVE RESULTS
                # -------------------------

                st.session_state["results"] = {

                    "audio_data": audio_data,

                    "transcript": transcript,

                    "analysis": analysis
                }


    else:

        st.info(
            "Upload or record audio on the left "
            "to begin analysis."
        )


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if "results" in st.session_state:

    res = st.session_state["results"]

    audio_data = res["audio_data"]

    analysis = res["analysis"]


    # Safely retrieve values

    synthetic_prob = audio_data.get(
        "synthetic_prob",
        50.0
    )

    speaker_similarity = audio_data.get(
        "speaker_similarity",
        50.0
    )

    risk = analysis.get(
        "risk_score",
        50
    )


    # --------------------------------------------------
    # THREAT ASSESSMENT
    # --------------------------------------------------

    st.divider()

    st.subheader(
        "3. Threat Assessment Dashboard"
    )


    m1, m2, m3, m4 = st.columns(4)


    with m1:

        st.metric(
            "Synthetic Speech Prob.",
            f"{synthetic_prob}%"
        )


    with m2:

        st.metric(
            "Speaker Similarity",
            f"{speaker_similarity}%"
        )


    with m3:

        st.metric(
            "Contextual Threat",
            analysis.get(
                "context_risk",
                "UNKNOWN"
            )
        )


    with m4:

        st.metric(
            "Overall Risk Score",
            f"{risk}/100"
        )


    # --------------------------------------------------
    # GAUGE + TRANSCRIPT
    # --------------------------------------------------

    g_col, t_col = st.columns([1, 1])


    # -------------------------
    # RISK GAUGE
    # -------------------------

    with g_col:

        if risk > 70:

            gauge_color = "#ef4444"

        elif risk > 40:

            gauge_color = "#eab308"

        else:

            gauge_color = "#22c55e"


        fig = go.Figure(

            go.Indicator(

                mode="gauge+number",

                value=risk,

                title={
                    "text": "Impersonation Threat Level"
                },

                gauge={

                    "axis": {
                        "range": [0, 100]
                    },

                    "bar": {
                        "color": gauge_color
                    },

                    "steps": [

                        {
                            "range": [0, 40],
                            "color": "#1e293b"
                        },

                        {
                            "range": [40, 70],
                            "color": "#334155"
                        },

                        {
                            "range": [70, 100],
                            "color": "#475569"
                        }

                    ],

                    "threshold": {

                        "line": {
                            "color": "red",
                            "width": 4
                        },

                        "thickness": 0.75,

                        "value": 75
                    }
                }
            )
        )


        fig.update_layout(

            height=260,

            margin=dict(
                l=20,
                r=20,
                t=30,
                b=20
            ),

            paper_bgcolor="rgba(0,0,0,0)"
        )


        st.plotly_chart(
            fig,
            use_container_width=True
        )


    # -------------------------
    # TRANSCRIPT
    # -------------------------

    with t_col:

        st.markdown(
            "**ASR Transcript (Speech-to-Text):**"
        )

        st.write(
            f"_{res['transcript']}_"
        )


        st.markdown(
            "**Identified Triggers:** "
            f"`{analysis.get('triggers', 'None detected')}`"
        )


        if risk > 60:

            st.markdown(
                "**Verdict:** 🚨 Potential Voice Impersonation"
            )

        else:

            st.markdown(
                "**Verdict:** ✅ Authentic Speech"
            )


    # --------------------------------------------------
    # ACTION RECOMMENDATION
    # --------------------------------------------------

    st.subheader(
        "4. Action Recommendation & Incident Response"
    )


    recommendation = analysis.get(
        "recommendation",
        "Verify the caller through an independent channel."
    )


    if risk >= 70:

        st.error(
            f"**CRITICAL ACTION REQUIRED:**\n\n"
            f"{recommendation}"
        )


        b1, b2 = st.columns(2)


        with b1:

            st.button(
                "🔒 Block Transaction & Issue Alert",
                type="primary",
                use_container_width=True
            )


        with b2:

            st.button(
                "📞 Initiate Out-of-Band Callback",
                use_container_width=True
            )


    elif risk >= 40:

        st.warning(
            f"**VERIFICATION RECOMMENDED:**\n\n"
            f"{recommendation}"
        )


        st.button(
            "🔑 Request Predefined Challenge Phrase",
            use_container_width=True
        )


    else:

        st.success(
            f"**SAFE:**\n\n"
            f"{recommendation}"
        )
