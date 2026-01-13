# 🚀 Quick Start Guide

## Instant Launch (Windows)

### CLI Interface
**Double-click:** `RUN_CLI.bat`

### Web Interface  
**Double-click:** `RUN_WEB.bat`

---

## Manual Launch

### CLI
```bash
python main.py
```

### Web
```bash
streamlit run app.py
```

---

## Example Questions

**Property Counts:**
- "How many properties do I have?"
- "How many active properties do I have?"

**Profitability:**
- "What is the most profitable property?"
- "Show me properties with high rent"

**Financial:**
- "What is the average rent I received?"
- "List properties in Arizona"

**Filters:**
- "Show me 3-bedroom units"
- "Properties purchased after 2020"

---

## 🔐 Authentication

The system uses a two-step authentication process:

**Step 1: Role Selection**
- Choose your role (Admin, Owner, or Viewer)
- If Owner, select which LLC (1-5)

**Step 2: Password Entry**
- Enter the password for your selected role
- Passwords are masked for security (not visible on screen)
- Password hints are displayed based on your role selection

| Role | Password |
|------|----------|
| Admin | `admin` |
| LLC1 | `llc1` |
| LLC2 | `llc2` |
| LLC3 | `llc3` |
| LLC4 | `llc4` |
| LLC5 | `llc5` |
| Viewer | `viewer` |

**Note:** Passwords are case-insensitive.

---

## 💬 CLI Commands

While using the CLI interface:

- **Type your question** - Ask naturally about properties
- **`help`** - Show example questions
- **`change role`** - Switch to a different role (re-authentication required)
- **`quit`** or **`exit`** - End the session

---

## Tips

**CLI:**
- Passwords are hidden when typing
- Type `help` for examples
- Type `change role` to switch users
- Colorized output for easy reading

**Web:**
- Use sidebar to change role
- Click "View SQL Query" to see generated queries
- Chat history preserved in session

---

## Troubleshooting

**If you see "Database not found":**
```bash
python scripts/generate_mock_db.py
```

**If you see "API key error":**
```bash
python scripts/setup_env.py
```

**If packages are missing:**
```bash
pip install -r requirements.txt
```

---

## System Requirements

- Python 3.10+
- Internet connection (for Gemini API)
- ~50MB disk space

**Enjoy your AI-powered property management chatbot!** 🎉
