import os
import sqlite3
import json
from datetime import datetime
import streamlit as st
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import List, Literal

# ------------------------------------------------------------------
# API KEY CONFIGURATION & CLIENT INITIALIZATION
# ------------------------------------------------------------------
# 1. Try to get the key from local environment variables first
api_key = os.environ.get("OPENAI_API_KEY")

# 2. If it's not there, check Streamlit Secrets (Cloud)
if not api_key and "OPENAI_API_KEY" in st.secrets:
    api_key = st.secrets["OPENAI_API_KEY"]

# 3. If it's nowhere to be found, show the error
if not api_key:
    st.error("OpenAI API Key not found. Please set it via environment variables or Streamlit Secrets.")
    st.stop()

# Force-assign it back to the environment just in case, and initialize the client safely
os.environ["OPENAI_API_KEY"] = api_key
client = OpenAI(api_key=api_key) # Explicitly passing the key fixes initialization bugs

# ------------------------------------------------------------------
# DB SETUP & DATA LAYER
# ------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect("field_intelligence.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS field_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            visit_date TEXT,
            program_area TEXT,
            stakeholders TEXT,
            notes TEXT,
            key_findings TEXT,
            blockers TEXT,
            sentiment TEXT,
            sentiment_score INTEGER,
            follow_ups TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def save_entry(entry_data, ai_data):
    conn = sqlite3.connect("field_intelligence.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO field_entries (
            location, visit_date, program_area, stakeholders, notes,
            key_findings, blockers, sentiment, sentiment_score, follow_ups, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry_data['location'], entry_data['visit_date'], entry_data['program_area'],
        entry_data['stakeholders'], entry_data['notes'],
        json.dumps(ai_data.key_findings), json.dumps(ai_data.blockers_observed),
        ai_data.community_sentiment, ai_data.sentiment_score,
        json.dumps([f.model_dump() for f in ai_data.suggested_follow_ups]),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

# ------------------------------------------------------------------
# AI LAYER SCHEMA DEFINITION
# ------------------------------------------------------------------
class FollowUp(BaseModel):
    task: str = Field(description="Actionable next step task description.")
    priority: Literal["Low", "Medium", "High"]

class AIDebriefSchema(BaseModel):
    key_findings: List[str] = Field(description="Top critical takeaways from the field visit.")
    blockers_observed: List[str] = Field(description="Obstacles, delays, issues or system failures noticed.")
    community_sentiment: Literal["Positive", "Neutral", "Concerned", "Frustrated"]
    sentiment_score: int = Field(description="1 (Very Negative/Frustrated) to 5 (Very Positive)")
    suggested_follow_ups: List[FollowUp]

def process_field_data_with_ai(notes: str, program_area: str) -> AIDebriefSchema:
    import time
    
    # Simulate realistic network delay for the screen recording loading animation
    time.sleep(2) 
    
    # Return structured mock intelligence matching your Pydantic schema perfectly
    return AIDebriefSchema(
        key_findings=[
            f"Successfully evaluated the {program_area} facility constraints.",
            "Gathered direct critical stakeholder feedback regarding systemic issues.",
            "Local community expressed clear logistical requirements for immediate relief."
        ],
        blockers_observed=[
            "Critical operational bottleneck/machinery failure disrupting active delivery.",
            "Delayed materials processing slowing local community progression."
        ],
        community_sentiment="Concerned",
        sentiment_score=2,
        suggested_follow_ups=[
            FollowUp(task="Dispatch specialized technical unit to address immediate systemic blockages.", priority="High"),
            FollowUp(task="Schedule secondary follow-up accountability workshop with key stakeholders.", priority="Medium")
        ]
    )

# ------------------------------------------------------------------
# STREAMLIT USER INTERFACE
# ------------------------------------------------------------------
st.set_page_config(page_title="Field Intel", page_icon="🌐", layout="wide")

app_mode = st.sidebar.radio("Navigate", ["📝 Log Field Visit", "📊 Manager Dashboard"])

# --- MODE 1: LOG FIELD VISIT ---
if app_mode == "📝 Log Field Visit":
    st.title("📝 New Field Observation Log")
    st.subheader("Quick-submit portal for ground teams")
    
    # Switched clear_on_submit to False to safeguard async operations
    with st.form("field_log_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("📍 Location / Community Name", placeholder="e.g. Village Alpha, District 4")
            visit_date = st.date_input("📅 Date of Visit", value=datetime.today())
        with col2:
            program_area = st.selectbox("🚀 Program Area", ["Water & Sanitation", "Primary Education", "Mobile Clinics", "Infrastructure"])
            stakeholders = st.text_input("👥 Stakeholders Met", placeholder="e.g. Chief Elder, Dr. Smith, Local Teachers")
            
        st.write("---")
        notes = st.text_area("✍️ Free-form Notes & Brain Dump", height=150, 
                             placeholder="Type details here...")
        
        st.write("🎙️ **Voice Memo Intake**")
        # Native, hassle-free microphone recorder component
        audio_file_buffer = st.audio_input("Record your voice memo directly from your browser")
        
        submitted = st.form_submit_button("Submit & Analyze Log", type="primary")
        
        if submitted:
            if not location or (not notes and not audio_file_buffer):
                st.error("Please fill in the Location and add either text notes or a voice memo.")
            else:
                with st.spinner("Processing entry and extracting structured intelligence via AI..."):
                    
                    # Process native voice memo buffer if captured
                    if audio_file_buffer is not None:
                        st.info("Transcribing voice memo via Whisper...")
                        audio_filename = "temp_recording.wav"
                        
                        # Save buffer to a temp file for OpenAI's transcription SDK
                        with open(audio_filename, "wb") as f:
                            f.write(audio_file_buffer.getbuffer())
                        
                        with open(audio_filename, "rb") as audio_file:
                            transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                        
                        notes += f"\n\n[Transcribed Voice Memo]: {transcript.text}"
                        os.remove(audio_filename) # Clean up temp file

                    # Process final text package using OpenAI Structured Outputs
                    ai_insights = process_field_data_with_ai(notes, program_area)
                    
                    # Save into local SQLite DB
                    entry_payload = {
                        "location": location, "visit_date": str(visit_date),
                        "program_area": program_area, "stakeholders": stakeholders, "notes": notes
                    }
                    save_entry(entry_payload, ai_insights)
                    
                    st.success("Entry logged successfully! AI Summary generated.")
                    st.json(ai_insights.model_dump())

# --- MODE 2: MANAGER DASHBOARD ---
elif app_mode == "📊 Manager Dashboard":
    st.title("📊 Field Intelligence Dashboard")
    
    conn = sqlite3.connect("field_intelligence.db")
    import pandas as pd
    df = pd.read_sql_query("SELECT * FROM field_entries ORDER BY created_at DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("No field logs found yet.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Visits Logged", len(df))
        col2.metric("Unique Geographies", df['location'].nunique())
        col3.metric("Avg Sentiment Score", round(df['sentiment_score'].mean(), 1))
        
        st.write("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📈 Sentiment Trends by Program")
            sentiment_df = df.groupby('program_area')['sentiment_score'].mean().reset_index()
            st.bar_chart(data=sentiment_df, x='program_area', y='sentiment_score', use_container_width=True)
            
        with c2:
            st.markdown("### 🚨 High Priority Follow-ups")
            high_priority_tasks = []
            for idx, row in df.iterrows():
                tasks = json.loads(row['follow_ups'])
                for t in tasks:
                    if t.get('priority') == 'High':
                        high_priority_tasks.append({"Location": row['location'], "Program": row['program_area'], "Task": t.get('task')})
            if high_priority_tasks:
                st.dataframe(pd.DataFrame(high_priority_tasks), use_container_width=True, hide_index=True)
            else:
                st.write("No high priority issues flagged!")

        st.write("---")
        st.markdown("### 🗂️ Detailed Log Registry")
        for idx, row in df.iterrows():
            with st.expander(f"📍 {row['location']} — {row['program_area']} ({row['visit_date']})"):
                sub1, sub2 = st.columns(2)
                with sub1:
                    st.info(f"**Raw Notes:**\n{row['notes']}")
                with sub2:
                    st.success(f"**AI Generated Debrief:**\n"
                               f"* **Sentiment:** {row['sentiment']} ({row['sentiment_score']}/5)\n"
                               f"* **Key Findings:** {', '.join(json.loads(row['key_findings']))}\n"
                               f"* **Blockers:** {', '.join(json.loads(row['blockers']))}")
