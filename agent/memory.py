"""
Conversation Memory Module
==========================
Tracks conversation history and context for natural follow-up queries.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class ConversationTurn:
    """Represents a single conversation turn"""
    timestamp: str
    query: str
    sql_query: Optional[str]
    result: Any
    answer: str
    context: Dict[str, str]


class ConversationMemory:
    """Manages conversation history and context tracking"""
    
    # Known location aliases
    STATE_ALIASES = {
        'california': 'California', 'ca': 'California', 'cali': 'California',
        'texas': 'Texas', 'tx': 'Texas',
        'arizona': 'Arizona', 'az': 'Arizona', 'ariz': 'Arizona',
        'florida': 'Florida', 'fl': 'Florida',
        'new york': 'New York', 'ny': 'New York',
        'illinois': 'Illinois', 'il': 'Illinois',
    }
    
    # Known property type patterns
    PROPERTY_TYPES = [
        'Single Family', 'Multi-Family', 'Commercial',
        'Residential', 'Apartment', 'Condo'
    ]
    
    def __init__(self, max_history: int = 10):
        """
        Initialize conversation memory
        
        Args:
            max_history: Maximum number of interactions to remember
        """
        self.max_history = max_history
        self.history: List[ConversationTurn] = []
        self.current_context: Dict[str, str] = {}
    
    def add_interaction(
        self,
        query: str,
        sql_query: Optional[str],
        result: Any,
        answer: str
    ) -> None:
        """
        Add a new interaction to memory
        
        Args:
            query: User query
            sql_query: Generated SQL query (if any)
            result: Query result
            answer: Bot answer
        """
        # Extract context from this interaction
        context = self._extract_context(query, sql_query or "")
        
        # Create conversation turn
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            query=query,
            sql_query=sql_query,
            result=result,
            answer=answer,
            context=context
        )
        
        # Add to history
        self.history.append(turn)
        
        # Maintain max history size
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        # Update current context
        self._update_context()
    
    def _extract_context(self, query: str, sql: str) -> Dict[str, str]:
        """
        Extract contextual entities from query and SQL
        
        Args:
            query: User query text
            sql: SQL query text
            
        Returns:
            Dictionary of context entities
        """
        context = {}
        combined_text = f"{query} {sql}".lower()
        
        # Extract locations (states, cities)
        for alias, standard in self.STATE_ALIASES.items():
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, combined_text, re.IGNORECASE):
                context['location'] = standard
                break
        
        # Extract property types
        for prop_type in self.PROPERTY_TYPES:
            if prop_type.lower() in combined_text:
                context['property_type'] = prop_type
                break
        
        # Extract topics based on keywords
        if any(word in combined_text for word in ['rent', 'rental', 'income', 'average']):
            context['topic'] = 'rent'
        elif any(word in combined_text for word in ['profit', 'profitable', 'profitability']):
            context['topic'] = 'profitability'
        elif any(word in combined_text for word in ['count', 'how many', 'number of']):
            context['topic'] = 'count'
        elif any(word in combined_text for word in ['property', 'properties']):
            context['topic'] = 'properties'
        
        # Extract owner references
        owner_match = re.search(r'\b(LLC\d+)\b', query, re.IGNORECASE)
        if owner_match:
            context['owner'] = owner_match.group(1).upper()
        
        return context
    
    def _update_context(self) -> None:
        """Update current context from recent history"""
        if not self.history:
            self.current_context = {}
            return
        
        # Merge contexts from last 3 interactions (more recent = higher priority)
        self.current_context = {}
        for turn in self.history[-3:]:
            self.current_context.update(turn.context)
    
    def get_context_prompt(self) -> str:
        """
        Generate context prompt to enhance LLM understanding
        Provides recent context to help with follow-up questions
        
        Returns:
            Formatted context string for LLM prompt
        """
        if not self.current_context or not self.history:
            return ""
        
        # Get the most recent query to check for follow-up patterns
        last_query = self.history[-1].query.lower() if self.history else ""
        
        # Check if this is a follow-up question (short query starting with "and", "also", etc.)
        is_followup = (
            len(last_query.split()) <= 5 and 
            any(last_query.startswith(word) for word in ['and ', 'also ', 'what about', 'how about'])
        )
        
        if not is_followup:
            # Not a follow-up, don't provide confusing context
            return ""
        
        parts = ["Previous query context:"]
        
        # Always include owner if available (most important for follow-ups)
        if 'owner' in self.current_context:
            parts.append(f"- Owner: {self.current_context['owner']}")
        
        # Include location only if query mentions location terms
        if 'location' in self.current_context:
            if any(word in last_query for word in ['in ', 'from ', 'out of', 'outside', 'arizona', 'california', 'texas', 'az', 'ca', 'tx']):
                parts.append(f"- Previous location: {self.current_context['location']}")
        
        # Include topic if relevant
        if 'topic' in self.current_context:
            parts.append(f"- Topic: {self.current_context['topic']}")
        
        if len(parts) > 1:  # Has context beyond header
            return "\n".join(parts)
        
        return ""
    
    def get_recent_summary(self, n: int = 3) -> str:
        """
        Get summary of recent queries
        
        Args:
            n: Number of recent interactions to include
            
        Returns:
            Formatted summary of recent conversation
        """
        if not self.history:
            return ""
        
        recent = self.history[-n:]
        lines = ["Recent questions:"]
        
        for i, turn in enumerate(recent, 1):
            # Truncate long queries
            query_preview = turn.query[:80]
            if len(turn.query) > 80:
                query_preview += "..."
            
            # Truncate long answers
            answer_preview = turn.answer[:100]
            if len(turn.answer) > 100:
                answer_preview += "..."
            
            lines.append(f"{i}. Q: {query_preview}")
            lines.append(f"   A: {answer_preview}")
        
        return "\n".join(lines)
    
    def enhance_query(self, query: str) -> str:
        """
        Enhance user query with conversation context
        
        Args:
            query: Original user query
            
        Returns:
            Enhanced query with context
        """
        # Check if query is a follow-up question
        follow_up_patterns = [
            r'^what about',
            r'^how about',
            r'^and\s+',
            r'^also\s+',
            r'^in\s+\w+\?$',  # e.g., "in Arizona?"
            r'^for\s+\w+\?$',  # e.g., "for LLC2?"
        ]
        
        is_follow_up = any(
            re.search(pattern, query.lower())
            for pattern in follow_up_patterns
        )
        
        if not is_follow_up or not self.current_context:
            return query
        
        # Enhance follow-up queries with context
        enhanced = query
        
        # If query is very short (likely a follow-up)
        if len(query.split()) <= 4 and self.current_context:
            context_parts = []
            
            # Add topic context
            if 'topic' in self.current_context:
                topic = self.current_context['topic']
                if topic not in query.lower():
                    context_parts.append(topic)
            
            # Add location only if query might be asking about different location
            location_in_query = any(
                loc.lower() in query.lower()
                for loc in self.STATE_ALIASES.keys()
            )
            
            if location_in_query and 'location' in self.current_context:
                # Query mentions a location, so don't add old location
                pass
            elif 'property' in query.lower() or 'count' in query.lower():
                # Could add property type context if relevant
                if 'property_type' in self.current_context:
                    prop_type = self.current_context['property_type']
                    if prop_type.lower() not in query.lower():
                        context_parts.append(prop_type)
            
            if context_parts:
                enhanced = f"{' '.join(context_parts)} {query}"
        
        return enhanced
    
    def clear_context(self) -> None:
        """Clear current context (start fresh conversation)"""
        self.current_context = {}
    
    def clear_history(self) -> None:
        """Clear entire conversation history"""
        self.history = []
        self.current_context = {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get conversation statistics
        
        Returns:
            Dictionary with conversation stats
        """
        if not self.history:
            return {
                'total_interactions': 0,
                'most_common_topic': None,
                'most_common_location': None,
                'current_context': self.current_context.copy()
            }
        
        # Count topics
        topics = [turn.context.get('topic') for turn in self.history if 'topic' in turn.context]
        most_common_topic = max(set(topics), key=topics.count) if topics else None
        
        # Count locations
        locations = [turn.context.get('location') for turn in self.history if 'location' in turn.context]
        most_common_location = max(set(locations), key=locations.count) if locations else None
        
        return {
            'total_interactions': len(self.history),
            'most_common_topic': most_common_topic,
            'most_common_location': most_common_location,
            'current_context': self.current_context.copy()
        }
    
    def export_history(self) -> List[Dict]:
        """
        Export conversation history as list of dictionaries
        
        Returns:
            List of conversation turns as dicts
        """
        return [asdict(turn) for turn in self.history]
