# 📘 Guide: Adding New Tables to the System

**Property Management Chatbot - Table Extension Procedure**

---

## 🎯 Overview

The system is designed to be **extensible** and **metadata-driven**. Adding new tables requires:
1. ✅ Database schema update (SQL)
2. ✅ Metadata registration (schema.json)
3. ✅ No code changes! (system auto-discovers)

**Time Required:** 10-30 minutes (depending on table complexity)

---

## 📋 Step-by-Step Procedure

### **Step 1: Design Your New Table**

**Example:** Adding a `MaintenanceRequests` table

```sql
CREATE TABLE MaintenanceRequests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id INTEGER NOT NULL,
    request_date TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT,
    cost REAL,
    completed_date TEXT,
    FOREIGN KEY (unit_id) REFERENCES Units(unit_id)
);
```

**Design Checklist:**
- [ ] Primary key defined
- [ ] Foreign keys for relationships
- [ ] Column types specified
- [ ] Constraints defined (NOT NULL, etc.)
- [ ] Indexes planned (if needed)

---

### **Step 2: Update Database Schema**

#### **Option A: Modify `generate_mock_db.py`**

Add table creation to the database generation script:

```python
# In scripts/generate_mock_db.py

def create_tables(cursor):
    """Create all tables"""
    
    # ... existing tables ...
    
    # NEW TABLE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS MaintenanceRequests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            request_date TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('open', 'in_progress', 'completed')),
            priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
            cost REAL,
            completed_date TEXT,
            FOREIGN KEY (unit_id) REFERENCES Units(unit_id)
        )
    """)
    
    print("Created MaintenanceRequests table")

def populate_maintenance_requests(cursor):
    """Populate maintenance requests with sample data"""
    
    # Get all unit IDs
    cursor.execute("SELECT unit_id FROM Units")
    unit_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate sample maintenance requests
    statuses = ['open', 'in_progress', 'completed']
    priorities = ['low', 'medium', 'high', 'urgent']
    
    for i in range(50):  # 50 sample requests
        unit_id = random.choice(unit_ids)
        status = random.choice(statuses)
        
        request = {
            'unit_id': unit_id,
            'request_date': fake.date_between(start_date='-1y', end_date='today').isoformat(),
            'description': fake.sentence(nb_words=10),
            'status': status,
            'priority': random.choice(priorities),
            'cost': round(random.uniform(50, 2000), 2) if status == 'completed' else None,
            'completed_date': fake.date_between(start_date='-6m', end_date='today').isoformat() if status == 'completed' else None
        }
        
        cursor.execute("""
            INSERT INTO MaintenanceRequests 
            (unit_id, request_date, description, status, priority, cost, completed_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request['unit_id'],
            request['request_date'],
            request['description'],
            request['status'],
            request['priority'],
            request['cost'],
            request['completed_date']
        ))
    
    print(f"Inserted {cursor.rowcount} maintenance requests")

# Update main() function
def main():
    # ... existing code ...
    create_tables(cursor)
    # ... existing population ...
    populate_maintenance_requests(cursor)  # ADD THIS
    # ... rest of code ...
```

#### **Option B: Direct SQL Migration**

For existing databases, create a migration script:

```python
# scripts/add_maintenance_table.py

import sqlite3

def migrate():
    """Add MaintenanceRequests table to existing database"""
    
    conn = sqlite3.connect("property_management.db")
    cursor = conn.cursor()
    
    # Check if table already exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='MaintenanceRequests'
    """)
    
    if cursor.fetchone():
        print("MaintenanceRequests table already exists")
        return
    
    # Create table
    cursor.execute("""
        CREATE TABLE MaintenanceRequests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            request_date TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT,
            cost REAL,
            completed_date TEXT,
            FOREIGN KEY (unit_id) REFERENCES Units(unit_id)
        )
    """)
    
    conn.commit()
    print("✓ MaintenanceRequests table created successfully")
    
    # Optionally populate with sample data
    # ... (same as above)
    
    conn.close()

if __name__ == "__main__":
    migrate()
```

