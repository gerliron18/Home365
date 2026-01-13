# 🚀 Developer Quick Start Guide

Quick reference for developers working with the Property Management Chatbot system.

---

## 📦 **Essential Files**

| File | Purpose | Command |
|------|---------|---------|
| `scripts/inspect_database.py` | Database exploration tool | `py scripts/inspect_database.py` |
| `scripts/generate_mock_db.py` | Generate test database | `py scripts/generate_mock_db.py` |
| `scripts/setup_env.py` | Setup environment | `py scripts/setup_env.py` |
| `main.py` | CLI interface (with role switching) | `py main.py` |
| `app.py` | Web UI (Streamlit) | `streamlit run app.py` |
| `tests/test_agent.py` | Test suite | `pytest tests/test_agent.py -v` |

---

## 🔧 **Common Developer Tasks**

### 1. Inspect the Database

```bash
# Quick summary
py scripts/inspect_database.py --summary-only

# Full detailed report
py scripts/inspect_database.py

# Export to JSON
py scripts/inspect_database.py --export
```

**What you get:**
- Table schemas with all columns
- Foreign key relationships
- Row counts and statistics
- Sample data (3 rows per table)
- JSON export for documentation

---

### 2. Regenerate Database

```bash
# Clean regeneration
py scripts/generate_mock_db.py
```

**Generated data:**
- 6 Owners (LLC1-LLC6)
- 161 Properties
- 166 Units
- 166 Leases

**Key test values:**
- LLC1: 22 properties
- LLC2: 12 properties
- Total active: 115 properties
- Average rent: $970.49

---

### 3. Test the System

```bash
# Run all tests
pytest tests/test_agent.py -v

# Run specific test
pytest tests/test_agent.py::TestPropertyQuestions::test_llc1_property_count -v

# With coverage
pytest tests/test_agent.py --cov=agent --cov-report=html
```

---

### 4. Launch Interfaces

```bash
# CLI (Command Line)
py main.py

# Web UI (Streamlit)
streamlit run app.py
# Open: http://localhost:8501
```

---

## 📊 **Database Structure**

```
Owners (6 rows)
  |-> Properties (161 rows)
       |-> Units (166 rows)
            |-> Leases (166 rows)
```

### Tables Overview

**Owners**
- `owner_id` (PK)
- `owner_name` (LLC1-LLC6)
- `contact_email`, `contact_phone`

**Properties**
- `property_id` (PK)
- `owner_id` (FK → Owners)
- `address`, `city`, `state`, `zip_code`
- `property_type`, `purchase_date`, `purchase_price`
- `is_active` (1=active, 0=inactive)

**Units**
- `unit_id` (PK)
- `property_id` (FK → Properties)
- `unit_number`, `bedrooms`, `bathrooms`
- `square_feet`, `monthly_rent`

**Leases**
- `lease_id` (PK)
- `unit_id` (FK → Units)
- `tenant_name`, `start_date`, `end_date`
- `monthly_rent`, `security_deposit`
- `is_active`

---

## 🔐 **Security Layers**

### 1. Role-Based Access Control (RBAC)

| Role | Access | Filter |
|------|--------|--------|
| **Admin** | All properties, detailed data | None |
| **Owner** | Own properties only | `WHERE owner_id = X` |
| **Viewer** | Aggregated data only | No sensitive details |

### 2. SQL Injection Prevention

✅ **Blocked Operations:**
- `INSERT`, `UPDATE`, `DELETE`
- `DROP`, `ALTER`, `CREATE`
- `EXEC`, `EXECUTE`

✅ **Security Methods:**
- Prompt engineering
- Regex validation
- Parameterized queries

### 3. Authorization Checks

✅ **Pre-validation:**
- Owners can't query other owners
- Viewers can't see detailed data
- All roles: read-only access

---

## 🧪 **Testing Scenarios**

### Property Count Tests
```python
# LLC1 property count
assert response.contains("22 properties")

# LLC2 property count
assert response.contains("12 properties")

# Total properties
assert response.contains("161 properties")
```

### RBAC Tests
```python
# Owner accessing other owner's data
assert "Access denied" in response

# Viewer requesting detailed data
assert "Access denied" in response
```

### Security Tests
```python
# SQL injection attempt
query = "'; DROP TABLE Properties; --"
assert "not allowed" in response

# DML attempt
query = "DELETE FROM Properties WHERE owner_id = 1"
assert "not allowed" in response
```

---

## 🎯 **Debugging Workflow**

