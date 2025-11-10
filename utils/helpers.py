# small helpers if needed
def short(s, n=80):
    if not s:
        return ""
    return s if len(s) <= n else s[:n-1] + "…"
