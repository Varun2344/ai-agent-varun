# app.py (Final Version with Digest View)
import gradio as gr
import subprocess
import json
import os
import datetime
import time
from collections import defaultdict

LOG_FILE = "summary_log.jsonl"
PYTHON_EXECUTABLE = ".\\.venv\\Scripts\\python.exe" # For Windows venv
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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" # Paste your Slack URL here

def load_and_format_digest():
    """
    Loads the latest summary for each competitor page from the log file
    and formats it into a single, beautiful markdown string for the UI.
    """
    if not os.path.exists(LOG_FILE):
        return "No history found. Run the monitor to generate a report."

    # This dictionary will store the most recent entry for each unique competitor page
    latest_entries = {}
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                # Create a unique key for each competitor page (e.g., "Figma_Pricing")
                competitor_key = data.get('competitor')
                if competitor_key:
                    latest_entries[competitor_key] = data # The last entry in the file is the newest
            except json.JSONDecodeError:
                continue

    if not latest_entries:
        return "Log file is empty. Run the monitor to generate a report."

    # Group the latest entries by company name
    results_by_company = defaultdict(list)
    for key, data in latest_entries.items():
        company_name = key.split('_')[0]
        results_by_company[company_name].append(data)

    # Build the final markdown string
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
            if summary.get("change_detected", False):
                summary_text = "\n".join([f"  - {p}" for p in points])
                digest_md += f"**{title}**\n{summary_text}\n"
            else:
                # In a real scenario, we'd log "no change", but our log only contains changes.
                # For the UI, we can assume anything in the log is a change.
                # Let's adjust this to always show the summary if an entry exists.
                summary_text = "\n".join([f"  - {p}" for p in points])
                digest_md += f"**{title}**\n{summary_text}\n"
            page_letter_code += 1
        competitor_number += 1
        
    return digest_md

def run_monitor_script(model_name):
    """Runs the monitor.py script and yields its output."""
    yield "Agent is starting the monitoring process..."
    command = [PYTHON_EXECUTABLE, "monitor.py", "--model", model_name]
    if SLACK_WEBHOOK_URL and "YOUR/URL/HERE" not in SLACK_WEBHOOK_URL:
        command.extend(["--slack", SLACK_WEBHOOK_URL])

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
    
    output_log = "--- Agent Log ---\n"
    for line in iter(process.stdout.readline, ''):
        output_log += line
        yield output_log
    
    process.wait()
    time.sleep(2)
    yield output_log + "\n\nAgent run complete. The digest below will now update."

# --- Gradio Interface Definition ---
with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as demo:
    gr.Markdown("# Competitor Intelligence Agent")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Controls")
            model_dropdown = gr.Dropdown(choices=["phi3", "mistral:7b", "llama3:8b"], value="phi3", label="Select AI Model")
            run_button = gr.Button("Run Monitor Now", variant="primary")
        with gr.Column(scale=3):
            gr.Markdown("### Agent Log")
            log_output = gr.Textbox(label="Live Output", interactive=False, lines=10, max_lines=10)

    gr.Markdown("---")
    gr.Markdown("### Latest Intelligence Digest")
    
    # We now use a Markdown component instead of a DataFrame
    summary_display = gr.Markdown(value=load_and_format_digest())

    # --- Event Handlers ---
    run_button.click(
        fn=run_monitor_script,
        inputs=[model_dropdown],
        outputs=log_output
    ).then(
        fn=load_and_format_digest,
        outputs=summary_display # Update the markdown display
    )

if __name__ == "__main__":
    demo.launch(share=True)