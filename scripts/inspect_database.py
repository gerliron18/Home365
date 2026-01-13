"""
Database Inspection Tool
========================
Standalone utility for developers to explore the Property Management database.

Usage:
    python scripts/inspect_database.py

Features:
- Display all tables and schemas
- Show table relationships (foreign keys)
- Provide statistics and sample data
- Export schema information
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class DatabaseInspector:
    """Comprehensive database inspection tool"""
    
    def __init__(self, db_path: str = "property_management.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
        )
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get detailed schema information for a table"""
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for col in self.cursor.fetchall():
            col_id, col_name, col_type, not_null, default_val, pk = col
            columns.append({
                'name': col_name,
                'type': col_type,
                'nullable': not not_null,
                'default': default_val,
                'primary_key': bool(pk)
            })
        return columns
    
    def get_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """Get foreign key relationships for a table"""
        self.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = []
        for fk in self.cursor.fetchall():
            fks.append({
                'column': fk[3],
                'references_table': fk[2],
                'references_column': fk[4]
            })
        return fks
    
    def get_table_count(self, table_name: str) -> int:
        """Get row count for a table"""
        self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return self.cursor.fetchone()[0]
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Tuple]:
        """Get sample rows from a table"""
        self.cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        return self.cursor.fetchall()
    
    def get_column_names(self, table_name: str) -> List[str]:
        """Get column names for a table"""
        schema = self.get_table_schema(table_name)
        return [col['name'] for col in schema]
    
    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get statistics for numeric columns in a table"""
        schema = self.get_table_schema(table_name)
        stats = {}
        
        for col in schema:
            col_name = col['name']
            col_type = col['type'].upper()
            
            # Only calculate stats for numeric columns
            if any(t in col_type for t in ['INTEGER', 'REAL', 'NUMERIC', 'DECIMAL']):
                try:
                    self.cursor.execute(f"""
                        SELECT 
                            MIN({col_name}) as min_val,
                            MAX({col_name}) as max_val,
                            AVG({col_name}) as avg_val,
                            COUNT(DISTINCT {col_name}) as distinct_count
                        FROM {table_name}
                        WHERE {col_name} IS NOT NULL
                    """)
                    result = self.cursor.fetchone()
                    if result and result[0] is not None:
                        stats[col_name] = {
                            'min': result[0],
                            'max': result[1],
                            'avg': result[2],
                            'distinct_values': result[3]
                        }
                except sqlite3.OperationalError:
                    pass  # Skip if calculation fails
        
        return stats
    
    def print_header(self, text: str, char: str = "="):
        """Print a formatted header"""
        print(f"\n{char * 80}")
        print(f"{text}")
        print(f"{char * 80}")
    
    def print_table_overview(self, table_name: str):
        """Print comprehensive overview of a table"""
        self.print_header(f"TABLE: {table_name}")
        
        # Schema
        print("\nSCHEMA:")
        print("-" * 80)
        schema = self.get_table_schema(table_name)
        for col in schema:
            pk = " [PRIMARY KEY]" if col['primary_key'] else ""
            nullable = " (nullable)" if col['nullable'] else " (NOT NULL)"
            default = f" DEFAULT: {col['default']}" if col['default'] else ""
            print(f"  {col['name']:20} {col['type']:15}{pk}{nullable}{default}")
        
        # Foreign Keys
        fks = self.get_foreign_keys(table_name)
        if fks:
            print("\nFOREIGN KEYS:")
            print("-" * 80)
            for fk in fks:
                print(f"  {fk['column']} -> {fk['references_table']}.{fk['references_column']}")
        
        # Row Count
        count = self.get_table_count(table_name)
        print(f"\nTOTAL ROWS: {count}")
        
        # Sample Data
        if count > 0:
            print(f"\nSAMPLE DATA (first 3 rows):")
            print("-" * 80)
            columns = self.get_column_names(table_name)
            sample_data = self.get_sample_data(table_name, 3)
            
            # Print header
            header = " | ".join([col[:15].ljust(15) for col in columns])
            print(header)
            print("-" * len(header))
            
            # Print rows
            for row in sample_data:
                row_str = " | ".join([str(val)[:15].ljust(15) for val in row])
                print(row_str)
        
        # Statistics
        stats = self.get_table_statistics(table_name)
        if stats:
            print(f"\nSTATISTICS:")
            print("-" * 80)
            for col_name, col_stats in stats.items():
                print(f"  {col_name}:")
                if 'avg' in col_stats and col_stats['avg'] is not None:
                    min_val = f"{col_stats['min']:.2f}" if isinstance(col_stats['min'], float) else str(col_stats['min'])
                    max_val = f"{col_stats['max']:.2f}" if isinstance(col_stats['max'], float) else str(col_stats['max'])
                    avg_val = f"{col_stats['avg']:.2f}"
                    print(f"    Min: {min_val}")
                    print(f"    Max: {max_val}")
                    print(f"    Avg: {avg_val}")
                print(f"    Distinct values: {col_stats['distinct_values']}")
    
    def print_database_summary(self):
        """Print summary of entire database"""
        self.print_header("DATABASE SUMMARY", "=")
        
        tables = self.get_all_tables()
        print(f"\nDatabase: {self.db_path}")
        print(f"Total Tables: {len(tables)}")
        print(f"Inspection Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\nTABLES OVERVIEW:")
        print("-" * 80)
        
        total_rows = 0
        for table in tables:
            count = self.get_table_count(table)
            total_rows += count
            fks = self.get_foreign_keys(table)
            fk_info = f" ({len(fks)} foreign keys)" if fks else ""
            print(f"  {table:20} {count:10,} rows{fk_info}")
        
        print("-" * 80)
        print(f"  {'TOTAL':20} {total_rows:10,} rows")
    
    def print_relationships(self):
        """Print all table relationships"""
        self.print_header("TABLE RELATIONSHIPS")
        
        tables = self.get_all_tables()
        relationships = []
        
        for table in tables:
            fks = self.get_foreign_keys(table)
            for fk in fks:
                relationships.append({
                    'from_table': table,
                    'from_column': fk['column'],
                    'to_table': fk['references_table'],
                    'to_column': fk['references_column']
                })
        
        if relationships:
            print("\nFOREIGN KEY RELATIONSHIPS:")
            print("-" * 80)
            for rel in relationships:
                print(f"  {rel['from_table']}.{rel['from_column']}")
                print(f"    -> {rel['to_table']}.{rel['to_column']}")
        else:
            print("\nNo foreign key relationships defined.")
        
        # Print hierarchy
        print("\nTABLE HIERARCHY:")
        print("-" * 80)
        print("Owners (owner_id)")
        print("  |-> Properties (owner_id)")
        print("       |-> Units (property_id)")
        print("            |-> Leases (unit_id)")
    
    def export_schema_json(self, output_file: str = "database_schema_export.json"):
        """Export complete database schema to JSON"""
        tables = self.get_all_tables()
        schema_export = {
            'database': self.db_path,
            'exported_at': datetime.now().isoformat(),
            'tables': {}
        }
        
        for table in tables:
            schema_export['tables'][table] = {
                'columns': self.get_table_schema(table),
                'foreign_keys': self.get_foreign_keys(table),
                'row_count': self.get_table_count(table),
                'statistics': self.get_table_statistics(table)
            }
        
        with open(output_file, 'w') as f:
            json.dump(schema_export, f, indent=2)
        
        print(f"\nSchema exported to: {output_file}")
    
    def run_full_inspection(self, export_json: bool = False):
        """Run complete database inspection"""
        print("=" * 80)
        print("DATABASE INSPECTION TOOL")
        print("Property Management System")
        print("=" * 80)
        
        # Summary
        self.print_database_summary()
        
        # Relationships
        self.print_relationships()
        
        # Detailed table information
        tables = self.get_all_tables()
        for table in tables:
            self.print_table_overview(table)
        
        # Export
        if export_json:
            self.print_header("EXPORT")
            self.export_schema_json()
        
        # Footer
        self.print_header("INSPECTION COMPLETE", "=")
        print("\nDatabase is healthy and ready for use!")
        print(f"Total tables: {len(tables)}")
        print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Inspect Property Management Database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/inspect_database.py                    # Full inspection
  python scripts/inspect_database.py --export           # Export to JSON
  python scripts/inspect_database.py --db custom.db     # Custom database
        """
    )
    
    parser.add_argument(
        '--db',
        default='property_management.db',
        help='Database file path (default: property_management.db)'
    )
    
    parser.add_argument(
        '--export',
        action='store_true',
        help='Export schema to JSON file'
    )
    
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='Show only database summary'
    )
    
    args = parser.parse_args()
    
    # Check if database exists
    if not os.path.exists(args.db):
        print(f"ERROR: Database file not found: {args.db}")
        print("\nGenerate the database first:")
        print("  python scripts/generate_mock_db.py")
        sys.exit(1)
    
    # Run inspection
    with DatabaseInspector(args.db) as inspector:
        if args.summary_only:
            inspector.print_database_summary()
            inspector.print_relationships()
        else:
            inspector.run_full_inspection(export_json=args.export)


if __name__ == "__main__":
    main()
