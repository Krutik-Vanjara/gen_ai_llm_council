import streamlit as st
import requests
import pandas as pd
import sys
import os

# Path setup for local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import COUNCIL_MEMBERS, CHAIRMAN

st.set_page_config(page_title="Council Dashboard", layout="wide")

# 1. CUSTOM DARK UI
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    .stChatMessage { border: 1px solid #30363D; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    .status-online { color: #3FB950; font-weight: bold; text-shadow: 0 0 5px #3FB950; }
    .status-offline { color: #F85149; }
    </style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# 2. SIDEBAR HEALTH MONITOR
with st.sidebar:
    st.title("🏛️ Council Ops")
    if st.button("➕ New Session", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.subheader("📡 Heartbeat")

    # Check Chairman
    try:
        r = requests.get(f"{CHAIRMAN['url']}/api/tags", timeout=1.5)
        st.markdown(f"**Chairman:** <span class='status-online'>● ONLINE</span>", unsafe_allow_html=True)
    except:
        st.markdown("**Chairman:** <span class='status-offline'>● OFFLINE</span>", unsafe_allow_html=True)

    # Check Nodes
    for name, info in COUNCIL_MEMBERS.items():
        try:
            r = requests.get(f"{info['url']}/api/tags", timeout=1.0)
            st.markdown(f"**{name}:** <span class='status-online'>● ONLINE</span>", unsafe_allow_html=True)
        except:
            st.markdown(f"**{name}:** <span class='status-offline'>● OFFLINE</span>", unsafe_allow_html=True)

# 3. CHAT DISPLAY
st.title("Local LLM Council")
st.caption("Distributed Multi-Agent Consensus Network")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. CHAT INPUT & PROCESSING
if prompt := st.chat_input("Ask the council..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.status("🔗 Deliberating across distributed nodes...", expanded=True) as status:
            try:
                # Target the Orchestrator (Samuel-PC)
                response = requests.post("http://localhost:8000/api/chat", json={"message": prompt}, timeout=500)

                if response.status_code == 200:
                    data = response.json()
                    status.update(label=f"✅ Consensus Reached in {data['total_time']}", state="complete")

                    # --- RENDER ANALYTICS ---
                    st.subheader("📊 Council Performance")
                    c1, c2 = st.columns(2)

                    with c1:
                        st.write("**Latency (Seconds)**")
                        # Extract latency from the opinions dictionary
                        lats = {n: m["latency"] for n, m in data["opinions"].items()}
                        lats["Chairman"] = data["final"]["latency"]
                        st.bar_chart(pd.Series(lats))

                    with c2:
                        st.write("**Peer Review Scores**")
                        # Map scores from the reviews dictionary
                        score_data = [{"Node": name, "Score": r["score"]} for name, r in data["reviews"].items()]
                        st.table(pd.DataFrame(score_data))

                    st.divider()

                    # STAGE 1: INITIAL OPINIONS
                    st.markdown("### 📍 Stage 1: Initial Opinions")
                    node_tabs = st.tabs(list(data['opinions'].keys()))
                    for i, (name, content) in enumerate(data['opinions'].items()):
                        with node_tabs[i]:
                            st.info(f"Inference Time: {content['latency']}s")
                            st.write(content['response'])

                    st.divider()

                    # STAGE 2: PEER REVIEW
                    st.markdown("### ⚖️ Stage 2: Peer Review (Ring Logic)")
                    p_cols = st.columns(len(data['reviews']))
                    for i, (reviewer, r_data) in enumerate(data['reviews'].items()):
                        with p_cols[i]:
                            st.metric(f"Review by {reviewer}", f"{r_data['score']}/10")
                            with st.expander("View Critique"):
                                st.write(r_data['response'])

                    st.divider()

                    # STAGE 3: FINAL OUTPUT
                    st.markdown("### 👑 Stage 3: Chairman's Final Synthesis")
                    final_text = data['final']['response']
                    st.success(final_text)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": final_text
                    })
                else:
                    st.error(f"Backend Error: {response.status_code}")
            except Exception as e:
                st.error(f"Connection Failed: {e}")