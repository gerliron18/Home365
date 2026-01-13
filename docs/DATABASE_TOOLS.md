# 🛠️ Database Developer Tools

This document describes the developer utilities available for inspecting and managing the Property Management database.

---

## 📊 Database Inspection Tool

**File:** `scripts/inspect_database.py`

A comprehensive standalone utility for developers to explore the database structure, relationships, and statistics **without running the chatbot**.

### Features

✅ **Complete Schema Information**
- View all tables and column definitions
- See data types, constraints, and defaults
- Identify primary keys and nullable fields

✅ **Relationship Mapping**
- Display all foreign key relationships
- Visualize table hierarchy
- Understand data dependencies

✅ **Statistical Analysis**
- Row counts for each table
- Min/Max/Average values for numeric columns
- Distinct value counts
- Distribution insights

✅ **Sample Data Preview**
- View first 3 rows of each table
- Quick data quality checks
- Verify data generation

✅ **JSON Export**
- Export complete schema to JSON
- Use for documentation or automation
- Share with team members

---

## 🚀 Usage

### Basic Usage

```bash
# Full comprehensive inspection
python scripts/inspect_database.py
```

**Output includes:**
- Database summary
- Table relationships
- Detailed schema for each table
- Foreign key mappings
- Sample data (3 rows per table)
- Statistical analysis

---

### Quick Summary

```bash
# Show only summary and relationships
python scripts/inspect_database.py --summary-only
```

**Output:**
```
================================================================================
DATABASE SUMMARY
================================================================================

Database: property_management.db
Total Tables: 4
Inspection Date: 2026-01-12 16:05:06

TABLES OVERVIEW:
--------------------------------------------------------------------------------
  Owners                        6 rows
  Properties                  161 rows (1 foreign keys)
  Units                       166 rows (1 foreign keys)
  Leases                      166 rows (1 foreign keys)
--------------------------------------------------------------------------------
  TOTAL                       499 rows
```

---

### Export to JSON

```bash
# Export schema and statistics to JSON file
python scripts/inspect_database.py --export
```

Creates `database_schema_export.json` with:
```json
{
  "database": "property_management.db",
  "exported_at": "2026-01-12T16:05:06",
  "tables": {
    "Owners": {
      "columns": [...],
      "foreign_keys": [...],
      "row_count": 6,
      "statistics": {...}
    },
    ...
  }
}
```

---

### Custom Database

```bash
# Inspect a different database file
python scripts/inspect_database.py --db path/to/custom.db
```

---

### Windows Quick Launch

```bash
# Double-click or run:
INSPECT_DB.bat
```

---

## 📋 Command-Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--db PATH` | Specify database file path | `--db custom.db` |
| `--export` | Export schema to JSON | `--export` |
| `--summary-only` | Show only summary (no details) | `--summary-only` |
| `--help` | Show help message | `--help` |

---

## 🔍 What You'll See

### 1. Database Summary
- Total number of tables
- Row count per table
- Foreign key count
- Total rows across all tables

### 2. Table Relationships
```
FOREIGN KEY RELATIONSHIPS:
  Properties.owner_id -> Owners.owner_id
  Units.property_id -> Properties.property_id
  Leases.unit_id -> Units.unit_id

TABLE HIERARCHY:
Owners (owner_id)
  |-> Properties (owner_id)
       |-> Units (property_id)
            |-> Leases (unit_id)
```

### 3. Table Schema (for each table)
```
SCHEMA:
  property_id          INTEGER         [PRIMARY KEY] (nullable)
  owner_id             INTEGER         (NOT NULL)
  address              TEXT            (NOT NULL)
  city                 TEXT            (NOT NULL)
  state                TEXT            (NOT NULL)
  zip_code             TEXT            (NOT NULL)
  property_type        TEXT            (NOT NULL)
  purchase_date        TEXT            (NOT NULL)
  purchase_price       REAL            (NOT NULL)
  is_active            INTEGER         (NOT NULL) DEFAULT: 1

FOREIGN KEYS:
  owner_id -> Owners.owner_id

TOTAL ROWS: 161
```

### 4. Sample Data
```
SAMPLE DATA (first 3 rows):
property_id | owner_id | address      | city    | state | ...
------------|----------|--------------|---------|-------|----
1           | 1        | 3574 Elm St  | Phoenix | TX    | ...
2           | 1        | 7042 Main St | Phoenix | IL    | ...
3           | 1        | 9274 Maple St| Seattle | TX    | ...
```

### 5. Statistics
```
STATISTICS:
  property_id:
    Min: 1
    Max: 161
    Avg: 81.00
    Distinct values: 161
  
  purchase_price:
    Min: 153512.00
    Max: 799584.58
    Avg: 448775.20
    Distinct values: 161
  
  is_active:
    Min: 0
    Max: 1
    Avg: 0.71
    Distinct values: 2
```

---

## 💡 Use Cases

### For Developers