Run migration:
```bash
python scripts/add_maintenance_table.py
```

---

### **Step 3: Update schema.json (CRITICAL)**

This is where the **magic happens** - register your new table so the LLM knows about it.

**Open:** `schema.json`

**Add your table definition:**

```json
{
  "database": "property_management",
  "tables": {
    "Owners": { ... },
    "Properties": { ... },
    "Units": { ... },
    "Leases": { ... },
    
    "MaintenanceRequests": {
      "description": "Maintenance requests for rental units. Tracks repair and maintenance issues reported by tenants or property managers.",
      "columns": {
        "request_id": {
          "type": "INTEGER",
          "description": "Unique identifier for maintenance request",
          "primary_key": true
        },
        "unit_id": {
          "type": "INTEGER",
          "description": "Foreign key to Units table - which unit needs maintenance",
          "foreign_key": {
            "table": "Units",
            "column": "unit_id"
          }
        },
        "request_date": {
          "type": "TEXT",
          "description": "Date when maintenance was requested (ISO format YYYY-MM-DD)"
        },
        "description": {
          "type": "TEXT",
          "description": "Detailed description of the maintenance issue or request"
        },
        "status": {
          "type": "TEXT",
          "description": "Current status of request: 'open', 'in_progress', or 'completed'"
        },
        "priority": {
          "type": "TEXT",
          "description": "Priority level: 'low', 'medium', 'high', or 'urgent'"
        },
        "cost": {
          "type": "REAL",
          "description": "Total cost of completed maintenance (null if not completed)"
        },
        "completed_date": {
          "type": "TEXT",
          "description": "Date when maintenance was completed (null if still in progress)"
        }
      },
      "relationships": {
        "Units": "MaintenanceRequests.unit_id -> Units.unit_id (many-to-one)"
      },
      "indexes": [
        "unit_id",
        "status",
        "request_date"
      ],
      "sample_queries": [
        "How many open maintenance requests are there?",
        "What is the average maintenance cost?",
        "Show me urgent maintenance requests",
        "How many requests per unit?"
      ]
    }
  },
  
  "relationships": [
    "Owners (1) -> (many) Properties",
    "Properties (1) -> (many) Units",
    "Units (1) -> (many) Leases",
    "Units (1) -> (many) MaintenanceRequests"
  ]
}
```

**Key Points:**
- ✅ **description**: High-level table purpose (helps LLM understand)
- ✅ **columns**: Each column with type and description
- ✅ **relationships**: Foreign keys and how tables connect
- ✅ **sample_queries**: Example questions users might ask (guides LLM)

---

### **Step 4: Verify Schema Registration**

Test that the system can see your new table:

```bash
python scripts/inspect_database.py --summary-only
```

**Expected Output:**
```
TABLES OVERVIEW:
--------------------------------------------------------------------------------
  Owners                        6 rows
  Properties                  161 rows (1 foreign keys)
  Units                       166 rows (1 foreign keys)
  Leases                      166 rows (1 foreign keys)
  MaintenanceRequests          50 rows (1 foreign keys)  ← NEW TABLE!
--------------------------------------------------------------------------------
```

---

### **Step 5: Test with the Chatbot**

**Start the chatbot:**
```bash
python main.py
# or
streamlit run app.py
```

**Test queries:**
1. "How many maintenance requests are there?"
2. "Show me open maintenance requests"
3. "What's the average maintenance cost?"
4. "How many urgent requests do I have?"

**The LLM should automatically:**
- ✅ Understand the new table exists
- ✅ Know what columns are available
- ✅ Generate correct SQL JOINs with related tables
- ✅ Answer questions about maintenance data

---

### **Step 6: Update RBAC Rules (If Needed)**

If your new table needs special access control:

#### **Option A: Simple - All roles see it**

No changes needed - existing RBAC will apply owner_id filtering if the table has owner relationships.

