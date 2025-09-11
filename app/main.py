import os, hmac, hashlib, time, urllib.parse
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from app.jira_client import jira_create_issue, jira_update_issue, jira_add_comment
from app.llm_client import summarize_text_markdown
load_dotenv()
app = FastAPI()
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "")
def verify_slack(req: Request, raw_body: bytes) -> bool:
   try:
       ts = req.headers["x-slack-request-timestamp"]
       if abs(time.time() - int(ts)) > 60 * 5:
           return False
       base = f"v0:{ts}:{raw_body.decode()}".encode()
       digest = "v0=" + hmac.new(SLACK_SIGNING_SECRET.encode(), base, hashlib.sha256).hexdigest()
       return hmac.compare_digest(digest, req.headers["x-slack-signature"])
   except Exception:
       return False
@app.post("/slack/command")
async def slack_command(req: Request):
   raw = await req.body()
#    if SLACK_SIGNING_SECRET and not verify_slack(req, raw):
#        return PlainTextResponse("Invalid signature", status_code=403)
   # Parse application/x-www-form-urlencoded safely
   form = urllib.parse.parse_qs(raw.decode())
   # Helpers to get single values
   print("Form data received:")
   for k, v in form.items():
       print(f"{k}: {v}")
   command = form.get("command")[0] # pyright: ignore[reportOptionalSubscript] # debug
   action_data  = form.get("text", [""])[0].split(" ")
   action = action_data[0] if action_data else ""
   data = " ".join(action_data[1:]) if len(action_data) > 1 else ""
   # Unified command: /sprint <action> ...
   if command.startswith("/sprint"):
       if not action:
           return PlainTextResponse("Usage: /sprint create|update|comment|summarize …")
       if action == "create":
           # Expect: create "Title" [desc="..."] [priority=P2] [labels=a,b]
           import re
           title_match = re.search(r'"([^"]+)"', data)
           title = title_match.group(1) if title_match else data.strip() or "Untitled"
           # crude kv parse: key=value with optional quotes
           kv = dict(re.findall(r'(\w+)=(".*?"|\'.*?\'|\S+)', data))
           desc = kv.get("desc", "").strip('"\'')
           prio = kv.get("priority")
           labels = kv.get("labels", "")
           key, url = jira_create_issue(title, desc or "Created from Slack")
           # Optional: handle priority/labels via jira_update_issue if needed
           return PlainTextResponse(f"✅ Created {key}: {url}")
       elif action == "comment":
           # Expect: comment KEY-123 "Your text"
           if not data:
               return PlainTextResponse('Usage: /sprint comment KEY-123 "text"')
           issue, _, comment = data.partition(" ")
           if not comment:
               return PlainTextResponse('Usage: /sprint comment KEY-123 "text"')
           jira_add_comment(issue, comment.strip().strip('"'))
           return PlainTextResponse(f"💬 Comment added to {issue}")
       elif action == "update":
           # Minimal example: update KEY-123 summary="New title"
           if not data:
               return PlainTextResponse('Usage: /sprint update KEY-123 field=value …')
           issue, _, kvraw = data.partition(" ")
           import re
           kv_pairs = re.findall(r'(\w+)=(".*?"|\'.*?\'|\S+)', kvraw)
           kv = {k: v.strip('"\'') for k, v in kv_pairs}
           jira_update_issue(issue, kv)
           return PlainTextResponse(f"🛠️ Updated {issue}")
       elif action == "summarize":
           # Expect: summarize KEY-123 "meeting notes…"
           if not data:
               return PlainTextResponse('Usage: /sprint summarize KEY-123 "notes"')
           issue, _, notes = data.partition(" ")
           if not notes:
               return PlainTextResponse('Usage: /sprint summarize KEY-123 "notes"')
           md = summarize_text_markdown(notes.strip().strip('"'))
           jira_add_comment(issue, f"*Meeting Summary*\n{md}")
           return PlainTextResponse(f"🧠 Summary added to {issue}")
       else:
           return PlainTextResponse("Unknown action. Use: create | update | comment | summarize")
   # Backwards compatibility: if you also configured separate commands
   if command == "/create":
       key, url = jira_create_issue(data or "Untitled", "Created from Slack")
       return PlainTextResponse(f"✅ Created {key}: {url}")
   if command == "/comment":
       issue, _, comment = data.partition(" ")
       jira_add_comment(issue, comment)
       return PlainTextResponse(f"💬 Comment added to {issue}")
   return PlainTextResponse("Unknown command")