# VISTA: Visually Impaired Speech Technology Assistant

**VISTA** is an AI-powered browser extension designed to enable visually impaired users to navigate and interact with websites using natural voice commands. Developed during the **Meta AI Llama Hackathon 2024** in Toronto, VISTA combines advanced web scraping, large language models, and speech technology to provide seamless, conversational access to web content.

## 🚀 Motivation

The web remains largely inaccessible to visually impaired individuals, especially when websites are poorly structured or lack assistive tagging. VISTA was built to address this gap—empowering users to obtain relevant information through voice in a natural, intuitive manner.

By integrating a transformer-based web scraper, the **Llama 3.1-8B** model, and **Retrieval-Augmented Generation (RAG)**, VISTA delivers context-aware answers extracted directly from any webpage. Paired with **speech-to-text** and **text-to-speech** capabilities, it enables fluid conversation with the web, enhancing independence and accessibility.

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- [Ollama](https://ollama.com) (for running Llama 3.1 models locally)
- Chrome or any Chromium-based browser (for extension deployment)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/vista-ai-assistant.git
   cd vista-meta-hackathon
   ```
2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt -r rag/requirements.txt
   ```
3. **Run Flask Server**
   ```bash
   cd rag
   export FLASK_APP=main.py       # Use 'set FLASK_APP=main.py' on Windows
   flask run
   ```
4. **Running the Speech Assistant**
   ```bash
   python speech_tasks/speech.py
   ```
5. **Start Voice Assistant Server**
   ```bash
   python server.py
   ```
6. **Load the Chrome Extension**
	- Open Chrome and go to: ```chrome://extensions```
	- Enable Developer Mode (top right)
	- Click **“Load unpacked”**
	- Select the url_server directory (contains ```manifest.json```, ```popup.js```, etc.)
7. **Using the Extension**
    1. Click the extension icon in your Chrome toolbar.
    2. The extension:
        - Displays the current URL.
        - Extracts all links on the current page.
        - Sends this data to your running Flask server (`/process-links`).
    3. If the voice assistant is active, say **“Hey Vista”** to start interaction.
   


## 💻 Technology Stack
<p align="center">
  <a href="https://go-skill-icons.vercel.app/">
    <img
      src="https://go-skill-icons.vercel.app/api/icons?i=python,javascript,flask,langchain,ollama,git"
    />
  </a>
</p>
<p align="center">

## 👏 Contributing
I would love your help! Contribute by forking the repo and opening pull requests.
