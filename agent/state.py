"""
Agent State Management
Defines the TypedDict state for LangGraph agent
"""
from typing import TypedDict, List, Optional, Dict, Any
from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """User context for RBAC"""
    user_id: int = Field(description="Unique user identifier")
    role: str = Field(description="User role (owner, admin, viewer)")
    owner_id: Optional[int] = Field(default=None, description="Owner ID for 'owner' role")


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: List[Dict[str, str]]  # Chat history
    user_context: UserContext  # User context for RBAC
    user_query: str  # Current user question
    sql_query: Optional[str]  # Generated SQL query
    sql_result: Optional[Any]  # Query execution result
    final_answer: Optional[str]  # Natural language answer
    retry_count: int  # Number of retry attempts
    error_log: List[str]  # List of errors encountered
    schema_metadata: Dict[str, Any]  # Database schema information
    validation_passed: bool  # Whether answer validation passed
    confidence_score: float  # Confidence score (0.0 to 1.0)
