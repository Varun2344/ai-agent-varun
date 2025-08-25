# app.py (FINAL SUBMISSION VERSION)
import gradio as gr
import subprocess
import json
import os
import datetime
from collections import defaultdict
from dotenv import load_dotenv

# --- Load Environment Variables and Config ---
load_dotenv()
LOG_FILE = "summary_log.jsonl"
CONFIG_FILE = "competitors.json"
PYTHON_EXECUTABLE = ".\\.venv\\Scripts\\python.exe"

# --- Functions ---
def load_and_format_digest():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f: competitors_config = json.load(f)
        status_report = {}
        for item in competitors_config: status_report[item['name']] = "No significant changes detected."
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if data.get("competitor") in status_report and data.get("summary", {}).get("change_detected"):
                            status_report[data["competitor"]] = data["summary"]
                    except json.JSONDecodeError: continue
        results_by_company = defaultdict(list)
        for key, summary_or_status in status_report.items():
            company_name, page_type = key.split('_')[0], key.split('_')[1] if '_' in key else 'General'
            results_by_company[company_name].append((page_type, summary_or_status))
        digest_md, competitor_number = f"## Competitor Intelligence Digest - {datetime.date.today()}\n", 1
        for company_name, pages in sorted(results_by_company.items()):
            digest_md += f"\n### {competitor_number}) {company_name} Summary:\n"
            page_letter_code = ord('A')
            for page_type, result in sorted(pages):
                digest_md += f"\n**{chr(page_letter_code)}.** `{page_type}`: "
                if isinstance(result, str): digest_md += result + "\n"
                else:
                    title, points = result.get('change_title', 'N/A'), result.get('summary_points', [])
                    summary_text = "\n".join([f"  - {p}" for p in points])
                    digest_md += f"**{title}**\n{summary_text}\n"
                page_letter_code += 1
            competitor_number += 1
        return digest_md
    except Exception as e:
        return f"## 🚨 Error Displaying Digest\n\nAn error occurred: \n\n```\n{str(e)}\n```"

def run_monitor_script(model_name):
    yield "🏃 Agent is starting the monitoring process..."
    command = [PYTHON_EXECUTABLE, "monitor.py", "--model", model_name]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
    output_log = "--- Agent Log ---\n"
    for line in iter(process.stdout.readline, ''):
        output_log += line
        yield output_log
    process.wait()
    yield output_log + "\n\n✅ Agent run complete. Click 'Generate Digest' to update."

# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🕵️ Competitor Intelligence Agent")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Controls")
            model_dropdown = gr.Dropdown(choices=["phi3", "mistral:7b", "llama3:8b"], value="phi3", label="Select AI Model")
            run_button = gr.Button("🚀 Run Monitor Now", variant="primary")
        with gr.Column(scale=3):
            gr.Markdown("### Agent Log")
            log_output = gr.Textbox(label="Live Output", interactive=False, lines=15, max_lines=15)
    gr.Markdown("---")
    gr.Markdown("### 📊 Latest Intelligence Digest")
    digest_button = gr.Button("📊 Generate Digest from History")
    summary_display = gr.Markdown(value=load_and_format_digest())
    run_button.click(fn=run_monitor_script, inputs=[model_dropdown], outputs=log_output)
    digest_button.click(fn=load_and_format_digest, outputs=summary_display)

if __name__ == "__main__":
    demo.launch(share=True)