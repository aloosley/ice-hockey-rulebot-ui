# Ice Hockey Rulebot UI

The UI is based on [Streamlit](https://streamlit.io/).  

# Install

Clone the repository and ensure [Python](https://www.python.org/downloads/)>=3.12 is installed.

```bash
pip install -r requirements.txt
```

# Run

```bash
streamlit run app.py
```

# Config
The UI calls the [Ice Hockey Rulebot API](https://github.com/aloosley/ice-hockey-rulebot-api) to provide responses.
For the moment, config is hardcoded in `app.py` (e.g. `API_URL` and `API_ENDPOINT`).
