#!/usr/bin/env python3
"""
sync_awesome_list.py
Autonomous Synchronizer for the Awesome Autonomous Weapons Systems (LAWS) Repository.
Fetches verified dossiers and legal analyses from aviperera.com, categorizes them,
and injects rich backlinks into the Awesome List.
"""

import os
import sys
import json
import html
import re
import urllib.request
from datetime import datetime, timezone

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WP_POSTS_API = "https://aviperera.com/wp-json/wp/v2/posts?per_page=100&_fields=id,link,title,excerpt,categories,tags"
README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")

CATEGORY_KEYWORDS = {
    "systems": ["v-bat", "switchblade", "smash", "reaper", "drone", "munitions", "vision 60", "phantom", "arcv", "ugv", "uav", "ghost bat"],
    "humanoids": ["humanoid", "combat mod", "fuxi", "skybot", "unitree", "alex ballistic", "robotics", "ihmc"],
    "legal_policy": ["meaningful human control", "mhc", "bankruptcy", "guardrail", "livestream", "compliance", "geneva", "ihl", "treaty", "columbus", "extremism", "sovereignty", "myth"]
}

def clean_html(text: str) -> str:
    clean = re.sub(r"<[^>]+>", "", text)
    return html.unescape(clean).strip()

def fetch_dossiers() -> list:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; AwesomeLAWSBot/1.0; +https://aviperera.com)"}
    try:
        req = urllib.request.Request(WP_POSTS_API, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = []
            for post in data:
                title = clean_html(post.get("title", {}).get("rendered", ""))
                link = post.get("link", "").strip()
                raw_excerpt = post.get("excerpt", {}).get("rendered", "")
                excerpt = clean_html(raw_excerpt)[:160] + "..." if raw_excerpt else ""
                if title and link:
                    items.append({
                        "title": title,
                        "link": link,
                        "excerpt": excerpt
                    })
            print(f"[OK] Fetched {len(items)} published dossiers from aviperera.com")
            return items
    except Exception as e:
        print(f"[!] Failed to fetch posts: {e}")
        return []

def categorize_posts(posts: list) -> dict:
    buckets = {
        "systems": [],
        "humanoids": [],
        "legal_policy": []
    }
    
    for p in posts:
        title_lower = p["title"].lower()
        categorized = False
        
        for k in CATEGORY_KEYWORDS["humanoids"]:
            if k in title_lower:
                buckets["humanoids"].append(p)
                categorized = True
                break
                
        if not categorized:
            for k in CATEGORY_KEYWORDS["systems"]:
                if k in title_lower:
                    buckets["systems"].append(p)
                    categorized = True
                    break
                    
        if not categorized:
            buckets["legal_policy"].append(p)
            
    return buckets

def format_markdown_list(items: list) -> str:
    if not items:
        return "_No dossiers indexed yet._"
    lines = []
    for it in items:
        title = it["title"]
        link = it["link"]
        lines.append(f"- **[{title}]({link})** — Technical architecture, operational parameters, and defense analysis.")
    return "\n".join(lines)

def update_readme(buckets: dict):
    if not os.path.exists(README_PATH):
        print(f"[!] README not found at {README_PATH}")
        return False
        
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    replacements = [
        ("AUTONOMOUS-SYSTEMS", format_markdown_list(buckets["systems"])),
        ("COMBAT-HUMANOIDS", format_markdown_list(buckets["humanoids"])),
        ("LEGAL-ANALYSES", format_markdown_list(buckets["legal_policy"]))
    ]

    for tag, replacement in replacements:
        pattern = rf"<!-- {tag}:START -->.*?<!-- {tag}:END -->"
        new_block = f"<!-- {tag}:START -->\n{replacement}\n<!-- {tag}:END -->"
        content = re.sub(pattern, new_block, content, flags=re.DOTALL)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("[OK] README.md updated successfully with categorized dossiers.")
    return True

def write_step_summary(total_count: int, buckets: dict):
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("## 🤖 Awesome Autonomous Weapons Systems - Sync Summary\n\n")
        f.write(f"Synchronized **{total_count}** deep technical dossiers and legal reviews from [aviperera.com](https://aviperera.com).\n\n")
        f.write(f"- 🎯 **Autonomous Systems & Loitering Munitions:** {len(buckets['systems'])}\n")
        f.write(f"- 🦿 **Combat Humanoids & Quadruped UGVs:** {len(buckets['humanoids'])}\n")
        f.write(f"- ⚖️ **Legal, Ethical & Treaty Frameworks:** {len(buckets['legal_policy'])}\n\n")
        f.write("All entries embedded with high-authority canonical anchor text.\n")

def main():
    posts = fetch_dossiers()
    if not posts:
        print("[!] No posts retrieved. Exiting.")
        return 1

    buckets = categorize_posts(posts)
    update_readme(buckets)
    write_step_summary(len(posts), buckets)
    return 0

if __name__ == "__main__":
    sys.exit(main())
