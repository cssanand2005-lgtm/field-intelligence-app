# Field Intelligence Platform

A lightweight, high-performance edge intelligence pipeline designed for field monitoring, infrastructural tracking, and humanitarian operations. This platform bridges the gap between unstructured ground logs and structured enterprise analytics by transcribing voice memos and applying strict JSON schema constraints via AI.

## ?? Key Features
- **Dual-Modal Ingestion:** Supports direct free-form text inputs alongside browser-native audio capturing via st.audio_input.
- **Structured Data Extraction:** Processes raw logs through OpenAI's structured output engine to enforce absolute schema validation without structural hallucinations.
- **Embedded Caching Layer:** Zero-dependency relational database storage utilizing an embedded SQLite layer to ensure easy deployment.
- **Analytical Dashboard:** Aggregates real-time KPIs, program-specific sentiment distributions, and filters high-priority action items.

## ?? Quickstart Guide

### Installation
1. Clone this repository:
   git clone https://github.com/cssanand2005-lgtm/field-intelligence-app.git
2. Install dependencies:
   pip install -r requirements.txt

### Execution
   streamlit run app2.py
