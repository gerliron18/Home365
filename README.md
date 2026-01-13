# 🏠 Property Management Chatbot

**Version 1.0.0**

Intelligent Text-to-SQL Chatbot with LangGraph ReAct Agent, Role-Based Security, and Natural Conversation

---

## 📖 Overview

A production-grade chatbot system that converts natural language questions into SQL queries for property management data. Built with LangGraph and Google Gemini, featuring comprehensive security, answer validation to prevent hallucinations, and conversation memory for natural interactions.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **ReAct Agent** | Self-correcting LangGraph agent with retry logic |
| 🔐 **Password Authentication** | Simple role-based login (admin/llc1-5/viewer) |
| ✅ **Answer Validation** | Prevents LLM hallucinations with smart confidence scoring |
| 💬 **Conversation Memory** | Natural follow-up questions with context tracking (last 10 turns) |
| 🔒 **RBAC Security** | Role-based access (Admin, Owner, Viewer) with intent validation |
| 🛡️ **SQL Injection Prevention** | Multi-layer security with DML blocking + semicolon stripping |
| 📊 **Dynamic Schema** | Understands database structure via `schema.json` |
| 💻 **Dual Interfaces** | CLI + Streamlit Web UI |
| 🧪 **Comprehensive Testing** | Full test suite with security, validation, and memory tests |
| 😊 **User-Friendly Errors** | Graceful error handling with actionable messages |

---

## 🚀 Quick Start

### **1. Installation**

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment (API key & configuration)
python scripts/setup_env.py

# Generate mock database
python scripts/generate_mock_db.py
```

### **2. Run the Application**

**CLI Interface:**
```bash
python main.py
# Or on Windows: RUN_CLI.bat

# Authentication: Two-step process
# 1. Select role (admin/owner/viewer)
# 2. Enter password (masked input)
# 
# Commands during session:
# - Type questions naturally
# - 'help' - Show examples
# - 'change role' - Switch roles
# - 'quit' - Exit
```

**Web Interface:**
```bash
streamlit run app.py
# Or on Windows: RUN_WEB.bat

# Two-step login:
# 1. Select role (Admin/Owner/Viewer)
# 2. Enter password (hint shown based on selected role)
```

---

## 💡 Usage Examples

### **CLI Demo**

```
$ python main.py

Select role: 2 (owner)
Select owner: 2 (LLC2)

You: How many properties do I have?
Bot: You have 12 properties.
✓ Confidence: 100%

You: What about California?
Bot: You have 3 properties in California.

You: What's my average rent?
Bot: Your average rent is $1,016.30 per month.
✓ Confidence: 100%
```

### **Example Queries**

| Role | Query | Result |
|------|-------|--------|
| Owner | "How many properties do I have?" | "You have 12 properties" |
| Owner | "What is my most profitable property?" | "Your most profitable property is..." |
| Admin | "How many total properties?" | "There are 161 properties" |
| Viewer | "What's the average rent?" | "$970.49" |
| Viewer | "List all properties" | ❌ Access denied |

---

## 🏗️ Project Structure

```
Home365/
├── agent/                          # Core agent logic
│   ├── __init__.py                # Package exports
│   ├── state.py                   # State management (TypedDict)
│   ├── graph.py                   # LangGraph ReAct agent
│   ├── security.py                # RBAC + SQL validation
│   ├── database.py                # Database manager
│   ├── validation.py              # Answer validation
│   └── memory.py                  # Conversation memory
│
├── scripts/                        # Utility scripts
│   ├── setup_env.py               # Environment setup
│   ├── generate_mock_db.py        # Database generation
│   └── inspect_database.py        # Database inspection tool
│
├── tests/                          # Test suite
│   ├── conftest.py                # Pytest configuration
│   ├── test_agent.py              # Core agent tests
│   ├── test_validation.py         # Answer validation tests
│   ├── test_memory.py             # Conversation memory tests
│   └── test_security.py           # Security & RBAC tests
│
├── docs/                           # Documentation
│   ├── README.md                  # Documentation index
│   ├── ARCHITECTURE.md            # System architecture + diagram
│   ├── QUICK_START.md             # User quick start guide
│   ├── SECURITY_AND_FEATURES.md   # Security implementation
│   ├── ROLE_DIFFERENCES.md        # RBAC comparison
│   ├── ERROR_HANDLING.md          # Error handling strategy
│   ├── ADD_NEW_TABLE_GUIDE.md     # Guide for adding tables
│   ├── DATABASE_TOOLS.md          # Database utilities
│   └── DEVELOPER_QUICKSTART.md    # Developer reference
│
├── main.py                         # CLI entry point
├── app.py                          # Streamlit web UI
├── schema.json                     # Database schema metadata
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Test configuration
├── generate_architecture_diagram.py # Architecture diagram generator
├── property_management.db          # SQLite database
├── RUN_CLI.bat                     # Windows CLI launcher
├── RUN_WEB.bat                     # Windows web launcher
└── INSPECT_DB.bat                  # Windows DB inspection tool
```

---

## 🔐 Security Features

### **Multi-Layer Security Architecture**

```
┌─────────────────────────────────────┐
│  Layer 1: Authorization Check       │  ← Pre-validation (RBAC)
├─────────────────────────────────────┤
│  Layer 2: Prompt Engineering        │  ← LLM instruction
├─────────────────────────────────────┤
│  Layer 3: Regex Validation          │  ← DML detection
├─────────────────────────────────────┤
│  Layer 4: Query Modification        │  ← Owner filtering
├─────────────────────────────────────┤
│  Layer 5: Result Validation         │  ← Answer verification
└─────────────────────────────────────┘
```

### **Role-Based Access Control (RBAC)**

| Role | Access | Filter Applied |
|------|--------|----------------|
| **Admin** | All properties, detailed data | None |
| **Owner** | Own properties only | `WHERE owner_id = X` |
| **Viewer** | Aggregated data only | No sensitive details |

**See:** [docs/ROLE_DIFFERENCES.md](docs/ROLE_DIFFERENCES.md) for complete comparison

---

## ✅ Answer Validation

**Prevents LLM Hallucinations:**

```
SQL Result: [(12,)]
LLM Says: "You have 15 properties"  ❌

