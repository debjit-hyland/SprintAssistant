import os, base64, requests
JIRA_BASE=os.getenv("JIRA_BASE"); JIRA_PROJECT=os.getenv("JIRA_PROJECT")
EMAIL=os.getenv("JIRA_EMAIL"); TOKEN=os.getenv("JIRA_API_TOKEN")
BASIC=base64.b64encode(f"{EMAIL}:{TOKEN}".encode()).decode()
HEAD={"Authorization":f"Basic {BASIC}","Content-Type":"application/json"}
def jira_create_issue(summary:str, description:str):
   r=requests.post(f"{JIRA_BASE}/rest/api/3/issue",json={
       "fields":{"project":{"key":JIRA_PROJECT},
                 "summary":summary,
                 "issuetype":{"name":"Task"},
                 "description":description}
   },headers=HEAD)
   r.raise_for_status(); data=r.json()
   return data["key"], f"{JIRA_BASE}/browse/{data['key']}"
def jira_add_comment(key:str, text:str):
   r=requests.post(f"{JIRA_BASE}/rest/api/3/issue/{key}/comment",
                   json={"body":text},headers=HEAD)
   r.raise_for_status()