import streamlit as st
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from src.document_processor import DocumentProcessor
from src.vector_store import VectorStore
from src.qa_chain import QAChain
from src.utils import format_source_info, get_file_icon

# Load GROQ_API_KEY from a local .env file if present (no-op on HF Spaces,
# where the key comes from Settings → Secrets as a real env var instead).
load_dotenv()

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocMind — Document Q&A Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Main background */
.stApp { background-color: #0F1117; color: #E2E8F0; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161B27;
    border-right: 1px solid #1E2D40;
}

/* Chat messages */
.user-message {
    background: #1A2744;
    border: 1px solid #2D4A7A;
    border-radius: 12px 12px 4px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #CBD5E1;
    font-size: 0.95rem;
}
.assistant-message {
    background: #0D1F1A;
    border: 1px solid #1A3D2F;
    border-left: 3px solid #10B981;
    border-radius: 4px 12px 12px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    color: #D1FAE5;
    font-size: 0.95rem;
    line-height: 1.65;
}
.source-chip {
    display: inline-block;
    background: #1E2D40;
    border: 1px solid #2D4A7A;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 0.75rem;
    color: #7DD3FC;
    margin: 4px 3px 0 0;
    font-family: 'JetBrains Mono', monospace;
}
.stat-card {
    background: #161B27;
    border: 1px solid #1E2D40;
    border-radius: 8px;
    padding: 14px;
    text-align: center;
}
.stat-number {
    font-size: 1.8rem;
    font-weight: 600;
    color: #10B981;
}
.stat-label {
    font-size: 0.75rem;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.doc-badge {
    background: #0D1F1A;
    border: 1px solid #1A3D2F;
    border-radius: 6px;
    padding: 8px 10px;
    margin: 6px 0;
    display: flex;
    align-items: center;
    font-size: 0.85rem;
    color: #A7F3D0;
}
.welcome-hero {
    text-align: center;
    padding: 60px 20px 40px;
    color: #475569;
}
.welcome-hero h2 {
    font-size: 1.5rem;
    font-weight: 300;
    color: #64748B;
    margin-bottom: 8px;
}
.welcome-hero p {
    color: #374151;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ── Session state initialization ──────────────────────────────────────────────
defaults = {
    "chat_history": [],
    "vector_store": None,
    "qa_chain": None,
    "uploaded_docs": [],
    "doc_stats": {"chunks": 0, "docs": 0},
    "groq_key_set": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 DocMind")
    st.markdown("<p style='color:#475569;font-size:0.8rem;margin-top:-8px'>Personal Document Q&A Agent</p>", unsafe_allow_html=True)
    st.divider()

    # API Key input — auto-detected from .env (local) or Space Secrets (HF)
    st.markdown("### 🔑 API Configuration")
    env_key = os.environ.get("GROQ_API_KEY", "")

    if env_key:
        st.session_state.groq_key_set = True
        st.success("✓ Using configured API key", icon="✅")
        with st.expander("Use a different key instead"):
            override_key = st.text_input(
                "Groq API Key",
                type="password",
                placeholder="gsk_...",
                help="Overrides the configured key for this session only.",
                label_visibility="collapsed",
            )
            if override_key:
                os.environ["GROQ_API_KEY"] = override_key
    else:
        groq_key = st.text_input(
            "Groq API Key",
            type="password",
            placeholder="gsk_...",
            help="Get a free key at console.groq.com",
        )
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
            st.session_state.groq_key_set = True
            st.success("✓ Key saved", icon="✅")

    st.divider()

    # File upload
    st.markdown("### 📂 Upload Documents")
    uploaded_files = st.file_uploader(
        "Drag & drop files here",
        type=["pdf", "txt", "docx", "csv"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    chunk_size = st.slider("Chunk Size (tokens)", 256, 1024, 512, 64,
                            help="Smaller = more precise retrieval. Larger = more context per chunk.")
    chunk_overlap = st.slider("Chunk Overlap", 0, 200, 64, 16)
    top_k = st.slider("Top K Sources", 1, 8, 4,
                       help="Number of source chunks retrieved per question.")

    process_btn = st.button("⚡ Process Documents", type="primary", use_container_width=True,
                             disabled=not (uploaded_files and st.session_state.groq_key_set))

    if process_btn and uploaded_files:
        with st.spinner("Processing documents…"):
            processor = DocumentProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            all_chunks = []
            doc_names = []

            for uf in uploaded_files:
                suffix = Path(uf.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uf.getvalue())
                    tmp_path = tmp.name

                chunks = processor.load_and_split(tmp_path, source_name=uf.name)
                all_chunks.extend(chunks)
                doc_names.append(uf.name)
                os.unlink(tmp_path)

            if all_chunks:
                vs = VectorStore()
                vs.build(all_chunks)
                st.session_state.vector_store = vs
                st.session_state.qa_chain = QAChain(vs, top_k=top_k)
                st.session_state.uploaded_docs = doc_names
                st.session_state.doc_stats = {"chunks": len(all_chunks), "docs": len(doc_names)}
                st.session_state.chat_history = []
                st.success(f"✓ {len(all_chunks)} chunks indexed from {len(doc_names)} document(s)")

    # Stats
    if st.session_state.vector_store:
        st.divider()
        st.markdown("### 📊 Index Stats")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class='stat-card'>
                <div class='stat-number'>{st.session_state.doc_stats['docs']}</div>
                <div class='stat-label'>Docs</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='stat-card'>
                <div class='stat-number'>{st.session_state.doc_stats['chunks']}</div>
                <div class='stat-label'>Chunks</div></div>""", unsafe_allow_html=True)

        st.markdown("**Loaded files:**")
        for doc in st.session_state.uploaded_docs:
            icon = get_file_icon(doc)
            st.markdown(f"<div class='doc-badge'>{icon} &nbsp;{doc}</div>", unsafe_allow_html=True)

    # Clear chat
    if st.session_state.chat_history:
        st.divider()
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.chat_history = []
            if st.session_state.qa_chain:
                st.session_state.qa_chain.clear_memory()
            st.rerun()

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown("## Document Q&A")

if not st.session_state.groq_key_set:
    st.info("👈 Enter your **Groq API key** in the sidebar to get started. Free at [console.groq.com](https://console.groq.com)", icon="🔑")

elif not st.session_state.vector_store:
    st.markdown("""<div class='welcome-hero'>
        <h2>No documents loaded yet</h2>
        <p>Upload PDF, TXT, DOCX, or CSV files in the sidebar<br>then click <strong>Process Documents</strong></p>
    </div>""", unsafe_allow_html=True)

else:
    # Chat display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""<div class='welcome-hero'>
                <h2>Ready to answer questions</h2>
                <p>Ask anything about your uploaded documents below</p>
            </div>""", unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"<div class='user-message'>🙋 {msg['content']}</div>", unsafe_allow_html=True)
            else:
                answer_html = msg["content"].replace("\n", "<br>")
                sources_html = "".join(
                    f"<span class='source-chip'>📄 {s}</span>"
                    for s in msg.get("sources", [])
                )
                st.markdown(
                    f"<div class='assistant-message'>🧠 {answer_html}"
                    f"{'<br><br>' + sources_html if sources_html else ''}</div>",
                    unsafe_allow_html=True,
                )

    # Input
    st.divider()
    col_input, col_send = st.columns([5, 1])
    with col_input:
        user_query = st.text_input(
            "Ask a question",
            placeholder="What is the main topic of this document?",
            label_visibility="collapsed",
            key="query_input",
        )
    with col_send:
        send = st.button("Send →", type="primary", use_container_width=True)

    # Quick prompts
    st.markdown("<p style='color:#374151;font-size:0.78rem;margin-top:6px'>Quick prompts:</p>", unsafe_allow_html=True)
    qp_cols = st.columns(4)
    quick_prompts = ["Summarize this document", "List the key points", "What are the conclusions?", "Find any numbers or data"]
    chosen_prompt = None
    for i, (col, prompt) in enumerate(zip(qp_cols, quick_prompts)):
        with col:
            if st.button(prompt, key=f"qp_{i}", use_container_width=True):
                chosen_prompt = prompt

    query = chosen_prompt or (user_query if send and user_query else None)

    if query:
        st.session_state.chat_history.append({"role": "user", "content": query})

        with st.spinner("Thinking…"):
            result = st.session_state.qa_chain.ask(query)

        sources = format_source_info(result.get("source_documents", []))
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": result["answer"],
            "sources": sources,
        })
        st.rerun()
