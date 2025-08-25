# app.py (FINAL "Read-Only" Dashboard Version)
import gradio as gr
import json
import os
import datetime
from collections import defaultdict

LOG_FILE = "summary_log.jsonl"
CONFIG_FILE = "competitors.json"
AGENT_LOG_FILE = "last_run_log.txt" # The file where we will save the monitor's log

def load_agent_log():
    """Loads the raw log from the last run of monitor.py."""
    if os.path.exists(AGENT_LOG_FILE):
        with open(AGENT_LOG_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return "No agent run has been logged yet. Please run the monitor script once."

def load_and_format_digest():
    """Loads and formats the latest summaries from the log file."""
    if not os.path.exists(LOG_FILE):
        return "No intelligence digest has been generated yet."

    latest_changes = {}
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if data.get("competitor") and data.get("summary", {}).get("change_detected"):
                    latest_changes[data["competitor"]] = data
    except (json.JSONDecodeError, IOError) as e:
        return f"Error reading log file: {e}"

    if not latest_changes:
        return "No significant changes were found in the latest run."

    changes_by_category = defaultdict(list)
    for change in latest_changes.values():
        category = change['summary'].get('change_category', 'General Update')
        company = change['competitor'].split('_')[0]
        change['_company_name'] = company
        changes_by_category[category].append(change)

    digest_md = f"## Weekly Competitor Summary - {datetime.date.today()}\n"
    for category, changes in sorted(changes_by_category.items()):
        digest_md += f"\n### 📄 {category}:\n"
        for change in sorted(changes, key=lambda x: x['_company_name']):
            company = change['_company_name']
            title = change['summary'].get('change_title', 'N/A')
            update = change['summary'].get('update', 'N/A')
            impact = change['summary'].get('impact', 'N/A')
            analysis = change['summary'].get('analysis', 'N/A')
            digest_md += (
                f"- **`{company}` | {title}**\n"
                f"    - **Update:** {update}\n"
                f"    - **Impact:** {impact}\n"
                f"    - **Analysis:** {analysis}\n"
            )
    return digest_md

# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🕵️ Competitor Intelligence Agent Dashboard")
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Log of Last Automated Run")
            log_output = gr.Textbox(value=load_agent_log, label="Agent Log", interactive=False, lines=15, max_lines=15)
        with gr.Column():
            gr.Markdown("### Latest Intelligence Digest")
            summary_display = gr.Markdown(value=load_and_format_digest)

if __name__ == "__main__":
    demo.launch(share=True)