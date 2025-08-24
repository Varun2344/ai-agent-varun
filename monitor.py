# NEW "DEBUG" VERSION of run_monitor
def run_monitor(config_path: str, snapshot_dir: str, model_name: str, slack_url: str):
    print(f"--- Starting Competitor Monitor (using model: {model_name}) ---")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f: competitors = json.load(f)
    except FileNotFoundError:
        print(f"[Error] Config file not found: {config_path}"); return

    os.makedirs(snapshot_dir, exist_ok=True)
    
    monitoring_results = {}
    for competitor in competitors:
        name = competitor.get("name")
        company_name = name.split('_')[0]
        page_type = name.split('_')[1] if '_' in name else 'General'
        if company_name not in monitoring_results:
            monitoring_results[company_name] = {}
        monitoring_results[company_name][page_type] = "No change"

    for competitor in competitors:
        name, url = competitor.get("name"), competitor.get("url")
        company_name = name.split('_')[0]
        page_type = name.split('_')[1] if '_' in name else 'General'
        
        print(f"\nChecking: {name} ({url})")

        new_text = fetch_text_from_url(url)
        if new_text is None: continue
        
        new_hash, snapshot_file_path = get_text_hash(new_text), os.path.join(snapshot_dir, f"{name}.txt")
        
        if os.path.exists(snapshot_file_path):
            with open(snapshot_file_path, 'r', encoding='utf-8') as f: old_text = f.read()
            old_hash = get_text_hash(old_text)

            print(f"  -> Old Hash: {old_hash}")
            print(f"  -> New Hash: {new_hash}")

            if new_hash != old_hash:
                print("  -> DEBUG: Hashes are different. A change was found!")
                ai_summary = summarize_change_with_ai(old_text, new_text, url, model_to_use=model_name)
                print(f"  -> DEBUG: AI summary received: {ai_summary}")
                
                if ai_summary and ai_summary.get("change_detected"):
                    print("  -> DEBUG: AI confirmed a significant change.")
                    monitoring_results[company_name][page_type] = ai_summary
                    print("  -> Change collected for digest.")
                else:
                    print("  -> DEBUG: AI summary failed or reported no significant change.")
                
                with open(snapshot_file_path, 'w', encoding='utf-8') as f: f.write(new_text)
            else:
                print("  -> DEBUG: Hashes are the same. No change.")
        else:
            print(f"  -> First time seeing {name}. Creating snapshot."); 
            with open(snapshot_file_path, 'w', encoding='utf-8') as f: f.write(new_text)

    if slack_url:
        print("\nDEBUG: Preparing to send digest to Slack...")
        format_and_send_digest(monitoring_results, slack_url)
    else:
        print("\nNo Slack URL provided. Skipping digest.")
                
    print("\n--- Monitor run complete ---")