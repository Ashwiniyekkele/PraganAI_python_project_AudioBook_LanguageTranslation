import streamlit as st
from pypdf import PdfReader
from deep_translator import GoogleTranslator
from gtts import gTTS
from langdetect import detect
import time
import os


# ============================================================
# PAGE CONFIG
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
    font-size: 38px;
    font-weight: bold;
    text-align: center;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    margin-bottom: 25px;
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
# MAIN PROCESS
# ============================================================

if uploaded_file is not None:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    try:

        # ----------------------------------------------------
        # READ PDF
        # ----------------------------------------------------

        reader = PdfReader(uploaded_file)

        total_pages = len(reader.pages)

        extracted_text = ""

        for page in reader.pages:

            text = page.extract_text()

            if text:
                extracted_text += text + "\n"

        # ----------------------------------------------------
        # CHECK TEXT
        # ----------------------------------------------------

        if not extracted_text.strip():

            st.error(
                "❌ No text found in this PDF."
            )

            st.warning(
                "If your PDF is scanned/image-based, "
                "OCR is required."
            )

            st.stop()

        # ----------------------------------------------------
        # DETECT LANGUAGE
        # ----------------------------------------------------

        try:

            detected_language = detect(
                extracted_text[:3000]
            )

        except Exception:

            detected_language = "unknown"

        st.info(
            f"📄 Pages: {total_pages}"
        )

        st.info(
            f"🌐 Detected language: {detected_language}"
        )

        # ----------------------------------------------------
        # LANGUAGE DROPDOWN
        # ----------------------------------------------------

        st.subheader("🌐 Select Audio Language")

        selected_language = st.selectbox(
            "Choose the language:",
            list(LANGUAGES.keys())
        )

        target_code = LANGUAGES[
            selected_language
        ]

        # ----------------------------------------------------
        # SHOW ORIGINAL TEXT
        # ----------------------------------------------------

        with st.expander(
            "📄 View Extracted PDF Text"
        ):

            st.text_area(
                "Original Text",
                extracted_text,
                height=250
            )

        # ====================================================
        # TRANSLATE BUTTON
        # ====================================================

        if st.button(
            "🎧 Translate & Create Audiobook",
            use_container_width=True
        ):

            # ------------------------------------------------
            # TRANSLATION
            # ------------------------------------------------

            with st.spinner(
                f"Translating to {selected_language}..."
            ):

                try:

                    # If the selected language is already
                    # the original language, no translation
                    # request is required.

                    if (
                        detected_language != "unknown"
                        and
                        detected_language == target_code
                    ):

                        translated_text = extracted_text

                    else:

                        # ------------------------------------
                        # CLEAN TEXT
                        # ------------------------------------

                        lines = []

                        for line in extracted_text.splitlines():

                            line = line.strip()

                            if line:
                                lines.append(line)

                        # ------------------------------------
                        # CREATE LARGER CHUNKS
                        # ------------------------------------

                        chunks = []

                        current_chunk = ""

                        for line in lines:

                            if len(
                                current_chunk
                            ) + len(line) < 2500:

                                current_chunk += (
                                    " " + line
                                )

                            else:

                                if current_chunk.strip():
                                    chunks.append(
                                        current_chunk.strip()
                                    )

                                current_chunk = line

                        if current_chunk.strip():

                            chunks.append(
                                current_chunk.strip()
                            )

                        # ------------------------------------
                        # TRANSLATOR
                        # ------------------------------------

                        translator = GoogleTranslator(
                            source="auto",
                            target=target_code
                        )

                        translated_chunks = []

                        # ------------------------------------
                        # TRANSLATE WITH RETRY
                        # ------------------------------------

                        for i, chunk in enumerate(chunks):

                            success = False

                            for attempt in range(3):

                                try:

                                    translated = (
                                        translator.translate(
                                            chunk
                                        )
                                    )

                                    translated_chunks.append(
                                        translated
                                    )

                                    success = True

                                    # Small delay to avoid
                                    # rate limiting
                                    time.sleep(1.2)

                                    break

                                except Exception as e:

                                    if attempt < 2:

                                        time.sleep(3)

                                    else:

                                        raise e

                            if not success:

                                raise Exception(
                                    "Translation request failed."
                                )

                            st.write(
                                f"Translation progress: "
                                f"{i + 1}/{len(chunks)}"
                            )

                        translated_text = "\n".join(
                            translated_chunks
                        )

                except Exception as e:

                    st.error(
                        "❌ Translation failed."
                    )

                    st.warning(
                        "Google Translate is temporarily "
                        "rate-limiting requests. "
                        "Please wait 1–2 minutes and try again."
                    )

                    st.code(
                        str(e)
                    )

                    st.stop()

            # ------------------------------------------------
            # TRANSLATION SUCCESS
            # ------------------------------------------------

            st.success(
                f"✅ Translation completed in "
                f"{selected_language}"
            )

            # ------------------------------------------------
            # SHOW TRANSLATED TEXT
            # ------------------------------------------------

            st.subheader(
                f"📝 Translated Text - {selected_language}"
            )

            st.text_area(
                "Translated Text",
                translated_text,
                height=300
            )

            # =================================================
            # TEXT TO SPEECH
            # =================================================

            with st.spinner(
                f"Creating {selected_language} audiobook..."
            ):

                try:

                    # ----------------------------------------
                    # SPLIT TEXT FOR TTS
                    # ----------------------------------------

                    words = translated_text.split()

                    audio_files = []

                    audio_chunk_size = 250

                    for i in range(
                        0,
                        len(words),
                        audio_chunk_size
                    ):

                        audio_text = " ".join(
                            words[
                                i:i + audio_chunk_size
                            ]
                        )

                        audio_file = (
                            f"/tmp/audio_{i}.mp3"
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

                        time.sleep(0.5)

                    # ----------------------------------------
                    # MERGE AUDIO
                    # ----------------------------------------

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
                        "❌ Audio generation failed."
                    )

                    st.code(
                        str(e)
                    )

                    st.stop()

            # =================================================
            # SUCCESS
            # =================================================

            st.success(
                "✅ Audiobook created successfully!"
            )

            st.info(
                f"🌐 Audio language: "
                f"{selected_language}"
            )

            # ------------------------------------------------
            # AUDIO PLAYER
            # ------------------------------------------------

            st.subheader(
                "🎧 Listen to Translated Audiobook"
            )

            with open(
                final_audio,
                "rb"
            ) as audio:

                audio_bytes = audio.read()

            st.audio(
                audio_bytes,
                format="audio/mp3"
            )

            # ------------------------------------------------
            # DOWNLOAD
            # ------------------------------------------------

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
            f"❌ PDF processing error: {e}"
        )
