import os
import tempfile
import fitz  # PyMuPDF
import speech_recognition as sr
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS

from utils.app_utils import get_theme_colors, init_session_state, reset_session_state
from utils.config import DEFAULT_LANGUAGE, get_api_key
from utils.download_pdf import create_pdf
from utils.embeddings import get_embeddings
from utils.pdf_loader import load_pdf
from utils.rag_chain import create_rag_chain
from utils.text_splitter import split_text
from utils.vector_store import create_vector_store

api_key = get_api_key()
if api_key:
    os.environ["GROQ_API_KEY"] = api_key
else:
    st.warning("⚠️ GROQ_API_KEY missing! Add it to .env or Streamlit secrets.")

init_session_state()


def safe_call_llm(llm, prompt, fallback_message):
    try:
        response = llm.invoke(prompt)
        return getattr(response, "content", str(response))
    except Exception as exc:
        st.error(f"⚠️ {fallback_message}")
        return f"{fallback_message}\n\nReason: {exc}"


def safe_load_pdf_documents(uploaded_file):
    try:
        uploaded_file.seek(0)
        return load_pdf(uploaded_file)
    except Exception as exc:
        st.error(f"⚠️ Unable to read the uploaded PDF: {exc}")
        return []


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
    st.markdown("### 🧭 Navigation")

    page = st.radio(
        "",
        [
            "Home",
            "Upload",
            "Chat",
            "Summary",
            "Notes",
            "Quiz",
            "Flashcards"
        ]
    )

    st.divider()
    st.markdown("### ⚙️ Settings")

    theme = st.selectbox(
        "🎨 Theme",
        ["🌞 Light", "🌙 Dark"],
        index=1
    )

    if st.button("🧹 Clear session"):
        reset_session_state()
        st.rerun()

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
colors = get_theme_colors(theme)
text_color = colors["text_color"]
bg_color = colors["bg_color"]
card_bg = colors["card_bg"]
border_color = colors["border_color"]
input_bg = colors["input_bg"]

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

/* Hero and Feature Cards */
.welcome-card {{
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.16), rgba(56, 189, 248, 0.12));
    border: 1px solid rgba(56, 189, 248, 0.24);
    border-radius: 24px;
    padding: 22px 24px;
    margin-bottom: 18px;
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.08);
}}

.pill {{
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(37, 99, 235, 0.14);
    color: #2563EB !important;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 10px;
    letter-spacing: 0.02em;
}}

.section-card {{
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 14px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}}

.section-card strong {{
    color: #38BDF8 !important;
}}

.info-banner {{
    background: rgba(37, 99, 235, 0.10);
    border: 1px solid rgba(56, 189, 248, 0.24);
    border-radius: 14px;
    padding: 10px 12px;
    margin: 10px 0 12px;
    font-size: 14px;
}}

.feature-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    margin: 10px 0 22px;
}}

.feature-card {{
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}}

.feature-card strong {{
    display: block;
    margin-bottom: 6px;
    color: #38BDF8 !important;
}}

.section-title {{
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 8px;
}}

.upload-card {{
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(56, 189, 248, 0.08));
    border: 1px solid rgba(56, 189, 248, 0.24);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 12px;
}}

.hero-shell {{
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.18), rgba(56, 189, 248, 0.14));
    border: 1px solid rgba(56, 189, 248, 0.24);
    border-radius: 24px;
    padding: 24px 24px 20px;
    margin-bottom: 18px;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
}}

.hero-content h1 {{
    font-size: 32px;
    font-weight: 800;
    margin: 0 0 10px;
    color: #F8FAFC !important;
}}

.hero-content p {{
    font-size: 15px;
    line-height: 1.6;
    margin-bottom: 12px;
    color: #E2E8F0 !important;
}}

.hero-actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
}}

.hero-chip {{
    display: inline-block;
    padding: 7px 11px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.16);
    color: #F8FAFC !important;
    font-size: 12px;
    font-weight: 700;
    border: 1px solid rgba(255, 255, 255, 0.16);
}}

.status-pill {{
    display: inline-block;
    margin-bottom: 12px;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(34, 197, 94, 0.16);
    color: #22C55E !important;
    font-size: 12px;
    font-weight: 700;
}}

