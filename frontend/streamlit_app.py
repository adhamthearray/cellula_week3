import os

import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Code Assistant",
    page_icon="🤖",
    layout="wide"
)


# ============================================================
# API CONFIG
# ============================================================

API_BASE = "http://127.0.0.1:" + os.getenv("API_PORT", "8002")


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "dataset" not in st.session_state:
    st.session_state.dataset = None


# ============================================================
# ERROR HANDLER
# ============================================================

def request_error(prefix: str, exc: requests.RequestException) -> None:
    detail = str(exc)

    if exc.response is not None:
        try:
            detail = exc.response.json().get("detail", detail)
        except ValueError:
            detail = exc.response.text or detail

    st.error(f"{prefix}: {detail}")


# ============================================================
# TABS
# ============================================================

code_tab, data_tab = st.tabs(
    [
        "💻 Code Assistant",
        "🎙️ Voice Data Analysis"
    ]
)


# ============================================================
# CODE ASSISTANT TAB
# ============================================================

with code_tab:

    st.title("AI Code Assistant")

    st.caption(
        "Explain code, generate code with RAG, and execute it safely"
    )

    # Display previous messages
    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

            if message.get("intent"):
                st.caption(
                    f"Intent: {message['intent']}"
                )

            if message.get("execution"):
                st.code(
                    message["execution"]
                )

    # Chat input
    prompt = st.chat_input(
        "Ask about code or request a solution"
    )

    if prompt:

        # Save user message
        st.session_state.messages.append(
            {
                "role": "user",
                "content": prompt
            }
        )

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        try:

            with st.spinner("Thinking..."):

                response = requests.post(
                    f"{API_BASE}/chat",
                    json={
                        "message": prompt
                    },
                    timeout=60
                )

                response.raise_for_status()

                payload = response.json()

            # Extract response
            assistant_text = payload.get(
                "answer",
                ""
            )

            # Save assistant message
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                    "intent": payload.get("intent"),
                    "execution": payload.get(
                        "execution_result"
                    )
                }
            )

            # Display assistant response
            with st.chat_message("assistant"):

                st.markdown(
                    assistant_text
                )

                intent = payload.get(
                    "intent",
                    ""
                )

                if intent:
                    st.caption(
                        f"Intent: {intent}"
                    )

                if payload.get("execution_result"):

                    st.code(
                        payload["execution_result"]
                    )

        except requests.RequestException as exc:

            request_error(
                "Request failed",
                exc
            )


# ============================================================
# VOICE DATA ANALYSIS TAB
# ============================================================

with data_tab:

    st.title("Voice Data Analysis")

    st.caption(
        "Upload CSV or Excel data and ask a question by text or audio."
    )


    # --------------------------------------------------------
    # DATASET UPLOAD
    # --------------------------------------------------------

    uploaded = st.file_uploader(
        "Dataset",
        type=["csv", "xlsx", "xls"],
        key="dataset_upload"
    )


    if uploaded and st.button(
        "Load dataset",
        key="load_dataset"
    ):

        try:

            with st.spinner(
                "Loading dataset into SQLite..."
            ):

                response = requests.post(
                    f"{API_BASE}/data/upload",
                    files={
                        "file": (
                            uploaded.name,
                            uploaded.getvalue(),
                            uploaded.type
                        )
                    },
                    timeout=60
                )

                response.raise_for_status()

            st.session_state.dataset = response.json()

            st.success(
                "Dataset loaded successfully."
            )

        except requests.RequestException as exc:

            request_error(
                "Upload failed",
                exc
            )


    # --------------------------------------------------------
    # DATASET INFORMATION
    # --------------------------------------------------------

    dataset = st.session_state.get("dataset")


    if dataset:

        st.divider()

        st.subheader("📊 Loaded Dataset")

        st.write(
            f"**File:** {dataset['filename']}  |  "
            f"**Rows:** {dataset['rows']}  |  "
            f"**Table:** `{dataset['table_name']}`"
        )

        st.caption(
            "Columns: "
            + ", ".join(dataset["columns"])
        )


        # ====================================================
        # TEXT INPUT
        # ====================================================

        st.subheader("⌨️ Ask by Text")

        question = st.text_input(
            "Ask about your data",
            placeholder="For example: What is the average GPA?",
            key="text_question"
        )

        text_clicked = st.button(
            "Analyze text",
            disabled=not question,
            key="analyze_text"
        )


        # ====================================================
        # VOICE INPUT
        # ====================================================

        st.divider()

        st.subheader("🎙️ Ask by Voice")

        st.caption(
            "Record your question using your microphone, "
            "then click Analyze audio."
        )


        # Streamlit microphone recorder
        audio = st.audio_input(
            "Record your question",
            key="audio_recording"
        )


        # Optional: show the recorded audio
        if audio:

            st.success(
                "Recording ready!"
            )

            st.audio(
                audio,
                format=audio.type
            )


        voice_clicked = st.button(
            "🎤 Analyze audio",
            disabled=audio is None,
            key="analyze_audio"
        )


        # ====================================================
        # ANALYSIS
        # ====================================================

        try:

            payload = None


            # ------------------------------------------------
            # TEXT ANALYSIS
            # ------------------------------------------------

            if text_clicked:

                with st.spinner(
                    "Generating and safely running SQL..."
                ):

                    response = requests.post(
                        f"{API_BASE}/data/analyze/text",
                        json={
                            "dataset_id": dataset["dataset_id"],
                            "query": question
                        },
                        timeout=90
                    )

                    response.raise_for_status()

                    payload = response.json()


            # ------------------------------------------------
            # VOICE ANALYSIS
            # ------------------------------------------------

            elif voice_clicked and audio:

                with st.spinner(
                    "Transcribing and analyzing your question..."
                ):

                    response = requests.post(
                        f"{API_BASE}/data/analyze/voice",
                        data={
                            "dataset_id": dataset["dataset_id"]
                        },
                        files={
                            "audio": (
                                audio.name,
                                audio.getvalue(),
                                audio.type
                            )
                        },
                        timeout=180
                    )

                    response.raise_for_status()

                    payload = response.json()


            # ------------------------------------------------
            # DISPLAY RESULTS
            # ------------------------------------------------

            if payload:

                st.divider()

                st.subheader("📈 Analysis Results")


                # Voice transcription
                if payload.get("transcription"):

                    st.write(
                        "**🎙️ Transcription:**"
                    )

                    st.info(
                        payload["transcription"]
                    )


                # User question
                st.write(
                    "**Question:**"
                )

                st.write(
                    payload.get(
                        "query",
                        "Unknown"
                    )
                )


                # Generated SQL
                if payload.get("generated_sql"):

                    st.write(
                        "**Generated SQL:**"
                    )

                    st.code(
                        payload["generated_sql"],
                        language="sql"
                    )


                # Number of rows
                if "row_count" in payload:

                    st.write(
                        f"**Rows returned:** "
                        f"{payload['row_count']}"
                    )


                # Data results
                if payload.get("rows"):

                    st.write(
                        "**Results:**"
                    )

                    st.dataframe(
                        payload["rows"],
                        use_container_width=True
                    )


                # AI analysis
                if payload.get("analysis"):

                    st.write(
                        "**AI Analysis:**"
                    )

                    st.info(
                        payload["analysis"]
                    )


        except requests.RequestException as exc:

            request_error(
                "Analysis failed",
                exc
            )