⚠️ VALIDATION WARNING: Number 15 doesn't match SQL result 12
🔴 Confidence: LOW (30%)
📊 Raw SQL Result: [(12,)]
```

**Features:**
- Automatic validation of all numeric answers
- Smart filtering of street addresses (prevents false positives)
- 2% tolerance for rounding
- Confidence scores (0-100%)
- Warnings shown only for very low confidence (<25%)
- Raw SQL results displayed when validation fails

---

## 💬 Conversation Memory

**Natural Follow-Up Questions:**

```
Q1: "How many properties in California?"
A1: "You have 5 properties in California."

Q2: "What about Arizona?"  ← Memory provides context!
A2: "You have 3 properties in Arizona."

Q3: "What's the average rent?"  ← Still remembers context
A3: "The average rent in Arizona is $950."
```

**Features:**
- Tracks last 10 interactions per session
- Extracts context (locations, owners, topics, property types)
- Prioritizes owner context for follow-up queries
- Clears automatically on role changes
- Smart context application (only for follow-ups, not standalone queries)
- Provides conversation statistics

---

## 🧪 Testing

### **Run Tests**

```bash
# Run all tests
pytest -v

# Run specific test suite
pytest tests/test_agent.py -v
pytest tests/test_validation.py -v
pytest tests/test_memory.py -v

# Run with coverage
pytest --cov=agent --cov-report=html
```

### **Test Coverage**

| Test Suite | Tests | Coverage |
|------------|-------|----------|
| Agent Tests | 17 | Core functionality |
| Validation Tests | 29 | Answer validation |
| Memory Tests | 29 | Conversation memory |
| **Total** | **75** | **100% critical paths** |

---

## 🛠️ Database Tools

**Inspect Database:**

```bash
# Quick summary
python scripts/inspect_database.py --summary-only

# Full detailed report
python scripts/inspect_database.py

# Export to JSON
python scripts/inspect_database.py --export

# Or on Windows
INSPECT_DB.bat
```

**See:** [docs/DATABASE_TOOLS.md](docs/DATABASE_TOOLS.md) for complete documentation

---

## 📊 Architecture Diagram

Generate visual architecture diagram:

```bash
python generate_architecture_diagram.py
```

This creates `docs/architecture_diagram.png` showing:
- All LangGraph nodes
- Node connections and transitions
- Self-correction loops
- Conditional routing

**See:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system architecture

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](README.md) | This file - Quick start and overview |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Complete system architecture |
| [docs/QUICK_START.md](docs/QUICK_START.md) | User quick start guide |
| [docs/SECURITY_AND_FEATURES.md](docs/SECURITY_AND_FEATURES.md) | Security implementation details |
| [docs/ROLE_DIFFERENCES.md](docs/ROLE_DIFFERENCES.md) | RBAC role comparison table |
| [docs/DATABASE_TOOLS.md](docs/DATABASE_TOOLS.md) | Database inspection utilities |
| [docs/ADD_NEW_TABLE_GUIDE.md](docs/ADD_NEW_TABLE_GUIDE.md) | How to add new database tables |
| [docs/ERROR_HANDLING.md](docs/ERROR_HANDLING.md) | Error messages and troubleshooting |
| [docs/DEVELOPER_QUICKSTART.md](docs/DEVELOPER_QUICKSTART.md) | Developer reference guide |

---

## ⚙️ Configuration

### **Environment Variables** (`.env`)

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp
MAX_RETRIES=3
DEBUG_MODE=false
```

