print("START", flush=True)
print("IMPORTING event_analysis", flush=True)

import event_analysis

print("IMPORTED event_analysis", flush=True)

try:
    from event_analysis import get_grok_client, GROK_API_KEY
    print("Grok API Key configured:", bool(GROK_API_KEY), flush=True)
    print("Grok client ready:", get_grok_client(), flush=True)
except Exception as e:
    print("error:", e, flush=True)