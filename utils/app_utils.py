import streamlit as st


def init_session_state():
    defaults = {
        "chat_history": [],
        "bookmarks": [],
        "recent_questions": [],
        "pdf_page_num": 1,
        "summary_text": None,
        "summary_pdf_path": None,
        "translation_text": None,
        "notes_text": None,
        "notes_pdf_path": None,
        "flashcards_text": None,
        "quiz_text": None,
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def get_theme_colors(theme_name):
    if theme_name == "🌙 Dark":
        return {
            "text_color": "#F8FAFC",
            "bg_color": "#0B0F17",
            "card_bg": "#111827",
            "border_color": "#1F2937",
            "input_bg": "#111827",
        }

    return {
        "text_color": "#0F172A",
        "bg_color": "#F8FAFC",
        "card_bg": "#FFFFFF",
        "border_color": "#E2E8F0",
        "input_bg": "#FFFFFF",
    }


def reset_session_state():
    keys_to_clear = [
        "chat_history",
        "bookmarks",
        "recent_questions",
        "summary_text",
        "summary_pdf_path",
        "translation_text",
        "notes_text",
        "notes_pdf_path",
        "flashcards_text",
        "quiz_text",
    ]

    for key in keys_to_clear:
        st.session_state.pop(key, None)
