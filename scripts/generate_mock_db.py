"""
Mock Database Generator
Creates property_management.db with data matching specific test scenarios
"""
import sqlite3
import random
from pathlib import Path
from datetime import datetime, timedelta


def create_database():
    """Create SQLite database with schema and mock data"""
    db_path = Path(__file__).parent.parent / "property_management.db"
    
    # Remove existing database
    if db_path.exists():
        db_path.unlink()
        print(f"Removed existing database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating database schema...")
    
    # Create Owners table
    cursor.execute("""
        CREATE TABLE Owners (
            owner_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_name TEXT NOT NULL,
            contact_email TEXT,
            contact_phone TEXT
        )
    """)
    
    # Create Properties table
    cursor.execute("""
        CREATE TABLE Properties (
            property_id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            zip_code TEXT NOT NULL,
            property_type TEXT NOT NULL,
            purchase_date TEXT NOT NULL,
            purchase_price REAL NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (owner_id) REFERENCES Owners(owner_id)
        )
    """)
    
    # Create Units table
    cursor.execute("""
        CREATE TABLE Units (
            unit_id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER NOT NULL,
            unit_number TEXT NOT NULL,
            bedrooms INTEGER NOT NULL,
            bathrooms REAL NOT NULL,
            square_feet INTEGER NOT NULL,
            monthly_rent REAL NOT NULL,
            FOREIGN KEY (property_id) REFERENCES Properties(property_id)
        )
    """)
    
    # Create Leases table
    cursor.execute("""
        CREATE TABLE Leases (
            lease_id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER NOT NULL,
            tenant_name TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            monthly_rent REAL NOT NULL,
            security_deposit REAL NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (unit_id) REFERENCES Units(unit_id)
        )
    """)
    
    print("Populating with mock data...")
    
    # Insert Owners
    # Need: LLC1(22 props), LLC2(12 props), LLC3(41 active), LLC4(14 active), LLC5(most profitable)
    # Total: 161 properties, 115 active
    owners = [
        (1, "LLC1", "contact@llc1.com", "555-0101"),
        (2, "LLC2", "contact@llc2.com", "555-0102"),
        (3, "LLC3", "contact@llc3.com", "555-0103"),
        (4, "LLC4", "contact@llc4.com", "555-0104"),
        (5, "LLC5", "contact@llc5.com", "555-0105"),
        (6, "Other Holdings LLC", "contact@other.com", "555-0106"),
    ]
    cursor.executemany("INSERT INTO Owners VALUES (?, ?, ?, ?)", owners)
    
    # Property generation helper
    def generate_properties(owner_id, count, active_count, start_id):
        """Generate properties for an owner"""
        properties = []
        cities = ["Philadelphia", "Phoenix", "Los Angeles", "Chicago", "Houston", "Miami", "Seattle"]
        states = ["PA", "AZ", "CA", "IL", "TX", "FL", "WA"]
        property_types = ["Single Family", "Multi-Family", "Commercial"]
        
        for i in range(count):
            prop_id = start_id + i
            is_active = 1 if i < active_count else 0
            city = random.choice(cities)
            state = random.choice(states)
            
            properties.append((
                prop_id,
                owner_id,
                f"{random.randint(100, 9999)} {random.choice(['Main', 'Oak', 'Elm', 'Maple', 'Park'])} St",
                city,
                state,
                f"{random.randint(10000, 99999)}",
                random.choice(property_types),
                f"20{random.randint(15, 23)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
                random.uniform(150000, 800000),
                is_active
            ))
        return properties
    
    # Calculate distribution
    # Total: 161 properties, 115 active
    # LLC1: 22 properties
    # LLC2: 12 properties
    # LLC3: 41 active (can have more inactive)
    # LLC4: 14 active (can have more inactive)
    # LLC5: needs at least 1 for most profitable
    
    all_properties = []
    prop_id = 1
    
    # LLC1: 22 properties (16 active to contribute to total)
    llc1_props = generate_properties(1, 22, 16, prop_id)
    all_properties.extend(llc1_props)
    prop_id += 22
    
    # LLC2: 12 properties (10 active)
    llc2_props = generate_properties(2, 12, 10, prop_id)
    all_properties.extend(llc2_props)
    prop_id += 12
    
    # LLC3: 50 total properties, 41 active
    llc3_props = generate_properties(3, 50, 41, prop_id)
    all_properties.extend(llc3_props)
    prop_id += 50
    
    # LLC4: 20 total properties, 14 active
    llc4_props = generate_properties(4, 20, 14, prop_id)
    all_properties.extend(llc4_props)
    prop_id += 20
    
    # LLC5: 30 properties (20 active) - one will be most profitable overall
    llc5_props = generate_properties(5, 30, 20, prop_id)
    
    # Replace FIRST LLC5 property with Eshelman Mill Rd (BEFORE adding to list)
    llc5_props[0] = (
        prop_id,  # First LLC5 property ID
        5,
        "5678 Eshelman Mill Rd",
        "Willow Street",
        "PA",
        "17584",
        "Single Family",
        "2019-03-20",
        175000,  # Low purchase price for high profitability
        1
    )
    
    all_properties.extend(llc5_props)
    llc5_eshelman_id = prop_id  # Store for unit assignment
    prop_id += 30
    
    # Others: Remaining to reach 161 total
    # 161 - (22 + 12 + 50 + 20 + 30) = 27 more properties
    # Active: 115 - (16 + 10 + 41 + 14 + 20) = 14 active
    other_props = generate_properties(6, 27, 14, prop_id)
    
    # Replace FIRST other property with Yucca St (BEFORE adding to list)
    other_props[0] = (
        prop_id,  # First other property ID
        6,  # Owner 6 (Other Holdings)
        "1234 W Yucca St",
        "Glendale",
        "AZ",
        "85301",
        "Multi-Family",
        "2018-06-15",
        180000,  # Low purchase price for high profitability
        1
    )
    
    all_properties.extend(other_props)
    yucca_id = prop_id  # Store for unit assignment
    prop_id += 27
    
    cursor.executemany("""
        INSERT INTO Properties VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, all_properties)
    
    print(f"  Created {len(all_properties)} properties")
    
    # Generate Units - need to ensure average rent matches
    # LLC2 average rent: $1,016.30
    # All average rent: $917.64
    
    units = []
    unit_id = 1
    
    # For LLC2 properties (IDs 23-34), create units with average rent $1,016.30
    llc2_property_ids = [p[0] for p in llc2_props]
    llc2_rents = [950, 1000, 1050, 1100, 980, 1020, 1015, 1030, 990, 1025, 1040, 996]
    # Average: sum = 12196, avg = 1016.33
    
    for i, prop_id in enumerate(llc2_property_ids):
        units.append((
            unit_id,
            prop_id,
            "Unit A",
            random.randint(1, 3),
            random.choice([1.0, 1.5, 2.0]),
            random.randint(600, 1200),
            llc2_rents[i]
        ))
        unit_id += 1
    
    # For Yucca St property (most profitable overall) - VERY high-rent units
    for i in range(4):  # 4 units
        units.append((
            unit_id,
            yucca_id,
            f"Unit {chr(65+i)}",
            3,
            2.0,
            1200,
            3500  # VERY High rent for profitability (total: $14,000/month)
        ))
        unit_id += 1
    
    # Eshelman Mill Rd (LLC5 most profitable) - Very high rent
    for i in range(3):  # 3 units
        units.append((
            unit_id,
            llc5_eshelman_id,
            f"Unit {chr(65+i)}" if i > 0 else "Unit X",
            3,
            2.0,
            1100,
            3200  # Very high rent for profitability (total: $9,600/month)
        ))
        unit_id += 1
    
    # Generate units for remaining properties to hit average of $917.64
    # We have 12 LLC2 units, 4 Yucca units, 3 Eshelman units = 19 units so far
    # Need many more units to calculate average properly
    
    remaining_property_ids = [p[0] for p in all_properties if p[0] not in llc2_property_ids 
                              and p[0] != yucca_id and p[0] != llc5_eshelman_id]
    
    # Create ~150 more units with varied rents to average $917.64 overall
    total_rent_so_far = sum(llc2_rents) + (4 * 2200) + (3 * 2100)
    units_so_far = 19
    
    # To get average of 917.64 with ~170 total units:
    # Need to adjust rent values to hit target average
    # Target total: 170 * 917.64 = 155999
    # Already have: 12196 + 8800 + 6300 = 27296
    # Need: 155999 - 27296 = 128703 from ~143 units
    # Average for remaining: 128703 / 143 = 900
    
    target_avg_remaining = 850
    variance = 150
    
    for prop_id in remaining_property_ids[:151]:  # Limit to reasonable number
        rent = max(600, target_avg_remaining + random.randint(-variance, variance))
        units.append((
            unit_id,
            prop_id,
            "Unit A",
            random.randint(1, 3),
            random.choice([1.0, 1.5, 2.0]),
            random.randint(600, 1200),
            rent
        ))
        unit_id += 1
    
    cursor.executemany("""
        INSERT INTO Units VALUES (?, ?, ?, ?, ?, ?, ?)
    """, units)
    
    print(f"  Created {len(units)} units")
    
    # Generate Leases - at least one active lease per unit
    leases = []
    lease_id = 1
    base_date = datetime.now()
    
    for unit in units:
        # Active lease
        start_date = base_date - timedelta(days=random.randint(30, 365))
        end_date = start_date + timedelta(days=365)
        
        leases.append((
            lease_id,
            unit[0],  # unit_id
            f"Tenant {lease_id}",
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            unit[6],  # monthly_rent from unit
            unit[6] * 1.5,  # security_deposit
            1 if end_date > base_date else 0
        ))
        lease_id += 1
    
    cursor.executemany("""
        INSERT INTO Leases VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, leases)
    
    print(f"  Created {len(leases)} leases")
    
    conn.commit()
    
    # Verify data
    print("\nVerifying data...")
    
    cursor.execute("SELECT COUNT(*) FROM Properties")
    total_props = cursor.fetchone()[0]
    print(f"  Total properties: {total_props}")
    
    cursor.execute("SELECT COUNT(*) FROM Properties WHERE is_active = 1")
    active_props = cursor.fetchone()[0]
    print(f"  Active properties: {active_props}")
    
    cursor.execute("""
        SELECT o.owner_name, COUNT(p.property_id) 
        FROM Owners o
        LEFT JOIN Properties p ON o.owner_id = p.owner_id
        GROUP BY o.owner_id
        ORDER BY o.owner_id
    """)
    for owner, count in cursor.fetchall():
        print(f"  {owner}: {count} properties")
    
    cursor.execute("""
        SELECT AVG(u.monthly_rent)
        FROM Units u
        JOIN Properties p ON u.property_id = p.property_id
        WHERE p.owner_id = 2
    """)
    llc2_avg = cursor.fetchone()[0]
    print(f"  LLC2 average rent: ${llc2_avg:.2f}")
    
    cursor.execute("SELECT AVG(monthly_rent) FROM Units")
    all_avg = cursor.fetchone()[0]
    print(f"  All average rent: ${all_avg:.2f}")
    
    conn.close()
    
    print(f"\n[SUCCESS] Database created successfully: {db_path}")
    print("\nNext step: Run 'python main.py' to start the chatbot")


if __name__ == "__main__":
    create_database()
