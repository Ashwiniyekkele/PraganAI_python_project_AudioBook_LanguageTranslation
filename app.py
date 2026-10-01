%%writefile app.py

import streamlit as st
from pypdf import PdfReader
from deep_translator import GoogleTranslator
from gtts import gTTS
from langdetect import detect
import os
import re


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PDF to Multilingual Audiobook",
    page_icon="📖",
    layout="centered"
)


# ============================================================
# LANGUAGE LIST
# ============================================================

LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Kannada": "kn",
    "Marathi": "mr",
    "Tamil": "ta",
    "Telugu": "te",
    "Malayalam": "ml",
    "Bengali": "bn",
    "Gujarati": "gu",
    "Punjabi": "pa",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
    "Arabic": "ar"
}


# ============================================================
# CSS
# ============================================================

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: bold;
    text-align: center;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    margin-bottom: 30px;
}

.success-box {
    padding: 15px;
    border-radius: 10px;
    background-color: #dff5e1;
    margin-top: 15px;
}

.info-box {
    padding: 15px;
    border-radius: 10px;
    background-color: #e8f4f8;
    margin-top: 15px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">📖 PDF to Multilingual Audiobook 🎧</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Upload a PDF, select a language, translate it and listen to the audiobook.'
    '</div>',
    unsafe_allow_html=True
)


# ============================================================
# UPLOAD PDF
# ============================================================

st.subheader("📄 Upload your PDF book")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"]
)


# ============================================================
# PROCESS PDF
# ============================================================

if uploaded_file is not None:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    # --------------------------------------------------------
    # READ PDF
    # --------------------------------------------------------

    try:

        reader = PdfReader(uploaded_file)

        total_pages = len(reader.pages)

        extracted_text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:
                extracted_text += page_text + "\n"

        # ----------------------------------------------------
        # CHECK TEXT
        # ----------------------------------------------------

        if not extracted_text.strip():

            st.error(
                "❌ No text could be extracted from this PDF. "
                "If it is a scanned PDF, OCR is required."
            )

            st.stop()

        # ----------------------------------------------------
        # DETECT LANGUAGE
        # ----------------------------------------------------

        try:

            detected_language = detect(
                extracted_text[:3000]
            )

        except:

            detected_language = "unknown"

        st.info(
            f"📄 Pages: {total_pages}"
        )

        st.info(
            f"🌐 Detected language: {detected_language}"
        )

        # ----------------------------------------------------
        # LANGUAGE SELECTION
        # ----------------------------------------------------

        st.subheader("🌐 Select Audio Language")

        selected_language = st.selectbox(
            "Choose the language in which you want to listen:",
            list(LANGUAGES.keys())
        )

        target_code = LANGUAGES[selected_language]

        st.write(
            f"Selected language: **{selected_language}**"
        )

        # ----------------------------------------------------
        # SHOW ORIGINAL TEXT
        # ----------------------------------------------------

        with st.expander("📄 View extracted PDF text"):

            st.text_area(
                "Original text",
                extracted_text,
                height=250
            )

        # ----------------------------------------------------
        # TRANSLATE + AUDIO BUTTON
        # ----------------------------------------------------

        if st.button(
            "🎧 Translate & Create Audiobook",
            use_container_width=True
        ):

            # ================================================
            # STEP 1 - TRANSLATION
            # ================================================

            with st.spinner(
                f"Translating PDF to {selected_language}..."
            ):

                try:

                    # Split text into smaller chunks
                    # because translation services have limits.

                    chunks = []

                    words = extracted_text.split()

                    chunk_size = 400

                    for i in range(
                        0,
                        len(words),
                        chunk_size
                    ):

                        chunk = " ".join(
                            words[i:i + chunk_size]
                        )

                        chunks.append(chunk)

                    translated_chunks = []

                    for chunk in chunks:

                        if target_code == detected_language:

                            translated = chunk

                        else:

                            translator = GoogleTranslator(
                                source="auto",
                                target=target_code
                            )

                            translated = translator.translate(
                                chunk
                            )

                        translated_chunks.append(
                            translated
                        )

                    translated_text = "\n".join(
                        translated_chunks
                    )

                except Exception as e:

                    st.error(
                        f"Translation error: {e}"
                    )

                    st.stop()

            st.success(
                f"✅ Translation completed in {selected_language}"
            )

            # ================================================
            # SHOW TRANSLATED TEXT
            # ================================================

            st.subheader(
                f"📝 Translated Text - {selected_language}"
            )

            st.text_area(
                "Translated text",
                translated_text,
                height=300
            )

            # ================================================
            # STEP 2 - TEXT TO SPEECH
            # ================================================

            with st.spinner(
                f"Creating {selected_language} audiobook..."
            ):

                try:

                    # gTTS has a practical text-size limit,
                    # so create multiple audio chunks.

                    text_words = translated_text.split()

                    audio_files = []

                    audio_chunk_size = 300

                    for index in range(
                        0,
                        len(text_words),
                        audio_chunk_size
                    ):

                        audio_text = " ".join(
                            text_words[
                                index:index + audio_chunk_size
                            ]
                        )

                        audio_file = (
                            f"/tmp/audio_{index}.mp3"
                        )

                        tts = gTTS(
                            text=audio_text,
                            lang=target_code,
                            slow=False
                        )

                        tts.save(
                            audio_file
                        )

                        audio_files.append(
                            audio_file
                        )

                    # ========================================
                    # MERGE AUDIO FILES
                    # ========================================

                    final_audio = (
                        "/tmp/translated_audiobook.mp3"
                    )

                    with open(
                        final_audio,
                        "wb"
                    ) as output:

                        for audio_file in audio_files:

                            with open(
                                audio_file,
                                "rb"
                            ) as audio:

                                output.write(
                                    audio.read()
                                )

                except Exception as e:

                    st.error(
                        f"Audio generation error: {e}"
                    )

                    st.stop()

            # ================================================
            # SUCCESS
            # ================================================

            st.markdown(
                '<div class="success-box">'
                '✅ Audiobook created successfully!'
                '</div>',
                unsafe_allow_html=True
            )

            st.write(
                f"🌐 Audio language: **{selected_language}**"
            )

            # ================================================
            # AUDIO PLAYER
            # ================================================

            st.subheader(
                "🎧 Listen to translated audiobook"
            )

            with open(
                final_audio,
                "rb"
            ) as audio_file:

                audio_bytes = audio_file.read()

            st.audio(
                audio_bytes,
                format="audio/mp3"
            )

            # ================================================
            # DOWNLOAD AUDIO
            # ================================================

            st.download_button(
                label="⬇️ Download Audiobook",
                data=audio_bytes,
                file_name=(
                    f"audiobook_{target_code}.mp3"
                ),
                mime="audio/mpeg",
                use_container_width=True
            )

    except Exception as e:

        st.error(
            f"PDF processing error: {e}"
)
