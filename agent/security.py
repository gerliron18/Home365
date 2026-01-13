"""
Security Layer for SQL Query Validation and RBAC
"""
import re
from typing import Tuple
from .state import UserContext


class SecurityValidator:
    """Validates SQL queries for security compliance"""
    
    # Dangerous SQL patterns
    DML_PATTERNS = [
        r'\bINSERT\b',
        r'\bUPDATE\b',
        r'\bDELETE\b',
        r'\bDROP\b',
        r'\bTRUNCATE\b',
        r'\bALTER\b',
        r'\bCREATE\b',
        r'\bREPLACE\b',
        r'\bEXEC\b',
        r'\bEXECUTE\b',
    ]
    
    # Owner names that might indicate cross-owner queries
    OWNER_NAMES = [r'\bLLC1\b', r'\bLLC2\b', r'\bLLC3\b', r'\bLLC4\b', r'\bLLC5\b']
    
    @classmethod
    def is_data_query(cls, user_query: str) -> Tuple[bool, str]:
        """
        Determine if user query is asking for data (SQL-able) or general conversation
        Returns: (is_data_query, response_if_not)
        """
        query_lower = user_query.lower().strip()
        
        # Non-data query patterns (general conversation)
        conversational_patterns = [
            r'\bhello\b', r'\bhi\b', r'\bhey\b', r'\bgreetings\b',
            r'\bhow are you\b', r'\bhow\'s it going\b',
            r'\bwhat can you do\b', r'\bwhat are you\b', r'\bwho are you\b',
            r'\bhelp me\b', r'\bexplain\b', r'\btell me about yourself\b',
            r'\bgood morning\b', r'\bgood afternoon\b', r'\bgood evening\b',
            r'\bthank you\b', r'\bthanks\b', r'\bbye\b', r'\bgoodbye\b'
        ]
        
        for pattern in conversational_patterns:
            if re.search(pattern, query_lower):
                response = """I'm a property management AI assistant specialized in analyzing your real estate data.

I can help you with:
• Property counts and statistics
• Rent analysis and averages
• Profitability calculations
• Unit details and occupancy
• Property searches and filters

Try asking:
- "How many properties do I have?"
- "What is my most profitable property?"
- "What's the average rent I received?"
- "Show me properties in Arizona"

What would you like to know about your properties?"""
                return False, response
        
        return True, ""
    
    @classmethod
    def validate_query_intent(cls, user_query: str, user_context: UserContext) -> Tuple[bool, str]:
        """
        Validate if user's question is within their permission scope
        Returns: (is_allowed, error_message)
        """
        query_lower = user_query.lower()
        
        # Check viewer restrictions
        if user_context.role.lower() == 'viewer':
            # Viewers cannot query sensitive/detailed information
            sensitive_patterns = [
                r'\baddress\b', r'\btenant\b', r'\bname\b', r'\bcontact\b',
                r'\bphone\b', r'\bemail\b', r'\bunit number\b',
                r'\blist\b.*\bproperties\b', r'\bshow\b.*\bproperties\b'
            ]
            
            for pattern in sensitive_patterns:
                if re.search(pattern, query_lower):
                    return False, "Access denied: Viewers can only access aggregated data (counts, averages, totals). Detailed property information is restricted to admin users."
            
            # CRITICAL FIX: Viewers cannot query specific owners
            owner_patterns = [
                r'\bllc\s*[1-6]\b',
                r'\bllc[1-6]\b',
                r'\bowner\s+[1-6]\b',
                r'\bfor\s+llc',
                r'\bof\s+llc',
                r'\bdoes\s+llc',
                r'\bdo\s+llc'
            ]
            
            for pattern in owner_patterns:
                if re.search(pattern, query_lower):
                    return False, "Access denied: Viewers cannot query data for specific owners. You can only access aggregated statistics across all properties."
        
        # Check owner restrictions
        if user_context.role.lower() != 'owner':
            return True, ""  # Admin can ask anything
        
        query_lower = user_query.lower()
        
        # Check if asking about other owners
        for pattern in cls.OWNER_NAMES:
            if re.search(pattern, user_query, re.IGNORECASE):
                # Check if it's asking about their own owner
                current_owner = f"LLC{user_context.owner_id}"
                if current_owner.lower() not in query_lower:
                    return False, f"Access denied: As an owner, you can only view your own properties (LLC{user_context.owner_id}). You cannot query other owners' data."
        
        # Check for "all" or "total" queries that might span all owners
        forbidden_terms = ['all properties', 'total properties', 'entire', 'every property', 
                          'admin', 'all owners', 'everyone']
        for term in forbidden_terms:
            if term in query_lower:
                return False, f"Access denied: As an owner, you can only view your own properties. Try asking 'How many properties do I have?' instead."
        
        return True, ""
    
    @classmethod
    def validate_query(cls, sql: str) -> Tuple[bool, str]:
        """
        Validate SQL query for security issues
        Returns: (is_valid, error_message)
        """
        sql_upper = sql.upper()
        
        # Check for DML operations
        for pattern in cls.DML_PATTERNS:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return False, f"Forbidden SQL operation detected: {pattern}"
        
        # Check for SQL injection patterns
        injection_patterns = [
            r';\s*DROP',
            r'--.*DROP',
            r'/\*.*DROP.*\*/',
            r'UNION.*SELECT.*FROM',
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return False, "Potential SQL injection detected"
        
        return True, ""
    
    @classmethod
    def apply_rbac(cls, sql: str, user_context: UserContext) -> str:
        """
        Apply Role-Based Access Control to SQL query
        If user is 'owner', append WHERE clause to filter by owner_id
        """
        if user_context.role.lower() != 'owner' or user_context.owner_id is None:
            return sql
        
        # Strip trailing semicolons to prevent SQL syntax errors
        sql = sql.rstrip().rstrip(';').rstrip()
        
        # Check if query involves Properties table
        sql_upper = sql.upper()
        if 'FROM PROPERTIES' not in sql_upper and 'JOIN PROPERTIES' not in sql_upper:
            return sql
        
        # Detect table alias for Properties
        # Look for "FROM Properties AS X" or "FROM Properties X" or "JOIN Properties AS X"
        alias_match = re.search(r'\b(?:FROM|JOIN)\s+PROPERTIES\s+(?:AS\s+)?(\w+)', sql, re.IGNORECASE)
        if alias_match:
            table_ref = alias_match.group(1)
        else:
            table_ref = "Properties"
        
        # Apply owner_id filter
        owner_id = user_context.owner_id
        owner_condition = f"{table_ref}.owner_id = {owner_id}"
        
        # Find WHERE clause or add one
        where_match = re.search(r'\bWHERE\b', sql, re.IGNORECASE)
        
        if where_match:
            # Add to existing WHERE clause
            sql_parts = sql[:where_match.end()] + f" {owner_condition} AND " + sql[where_match.end():]
            return sql_parts
        else:
            # Add new WHERE clause before GROUP BY, ORDER BY, LIMIT, etc.
            terminal_clauses = [
                r'\bGROUP BY\b',
                r'\bORDER BY\b',
                r'\bLIMIT\b',
                r'\bOFFSET\b',
            ]
            
            insert_pos = len(sql)
            for clause_pattern in terminal_clauses:
                match = re.search(clause_pattern, sql, re.IGNORECASE)
                if match and match.start() < insert_pos:
                    insert_pos = match.start()
            
            # Insert WHERE clause
            sql = sql[:insert_pos].rstrip() + f" WHERE {owner_condition} " + sql[insert_pos:]
        
        return sql
    
    @classmethod
    def sanitize_error(cls, error: str) -> str:
        """Remove sensitive information from error messages"""
        # Remove file paths
        error = re.sub(r'/[^\s]+/', '[PATH]/', error)
        error = re.sub(r'[A-Z]:\\[^\s]+', '[PATH]', error)
        
        return error
