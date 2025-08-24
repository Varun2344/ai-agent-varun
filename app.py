# app.py (Upgraded with Hardcoded Slack URL for simplicity)
import gradio as gr
import subprocess
import json
import pandas as pd
import os

LOG_FILE = "summary_log.jsonl"
PYTHON_EXECUTABLE = ".\\.venv\\Scripts\\python.exe" # For Windows venv
full_log_data = []

# --- IMPORTANT: PASTE YOUR SLACK WEBHOOK URL HERE ---
# This makes the UI cleaner, as you don't have to enter it every time.
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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" 

def load_summaries():
    """Loads and processes summaries from the log file."""
    global full_log_data
    summaries, full_log_data = [], []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    summary = data.get('summary', {})
                    summaries.append({
                        "Timestamp": data.get('timestamp', 'N/A').split('T')[0],
                        "Competitor": data.get('competitor', 'N/A').replace('_', ' '),
                        "Category": summary.get('change_category', 'N/A'),
                        "Title": summary.get('change_title', 'N/A'),
                        "Impact": summary.get('impact_level', 'N/A')
                    })
                    full_log_data.append(data)
                except json.JSONDecodeError:
                    continue
    if not summaries:
        return pd.DataFrame(columns=["Timestamp", "Competitor", "Category", "Title", "Impact"]), "Select a row to see details."
    
    full_log_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    df = pd.DataFrame(summaries).sort_values(by="Timestamp", ascending=False)
    return df, "Select a row in the history table to see full details."

def run_monitor_script(model_name):
    """Runs the monitor.py script and yields its output."""
    yield "Agent is starting the monitoring process..."
    
    command = [PYTHON_EXECUTABLE, "monitor.py", "--model", model_name]
    # Add the slack command only if a URL has been provided in the code
    if SLACK_WEBHOOK_URL and "YOUR/URL/HERE" not in SLACK_WEBHOOK_URL:
        command.extend(["--slack", SLACK_WEBHOOK_URL])

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
    
    output_log = "--- Agent Log ---\n"
    for line in iter(process.stdout.readline, ''):
        output_log += line
        yield output_log
    
    process.wait()
    yield output_log + "\n\n Agent run complete. You can now refresh the history."

def show_details(evt: gr.SelectData):
    """Displays the full details of a selected row."""
    if evt.index is None or not full_log_data:
        return "Select a row to see details."
    selected_data = full_log_data[evt.index[0]]
    summary = selected_data.get('summary', {})
    details_md = f"""
### Details for {selected_data.get('competitor')}
**Timestamp:** {selected_data.get('timestamp')}
**Category:** {summary.get('change_category')}
**Title:** {summary.get('change_title')}
**Impact:** {summary.get('impact_level')}
**Summary Points:**
"""
    for point in summary.get('summary_points', []): details_md += f"- {point}\n"
    details_md += "\n**Evidence Snippets:**\n"
    for evidence in summary.get('evidence', []): details_md += f"`{evidence}`\n"
    return details_md

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
    gr.Markdown("###  Detected Changes History")
    df, details_text = load_summaries()
    summary_df = gr.DataFrame(df, interactive=False, wrap=True)
    details_md_box = gr.Markdown(details_text)

    # --- Event Handlers ---
    run_button.click(
        fn=run_monitor_script,
        inputs=[model_dropdown], # Input is now just the model
        outputs=log_output
    ).then(
        fn=load_summaries,
        outputs=[summary_df, details_md_box]
    )
    summary_df.select(fn=show_details, outputs=details_md_box)

if __name__ == "__main__":
    demo.launch(share=True)