### Issue: Wrong Query Results

1. **Check Database**
   ```bash
   py scripts/inspect_database.py --summary-only
   ```

2. **Verify RBAC**
   ```bash
   # Check if filters are applied correctly
   py main.py
   # Test as owner role
   ```

3. **Inspect SQL**
   - Web UI shows generated SQL
   - CLI shows SQL in verbose mode

---

### Issue: Test Failures

1. **Regenerate Database**
   ```bash
   py scripts/generate_mock_db.py
   ```

2. **Verify Data**
   ```bash
   py scripts/inspect_database.py
   # Check statistics match requirements
   ```

3. **Run Single Test**
   ```bash
   pytest tests/test_agent.py::TestPropertyQuestions::test_llc1_property_count -v -s
   ```

---

### Issue: API Quota Exceeded

1. **Check Rate Limits**
   - Free tier: 5 requests/minute
   - Wait 60 seconds between batches

2. **Use Different API Key**
   ```bash
   # Edit .env file
   GEMINI_API_KEY=your_new_key_here
   ```

3. **Test with Fewer Queries**
   ```bash
   pytest tests/test_agent.py -k "test_llc1" -v
   ```

---

## 📝 **Code Structure**

```
agent/
  ├── __init__.py           # Package exports
  ├── state.py              # TypedDict state management
  ├── security.py           # RBAC + SQL validation
  ├── database.py           # SQLite connection manager
  └── graph.py              # LangGraph ReAct agent

scripts/
  ├── setup_env.py          # Environment setup
  ├── generate_mock_db.py   # Database generation
  └── inspect_database.py   # Database inspection tool

tests/
  ├── conftest.py           # Pytest configuration
  └── test_agent.py         # Comprehensive test suite

main.py                     # CLI interface
app.py                      # Streamlit web UI
schema.json                 # Database metadata
requirements.txt            # Dependencies
```

---

## 🔍 **Key Functions**

### Database Inspection
```python
from scripts.inspect_database import DatabaseInspector

with DatabaseInspector("property_management.db") as inspector:
    inspector.print_database_summary()
    inspector.export_schema_json("schema_export.json")
```

### Agent Querying
```python
from agent import PropertyManagementAgent, UserContext, DatabaseManager

db_manager = DatabaseManager("property_management.db")
agent = PropertyManagementAgent(db_manager, max_retries=3)

user_context = UserContext(user_id=2, role="owner", owner_id=2)
response = agent.query("How many properties do I have?", user_context)

print(response['answer'])
print(response['sql_query'])
```

---

## 📚 **Documentation Files**

| File | Description |
|------|-------------|
| `README.md` | Main project documentation |
| `architecture.md` | LangGraph architecture details |
| `DATABASE_TOOLS.md` | Database inspection tool docs |
| `ROLE_DIFFERENCES.md` | RBAC role comparison |
| `SECURITY_AND_FEATURES.md` | Security implementation |
| `QUICK_START.md` | User quick start guide |
| `DEVELOPER_QUICKSTART.md` | This file |

---

## 💡 **Pro Tips**

### Performance
- Database queries are cached
- LangGraph uses efficient state management
- SQLite is in-memory for tests

### Testing
- Use `conftest.py` rate limiting
- Run tests in batches to avoid quota
- Mock LLM calls for unit tests

### Debugging
- Web UI shows SQL queries
- CLI has verbose mode
- Check `schema.json` for metadata

### Code Quality
- Type hints throughout
- Pydantic for validation
- Clean, modular architecture

---

## 🆘 **Quick Troubleshooting**

| Issue | Solution |
|-------|----------|
| Database not found | `py scripts/generate_mock_db.py` |
| API quota exceeded | Wait 60s or use new API key |
| Tests failing | Regenerate database |
| Wrong results | Check RBAC filters |
| Import errors | `pip install -r requirements.txt` |

---

## 🚀 **Quick Start (30 seconds)**

```bash
# 1. Setup (one-time)
pip install -r requirements.txt
py scripts/setup_env.py
py scripts/generate_mock_db.py

# 2. Verify
py scripts/inspect_database.py --summary-only

# 3. Test
pytest tests/test_agent.py -v

# 4. Run
py main.py
```

---

**Happy Coding! 🎉**

For detailed documentation, see:
- [README.md](README.md) - Full project documentation
- [DATABASE_TOOLS.md](DATABASE_TOOLS.md) - Database tools documentation
- [architecture.md](architecture.md) - System architecture