### **Adjustable Parameters**

**Memory Size:**
```python
# In agent/graph.py
self.memory = ConversationMemory(max_history=10)
```

**Validation Tolerance:**
```python
# In agent/graph.py
is_valid, warning, confidence = self.answer_validator.validate_answer(
    sql_result_list, llm_answer, tolerance=0.02  # 2% tolerance
)
```

**Max Retries:**
```python
agent = PropertyManagementAgent(db_manager, max_retries=3)
```

---

## 🎯 Key Technologies

| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Programming language |
| **LangChain** | LLM orchestration framework |
| **LangGraph** | State machine for agent logic |
| **Google Gemini** | Large language model |
| **SQLite** | Database (portable for testing) |
| **Streamlit** | Web UI framework |
| **Pydantic** | Data validation |
| **Pytest** | Testing framework |

---

## 📈 Performance

| Metric | Typical Value |
|--------|---------------|
| Query Latency | 1-4 seconds |
| Memory Overhead | <10MB |
| Validation Time | <1ms |
| Memory Context | <1ms |
| Database Queries | 10-50ms |

**Bottleneck:** LLM API calls (2 per query: SQL generation + answer generation)

---

## 🐛 Troubleshooting

### **Common Issues**

**1. "GOOGLE_API_KEY not found"**
```bash
# Solution: Run setup script
python scripts/setup_env.py
```

**2. "Database not found"**
```bash
# Solution: Generate database
python scripts/generate_mock_db.py
```

**3. "API quota exceeded"**
```
Solution: 
- Wait 60 seconds (free tier: 5 requests/minute)
- Or use a different API key
- Or upgrade to paid tier
```

**4. "Module not found"**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**5. Getting errors?**

The system provides user-friendly error messages. For troubleshooting, see [docs/ERROR_HANDLING.md](docs/ERROR_HANDLING.md). Enable `DEBUG_MODE=true` in `.env` for technical details.

---

## 🎓 Learning Resources

### **Understanding the System**

1. Start with [docs/QUICK_START.md](docs/QUICK_START.md)
2. Read [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details
3. Review [docs/SECURITY_AND_FEATURES.md](docs/SECURITY_AND_FEATURES.md) for security
4. Check [docs/DEVELOPER_QUICKSTART.md](docs/DEVELOPER_QUICKSTART.md) for development

### **Code Walkthrough**

1. **Entry Point:** `main.py` or `app.py`
2. **Agent Logic:** `agent/graph.py` (LangGraph nodes)
3. **Security:** `agent/security.py` (RBAC + validation)
4. **Validation:** `agent/validation.py` (answer verification)
5. **Memory:** `agent/memory.py` (conversation context)

---

## 🤝 Contributing

### **Running Tests Before Commit**

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=agent --cov-report=html

# View coverage report
open htmlcov/index.html
```

### **Code Quality**

- Type hints throughout
- Docstrings for all classes/functions
- Pydantic for validation
- Modular, testable code

---

## 📝 License

This project is proprietary. All rights reserved.

---

## 👥 Authors

**Property Management Chatbot System**  
Built with LangGraph, Google Gemini, and enterprise-grade security.

---

## 📞 Support

For issues or questions:
1. Check [docs/](docs/) for documentation
2. Review troubleshooting section above
3. Run database inspection: `python scripts/inspect_database.py`
4. Check test results: `pytest -v`

---

## 🎯 Deployment Checklist

Before deploying:

- [ ] API key configured (`.env` file)
- [ ] Database generated (`python scripts/generate_mock_db.py`)
- [ ] All tests passing (`pytest -v`)
- [ ] Review [docs/SECURITY_AND_FEATURES.md](docs/SECURITY_AND_FEATURES.md)
- [ ] Configure environment variables as needed

---

**Version:** 1.0.0  
**Built with:** LangGraph, Google Gemini, Streamlit  
**Last Updated:** January 13, 2026  
