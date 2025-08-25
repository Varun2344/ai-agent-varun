# monitor.py (FINAL SUBMISSION VERSION)
import os
import argparse
import json
import hashlib
import time
import datetime
from datetime import timezone
import requests
from bs4 import BeautifulSoup
import ollama
import difflib
from collections import defaultdict
from dotenv import load_dotenv

def format_and_send_digest(all_changes: dict, slack_url: str):
    """Groups all changes by category and sends a professional digest to Slack."""
    if not slack_url or not all_changes:
        return

    changes_by_category = defaultdict(list)
    for change in all_changes:
        category = change['summary'].get('change_category', 'General Website Update')
        changes_by_category[category].append(change)

    master_blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"Weekly Competitor Summary - {datetime.date.today()}", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": "Here's a detailed breakdown of everything that happened this week across competitors."}}
    ]

    for category, changes in sorted(changes_by_category.items()):
        master_blocks.append({"type": "divider"})
        master_blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*{category}:*"}})
        for change in changes:
            company = change['competitor'].split('_')[0]
            title = change['summary'].get('change_title', 'N/A')
            update = change['summary'].get('update', 'N/A')
            impact = change['summary'].get('impact', 'N/A')
            analysis = change['summary'].get('analysis', 'N/A')

            report_text = (
                f"› `{company}` *{title}*\n"
                f"    • *Update:* {update}\n"
                f"    • *Impact:* {impact}\n"
                f"    • *Analysis:* {analysis}"
            )
            master_blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": report_text}})

    insight = f"Overall, this week saw {len(all_changes)} significant update(s), showing trends in {' and '.join(changes_by_category.keys())}."
    master_blocks.append({"type": "divider"})
    master_blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Summary Insight:* {insight}"}})

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

# FINAL, SUPERCHARGED AI function
def summarize_change_with_ai(old_text: str, new_text: str, url: str, model_to_use: str):
    print("  -> AI is generating a detailed analysis...")
    diff = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(), fromfile='old', tofile='new', n=5))
    if not diff: return {"change_detected": False}
    diff_report = "\n".join(diff)
    if len(diff_report) > 4000: diff_report = diff_report[:4000] + "\n... (diff truncated)"
    
    # FINAL, UPGRADED SYSTEM PROMPT
    system_prompt = """
    You are a world-class principal product analyst. Your job is to analyze a 'diff report' from a competitor's webpage and provide a deeply insightful, structured summary.
    Lines starting with '-' were removed. Lines starting with '+' were added.

    Your response MUST be a valid JSON object. ALL fields (`change_category`, `change_title`, `update`, `impact`, `analysis`) are REQUIRED.
    NEVER return 'N/A' for a field. If you cannot determine the impact or analysis, you must make a reasonable and logical inference based on the data.

    The JSON object must have this exact structure:
    {
      "change_detected": true,
      "change_category": "Pricing Change" | "Product Update & Release Notes" | "Marketing & Messaging",
      "change_title": "A concise, descriptive title of the change.",
      "update": "A factual, one-sentence summary of WHAT changed.",
      "impact": "A one-sentence analysis of the potential IMPACT on customers or the user experience.",
      "analysis": "A one-sentence analysis of the strategic REASON for this change (e.g., market positioning, new target audience, etc.)."
    }
    
    If the change is insignificant (typos, date changes), return JSON with "change_detected" set to false.
    """
    user_prompt = f"Analyze this diff report from {url}:\n\n{diff_report}"
    try:
        response = ollama.chat(model=model_to_use, messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}], format='json')
        return json.loads(response['message']['content'])
    except Exception as e:
        print(f"  -> AI summary failed with error: {e}"); return None

def save_summary_to_log(summary_json: dict, competitor_name: str, log_file="summary_log.jsonl"):
    entry = {"timestamp": datetime.datetime.now(timezone.utc).isoformat(), "competitor": competitor_name, "summary": summary_json}
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')

def run_monitor(config_path: str, snapshot_dir: str, model_name: str, slack_url: str):
    print(f"--- Starting Competitor Monitor (using model: {model_name}) ---")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f: competitors = json.load(f)
    except FileNotFoundError:
        print(f"[Error] Config file not found: {config_path}"); return

    os.makedirs(snapshot_dir, exist_ok=True)
    
    detected_changes = []

    for competitor in competitors:
        name, url = competitor.get("name"), competitor.get("url")
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
                
                if ai_summary and ai_summary.get("change_detected"):
                    change_data = {"competitor": name, "summary": ai_summary}
                    detected_changes.append(change_data)
                    save_summary_to_log(ai_summary, name)
                
                with open(snapshot_file_path, 'w', encoding='utf-8') as f: f.write(new_text)
        else:
            print(f"  -> First time seeing {name}. Creating snapshot."); 
            with open(snapshot_file_path, 'w', encoding='utf-8') as f: f.write(new_text)

    if slack_url and detected_changes:
        format_and_send_digest(detected_changes, slack_url)
    
    print("\n--- Monitor run complete ---")

if __name__ == "__main__":
    load_dotenv()
    SLACK_URL_FROM_ENV = os.getenv("SLACK_WEBHOOK_URL")
    parser = argparse.ArgumentParser(description="Monitor competitor websites for changes.")
    parser.add_argument("--config", default="competitors.json")
    parser.add_argument("--snapshots", default="./snapshots")
    parser.add_argument("--model", default="phi3")
    args = parser.parse_args()
    run_monitor(config_path=args.config, snapshot_dir=args.snapshots, model_name=args.model, slack_url=SLACK_URL_FROM_ENV)