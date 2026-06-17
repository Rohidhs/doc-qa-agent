# 🧠 DocMind — Personal Document Q&A Agent

Chat with any document using a fully local RAG pipeline + Groq LLM.  
Supports **PDF, TXT, DOCX, CSV** — all with conversation memory.

---

## 📦 Stack

| Component | Tool | Cost |
|-----------|------|------|
| LLM | [Groq](https://console.groq.com) (llama-3.1-8b-instant) | Free tier |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` | Free, local |
| Vector DB | FAISS | Free, local |
| RAG Framework | LangChain | Open source |
| UI | Streamlit | Free |
| PDF parsing | PyMuPDF | Open source |

---

## 🚀 Step-by-Step Setup

### Step 1 — Get a free Groq API key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key (starts with `gsk_…`)

---

### Step 2 — Clone / download this project

```bash
git clone https://github.com/your-username/doc-qa-agent.git
cd doc-qa-agent
```

Or just download the ZIP and unzip it.

---

### Step 3 — Create a Python virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ First run downloads the ~90 MB embedding model from HuggingFace. This is a one-time download cached locally.

---

### Step 5 — Run the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501**

---

### Step 6 — Use the app

1. Paste your Groq API key in the sidebar
2. Upload one or more documents (PDF, TXT, DOCX, CSV)
3. Adjust chunk size and top-K if desired
4. Click **⚡ Process Documents**
5. Ask questions in the chat!

---

## 🌐 Deploy to Hugging Face Spaces (Free Hosting)

1. Create a free account at [huggingface.co](https://huggingface.co)
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space)
3. Choose **Streamlit** as the SDK
4. Choose **CPU basic** (free tier)
5. Initialize a git repo in this folder:
   ```bash
   git init
   git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/doc-qa-agent
   git add .
   git commit -m "Initial commit"
   git push -u origin main
   ```
6. In your Space settings → **Variables and Secrets** → add:
   - Name: `GROQ_API_KEY`
   - Value: your Groq key
7. The Space rebuilds automatically — share the public URL!

---

## 🔧 Using on Google Colab

```python
# Cell 1 — Install
!pip install -q langchain langchain-community langchain-groq langchain-huggingface \
    groq sentence-transformers faiss-cpu pymupdf python-docx streamlit pyngrok

# Cell 2 — Set key and run
import os
os.environ["GROQ_API_KEY"] = "gsk_YOUR_KEY_HERE"

!streamlit run app.py &>/dev/null &

from pyngrok import ngrok
public_url = ngrok.connect(8501)
print("App URL:", public_url)
```

---

## 🗂️ Project Structure

```
doc-qa-agent/
├── app.py                    # Streamlit UI (entry point)
├── requirements.txt
├── README.md
└── src/
    ├── __init__.py
    ├── document_processor.py  # PDF/TXT/DOCX/CSV loader + chunker
    ├── vector_store.py        # FAISS index builder & retriever
    ├── qa_chain.py            # ConversationalRetrievalChain + memory
    └── utils.py               # Source formatting, file icons
```

---

## 🧩 How It Works (RAG Pipeline)

```
┌─────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Upload Doc │───▶│  Split into      │───▶│  Embed with  │
│ PDF/TXT/... │    │  chunks          │    │  MiniLM-L6   │
└─────────────┘    └──────────────────┘    └──────┬───────┘
                                                   │
                                                   ▼
┌─────────────┐    ┌──────────────────┐    ┌──────────────┐
│  LLM Answer │◀───│  Groq LLaMA 3.1  │◀───│  FAISS index │
│  + Sources  │    │  + Chat history  │    │  top-K chunks│
└─────────────┘    └──────────────────┘    └──────────────┘
        ▲                    ▲
        │                    │
   User question ────────────┘
```

---

## ⚡ Extension Ideas (all free)

| Extension | How |
|-----------|-----|
| **Conversation memory** | ✅ Already built in via `ConversationBufferMemory` |
| **Multi-file support** | ✅ Already built in — upload multiple files at once |
| **DOCX & CSV** | ✅ Already supported |
| **Free hosting** | Deploy to HF Spaces (see above) |
| **Export chat** | Add a download button for the conversation history |
| **Multi-agent layer** | Use LangChain Agents + tools for web search + doc search |

---

## 🛠️ Troubleshooting

**`ModuleNotFoundError: No module named 'fitz'`**  
→ `pip install pymupdf`

**`AuthenticationError` from Groq**  
→ Double-check your API key is pasted correctly (no extra spaces)

**Slow first run**  
→ Normal — the embedding model (~90 MB) is downloading. Subsequent runs are instant.

**`No such file` on uploaded CSV**  
→ Ensure the CSV uses UTF-8 encoding. Open in Excel → Save As → CSV UTF-8.
