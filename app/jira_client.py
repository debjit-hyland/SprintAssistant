import os, base64, requests
from dotenv import load_dotenv
load_dotenv()
JIRA_BASE=os.getenv("JIRA_BASE"); JIRA_PROJECT=os.getenv("JIRA_PROJECT")
EMAIL=os.getenv("JIRA_EMAIL"); TOKEN=os.getenv("JIRA_API_TOKEN")
BASIC=base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEAD={"Authorization":f"Basic {BASIC}","Content-Type":"application/json"}

def account_id_from_hint(hint: str) -> str | None:
   """
   - If hint == "me", return None (let Jira auto-assign or skip).
   - Otherwise, you could call GET /rest/api/3/user/search?query=<hint>
     to resolve a Jira accountId. Here we skip for simplicity.
   """
   if hint.lower() == "me":
       return None
   return None

def create_payload(summary: str, description: str) -> dict:
   description_adf = {
      "type": "doc",
      "version": 1,
      "content": [
         {
            "type": "paragraph",
            "content": [
               {
                  "type": "text",
                  "text": description
               }
            ]
         }
      ]
   }
 
   payload = {
      "fields": {
         "project": {"key": JIRA_PROJECT},
         "summary": summary,
         "issuetype": {"name": "Task"},
         "description": description_adf
      }
   }
   return payload

def jira_create_issue(summary:str, description:str):

   payload = create_payload(summary, description)
   r = requests.post(
      f"{JIRA_BASE}/rest/api/3/issue",
      json=payload,
      headers=HEAD
   )
   r.raise_for_status(); data=r.json()
   return data["key"], f"{JIRA_BASE}/browse/{data['key']}"

def jira_add_comment(key:str, text:str):
   r=requests.post(f"{JIRA_BASE}/rest/api/3/issue/{key}/comment",
                   json={"body":text},headers=HEAD)
   r.raise_for_status()

def jira_update_issue(key: str, kv: dict):
   """
   Update fields on an issue.
   """
   fields = {}
   if "summary" in kv:
       fields["summary"] = kv["summary"]
   if "priority" in kv:
       fields["priority"] = {"name": kv["priority"].upper()}
   if "labels" in kv:
       labels = [l.strip() for l in kv["labels"].split(",") if l.strip()]
       fields["labels"] = labels
   if "description" in kv:
       fields["description"] = kv["description"]
   if "assignee" in kv:
       acct = account_id_from_hint(kv["assignee"])
       if acct:
           fields["assignee"] = {"accountId": acct}
   if not fields:
       return  # nothing to update
   r = requests.put(
       f"{JIRA_BASE}/rest/api/3/issue/{key}",
       json={"fields": fields},
       headers=HEAD,
       timeout=20,
   )
   r.raise_for_status()
   return True