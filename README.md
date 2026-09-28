# Weather Look Up and Calculator API

A small chat agent built on Claude with two tools:

- **get_weather**: looks up the current temperature for a city (free Open-Meteo API, no key needed)
- **calculator**: safely evaluates math like `17 * 0.4` (no `eval()`)

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key-here
python agent.py
```

Type `exit` to quit.
