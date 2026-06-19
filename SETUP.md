# Setup & Deployment Guide

## Local setup

### 1 — Get a free Groq API key
Go to [console.groq.com](https://console.groq.com) → sign up → **API Keys** → Create one. Starts with `gsk_…`

### 2 — Clone and enter the project
```bash
git clone <this-repo>
cd doc-qa-agent
```

### 3 — Create a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4 — Install dependencies
```bash
pip install -r requirements.txt
```
> First run downloads the ~90 MB `all-MiniLM-L6-v2` embedding model. One-time download, cached locally after that.

### 5 — Run it
```bash
streamlit run app.py
```
Opens at **http://localhost:8501**

### 6 — Use it
1. Paste your Groq API key in the sidebar
2. Upload one or more documents (PDF, TXT, DOCX, CSV)
3. Adjust chunk size / overlap / top-K if desired
4. Click **⚡ Process Documents**
5. Ask questions in the chat

---

## Deploy to Hugging Face Spaces (free hosting)

1. Create a free account at [huggingface.co](https://huggingface.co)
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space) → choose SDK: **Streamlit**, hardware: **CPU basic**
3. Get a write-access token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
4. Push this repo to your new Space:
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/doc-qa-agent
   git branch -M main
   git push -u origin main
   ```
   When prompted: username = your HF username, password = your `hf_…` token.
5. In your Space → **Settings → Variables and Secrets** → add `GROQ_API_KEY` with your key
6. Your `README.md` needs a YAML metadata header for the Space to build correctly:
   ```yaml
   ---
   title: Doc QA Agent
   emoji: 🧠
   colorFrom: green
   colorTo: blue
   sdk: streamlit
   sdk_version: 1.39.0
   app_file: app.py
   pinned: false
   python_version: "3.11"
   ---
   ```
   This must match the `streamlit` version pinned in `requirements.txt`.
7. The Space rebuilds automatically on every push. Check **Logs → Build** for install errors and **Logs → Container** for runtime errors — they're different tabs and usually need different fixes.

### If your push is rejected for large files
A committed `venv/` folder or similar can exceed Hugging Face's per-file size limit. `git rm --cached` alone won't fix it — the files remain in earlier commits. Rewrite history instead:
```bash
echo "venv/" > .gitignore
echo "__pycache__/" >> .gitignore
git rm -r --cached venv/
git filter-branch --force --index-filter "git rm -rf --cached --ignore-unmatch venv/" --prune-empty --tag-name-filter cat -- --all
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push -u origin main --force
```

---

## Run on Google Colab

```python
# Cell 1 — Install
!pip install -q langchain langchain-community langchain-core langchain-groq \
    langchain-text-splitters langchain-huggingface groq httpx \
    sentence-transformers faiss-cpu pymupdf python-docx streamlit pyngrok

# Cell 2 — Set key and run
import os
os.environ["GROQ_API_KEY"] = "gsk_YOUR_KEY_HERE"

!streamlit run app.py &>/dev/null &

from pyngrok import ngrok
public_url = ngrok.connect(8501)
print("App URL:", public_url)
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'langchain.schema'` (or `.text_splitter`, etc.)**
LangChain split its core package into `langchain-core`, `langchain-community`, and `langchain-text-splitters`. Update the import to match the new location and ensure all `langchain-*` packages are pinned to compatible versions (see `requirements.txt`).

**`TypeError: Client.__init__() got an unexpected keyword argument 'proxies'`**
A version mismatch between `groq` and the `httpx` it depends on internally. Pin `httpx==0.27.2`, or pass an explicit client:
```python
import httpx
llm = ChatGroq(model_name=model, http_client=httpx.Client())
```

**`AuthenticationError` from Groq**
Double-check your API key is pasted correctly, with no extra spaces or line breaks.

**Hugging Face Space stuck on "Configuration error"**
Your `README.md` is missing or has malformed YAML front-matter. It must start with a `---` block declaring `sdk`, `sdk_version`, and `app_file` (see deployment section above).

**Slow first run**
Normal — the embedding model (~90 MB) is downloading. Subsequent runs are instant.

**Uploaded CSV fails to parse**
Ensure the file is UTF-8 encoded. In Excel: File → Save As → CSV UTF-8.