**Database Health Check**
```bash
python scripts/inspect_database.py --summary-only
```
Quick verification that database is properly generated and populated.

**Schema Documentation**
```bash
python scripts/inspect_database.py --export
```
Generate JSON schema for API documentation or team sharing.

**Data Quality Validation**
```bash
python scripts/inspect_database.py
```
Review sample data and statistics to ensure data generation is correct.

**Troubleshooting**
- Verify foreign key relationships are correct
- Check that all expected tables exist
- Confirm row counts match requirements

---

### For Data Analysis

**Understanding Data Structure**
- See what columns are available
- Understand relationships between tables
- Identify nullable vs required fields

**Query Planning**
- View statistical distributions
- Identify key columns for JOIN operations
- Plan optimal query structures

**Data Validation**
- Verify LLC1 has 22 properties
- Confirm 161 total properties
- Check average rent is ~$970.49

---

## 🎯 Example Workflows

### Workflow 1: Initial Setup Verification

```bash
# 1. Generate database
python scripts/generate_mock_db.py

# 2. Inspect to verify
python scripts/inspect_database.py --summary-only

# 3. Check for expected values
# Should see:
#   - Owners: 6 rows
#   - Properties: 161 rows
#   - Units: 166 rows
#   - Leases: 166 rows
```

### Workflow 2: Schema Documentation

```bash
# 1. Full inspection with export
python scripts/inspect_database.py --export

# 2. Share database_schema_export.json with team

# 3. Use JSON for:
#    - API documentation
#    - ORM model generation
#    - Database migration planning
```

### Workflow 3: Debugging Data Issues

```bash
# 1. Run full inspection
python scripts/inspect_database.py > db_report.txt

# 2. Review sample data in report

# 3. Check statistics for anomalies

# 4. Verify relationships are correct
```

---

## 🔧 Advanced Usage

### Automated Testing

```python
import subprocess
import json

# Run inspection with export
subprocess.run([
    "python", "scripts/inspect_database.py", 
    "--export", "--summary-only"
])

# Load and validate schema
with open("database_schema_export.json") as f:
    schema = json.load(f)

# Assert expected structure
assert len(schema['tables']) == 4
assert schema['tables']['Properties']['row_count'] == 161
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
- name: Validate Database Schema
  run: |
    python scripts/generate_mock_db.py
    python scripts/inspect_database.py --export
    python scripts/validate_schema.py  # Your custom validator
```

---

## 📝 Output Files

### database_schema_export.json

**Structure:**
```json
{
  "database": "property_management.db",
  "exported_at": "2026-01-12T16:05:06.123456",
  "tables": {
    "TableName": {
      "columns": [
        {
          "name": "column_name",
          "type": "INTEGER",
          "nullable": false,
          "default": null,
          "primary_key": true
        }
      ],
      "foreign_keys": [
        {
          "column": "owner_id",
          "references_table": "Owners",
          "references_column": "owner_id"
        }
      ],
      "row_count": 161,
      "statistics": {
        "column_name": {
          "min": 1,
          "max": 161,
          "avg": 81.0,
          "distinct_values": 161
        }
      }
    }
  }
}
```

**Use Cases:**
- Documentation generation
- Schema comparison between environments
- Automated validation
- Team collaboration

---

## ⚠️ Important Notes

### Independence from Chatbot
- This tool is **completely separate** from the chatbot
- No LLM or API calls required
- Works offline
- Pure Python + SQLite

### Safety
- **READ-ONLY operations only**
- No data modifications
- No schema changes
- Safe to run in production

### Performance
- Fast execution (< 1 second)
- Minimal memory footprint
- Works with databases of any size

---

## 🆘 Troubleshooting

### Database Not Found
```
ERROR: Database file not found: property_management.db

Solution:
  python scripts/generate_mock_db.py
```

### Permission Denied
```
ERROR: Permission denied

Solution:
  Close any applications using the database
  Check file permissions
```

### Export File Already Exists
The tool will **overwrite** existing `database_schema_export.json` files without prompting.

---

## 🎓 Learning Resources

### Understanding the Output

**Primary Keys**
- Marked with `[PRIMARY KEY]`
- Uniquely identify each row
- Usually auto-incrementing integers

**Foreign Keys**
- Reference primary keys in other tables
- Establish relationships
- Enforce referential integrity

**Nullable vs NOT NULL**
- Nullable: Can contain NULL values
- NOT NULL: Must have a value

**Statistics**
- Min/Max: Range of values
- Avg: Mean/average value
- Distinct: Number of unique values

---

## 📚 Related Documentation

- [README.md](README.md) - Main project documentation
- [architecture.md](architecture.md) - System architecture
- [schema.json](schema.json) - Database schema metadata
- [ROLE_DIFFERENCES.md](ROLE_DIFFERENCES.md) - RBAC documentation

---

**Created:** January 12, 2026  
**Version:** 1.0  
**Maintenance:** Part of Property Management Chatbot System
