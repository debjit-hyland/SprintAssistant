import os, base64, requests

JIRA_BASE = os.getenv("JIRA_BASE")
JIRA_PROJECT = os.getenv("JIRA_PROJECT")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

BASIC = base64.b64encode(f"{JIRA_EMAIL}:{JIRA_API_TOKEN}".encode()).decode()
HEAD = {"Authorization": f"Basic {BASIC}", "Accept": "application/json", "Content-Type": "application/json"}

def browse_url(key: str) -> str:
    return f"{JIRA_BASE}/browse/{key}"

def account_id_from_hint(hint: str) -> str | None:
    # For hackathon: if 'me', skip and let Jira auto-assign or leave unassigned.
    # Production: call GET /rest/api/3/user/search?query=<hint> to resolve.
    if hint.lower() == "me":
        return None
    return None

def jira_create_issue(title: str, description: str, issue_type: str = "Task",
                      priority: str | None = None, assignee: str | None = None,
                      labels: str = "") -> tuple[str, str]:
    body = {
        "fields": {
            "project": {"key": JIRA_PROJECT},
            "summary": title,
            "issuetype": {"name": issue_type},
            "description": description,
        }
    }
    if priority:
        body["fields"]["priority"] = {"name": priority.upper()}
    if labels:
        body["fields"]["labels"] = [l.strip() for l in labels.split(",") if l.strip()]
    acct = account_id_from_hint(assignee) if assignee else None
    if acct:
        body["fields"]["assignee"] = {"accountId": acct}

    r = requests.post(f"{JIRA_BASE}/rest/api/3/issue", json=body, headers=HEAD, timeout=20)
    r.raise_for_status()
    key = r.json()["key"]
    return key, browse_url(key)

def jira_update_issue(key: str, kv: dict):
    # Map a few common fields
    fields = {}
    if "summary" in kv:
        fields["summary"] = kv["summary"]
    if "priority" in kv:
        fields["priority"] = {"name": kv["priority"].upper()}
    if "labels" in kv:
        fields["labels"] = [l.strip() for l in kv["labels"].split(",") if l.strip()]
    if "description" in kv:
        fields["description"] = kv["description"]
    if "assignee" in kv:
        acct = account_id_from_hint(kv["assignee"])
        if acct:
            fields["assignee"] = {"accountId": acct}
    if not fields:
        return
    r = requests.put(f"{JIRA_BASE}/rest/api/3/issue/{key}", json={"fields": fields}, headers=HEAD, timeout=20)
    r.raise_for_status()

def jira_add_comment(key: str, text: str):
    r = requests.post(f"{JIRA_BASE}/rest/api/3/issue/{key}/comment", json={"body": text}, headers=HEAD, timeout=20)
    r.raise_for_status()

def jira_transition_issue(key: str, to_name: str):
    # Find available transitions, pick by name
    t = requests.get(f"{JIRA_BASE}/rest/api/3/issue/{key}/transitions", headers=HEAD, timeout=20).json()
    target = next((x for x in t.get("transitions", []) if x["to"]["name"].lower() == to_name.lower()), None)
    if not target:
        raise ValueError(f"No transition named '{to_name}' for {key}")
    r = requests.post(f"{JIRA_BASE}/rest/api/3/issue/{key}/transitions",
                      json={"transition": {"id": target["id"]}}, headers=HEAD, timeout=20)
    r.raise_for_status()

def jira_delete_issue(key: str):
    r = requests.delete(f"{JIRA_BASE}/rest/api/3/issue/{key}", headers=HEAD, timeout=20)
    r.raise_for_status()