#### **Option B: Restrict certain roles**

Update `agent/security.py`:

```python
class SecurityValidator:
    
    @classmethod
    def validate_query_intent(cls, user_query: str, user_context: UserContext):
        """Validate query permissions"""
        
        # Existing checks...
        
        # NEW: Restrict maintenance data for viewers
        if user_context.role.lower() == 'viewer':
            if 'maintenance' in user_query.lower():
                return False, "Access denied: Viewers cannot access maintenance request details."
        
        # ... rest of validation
```

---

### **Step 7: Update Tests (Optional but Recommended)**

Add test cases for your new table:

**Create:** `tests/test_maintenance.py`

```python
"""Test maintenance request queries"""

import pytest
from agent import PropertyManagementAgent, UserContext, DatabaseManager

@pytest.fixture
def agent():
    db_manager = DatabaseManager("property_management.db")
    return PropertyManagementAgent(db_manager, max_retries=3)

def test_maintenance_count(agent):
    """Test counting maintenance requests"""
    user_context = UserContext(user_id=999, role="admin", owner_id=None)
    response = agent.query("How many maintenance requests are there?", user_context)
    
    assert response['success']
    assert 'maintenance' in response['answer'].lower()
    assert response['sql_query'] is not None

def test_open_requests(agent):
    """Test filtering open requests"""
    user_context = UserContext(user_id=999, role="admin", owner_id=None)
    response = agent.query("How many open maintenance requests?", user_context)
    
    assert response['success']
    assert 'open' in response['sql_query'].lower()

def test_maintenance_cost(agent):
    """Test calculating average maintenance cost"""
    user_context = UserContext(user_id=999, role="admin", owner_id=None)
    response = agent.query("What is the average maintenance cost?", user_context)
    
    assert response['success']
    assert 'AVG' in response['sql_query'].upper()
```

**Run tests:**
```bash
pytest tests/test_maintenance.py -v
```

---

### **Step 8: Update Documentation**

Update relevant docs to mention the new table:

**1. Update README.md:**

```markdown
## Database Schema

The system manages:
- **Owners** (6) - Property owners (LLC1-LLC6)
- **Properties** (161) - Real estate properties
- **Units** (166) - Individual rental units
- **Leases** (166) - Tenant lease agreements
- **MaintenanceRequests** (50) - Maintenance and repair tracking  ← NEW
```

**2. Update docs/DATABASE_TOOLS.md:**

Add example queries for the new table.

---

## ✅ Verification Checklist

After adding a new table, verify:

- [ ] Table created in database
- [ ] Sample data populated
- [ ] schema.json updated with complete metadata
- [ ] System can inspect the table (`inspect_database.py`)
- [ ] Chatbot understands the table (test queries work)
- [ ] RBAC rules apply correctly (if applicable)
- [ ] Tests created and passing
- [ ] Documentation updated

---

## 🎯 Why This Works

### **Metadata-Driven Architecture**

```
User Query → LLM
               ↓
         Reads schema.json
               ↓
         Understands:
         - Table names
         - Column names
         - Data types
         - Relationships
         - Sample queries
               ↓
         Generates SQL
```

**Benefits:**
1. ✅ **No code changes** - Just update metadata
2. ✅ **Automatic discovery** - LLM reads schema dynamically
3. ✅ **Self-documenting** - schema.json serves as documentation
4. ✅ **Extensible** - Add unlimited tables without touching code

---

## 🔧 Advanced: Complex Table Relationships

### **Example: Many-to-Many Relationship**

Adding a `PropertyAmenities` junction table:

```sql
-- Amenities table
CREATE TABLE Amenities (
    amenity_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT
);

-- Junction table
CREATE TABLE PropertyAmenities (
    property_id INTEGER NOT NULL,
    amenity_id INTEGER NOT NULL,
    PRIMARY KEY (property_id, amenity_id),
    FOREIGN KEY (property_id) REFERENCES Properties(property_id),
    FOREIGN KEY (amenity_id) REFERENCES Amenities(amenity_id)
);
```

