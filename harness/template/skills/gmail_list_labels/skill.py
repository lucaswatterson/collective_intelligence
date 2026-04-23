from harness.integrations.gmail import get_service


def run(**input):
    service = get_service()
    resp = service.users().labels().list(userId="me").execute()
    labels = resp.get("labels", [])
    if not labels:
        return "No labels found."
    lines = [
        f"{lbl['id']:<40} {lbl.get('type', ''):<8} {lbl.get('name', '')}"
        for lbl in sorted(labels, key=lambda l: (l.get("type", ""), l.get("name", "")))
    ]
    return "\n".join(lines)
