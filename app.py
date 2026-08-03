import json
import os
import tempfile
import fitz  # PyMuPDF
import speech_recognition as sr
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv
from gtts import gTTS

from utils.download_pdf import create_pdf
from utils.embeddings import get_embeddings
from utils.pdf_loader import load_pdf
from utils.rag_chain import create_rag_chain
from utils.text_splitter import split_text
from utils.vector_store import create_vector_store

# Load environment variables
load_dotenv()

# Multi-level API Key Fallback
# Multi-level API Key Fallback (Local Env -> Cloud Secrets)
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    try:
        if "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

if api_key:
    os.environ["GROQ_API_KEY"] = api_key
else:
    st.warning("⚠️ GROQ_API_KEY missing! Add it to .env or Streamlit secrets.")
# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "bookmarks" not in st.session_state:
    st.session_state.bookmarks = []

if "recent_questions" not in st.session_state:
    st.session_state.recent_questions = []

if "pdf_page_num" not in st.session_state:
    st.session_state.pdf_page_num = 1

# Page Configuration
st.set_page_config(
    page_title="KnowGen AI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar Setup
with st.sidebar:
    st.markdown("""
    <div class="logo-box">
        <h1>🤖 KnowGen AI</h1>
        <p>Intelligent PDF Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🚀 Navigation")

    page = st.radio(
        "",
        [
            "🏠 Home",
            "📄 Upload PDF",
            "💬 AI Chat",
            "📝 Summary",
            "📚 Notes",
            "❓ Quiz",
            "🧠 Flashcards"
        ]
    )

    st.divider()
    st.markdown("### ⚙️ Settings")

    theme = st.selectbox(
        "🎨 Theme",
        ["🌞 Light", "🌙 Dark"],
        index=1
    )

    st.divider()
    st.markdown("""
    <div class="status-card">
        <h3>⚡ AI Status</h3>
        <p>🟢 Online</p>
        <p>🚀 Groq Powered</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("""
    <center>
    <small>
    Version 1.0<br>
    Made with ❤️ by Prajwal
    </small>
    </center>
    """, unsafe_allow_html=True)

    st.divider()
    st.markdown("### 🚀 Project Status")
    st.progress(100)
    st.success("✅ AI Ready")

# Dynamically Inject CSS based on selected Theme
if theme == "🌙 Dark":
    text_color = "#F8FAFC"
    bg_color = "#0B0F17"
    card_bg = "#111827"
    border_color = "#1F2937"
    input_bg = "#111827"
else:
    text_color = "#0F172A"
    bg_color = "#F8FAFC"
    card_bg = "#FFFFFF"
    border_color = "#E2E8F0"
    input_bg = "#FFFFFF"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}

.stApp {{
    background-color: {bg_color} !important;
    color: {text_color} !important;
}}

.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6, 
.stApp p, .stApp label, .stApp span, .stApp div, .stApp small {{
    color: {text_color} !important;
}}

section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #020617 0%, #1E3A8A 100%) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}}

section[data-testid="stSidebar"] * {{
    color: #FFFFFF !important;
}}

/* Form Inputs */
.stTextInput input, .stTextArea textarea, .stSelectbox div[role="button"] {{
    color: {text_color} !important;
    background-color: {input_bg} !important;
    border: 1px solid {border_color} !important;
    border-radius: 10px !important;
    padding: 10px 14px !important;
}}

.logo-box {{
    text-align: center;
}}

.logo-box h1 {{
    color: #60A5FA !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    margin-bottom: 0px !important;
}}

.logo-box p {{
    color: #94A3B8 !important;
    font-size: 13px !important;
}}

.status-card {{
    background: rgba(255, 255, 255, 0.08) !important;
    padding: 14px !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    backdrop-filter: blur(10px) !important;
}}

/* Metrics Box Styling */
div[data-testid="stMetric"] {{
    background-color: {card_bg} !important;
    border: 1px solid {border_color} !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
}}

div[data-testid="stMetricValue"] > div {{
    font-size: 24px !important;
    font-weight: 800 !important;
    color: #38BDF8 !important;
}}

.main-title {{
    text-align: center;
    color: #38BDF8 !important;
    font-size: 34px;
    font-weight: 800;
    margin-bottom: 0px;
}}

.sub-title {{
    text-align: center;
    color: #94A3B8 !important;
    font-size: 15px;
    margin-top: 4px;
}}

/* Standardized Buttons */
.stButton > button {{
    width: 100%;
    background: #2563EB !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}}

.stButton > button:hover {{
    background: #1D4ED8 !important;
}}

/* Custom Pagination Buttons */
div[data-testid="column"] div.stButton > button {{
    padding: 6px 12px !important;
    font-size: 13px !important;
    height: 38px !important;
}}

/* Page Number Badge Container */
.page-badge-box {{
    background: rgba(37, 99, 235, 0.12);
    border: 1px solid rgba(56, 189, 248, 0.3);
    color: #38BDF8 !important;
    height: 38px;
    line-height: 38px;
    border-radius: 8px;
    text-align: center;
    font-weight: 700;
    font-size: 13px;
}}

[data-testid="stFileUploader"] {{
    border: 2px dashed #3B82F6 !important;
    border-radius: 14px !important;
    padding: 20px !important;
    background-color: {card_bg} !important;
}}

.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 95% !important;
}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<h1 class='main-title'>🤖 KnowGen AI</h1>
<p class='sub-title'>Enterprise Intelligent PDF Knowledge Assistant</p>
""", unsafe_allow_html=True)

st.divider()

st.markdown("## 📄 Upload PDF")

uploaded_files = st.file_uploader(
    "Choose PDF files", type=["pdf"], accept_multiple_files=True, key="pdf_file_uploader"
)

# File Process Block
if uploaded_files:
    first_pdf = uploaded_files[0]
    st.success(f"✅ {len(uploaded_files)} File(s) Uploaded")
    st.subheader("📄 PDF Preview")

    first_pdf.seek(0)
    doc = fitz.open(stream=first_pdf.read(), filetype="pdf")
    total_pages = len(doc)

    # Validate Page Number State
    if st.session_state.pdf_page_num > total_pages:
        st.session_state.pdf_page_num = 1
    if st.session_state.pdf_page_num < 1:
        st.session_state.pdf_page_num = 1

    # Render High-Quality Page Preview
    page_doc = doc.load_page(st.session_state.pdf_page_num - 1)
    pix = page_doc.get_pixmap(dpi=140)

    # Centered Page Preview Container
    c1, c2, c3 = st.columns([1, 2.2, 1])

    with c2:
        st.image(pix.tobytes("png"), use_container_width=True)

        p_col1, p_col2, p_col3 = st.columns([1, 2, 1])

        with p_col1:
            if st.button("◄ Prev", key="btn_prev_page", disabled=(st.session_state.pdf_page_num <= 1)):
                st.session_state.pdf_page_num -= 1
                st.rerun()

        with p_col2:
            st.markdown(
                f"<div class='page-badge-box'>Page {st.session_state.pdf_page_num} of {total_pages}</div>",
                unsafe_allow_html=True
            )

        with p_col3:
            if st.button("Next ►", key="btn_next_page", disabled=(st.session_state.pdf_page_num >= total_pages)):
                st.session_state.pdf_page_num += 1
                st.rerun()

    progress = st.progress(0)
    status = st.empty()

    # Load & Combine Text from all PDFs
    status.info("📄 Reading PDF...")
    progress.progress(20)
    documents = []

    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        documents.extend(load_pdf(uploaded_file))

    pdf_text = "\n".join(
        [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in documents
        ]
    )
    word_count = len(pdf_text.split())
    reading_time = max(1, word_count // 200)

    status.info("✂️ Splitting Text...")
    progress.progress(50)
    chunks = split_text(documents)
    chunk_count = len(chunks)

    st.divider()

    # PDF Statistics
    st.subheader("📊 PDF Statistics")
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("📄 Words", f"{word_count:,}")

    with m2:
        st.metric("⏱ Reading Time", f"{reading_time} min")

    with m3:
        st.metric("📦 Chunks", chunk_count)

    with m4:
        st.metric("📃 Total Pages", total_pages)

    st.divider()

    st.subheader("🔍 Search in PDF")
    search_query = st.text_input("Enter keyword to search", key="pdf_search_input")

    if search_query:
        if search_query.lower() in pdf_text.lower():
            st.success(f'✅ "{search_query}" found in PDF')
        else:
            st.error(f'❌ "{search_query}" not found in PDF')

    # Vector Store & RAG Setup
    embeddings = get_embeddings()
    status.info("⚡ Generating Embeddings & Vector Store...")
    progress.progress(80)
    vector_store = create_vector_store(chunks, embeddings)
    status.success("✅ AI Ready!")
    progress.progress(100)
    llm, retriever, prompt = create_rag_chain(vector_store)

    # Chat Section
    st.divider()
    st.subheader("💬 Ask Your Question")
    st.write("### 🎤 Voice Input")

    audio_bytes = audio_recorder(
        text="Click to Record Voice",
        recording_color="#e74c3c",
        neutral_color="#2ecc71",
        icon_name="microphone",
        icon_size="2x",
        key="voice_recorder"
    )

    manual_question = st.text_input("Enter your question manually", key="chat_text_input")
    question = manual_question

    if audio_bytes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes)
            audio_path = f.name

        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        try:
            voice_question = recognizer.recognize_google(audio)
            st.success(f"🎤 You said: {voice_question}")
            question = voice_question
        except Exception:
            st.error("❌ Voice not recognized. Please try typing manually.")

    if question:
        docs = retriever.invoke(question)
        page_number = "Unknown"
        if docs:
            page_number = docs[0].metadata.get("page", "Unknown")

        context = "\n".join([doc.page_content for doc in docs])
        final_prompt = prompt.format(context=context, input=question)

        with st.spinner("🤖 AI is thinking..."):
            response = llm.invoke(final_prompt)

        st.session_state.chat_history.append(("You", question))
        st.session_state.recent_questions.append(question)
        st.session_state.chat_history.append(("AI", response.content))

        st.markdown(f"**Answer:**\n{response.content}")

        # Safe gTTS Execution to Prevent App Crash
        try:
            tts = gTTS(text=response.content, lang="en")
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(temp_audio.name)
            st.audio(temp_audio.name)
        except Exception:
            st.warning("⚠️ Audio response generation skipped due to connection speed.")

        st.info(f"📄 Source Page: {page_number}")

        if st.button("⭐ Bookmark this Answer", key="btn_bookmark_answer"):
            st.session_state.bookmarks.append(response.content)
            st.success("✅ Answer Bookmarked Successfully!")

    if st.session_state.chat_history:
        st.subheader("💬 Chat History")
        for sender, message in st.session_state.chat_history:
            st.markdown(f"**{sender}:** {message}")

    st.divider()

    st.subheader("⭐ Bookmarked Answers")
    if st.session_state.bookmarks:
        for i, answer in enumerate(st.session_state.bookmarks, start=1):
            with st.expander(f"📌 Bookmark {i}"):
                st.write(answer)
    else:
        st.info("No bookmarked answers yet.")

    st.divider()

    st.subheader("🕒 Recent Questions")
    if st.session_state.recent_questions:
        for q in st.session_state.recent_questions[-5:]:
            st.write("•", q)

    st.divider()

    # Summary Section
    if st.button("📝 Generate Summary", key="btn_gen_summary"):
        summary_prompt = f"""
        You are an AI assistant.
        Summarize the following document in simple points.

        Document:
        {pdf_text[:4000]}
        """
        with st.spinner("Generating Summary..."):
            summary = llm.invoke(summary_prompt)
            st.session_state["summary_text"] = summary.content
            st.session_state["summary_pdf_path"] = create_pdf(summary.content)

    if "summary_text" in st.session_state:
        st.subheader("📝 AI Summary")
        st.write(st.session_state["summary_text"])

        if "summary_pdf_path" in st.session_state and os.path.exists(st.session_state["summary_pdf_path"]):
            with open(st.session_state["summary_pdf_path"], "rb") as file:
                st.download_button(
                    "📥 Download Summary PDF",
                    data=file,
                    file_name="KnowGen_AI_Summary.pdf",
                    mime="application/pdf",
                    key="btn_download_summary"
                )

    st.divider()

    # Translation
    st.subheader("🌍 Translate PDF")
    language = st.selectbox(
        "Select Language",
        ["English", "Hindi", "Marathi"],
        key="select_language"
    )

    if st.button("🌍 Translate Summary", key="btn_translate_summary"):
        trans_prompt = f"""
        Translate the summary of the document into {language}.

        Document:
        {pdf_text[:3000]}
        """
        with st.spinner("Translating..."):
            translation = llm.invoke(trans_prompt)
            st.session_state["translation_text"] = translation.content

    if "translation_text" in st.session_state:
        st.subheader(f"🌍 Summary in {language}")
        st.write(st.session_state["translation_text"])

    st.divider()

    # Study Notes
    if st.button("📚 Generate Notes", key="btn_gen_notes"):
        notes_prompt = f"""
        You are an expert teacher.
        Create short and easy-to-understand study notes from the following document.
        Use bullet points.

        Document:
        {pdf_text[:3000]}
        """
        with st.spinner("Generating Notes..."):
            notes = llm.invoke(notes_prompt)
            st.session_state["notes_text"] = notes.content
            st.session_state["notes_pdf_path"] = create_pdf(notes.content)

    if "notes_text" in st.session_state:
        st.subheader("📚 AI Study Notes")
        st.write(st.session_state["notes_text"])

        if "notes_pdf_path" in st.session_state and os.path.exists(st.session_state["notes_pdf_path"]):
            with open(st.session_state["notes_pdf_path"], "rb") as file:
                st.download_button(
                    "📥 Download Notes PDF",
                    data=file,
                    file_name="KnowGen_Notes.pdf",
                    mime="application/pdf",
                    key="btn_download_notes"
                )

    st.divider()

    # Flashcards
    if st.button("🧠 Generate Flashcards", key="btn_gen_flashcards"):
        flashcard_prompt = f"""
        You are an expert teacher.
        Create 10 flashcards from the following document.

        Format:
        Q: Question
        A: Answer

        Document:
        {pdf_text[:3000]}
        """
        with st.spinner("Generating Flashcards..."):
            flashcards = llm.invoke(flashcard_prompt)
            st.session_state["flashcards_text"] = flashcards.content

    if "flashcards_text" in st.session_state:
        st.subheader("🧠 AI Flashcards")
        st.write(st.session_state["flashcards_text"])

    st.divider()

    # Quiz Section
    if st.button("❓ Generate Quiz", key="btn_gen_quiz"):
        quiz_prompt = f"""
        You are an expert teacher.
        Create 10 multiple-choice questions (MCQs) from the following document.

        Each question should have:
        - Question
        - 4 Options (A, B, C, D)
        - Correct Answer

        Document:
        {pdf_text[:3000]}
        """
        with st.spinner("Generating Quiz..."):
            quiz = llm.invoke(quiz_prompt)
            st.session_state["quiz_text"] = quiz.content

    if "quiz_text" in st.session_state:
        st.subheader("❓ AI Quiz")
        st.write(st.session_state["quiz_text"])

    st.divider()

    # Extracted Debug Info
    st.subheader("📚 Text Chunks")
    st.write(f"Total Chunks: {len(chunks)}")
    first_chunk_text = (
        chunks[0].page_content
        if hasattr(chunks[0], "page_content")
        else str(chunks[0])
    )
    st.text_area("First Chunk", first_chunk_text, height=180, key="first_chunk_area")

    st.subheader("📄 Extracted Text Preview")
    st.text_area("PDF Content Preview", pdf_text[:4000], height=220, key="pdf_content_area")

else:
    st.info("👆 Please upload a PDF file to get started!")

st.divider()

st.markdown("""
<div style="text-align:center;color:#94A3B8;padding:10px 0;">
    <h4 style="margin:0;">🤖 KnowGen AI</h4>
    <p style="margin:4px 0 0 0;">Enterprise Intelligent PDF Knowledge Assistant</p>
    <p style="margin:2px 0 0 0;font-size:12px;">Developed with ❤️ by Prajwal Khot</p>
</div>
""", unsafe_allow_html=True)