**In schema.json:**

```json
{
  "Amenities": {
    "description": "Available property amenities (pool, gym, parking, etc.)",
    "columns": { ... }
  },
  
  "PropertyAmenities": {
    "description": "Junction table linking properties to their amenities (many-to-many)",
    "columns": { ... },
    "relationships": {
      "Properties": "PropertyAmenities.property_id -> Properties.property_id",
      "Amenities": "PropertyAmenities.amenity_id -> Amenities.amenity_id"
    }
  }
}
```

**The LLM will automatically understand:**
- "Show me properties with a pool"
- "How many properties have parking?"
- "What amenities does property X have?"

---

## 🚨 Common Pitfalls to Avoid

### **1. Forgetting to Update schema.json**

❌ **Problem:** Table exists in database but not in schema.json  
✅ **Solution:** LLM won't know about it - always update schema.json!

### **2. Poor Column Descriptions**

❌ **Bad:** `"status": "The status"`  
✅ **Good:** `"status": "Current request status: 'open', 'in_progress', or 'completed'"`

### **3. Missing Relationships**

❌ **Problem:** Foreign keys not documented  
✅ **Solution:** LLM won't generate proper JOINs - document all relationships

### **4. No Sample Queries**

❌ **Problem:** LLM doesn't know what questions users might ask  
✅ **Solution:** Add 3-5 sample queries to guide the LLM

---

## 🎓 Best Practices

### **1. Descriptive Names**
Use clear, self-documenting table and column names:
- ✅ `MaintenanceRequests`, `request_date`, `completed_date`
- ❌ `MR`, `req_dt`, `comp_dt`

### **2. Comprehensive Descriptions**
Include:
- Purpose of the table
- What each column represents
- Valid values (enums)
- Nullable vs required

### **3. Sample Queries**
Help the LLM understand intent:
```json
"sample_queries": [
  "How many open maintenance requests?",
  "What's the average cost per request?",
  "Show urgent maintenance items"
]
```

### **4. Relationship Documentation**
Be explicit about how tables connect:
```json
"relationships": {
  "Units": "One unit can have many maintenance requests"
}
```

---

## 📊 Example: Complete Table Addition

**See the full example of MaintenanceRequests above.**

**Time to implement:** ~20 minutes
**Code changes required:** 0 (just metadata + data)

---

## 🔄 Rollback Procedure

If you need to remove a table:

1. **Remove from schema.json**
2. **Drop table:** `DROP TABLE MaintenanceRequests;`
3. **Regenerate database:** `python scripts/generate_mock_db.py`

---

## 📞 Troubleshooting

### **LLM doesn't recognize new table**

**Check:**
1. schema.json syntax is valid (use JSON validator)
2. schema.json is in the project root
3. Restart the chatbot application
4. Check logs for schema loading errors

### **Incorrect SQL generated**

**Fix:**
1. Improve column descriptions in schema.json
2. Add more sample queries
3. Document relationships more clearly

### **RBAC issues**

**Verify:**
1. Foreign keys to Owners/Properties exist (for owner filtering)
2. Security rules updated if needed
3. Test with different roles

---

## ✨ Summary

**Adding a new table is simple:**

```
1. Update database (SQL)
2. Update schema.json (metadata)
3. Test with chatbot
   ↓
   Done! No code changes needed!
```

**The system automatically:**
- Discovers new tables
- Understands structure
- Generates correct SQL
- Applies RBAC rules

---

## 📚 Related Documentation

- [DATABASE_TOOLS.md](DATABASE_TOOLS.md) - Database inspection
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [DEVELOPER_QUICKSTART.md](DEVELOPER_QUICKSTART.md) - Development guide

---

**Last Updated:** January 12, 2026  
**System Version:** 2.0  
**Strategy:** Metadata-Driven Schema Discovery ✓
