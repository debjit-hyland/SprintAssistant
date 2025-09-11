import os, base64, requests
from typing import Optional
from app.openrouter import ai_response
from dotenv import load_dotenv
load_dotenv()
JIRA_BASE=os.getenv("JIRA_BASE"); JIRA_PROJECT=os.getenv("JIRA_PROJECT")
EMAIL=os.getenv("JIRA_EMAIL"); TOKEN=os.getenv("JIRA_API_TOKEN")
BASIC=base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEAD={"Authorization":f"Basic {BASIC}","Content-Type":"application/json"}

def create_payload(summary:Optional[str], description:str) -> tuple[dict, dict]:
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
         "summary": summary or "Unknown Task Title",
         "issuetype": {"name": "Task"},
         "description": description_adf
      }
   }
   return description_adf, payload

def jira_create_issue(summary:str, description:str):

   _, payload = create_payload(summary, description)
   r = requests.post(
      f"{JIRA_BASE}/rest/api/3/issue",
      json=payload,
      headers=HEAD
   )
   r.raise_for_status(); data=r.json()
   return data["key"], f"{JIRA_BASE}/browse/{data['key']}"

def jira_add_comment(key:str, text:str):
   comment_adf = {
       "type": "doc",
       "version": 1,
       "content": [
           {
               "type": "paragraph",
               "content": [
                   {
                       "type": "text",
                       "text": text
                   }
               ]
           }
       ]
   }
   r=requests.post(f"{JIRA_BASE}/rest/api/3/issue/{key}/comment",
                   json={"body":comment_adf},headers=HEAD)
   r.raise_for_status()

def jira_update_issue(key: str, kv: dict):
   """
   Update fields on an issue.
   """
   fields = {}
   if "summary" in kv:
       fields["summary"] = kv["summary"]
   if "description" in kv:
       fields["description"],_ = create_payload(None, kv["description"])
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

def jira_summarise(key: str, text:str):
   """
   Add a summary comment to an issue.
   """
   resp = ai_response(command="Summarize for JIRA", data=text)
   if resp is None:
       return False
   jira_add_comment(key, resp["choices"][0]["message"]["content"])
   return True