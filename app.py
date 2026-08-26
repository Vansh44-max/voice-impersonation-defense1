import streamlit as st
import plotly.graph_objects as go
from engine import extract_audio_features, transcribe_audio, analyze_context_and_recommend

st.set_page_config(
    page_title="VoiceGuard | AI Impersonation Defense ",
    page_icon="🛡️",
    layout="wide"

)

st.title("🛡️ VoiceGuard: AI Impersonation Defense")

st.caption(" SIH Prototype: Deepfake Detection, Speaker Verification & Contextual Risk Engine")

with st.sidebar:
    st.header("Claimed Identity Profile")
    claimed_user = st.selectbox("Claimed Speaker", ["Manager / Executive", "Family Member", "Bank Official","Unknown"])
    st.divider()
    st.info("System evalutes acoustic synthesis , speaker profile similarity , and NLP urgency cues.")

col_left, col_right = st.columns([1, 1])
audio_bytes = None

with col_left:
    st.subheader("1. Audio Capture")
    input_method = st.radio("Select Input Mode",["Upload Audio File","Record Microphone"], horizontal=True)

    if input_method == "Upload Audio File":
        uploaded_file = st.file_uploader("Upload audio ( WAV,MP3)", type=["wav","mp3"])
        if uploaded_file is not None:
            audio_bytes = uploaded_file.read()
            st.audio(audio_bytes)
        else:
            recorded_audio = st.audio_input("Record voice sample")
            if recorded_audio is not None:
                audio_bytes= recorded_audio.read()

with col_right:
    st.subheader("2.Threat Analysis")
    if audio_bytes is not None:
        if st.button("Run Full Impersonation Scan", type="primary",use_container_width=True):
            with st.spinner("Processing acoustic features, transcription, and threat risk..."):
                audio_data = extract_audio_features(audio_bytes)
                transcript = transcribe_audio(audio_bytes)
                analysis = analyze_context_and_recommend(
                    transcript,
                    audio_data["synthetic_prob"],
                    audio_data["speaker_similarity"]
                )

                st.session_state["results"] = {
                    "audio_data": audio_data,
                    "transcript": transcript,
                    "analysis": analysis
                }
    else:
        st.info("Upload or record audio on the left to begin analysis.")
if "results" in st.session_state:
    res = st.session_state["results"]
    risk = res["analysis"]["risk_score"]

    st.divider()
    st.subheader("3. Threat Assessment Dashboard")

    m1,m2,m3,m4 = st.columns(4)
    with m1:
        st.metric("Synthetic Speech Prob.", f"{res['audio_data']['speaker_similarity']}%")
    with m2:
        st.metric("Speaker Similarity",f"{res['audio_data']['speaker_similarity']}%")
    with m3:
        st.metric("Contextual Threat", res["analysis"]["context_risk"])
    with m4:
        st.metric("Overall Riak Score : ", f"{risk}/100")

    g_col,t_col =st.columns([1, 1])

    with g_col:
        fig = go.Figure(go.indicator(
            mode = "gauge+number",
            value=risk,
            title={"text":"Impersonation Threat Level"},
            gauge={
                "axis":{"range":[0, 100]},
                "bar":{"color": "#ef4444" if risk > 70 else "#eab308" if risk > 40 else "#22c55e"},
                "steps": [
                    {"range": [0, 40], "color": "#1e293b"},
                    {"range": [40, 70], "color": "#334155"},
                    {"range": [70, 100], "color": "#475569" }
        
                    
                ],
                "threshold":{"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 75}

            }
        ))
        fig.update_layout(height=260, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig,use_container_width=True)

    with t_col:
        st.markdown("**ASR Transcript ( SPEECH-to-TEXT):**")
        st.write(f"_{res['transcript']}_")
        st.markdown(f"**Identified Triggers:** `{res['analysis']['triggers']}`")
        st.markdown(f"**Verdict:** {'🚨 Potential Voice Impersonation' if risk > 60 else '✅ Authentic Speech'}")


    st.subheader("4. Action Recommendation & Incident Response")
    if risk >= 70:
        st.error(f"**CRITICAL ACTION REQUIRED:**\n\n{res['analysis']['recommendation']}")
        b1,b2 = st.columns(2)
        with b1:
            st.button("🔒 Block Transaction & Issue Alert", type="primary", use_container_width=True)
        with b2:
            st.button("📞 Initiate Out-of-Band Callback", use_container_width=True)
    elif risk >= 40:
        st.warning(f"**VERIFICTION RECOMMENDED:**\n\n{res['analysis']['recommendation']}")
        st.button("🔑 Request Predefined Challenge Phrase",use_container_width=True)
    else:
        st.success(f"**SAFE:** {res['analysis']['recommendation']}") 
