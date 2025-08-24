# app.py
import gradio as gr
import subprocess
import json
import pandas as pd
import os
import time

LOG_FILE = "summary_log.jsonl"
PYTHON_EXECUTABLE = ".\\.venv\\Scripts\\python.exe" # For Windows venv

# --- Data Loading and UI Functions ---

def load_summaries():
    """Loads summaries from the log file and returns them as a pandas DataFrame."""
    summaries = []
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
                except json.JSONDecodeError:
                    continue # Skip any corrupted lines in the log
    
    if not summaries:
        # Return an empty DataFrame with the correct columns if the log is empty
        return pd.DataFrame(columns=["Timestamp", "Competitor", "Category", "Title", "Impact"])
        
    # Create DataFrame and sort by Timestamp descending
    return pd.DataFrame(summaries).sort_values(by="Timestamp", ascending=False)

def run_monitor_script(slack_url, model_name):
    """Runs the monitor.py script and yields its output in real-time."""
    yield "🏃 Agent is starting the monitoring process... This might take a minute."
    
    # Construct the command to run the monitor script
    command = [PYTHON_EXECUTABLE, "monitor.py", "--model", model_name]
    if slack_url:
        command.extend(["--slack", slack_url])

    # Start the subprocess
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1)
    
    output_log = "--- Agent Log ---\n"
    # Read and yield the output line by line
    for line in iter(process.stdout.readline, ''):
        print(line, end='') # Optional: print to the console for debugging
        output_log += line
        yield output_log
    
    process.wait() # Wait for the script to finish
    yield output_log + "\n\n✅ Agent run complete. You can now refresh the history."

# --- Gradio Interface Definition ---

with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as demo:
    gr.Markdown("# 🕵️ Competitor Intelligence Agent")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Controls")
            model_dropdown = gr.Dropdown(
                choices=["phi3", "mistral:7b", "tinyllama"], 
                value="phi3", 
                label="Select AI Model"
            )
            slack_textbox = gr.Textbox(label="Slack Webhook URL (Optional)", placeholder="Paste your Slack URL here...")
            run_button = gr.Button("🚀 Run Monitor Now", variant="primary")
        
        with gr.Column(scale=3):
            gr.Markdown("### Agent Log")
            log_output = gr.Textbox(
                label="Live Output", 
                interactive=False,
                lines=10,
                max_lines=10,
                placeholder="Agent logs will appear here..."
            )

    gr.Markdown("---")
    gr.Markdown("### 📊 Detected Changes History")
    
    with gr.Row():
        refresh_button = gr.Button("🔄 Refresh History")
    
    summary_df = gr.DataFrame(
        load_summaries(),
        interactive=False
    )

    # --- Event Handlers for Buttons ---
    run_button.click(
        fn=run_monitor_script,
        inputs=[slack_textbox, model_dropdown],
        outputs=log_output
    )
    
    refresh_button.click(fn=load_summaries, outputs=summary_df)


if __name__ == "__main__":
    demo.launch()