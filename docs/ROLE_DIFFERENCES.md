# 👥 Role-Based Access Control (RBAC) - Clear Differences

## 🎯 **Role Comparison**

| Feature | Admin | Owner | Viewer |
|---------|-------|-------|--------|
| **Access Scope** | All properties (all owners) | Only their own properties | All properties (aggregated) |
| **Can See Addresses** | ✅ Yes | ✅ Yes (own only) | ❌ No |
| **Can See Tenant Names** | ✅ Yes | ✅ Yes (own only) | ❌ No |
| **Can See Contact Info** | ✅ Yes | ✅ Yes (own only) | ❌ No |
| **Can List Properties** | ✅ Yes | ✅ Yes (own only) | ❌ No |
| **Can See Counts/Totals** | ✅ Yes | ✅ Yes (own only) | ✅ Yes |
| **Can See Averages** | ✅ Yes | ✅ Yes (own only) | ✅ Yes |
| **Can See Statistics** | ✅ Yes | ✅ Yes (own only) | ✅ Yes |
| **Can Modify Data** | ❌ No | ❌ No | ❌ No |

---

## 🔑 **Role Details**

### 1️⃣ Admin - Full Detailed Access
**Description:** System administrators and management

**Can Do:**
- ✅ View all properties across all owners
- ✅ See detailed information (addresses, tenants, contacts)
- ✅ List individual properties
- ✅ Access aggregate statistics
- ✅ Query any data in the system

**Example Queries:**
```
✅ "List all properties in Arizona"
✅ "Show me properties with tenant John Doe"
✅ "What's the address of property ID 123?"
✅ "How many properties are there?"
✅ "What's the average rent?"
```

**Use Case:** Property management company staff, system administrators

---

### 2️⃣ Owner - Own Properties Only
**Description:** Property owners (LLC1, LLC2, etc.)

**Can Do:**
- ✅ View their own properties only
- ✅ See detailed information about their properties
- ✅ List their properties
- ✅ Access their own statistics
- ❌ Cannot see other owners' data

**Example Queries:**
```
✅ "How many properties do I have?"
✅ "What is my most profitable property?"
✅ "List my properties in California"
✅ "What's my average rent?"
❌ "How many properties does LLC3 have?" → BLOCKED
❌ "Show me all properties" → BLOCKED
```

**Use Case:** Individual property owners checking their portfolio

---

### 3️⃣ Viewer - Summary Data Only
**Description:** Analysts, stakeholders, external auditors

**Can Do:**
- ✅ View aggregated data (counts, averages, totals)
- ✅ See high-level statistics
- ❌ Cannot see addresses or sensitive details
- ❌ Cannot list individual properties
- ❌ Cannot see tenant names or contact info

**Example Queries:**
```
✅ "How many properties are there?"
✅ "What is the average rent?"
✅ "How many active properties?"
✅ "Total property count by state"
❌ "List all properties" → BLOCKED
❌ "Show me addresses" → BLOCKED
❌ "What tenants are in property X?" → BLOCKED
```

**Use Case:** Financial analysts, board members, external auditors

---

## 🛡️ **Security Enforcement**

### Admin Access
**No Restrictions** (except read-only)
- Queries pass through all validation
- Can access all data tables
- Full SELECT capabilities

### Owner Access
**RBAC Filter Applied**
```sql
-- Original query
SELECT COUNT(*) FROM Properties

-- Auto-filtered
SELECT COUNT(*) FROM Properties 
WHERE Properties.owner_id = 2
```

**Blocked Queries:**
- Queries mentioning other owners (LLC1, LLC3, etc.)
- "All properties" or "total properties" queries
- Cross-owner data requests

### Viewer Access
**Sensitive Data Filter Applied**

**Blocked Patterns:**
- `address`, `tenant`, `name`, `contact`, `phone`, `email`
- `list properties`, `show properties`
- Queries requesting detailed/individual records

**Allowed Patterns:**
- `COUNT`, `AVG`, `SUM`, `MIN`, `MAX`
- Aggregate functions
- Statistical queries

---

## 📊 **Example Scenarios**

### Scenario 1: Property Count
```
Admin:  "How many properties?" → 161 properties ✅
Owner:  "How many properties?" → 12 properties (LLC2) ✅
Viewer: "How many properties?" → 161 properties ✅
```

### Scenario 2: Property List
```
Admin:  "List properties in AZ" → Shows addresses ✅
Owner:  "List my properties in AZ" → Shows their addresses ✅
Viewer: "List properties in AZ" → BLOCKED ❌
```

### Scenario 3: Average Rent
```
Admin:  "What's the average rent?" → $970.49 ✅
Owner:  "What's my average rent?" → $1,016.33 (LLC2) ✅
Viewer: "What's the average rent?" → $970.49 ✅
```

### Scenario 4: Cross-Owner Query
```
Admin:  "How many properties does LLC3 have?" → 50 properties ✅
Owner:  "How many properties does LLC3 have?" → BLOCKED ❌
Viewer: "How many properties does LLC3 have?" → 50 properties ✅
```

### Scenario 5: Detailed Information
```
Admin:  "Show me tenant names" → Shows names ✅
Owner:  "Show me my tenant names" → Shows their tenants ✅
Viewer: "Show me tenant names" → BLOCKED ❌
```

---

## 🔐 **Privacy & Security**

**Protected Information (Admin/Owner Only):**
- Property addresses
- Tenant names
- Contact information (phone, email)
- Individual property details
- Unit numbers and specifics

**Public Information (All Roles):**
- Property counts
- Aggregate statistics
- Average values
- Total counts by category

**Blocked for Everyone:**
- Data modifications (INSERT, UPDATE, DELETE)
- Schema changes (DROP, ALTER, CREATE)
- Administrative operations

---

## 🎯 **Role Selection Guide**

**Choose Admin if:**
- You're a property management company employee
- You need to see all properties and details
- You're responsible for system operations

**Choose Owner if:**
- You own properties (LLC1-5)
- You only want to see your own portfolio
- You need detailed info about your properties

**Choose Viewer if:**
- You're an analyst or auditor
- You only need summary statistics
- You don't need individual property details
- You're preparing reports or presentations

---

**Updated:** January 12, 2026  
**System:** Property Management Chatbot v1.0  
**Security Level:** Enterprise-Grade 🔒
