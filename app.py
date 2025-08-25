# app.py (FINAL SUBMISSION VERSION WITH MODERN UI)
import gradio as gr
import subprocess
import json
import os
import datetime
from collections import defaultdict
from dotenv import load_dotenv

# --- Load Environment Variables and Config ---
load_dotenv()
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
LOG_FILE = "summary_log.jsonl"
CONFIG_FILE = "competitors.json"
PYTHON_EXECUTABLE = ".\\.venv\\Scripts\\python.exe"

# --- FINAL, UPGRADED DIGEST FUNCTION for UI ---
def load_and_format_digest():
    """
    Loads the latest summaries and formats them into the new detailed
    markdown string for the UI, grouped by category.
    """
    if not os.path.exists(LOG_FILE):
        return "<div style='color: #f0f0f0;'>No history found. Run the monitor to generate a report.</div>"

    latest_changes = {}
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("competitor") and data.get("summary", {}).get("change_detected"):
                    latest_changes[(data["competitor"])] = data
            except json.JSONDecodeError:
                continue

    if not latest_changes:
        return "<div style='color: #f0f0f0;'>No significant changes detected in the latest logs.</div>"

    changes_by_category = defaultdict(list)
    for change in latest_changes.values():
        category = change['summary'].get('change_category', 'General Update')
        company_name = change['competitor'].split('_')[0]
        change['_company_name'] = company_name # Add company name for sorting
        changes_by_category[(category)].append(change)

    # Build the final markdown string with HTML for styling
    digest_md = f"<div style='color: #f0f0f0; padding: 20px;'>\n"
    digest_md += f"<h2 style='color: #add8e6;'>Weekly Competitor Summary - {datetime.date.today()}</h2>\n"
    digest_md += "<p style='color: #d3d3d3;'>Here's a detailed breakdown of the latest detected changes across competitors.</p>\n"

    for category, changes in sorted(changes_by_category.items()):
        digest_md += f"<h3 style='color: #87ceeb; margin-top: 20px;'>📄 {category}:</h3>\n"
        for change in sorted(changes, key=lambda x: x['_company_name']): # Sort by company
            company = change['_company_name']
            title = change['summary'].get('change_title', 'N/A')
            update = change['summary'].get('update', 'N/A')
            impact = change['summary'].get('impact', 'N/A')
            analysis = change['summary'].get('analysis', 'N/A')

            digest_md += f"<div style='margin-left: 20px; margin-bottom: 15px; border-left: 2px solid #4682b4; padding-left: 10px;'>\n"
            digest_md += f"<strong style='color: #eee;'>`{company}` | {title}</strong><br>\n"
            digest_md += f"<span style='color: #d3d3d3;'>• <strong>Update:</strong> {update}</span><br>\n"
            digest_md += f"<span style='color: #d3d3d3;'>• <strong>Impact:</strong> {impact}</span><br>\n"
            digest_md += f"<span style='color: #d3d3d3;'>• <strong>Analysis:</strong> {analysis}</span>\n"
            digest_md += "</div>\n"

    digest_md += "</div>\n"
    return digest_md

def run_monitor_script(model_name):
    """Runs the monitor.py script and yields its output."""
    yield "<div style='color: #f0f0f0;'>🏃 Agent is starting the monitoring process...</div>"
    command = [PYTHON_EXECUTABLE, "monitor.py", "--model", model_name]
    if SLACK_WEBHOOK_URL:
        command.extend(["--slack", SLACK_WEBHOOK_URL])

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
    output_log = "<div style='color: #d3d3d3;'>--- Agent Log ---<br>"
    for line in iter(process.stdout.readline, ''):
        output_log += line + "<br>"
        yield output_log + "</div>"
    process.wait()
    yield output_log + "<br><br><span style='color: #98fb98;'>✅ Agent run complete. Click 'Refresh History' to update the digest.</span></div>"

# --- Gradio Interface Definition with Dark Theme and Styling ---
with gr.Blocks(theme=gr.themes.Base(primary_hue="blue", secondary_hue="blue"), css="body { background-color: #1e1e24; color: #f0f0f0; } footer {display: none !important;}") as demo:
    gr.Markdown("<div style='color: #add8e6; text-align: center;'><h1>🕵️ Competitor Intelligence Agent</h1></div>")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("<h3 style='color: #d3d3d3;'>⚙️ Controls</h3>")
            model_dropdown = gr.Dropdown(choices=["phi3", "mistral:7b", "llama3:8b"], value="phi3", label="AI Model", elem_classes="dark-input")
            run_button = gr.Button("🚀 Run Monitor Now", variant="primary")
        with gr.Column(scale=3):
            gr.Markdown("<h3 style='color: #d3d3d3;'>📜 Agent Log</h3>")
            log_output = gr.HTML(label="Live Output")

    gr.HTML("<hr style='border-top: 1px solid #444; margin: 20px 0;'>")
    gr.Markdown("<h3 style='color: #d3d3d3;'>📊 Latest Intelligence Digest</h3>")
    refresh_button = gr.Button("📊 Generate Digest")
    summary_display = gr.HTML(value=load_and_format_digest())

    # --- Event Handlers ---
    run_button.click(fn=run_monitor_script, inputs=[model_dropdown], outputs=log_output)
    refresh_button.click(fn=load_and_format_digest, outputs=summary_display)

if __name__ == "__main__":
    demo.launch(share=True)