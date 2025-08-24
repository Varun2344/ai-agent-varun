# app.py (Final Polished Version)
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

# FINAL, CORRECTED DIGEST FUNCTION with formatting fix
def load_and_format_digest():
    """
    Loads all monitored pages from competitors.json, updates their status with the
    latest findings from the log file, and formats the complete digest with line breaks.
    """
    try:
        # Step 1: Build a complete list of all pages we should be tracking from the config file.
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            competitors_config = json.load(f)
        
        status_report = {}
        for item in competitors_config:
            status_report[item['name']] = "No significant changes detected." # Default status

        # Step 2: Read the log file to find the latest summary for any page that has changed.
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        competitor_key = data.get("competitor")
                        if competitor_key in status_report and data.get("summary", {}).get("change_detected"):
                            status_report[competitor_key] = data["summary"]
                    except json.JSONDecodeError:
                        continue
        
        # Step 3: Group all statuses by company to build the report.
        results_by_company = defaultdict(list)
        for key, summary_or_status in status_report.items():
            company_name = key.split('_')[0]
            page_type = key.split('_')[1] if '_' in key else 'General'
            results_by_company[company_name].append((page_type, summary_or_status))

        # Step 4: Format the final markdown with the A, B, C on separate lines.
        digest_md = f"## Competitor Intelligence Digest - {datetime.date.today()}\n"
        competitor_number = 1
        
        for company_name, pages in sorted(results_by_company.items()):
            digest_md += f"\n### {competitor_number}) {company_name} Summary:\n"
            page_letter_code = ord('A')
            for page_type, result in sorted(pages):
                digest_md += f"\n**{chr(page_letter_code)}.** `{page_type}`: "
                if isinstance(result, str):
                    # --- THIS IS THE FIX ---
                    # Added the "\n" to ensure a line break after "No significant changes detected."
                    digest_md += result + "\n"
                else:
                    title = result.get('change_title', 'N/A')
                    points = result.get('summary_points', [])
                    summary_text = "\n".join([f"  - {p}" for p in points])
                    digest_md += f"**{title}**\n{summary_text}\n"
                page_letter_code += 1
            competitor_number += 1
            
        return digest_md

    except Exception as e:
        return f"## 🚨 Error Displaying Digest\n\nAn error occurred: \n\n```\n{str(e)}\n```"

def run_monitor_script(model_name):
    """Runs the monitor.py script and yields its output."""
    yield "🏃 Agent is starting the monitoring process..."
    command = [PYTHON_EXECUTABLE, "monitor.py", "--model", model_name]
    if SLACK_WEBHOOK_URL:
        command.extend(["--slack", SLACK_WEBHOOK_URL])

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
    output_log = "--- Agent Log ---\n"
    for line in iter(process.stdout.readline, ''):
        output_log += line
        yield output_log
    process.wait()
    yield output_log + "\n\n✅ Agent run complete. Click 'Refresh History' to update the digest."

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
    refresh_button = gr.Button("🔄 Refresh History")
    summary_display = gr.Markdown(value=load_and_format_digest())

    # --- Event Handlers ---
    run_button.click(fn=run_monitor_script, inputs=[model_dropdown], outputs=log_output)
    refresh_button.click(fn=load_and_format_digest, outputs=summary_display)

if __name__ == "__main__":
    demo.launch(share=True)