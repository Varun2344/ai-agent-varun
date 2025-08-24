# 🕵️ Competitor Intelligence Agent

An AI-powered agent that monitors competitor websites for significant changes and delivers a consolidated, categorized summary to product managers via Slack.

*This project was built for the Product Space AI Agent Hackathon (August 2025).*

---

### 📹 Demo Video
*[A 90-second Loom or YouTube video showing the final project in action will go here after Day 2 or 3]*

---

## 🎯 Problem Statement
In a competitive market, product managers need to stay constantly updated on competitor activities. Manually checking multiple websites, changelogs, and pricing pages is time-consuming, inefficient, and prone to human error. Subtle but important changes in product messaging, features, or pricing can easily be missed, putting a team at a strategic disadvantage.

## ✨ Our Solution
This agent automates the entire monitoring and analysis process. It acts as a tireless analyst that runs in the background, providing a comprehensive daily digest of all competitor movements.

The agent's workflow:
1.  **Monitor:** It periodically checks a configurable list of competitor URLs (homepages, pricing, release notes).
2.  **Detect:** It intelligently finds changes by comparing the current page content to a previously saved snapshot using a diffing algorithm.
3.  **Analyze & Summarize:** Any detected change is sent to a local Large Language Model (LLM) which acts as a product analyst. The AI categorizes the change (e.g., "Pricing Change," "Product Update") and writes a concise summary of its impact.
4.  **Deliver:** It compiles all findings into a single, consolidated "Daily Digest" and delivers it to a designated Slack channel in a professional, easy-to-read format.

## 🔥 Features
- **Consolidated Daily Digest:** Get one clean report for each competitor instead of scattered alerts.
- **AI-Powered Analysis:** Uses local LLMs (e.g., `phi3`) via Ollama for private, cost-free, and intelligent summarization.
- **Change Categorization:** Automatically tags updates as Pricing, Marketing, Product Update, etc.
- **Slack Integration:** Delivers beautifully formatted reports directly to your team's workspace using Slack's Block Kit.
- **Interactive UI:** A simple Gradio interface to run the agent manually and view the history of all detected changes.
- **Configurable Targets:** Easily change which companies and pages to monitor by editing a simple `competitors.json` file.

## 🛠️ Tech Stack
- **Backend:** Python
- **AI:** Ollama with local LLMs (Phi-3, Mistral)
- **Web Scraping:** `requests`, `BeautifulSoup4`
- **UI:** Gradio
- **Notifications:** Slack Webhooks

## 🚀 How to Run Locally

1.  **Prerequisites:**
    - Python 3.10+
    - [Ollama](https://ollama.com/) installed and running.
    - Pull an AI model: `ollama pull phi3`

2.  **Clone the repository:**
    ```bash
    git clone [https://github.com/Varun2344/ai-agent-varun.git](https://github.com/Varun2344/ai-agent-varun.git)
    cd ai-agent-varun
    ```

3.  **Set up the environment:**
    ```bash
    # Create and activate a virtual environment
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    
    # Install dependencies
    pip install -r requirements.txt
    ```

4.  **Configure your targets:**
    - Edit the `competitors.json` file to add the URLs you want to monitor.

5.  **Run the UI:**
    ```bash
    python app.py
    ```
    - Open the local URL (e.g., `http://127.0.0.1:7860`) in your browser.
    - Click "Run Monitor Now" to start the agent.

---
### Screenshots
*[A screenshot of your Gradio UI will go here]*

*[A screenshot of a Slack notification will go here]*