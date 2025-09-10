import os, hmac, hashlib, time
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from app.jira_client import jira_create_issue, jira_add_comment
from app.llm_client import summarize_text_markdown
load_dotenv()
app = FastAPI()
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
def verify_slack(req: Request, body: str):
   ts = req.headers["x-slack-request-timestamp"]
   if abs(time.time() - int(ts)) > 60*5:
       return False
   sig_basestring = f"v0:{ts}:{body}".encode()
   my_sig = "v0=" + hmac.new(
       SLACK_SIGNING_SECRET.encode(), # pyright: ignore[reportOptionalMemberAccess]
       sig_basestring, hashlib.sha256
   ).hexdigest()
   return hmac.compare_digest(my_sig, req.headers["x-slack-signature"])

@app.post("/slack/command")
async def slack_command(req: Request):
   body = await req.body()
   if not verify_slack(req, body.decode()):
       return PlainTextResponse("Invalid signature", status_code=403)
   form = dict(x.split("=",1) for x in body.decode().split("&"))
   text = form.get("text","")
   cmd = form.get("command","")
   print(f"Received command: {str(cmd)} with text: {text}")
   if "create" in cmd:
       issue, url = jira_create_issue(text, "Auto-created from Slack")
       return PlainTextResponse(f"✅ Created {issue}: {url}")
   if cmd == "/comment":
       parts = text.split(" ",1)
       if len(parts)<2: return PlainTextResponse("Usage: /comment KEY-123 Your comment")
       key, comment = parts
       jira_add_comment(key, comment)
       return PlainTextResponse(f"💬 Comment added to {key}")
   if cmd == "/summarize":
       parts = text.split(" ",1)
       if len(parts)<2: return PlainTextResponse("Usage: /summarize KEY-123 Paste notes")
       key, notes = parts
       md = summarize_text_markdown(notes)
       jira_add_comment(key, f"*Meeting Summary*\n{md}")
       return PlainTextResponse(f"🧠 Summary added to {key}")
   return PlainTextResponse("Unknown command")