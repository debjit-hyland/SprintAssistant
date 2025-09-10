import re
from typing import Dict, Tuple
from jira_client import (
    jira_create_issue, jira_update_issue, jira_add_comment,
    jira_transition_issue, jira_delete_issue
)
from llm_client import summarize_text_markdown

def parse_kv_pairs(s: str) -> Dict[str, str]:
    # Parses key=value pairs (quotes allowed for values with spaces)
    pattern = r'(\w+)=(".*?"|\'.*?\'|\S+)'
    out = {}
    for k, v in re.findall(pattern, s):
        out[k.lower()] = v.strip('\'"')
    return out

async def handle_command(text: str, turn_context) -> str:
    """
    Supported:
      /create "Title here" desc="..." type=Task priority=P2 assignee=me labels=foo,bar
      /update KEY-123 summary="New title" priority=P3
      /comment KEY-123 "Comment text"
      /transition KEY-123 "In Progress"
      /delete KEY-123
      /summarize KEY-123 "raw meeting/chat text here"
    """
    if not text.startswith("/"):
        return "Try commands like `/create`, `/update`, `/comment`, `/summarize`."

    cmd, rest = (text.split(" ", 1) + [""])[:2]
    cmd = cmd.lower()

    try:
        if cmd == "/create":
            title_match = re.search(r'"([^"]+)"', rest)
            if not title_match:
                return "Usage: /create \"Title\" desc=\"...\" type=Task priority=P2 labels=a,b"
            title = title_match.group(1)
            kv_part = rest.replace(f"\"{title}\"", "", 1)
            kv = parse_kv_pairs(kv_part)
            issue_key, url = jira_create_issue(
                title=title,
                description=kv.get("desc", ""),
                issue_type=kv.get("type", "Task"),
                priority=kv.get("priority"),
                assignee=kv.get("assignee"),
                labels=kv.get("labels", "")
            )
            return f"✅ Created **{issue_key}** — {title}\n{url}"

        if cmd == "/update":
            m = re.match(r'(\S+)\s+(.+)$', rest)
            if not m:
                return "Usage: /update KEY-123 field=value ..."
            key, kvraw = m.group(1), m.group(2)
            kv = parse_kv_pairs(kvraw)
            jira_update_issue(key, kv)
            return f"🛠️ Updated **{key}**."

        if cmd == "/comment":
            m = re.match(r'(\S+)\s+"(.+)"$', rest)
            if not m:
                return 'Usage: /comment KEY-123 "Your comment"'
            key, comment = m.group(1), m.group(2)
            jira_add_comment(key, comment)
            return f"💬 Comment added to **{key}**."

        if cmd == "/transition":
            m = re.match(r'(\S+)\s+"(.+)"$', rest)
            if not m:
                return 'Usage: /transition KEY-123 "In Progress"'
            key, state = m.group(1), m.group(2)
            jira_transition_issue(key, state)
            return f"🔁 {key} → {state}"

        if cmd == "/delete":
            key = rest.strip()
            jira_delete_issue(key)
            return f"🗑️ Deleted **{key}**."

        if cmd == "/summarize":
            m = re.match(r'(\S+)\s+"(.+)"$', rest)
            if not m:
                return 'Usage: /summarize KEY-123 "Paste meeting/chat notes"'
            key, raw = m.group(1), m.group(2)
            md = summarize_text_markdown(raw)
            jira_add_comment(key, f"### Meeting Summary\n\n{md}")
            return f"🧠 Summary appended to **{key}**."

        return "Unknown command."
    except Exception as e:
        return f"⚠️ Error: {str(e)}"
