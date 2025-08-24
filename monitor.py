# monitor.py (Final Production-Ready Version)
import os
import argparse
import json
import hashlib
import time
import datetime
from datetime import timezone # <-- Import timezone for the fix
import requests
from bs4 import BeautifulSoup
import ollama
import difflib
from collections import defaultdict

# --- Helper Functions ---

def format_and_send_digest(monitoring_results: dict, slack_url: str):
    """Formats all monitoring results into a structured digest and posts it to Slack."""
    if not slack_url or not monitoring_results:
        return

    master_blocks = [{"type": "header", "text": {"type": "plain_text", "text": f"Competitor Intelligence Digest - {datetime.date.today()}", "emoji": True}}]
    master_blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": "A summary of all monitored competitor pages."}]})

    competitor_number = 1
    for company_name, pages in monitoring_results.items():
        master_blocks.append({"type": "divider"})
        report_text = f"*{competitor_number}) {company_name} Summary:*\n"
        page_letter_code = ord('A')
        for page_type, result in pages.items():
            report_text += f"\n*{chr(page_letter_code)}.* `{page_type}`: "
            if result == "No change":
                report_text += "No significant changes detected."
            else:
                title = result.get("change_title", "N/A")
                summary_points = "\n".join([f"    • {p}" for p in result.get("summary_points", [])])
                report_text += f"*{title}*\n{summary_points}"
            page_letter_code += 1
        master_blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": report_text}})
        competitor_number += 1

    try:
        requests.post(slack_url, json={"blocks": master_blocks}, timeout=15)
        print("Consolidated digest sent to Slack.")
    except Exception as e:
        print(f"Failed to send consolidated digest to Slack: {e}")

def fetch_text_from_url(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]): tag.decompose()
        from rag.utils import clean_text
        return clean_text(soup.get_text(separator=" "))
    except requests.RequestException as e:
        print(f"[Error] Could not fetch URL {url}: {e}"); return None

def get_text_hash(text: str):
    if not text: return None
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def summarize_change_with_ai(old_text: str, new_text: str, url: str, model_to_use: str):
    print("  -> AI is summarizing and categorizing the changes...")
    diff = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile='old', tofile='new', n=3))
    if not diff: return {"change_detected": False}
    diff_report = "\n".join(diff)
    if len(diff_report) > 4000: diff_report = diff_report[:4000] + "\n... (diff truncated)"
    system_prompt = """
    You are a sharp-eyed product analyst AI. Your goal is to analyze a 'diff report' from a competitor's page and provide a categorized summary.
    Lines starting with '-' were removed, lines with '+' were added.
    First, you MUST categorize the change into one of these 5 specific types:
    - "Pricing Change"
    - "Marketing & Messaging"
    - "Product Update & Release Notes"
    - "Social Media Announcement"
    - "General Website Update"
    Your response MUST be a clean JSON object with this exact structure:
    {"change_detected": true, "change_category": "The category you identified.", "change_title": "A concise title.", "summary_points": ["Bullet point 1.", "Bullet point 2."], "impact_level": "low" | "medium" | "high", "evidence": ["A direct quote of an important added line.", "Another quote of a removed line."]}
    If changes are insignificant, return JSON with "change_detected" set to false.
    """
    user_prompt = f"Analyze this diff report from {url}:\n\n{diff_report}"
    try:
        response = ollama.chat(model=model_to_use, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}], format='json')
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"  -> AI summary failed with error: {e}"); return None

def save_summary_to_log(summary_json: dict, competitor_name: str, log_file="summary_log.jsonl"):
    # FIX: Using the new, recommended way to get UTC time
    entry = {"timestamp": datetime.datetime.now(timezone.utc).isoformat(), "competitor": competitor_name, "summary": summary_json}
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')
    print(f"  -> Summary saved to {log_file}")

# --- Main Execution Function ---

def run_monitor(config_path: str, snapshot_dir: str, model_name: str, slack_url: str):
    print(f"--- Starting Competitor Monitor (using model: {model_name}) ---")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f: competitors = json.load(f)
    except FileNotFoundError:
        print(f"[Error] Config file not found: {config_path}"); return

    os.makedirs(snapshot_dir, exist_ok=True)
    
    monitoring_results = defaultdict(dict)
    for competitor in competitors:
        name = competitor.get("name")
        company_name, page_type = name.split('_')[0], name.split('_')[1] if '_' in name else 'General'
        monitoring_results[company_name][page_type] = "No change"

    for competitor in competitors:
        name, url = competitor.get("name"), competitor.get("url")
        company_name, page_type = name.split('_')[0], name.split('_')[1] if '_' in name else 'General'
        
        print(f"\nChecking: {name} ({url})")
        new_text = fetch_text_from_url(url)
        if new_text is None: continue
        
        new_hash, snapshot_file_path = get_text_hash(new_text), os.path.join(snapshot_dir, f"{name}.txt")
        
        if os.path.exists(snapshot_file_path):
            with open(snapshot_file_path, 'r', encoding='utf-8') as f: old_text = f.read()
            old_hash = get_text_hash(old_text)

            if new_hash != old_hash:
                print(f"  -> Change DETECTED for {name}!")
                ai_summary = summarize_change_with_ai(old_text, new_text, url, model_to_use=model_name)
                
                if ai_summary:
                    save_summary_to_log(ai_summary, name)
                    if ai_summary.get("change_detected"):
                        monitoring_results[company_name][page_type] = ai_summary
                
                with open(snapshot_file_path, 'w', encoding='utf-8') as f: f.write(new_text)
        else:
            print(f"  -> First time seeing {name}. Creating snapshot."); 
            with open(snapshot_file_path, 'w', encoding='utf-8') as f: f.write(new_text)

    if slack_url:
        format_and_send_digest(monitoring_results, slack_url)
    
    print("\n--- Monitor run complete ---")

# --- Engine Start Block ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor competitor websites for changes.")
    parser.add_argument("--config", default="competitors.json")
    parser.add_argument("--snapshots", default="./snapshots")
    parser.add_argument("--model", default="phi3")
    parser.add_argument("--slack", default=None)
    args = parser.parse_args()
    
    run_monitor(config_path=args.config, snapshot_dir=args.snapshots, model_name=args.model, slack_url=args.slack)