.workspace-shell {{
    background: {card_bg};
    border: 1px solid {border_color};
    border-radius: 18px;
    padding: 14px 16px;
    margin: 8px 0 16px;
    box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
}}

.workspace-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
}}

.workspace-badge {{
    padding: 7px 10px;
    border-radius: 999px;
    background: rgba(37, 99, 235, 0.14);
    color: #2563EB !important;
    font-size: 12px;
    font-weight: 700;
}}

.mini-panel {{
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.10), rgba(56, 189, 248, 0.10));
    border: 1px solid rgba(56, 189, 248, 0.24);
    border-radius: 16px;
    padding: 14px;
    height: 100%;
}}

.mini-stat {{
    margin-top: 8px;
    font-size: 14px;
    line-height: 1.5;
    color: {text_color} !important;
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
<div class='hero-shell'>
    <div class='hero-content'>
        <div class='pill'>⚡ Premium AI knowledge workspace</div>
        <h1>Turn documents into instant expertise</h1>
        <p>Upload PDFs, ask grounded questions, and generate summaries, notes, flashcards, quizzes, and translations from one polished workspace.</p>
        <div class='hero-actions'>
            <span class='hero-chip'>📄 PDF Intelligence</span>
            <span class='hero-chip'>💬 AI Chat</span>
            <span class='hero-chip'>🧠 Study Automation</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='feature-grid'>
    <div class='feature-card'><strong>📄 Smart upload</strong>Work with one or many PDFs in a single flow.</div>
    <div class='feature-card'><strong>💬 Conversational Q&A</strong>Ask questions and receive grounded answers with source context.</div>
    <div class='feature-card'><strong>🧠 Study assistant</strong>Create notes, summaries, flashcards, and quizzes automatically.</div>
    <div class='feature-card'><strong>🌍 Translation ready</strong>Translate outputs into English, Hindi, or Marathi instantly.</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='section-card'>
    <strong>⚡ What you can do next</strong>
    <div style='margin-top:6px;'>Upload a PDF, explore the content with AI, and instantly build study materials for faster learning.</div>
</div>
""", unsafe_allow_html=True)

st.divider()

st.markdown("""
<div class='section-card upload-panel'>
    <strong>📄 Upload your PDF</strong>
    <div style='margin-top:6px;'>Drop one or more documents and begin your smarter study session.</div>
</div>
""", unsafe_allow_html=True)

uploaded_files = st.file_uploader(
    "Upload PDF files", type=["pdf"], accept_multiple_files=True, key="pdf_file_uploader"
)

# File Process Block
if uploaded_files:
    if st.session_state.get("last_uploaded_count") != len(uploaded_files):
        st.session_state["last_uploaded_count"] = len(uploaded_files)
        reset_session_state()
    first_pdf = uploaded_files[0]

    st.markdown("""
    <div class='status-pill'>✅ Files ready for AI processing</div>
    """, unsafe_allow_html=True)

    try:
        first_pdf.seek(0)
        doc = fitz.open(stream=first_pdf.read(), filetype="pdf")
        total_pages = len(doc)
    except Exception as exc:
        st.error(f"⚠️ This PDF could not be processed: {exc}")
        st.stop()

    if st.session_state.pdf_page_num > total_pages:
        st.session_state.pdf_page_num = 1
    if st.session_state.pdf_page_num < 1:
        st.session_state.pdf_page_num = 1

    st.markdown("""
    <div class='workspace-shell'>
        <div class='workspace-header'>
            <div>
                <div class='pill'>📄 Document workspace</div>
                <h3 style='margin: 0 0 6px 0;'>Preview and analyze your PDF</h3>
            </div>
            <div class='workspace-badge'>{0} file(s) uploaded</div>
        </div>
    </div>
    """.format(len(uploaded_files)), unsafe_allow_html=True)

    page_doc = doc.load_page(st.session_state.pdf_page_num - 1)
    pix = page_doc.get_pixmap(dpi=140)

    preview_col, info_col = st.columns([1.35, 0.85])

    with preview_col:
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

    with info_col:
        st.markdown("""
        <div class='mini-panel'>
            <div class='pill'>⚡ Live insight</div>
            <div class='mini-stat'>AI is ready to read, search, and summarize your document.</div>
        </div>
        """, unsafe_allow_html=True)

    progress = st.progress(0)
    status = st.empty()

    # Load & Combine Text from all PDFs
    status.info("📄 Reading PDF...")
    progress.progress(20)
    documents = []

    for uploaded_file in uploaded_files:
        documents.extend(safe_load_pdf_documents(uploaded_file))

    pdf_text = "\n".join(
        [
            doc.page_content if hasattr(doc, "page_content") else str(doc)
            for doc in documents
        ]
    )

    if not documents:
        st.warning("No text could be extracted from the uploaded PDF. Please try another file.")
        st.stop()
    word_count = len(pdf_text.split())
    reading_time = max(1, word_count // 200)

    status.info("✂️ Splitting Text...")
    progress.progress(50)
    chunks = split_text(documents)
    chunk_count = len(chunks)

    st.divider()

    # PDF Statistics
    st.markdown("""
    <div class='section-card'>
        <strong>📊 Document overview</strong>
        <div style='margin-top:6px;'>A quick snapshot of your uploaded PDF before you start asking questions.</div>
    </div>
    """, unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Words", f"{word_count:,}")

    with m2:
        st.metric("Reading Time", f"{reading_time} min")

    with m3:
        st.metric("Chunks", chunk_count)

    with m4:
        st.metric("Pages", total_pages)

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
    st.markdown("""
    <div class='section-card'>
        <strong>💬 Ask your question</strong>
        <div style='margin-top:6px;'>Use voice or typing to get an answer from your PDF in seconds.</div>
    </div>
    """, unsafe_allow_html=True)

    audio_bytes = audio_recorder(
        text="Record voice",
        recording_color="#e74c3c",
        neutral_color="#2ecc71",
        icon_name="microphone",
        icon_size="2x",
        key="voice_recorder"
    )

    manual_question = st.text_input("Type your question", key="chat_text_input")
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
            response_text = safe_call_llm(llm, final_prompt, "Unable to generate an answer right now.")

        st.session_state.chat_history.append(("You", question))
        st.session_state.recent_questions.append(question)
        st.session_state.chat_history.append(("AI", response_text))

        st.markdown(f"**Answer:**\n{response_text}")

        # Safe gTTS Execution to Prevent App Crash
        try:
            tts = gTTS(text=response_text, lang="en")
            temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tts.save(temp_audio.name)
            st.audio(temp_audio.name)
        except Exception:
            st.warning("⚠️ Audio response generation skipped due to connection speed.")

        st.info(f"📄 Source Page: {page_number}")

        if st.button("⭐ Bookmark this Answer", key="btn_bookmark_answer"):
            st.session_state.bookmarks.append(response_text)
            st.success("✅ Answer Bookmarked Successfully!")

    if st.session_state.chat_history:
        st.markdown("""
        <div class='info-banner'>💬 Recent conversation appears here for quick review.</div>
        """, unsafe_allow_html=True)
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
            summary_text = safe_call_llm(llm, summary_prompt, "Summary generation failed.")
            st.session_state["summary_text"] = summary_text
            st.session_state["summary_pdf_path"] = create_pdf(summary_text)

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
        key="select_language",
        index=["English", "Hindi", "Marathi"].index(DEFAULT_LANGUAGE)
    )

    if st.button("🌍 Translate Summary", key="btn_translate_summary"):
        trans_prompt = f"""
        Translate the summary of the document into {language}.

        Document:
        {pdf_text[:3000]}
        """
        with st.spinner("Translating..."):
            translation_text = safe_call_llm(llm, trans_prompt, "Translation failed.")
            st.session_state["translation_text"] = translation_text

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
            notes_text = safe_call_llm(llm, notes_prompt, "Note generation failed.")
            st.session_state["notes_text"] = notes_text
            st.session_state["notes_pdf_path"] = create_pdf(notes_text)

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
            flashcards_text = safe_call_llm(llm, flashcard_prompt, "Flashcard generation failed.")
            st.session_state["flashcards_text"] = flashcards_text

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
            quiz_text = safe_call_llm(llm, quiz_prompt, "Quiz generation failed.")
            st.session_state["quiz_text"] = quiz_text

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
<div style="text-align:center;color:#94A3B8;padding:12px 0 4px 0;">
    <h4 style="margin:0;">🤖 KnowGen AI</h4>
    <p style="margin:4px 0 0 0;">Built for fast, smarter document understanding</p>
</div>
""", unsafe_allow_html=True)