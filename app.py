# app.py (Final Version with Manual Refresh Logic)
import gradio as gr
import subprocess
import json
import pandas as pd
import os
import datetime
from collections import defaultdict

LOG_FILE = "summary_log.jsonl"
PYTHON_EXECUTABLE = ".\\.venv\\Scripts\\python.exe"
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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" # Paste your Slack URL here

def load_and_format_digest():
    """Loads the latest summary for each competitor page and formats it into a markdown string."""
    if not os.path.exists(LOG_FILE):
        return "No history found. Run the monitor to generate a report."

    latest_entries = {}
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                competitor_key = data.get('competitor')
                if competitor_key:
                    latest_entries[competitor_key] = data
            except json.JSONDecodeError:
                continue

    if not latest_entries:
        return "Log file is empty. Run the monitor to see a report."

    results_by_company = defaultdict(list)
    for key, data in latest_entries.items():
        company_name = key.split('_')[0]
        results_by_company[company_name].append(data)

    digest_md = f"## Competitor Intelligence Digest - {datetime.date.today()}\n"
    competitor_number = 1
    
    for company_name, entries in sorted(results_by_company.items()):
        digest_md += f"### {competitor_number}) {company_name} Summary:\n"
        page_letter_code = ord('A')
        for entry in sorted(entries, key=lambda x: x['competitor']):
            page_type = entry['competitor'].replace(f"{company_name}_", "")
            summary = entry.get('summary', {})
            title = summary.get('change_title', 'N/A')
            points = summary.get('summary_points', [])

            digest_md += f"**{chr(page_letter_code)}.** `{page_type}`: "
            summary_text = "\n".join([f"  - {p}" for p in points])
            digest_md += f"**{title}**\n{summary_text}\n"
            page_letter_code += 1
        competitor_number += 1
        
    return digest_md

def run_monitor_script(model_name):
    """Runs the monitor.py script and yields its output."""
    yield "🏃 Agent is starting the monitoring process... Please wait."
    command = [PYTHON_EXECUTABLE, "monitor.py", "--model", model_name]
    if SLACK_WEBHOOK_URL and "YOUR/URL/HERE" not in SLACK_WEBHOOK_URL:
        command.extend(["--slack", SLACK_WEBHOOK_URL])

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
    
    output_log = "--- Agent Log ---\n"
    for line in iter(process.stdout.readline, ''):
        output_log += line
        yield output_log
    
    process.wait()
    # NEW FINAL MESSAGE to guide the user
    yield output_log + "\n\n✅ Agent run complete. Click the 'Refresh History' button to see the new digest."

# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as demo:
    gr.Markdown("# 🕵️ Competitor Intelligence Agent")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Controls")
            model_dropdown = gr.Dropdown(choices=["phi3", "mistral:7b", "llama3:8b"], value="phi3", label="Select AI Model")
            run_button = gr.Button("🚀 Run Monitor Now", variant="primary")
        with gr.Column(scale=3):
            gr.Markdown("### Agent Log")
            log_output = gr.Textbox(label="Live Output", interactive=False, lines=10, max_lines=10)

    gr.Markdown("---")
    gr.Markdown("### 📊 Latest Intelligence Digest")
    
    refresh_button = gr.Button("🔄 Refresh History") # Moved the button here for better flow
    summary_display = gr.Markdown(value=load_and_format_digest())

    # --- Event Handlers ---
    # The run button ONLY updates the log
    run_button.click(
        fn=run_monitor_script,
        inputs=[model_dropdown],
        outputs=log_output
    )
    
    # The refresh button ONLY updates the digest
    refresh_button.click(fn=load_and_format_digest, outputs=summary_display)

if __name__ == "__main__":
    demo.launch(share=True)