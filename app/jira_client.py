import os, base64, requests
import aiohttp
from typing import Optional
from app.openrouter import ai_response, ai_response_async
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

async def jira_add_comment_async(key: str, text: str):
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
   
   async with aiohttp.ClientSession() as session:
       async with session.post(
           f"{JIRA_BASE}/rest/api/3/issue/{key}/comment",
           json={"body": comment_adf},
           headers=HEAD
       ) as response:
           response.raise_for_status()

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
       timeout=200,
   )
   r.raise_for_status()
   return True

def jira_summarise(key: str, text:str):
   """
   Add a summary comment to an issue.
   """
   prompt = f"You are a technical writer for Jira. Turn developer notes into a clear Jira description with:\n"
   "- Context (1 short paragraph)\n"
   "- Scope (bullets)\n"
   "- Acceptance Criteria (Given/When/Then bullets)\n"
   "Return in bullet points only.\n"
   resp = ai_response(command=prompt, data=text)
   if resp is None:
       return False
   jira_add_comment(key, resp["choices"][0]["message"]["content"])
   return True

async def jira_summarise_async(key: str, text: str):
   """
   Add a summary comment to an issue asynchronously.
   """
   prompt = f"You are a technical writer for Jira. Turn developer notes into a clear Jira description with:\n"
   "- Context (1 short paragraph)\n"
   "- Scope (bullets)\n"
   "- Acceptance Criteria (Given/When/Then bullets)\n"
   "Return in bullet points only.\n"
   
   resp = await ai_response_async(command=prompt, data=text)
   if resp is None:
       return False
   
   await jira_add_comment_async(key, resp["choices"][0]["message"]["content"])
   return True