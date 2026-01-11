# backend/config.py

# Mapping of council roles to physical machines (via Tailscale)
COUNCIL_MEMBERS = {
    "Council_1": {
        "url": "http://100.64.243.5:11434",      #JD
        "model": "gemma2:2b"
    },  # <--- Added comma here
    "Council_2": {
        "url": "http://100.123.209.93:11434",
        "model": "llama3.2:1b"                   #Kuttu
    },
    "Council_3": {
        "url": "http://100.107.144.10:11435",    #Kali
        "model": "mistral:7b"
    }
}

CHAIRMAN = {
    "url": "http://100.114.119.33:11434",      # Abhi
    "model": "llama3.2:3b"
}

# Timeout kept high to tolerate cold starts
REQUEST_TIMEOUT = None

# Maximum history entries injected into prompts
MAX_HISTORY_MESSAGES = 6
