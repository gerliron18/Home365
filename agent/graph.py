"""
LangGraph Agent Implementation
ReAct pattern with self-correction loop
"""
import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .state import AgentState, UserContext
from .security import SecurityValidator
from .database import DatabaseManager
from .validation import AnswerValidator
from .memory import ConversationMemory


class PropertyManagementAgent:
    """ReAct agent for property management queries"""
    
    def __init__(self, db_manager: DatabaseManager, max_retries: int = 3):
        self.db_manager = db_manager
        self.max_retries = max_retries
        self.security_validator = SecurityValidator()
        self.answer_validator = AnswerValidator()
        self.memory = ConversationMemory(max_history=10)
        
        # Initialize LLM
        api_key = os.getenv("GOOGLE_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key,
            temperature=0.1,
            convert_system_message_to_human=True
        )
        
        # Build graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("generate_sql", self._generate_sql_node)
        workflow.add_node("validate_sql", self._validate_sql_node)
        workflow.add_node("execute_sql", self._execute_sql_node)
        workflow.add_node("handle_error", self._handle_error_node)
        workflow.add_node("generate_answer", self._generate_answer_node)
        
        # Define edges
        workflow.set_entry_point("generate_sql")
        workflow.add_conditional_edges(
            "generate_sql",
            self._sql_generation_router,
            {
                "validate": "validate_sql",
                "blocked": END
            }
        )
        workflow.add_conditional_edges(
            "validate_sql",
            self._validation_router,
            {
                "execute": "execute_sql",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "execute_sql",
            self._execution_router,
            {
                "success": "generate_answer",
                "error": "handle_error"
            }
        )
        workflow.add_conditional_edges(
            "handle_error",
            self._error_router,
            {
                "retry": "generate_sql",
                "fail": END
            }
        )
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()
    
    def _generate_sql_node(self, state: AgentState) -> AgentState:
        """Node: Generate SQL query from natural language"""
        # Check if this is a data query or general conversation (only on first attempt)
        if state["retry_count"] == 0:
            is_data_query, conversational_response = self.security_validator.is_data_query(state["user_query"])
            
            if not is_data_query:
                # Handle conversational query without SQL
                state["final_answer"] = conversational_response
                return state
        
        # Validate query intent for authorization (for owners)
        is_allowed, error_msg = self.security_validator.validate_query_intent(
            state["user_query"], 
            state["user_context"]
        )
        
        if not is_allowed:
            state["error_log"].append(f"Authorization error: {error_msg}")
            state["final_answer"] = error_msg
            return state
        
        schema_desc = self.db_manager.get_schema_description()
        
        system_prompt = f"""You are an expert SQL query generator for a property management database.

Database Schema:
{schema_desc}

CRITICAL SECURITY RULES:
1. ONLY generate SELECT queries - NEVER use INSERT, UPDATE, DELETE, DROP, or any data modification
2. Use proper JOIN clauses to connect related tables
3. Always use table aliases for clarity
4. For questions about "active" properties, use the is_active = 1 condition
5. For profitability calculations, consider monthly_rent as income indicator

IMPORTANT GUIDELINES:
- For counting properties, use COUNT(DISTINCT property_id)
- For average rent, use AVG(monthly_rent) from Units table
- When asked about "properties I have" or "my properties", the system will handle owner filtering
- Join Properties and Units tables when calculating rent-based metrics
- Join Properties and Owners when filtering by owner/holding company name
- ONLY add location/state filters if explicitly mentioned in the current question
- Do NOT assume location context from previous queries unless clearly referenced
- "out of [location]" means EXCLUDE that location (use NOT or !=)

Return ONLY the SQL query, nothing else. No explanations, no markdown, just raw SQL.
"""
        
        # Add error context if this is a retry
        error_context = ""
        if state["retry_count"] > 0 and state["error_log"]:
            last_error = state["error_log"][-1]
            error_context = f"\n\nPREVIOUS ATTEMPT FAILED with error:\n{last_error}\n\nPlease correct the SQL query to fix this error."
        
        user_message = f"""Generate a SQL query to answer this question: {state['user_query']}

{error_context}

SQL Query:"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        sql_query = response.content.strip()
        
        # Clean up SQL query (remove markdown if present)
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        state["sql_query"] = sql_query
        state["messages"].append({
            "role": "assistant",
            "content": f"Generated SQL: {sql_query}"
        })
        
        return state
    
    def _validate_sql_node(self, state: AgentState) -> AgentState:
        """Node: Validate SQL query for security"""
        sql = state["sql_query"]
        
        # Security validation
        is_valid, error_msg = self.security_validator.validate_query(sql)
        
        if not is_valid:
            state["error_log"].append(f"Security validation failed: {error_msg}")
            return state
        
        # Apply RBAC
        sql = self.security_validator.apply_rbac(sql, state["user_context"])
        state["sql_query"] = sql
        
        return state
    
    def _execute_sql_node(self, state: AgentState) -> AgentState:
        """Node: Execute SQL query"""
        sql = state["sql_query"]
        
        success, result, error = self.db_manager.execute_query(sql)
        
        if success:
            state["sql_result"] = result
            state["messages"].append({
                "role": "system",
                "content": f"Query executed successfully. Rows returned: {len(result)}"
            })
        else:
            sanitized_error = self.security_validator.sanitize_error(error)
            state["error_log"].append(f"SQL execution error: {sanitized_error}")
        
        return state
    
    def _handle_error_node(self, state: AgentState) -> AgentState:
        """Node: Handle errors and prepare for retry"""
        state["retry_count"] += 1
        return state
    
    def _generate_answer_node(self, state: AgentState) -> AgentState:
        """Node: Generate natural language answer from SQL results"""
        result_df = state["sql_result"]
        
        # Format result for LLM
        if result_df.empty:
            result_summary = "No results found."
        elif len(result_df) == 1 and len(result_df.columns) == 1:
            # Single value result
            result_summary = f"Result: {result_df.iloc[0, 0]}"
        elif len(result_df) <= 10:
            # Small result set - show all
            result_summary = result_df.to_string(index=False)
        else:
            # Large result set - show summary
            result_summary = f"Found {len(result_df)} results. First 5:\n{result_df.head().to_string(index=False)}"
        
        # Add conversation context to system prompt
        context_prompt = self.memory.get_context_prompt()
        context_section = f"\n\n{context_prompt}" if context_prompt else ""
        
        system_prompt = f"""You are a helpful property management assistant. 
        
Convert the SQL query results into a clear, natural language answer.
Be concise but informative. Format numbers appropriately (e.g., currency with $, counts as integers).

IMPORTANT: Base your answer ONLY on the SQL results provided, not on conversation context.{context_section}
"""
        
        user_message = f"""Question: {state['user_query']}

SQL Query: {state['sql_query']}

Results:
{result_summary}

Please provide a natural language answer to the question based on these results."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message)
        ]
        
        response = self.llm.invoke(messages)
        llm_answer = response.content.strip()
        
        # VALIDATE ANSWER against SQL results
        # Convert DataFrame to list of tuples for validation
        sql_result_list = result_df.values.tolist() if not result_df.empty else []
        
        # First validate without formatting to check if valid
        is_valid, warning, confidence = self.answer_validator.validate_answer(
            sql_result_list,
            llm_answer,
            tolerance=0.02
        )
        
        # Then format with validation results
        validated_answer = self.answer_validator.format_validated_answer(
            llm_answer,
            is_valid,
            warning,
            confidence,
            sql_result_list if not is_valid else None  # Show raw results if validation fails
        )
        
        state["final_answer"] = validated_answer
        state["validation_passed"] = is_valid
        state["confidence_score"] = confidence
        
        return state
    
    def _sql_generation_router(self, state: AgentState) -> str:
        """Route after SQL generation - check if blocked by auth or conversational"""
        if state["final_answer"]:
            # Either access denied or conversational response - skip to end
            return "blocked"
        return "validate"
    
    def _validation_router(self, state: AgentState) -> str:
        """Route after validation"""
        if state["error_log"] and state["error_log"][-1].startswith("Security validation"):
            return "error"
        return "execute"
    
    def _execution_router(self, state: AgentState) -> str:
        """Route after execution"""
        if state["sql_result"] is not None:
            return "success"
        return "error"
    
    def _error_router(self, state: AgentState) -> str:
        """Route after error handling"""
        if state["retry_count"] < self.max_retries:
            return "retry"
        return "fail"
    
    def query(self, user_query: str, user_context: UserContext) -> Dict[str, Any]:
        """
        Process a user query with error handling
        Returns: Dictionary with answer, SQL, and metadata
        """
        try:
            # Initialize state
            initial_state: AgentState = {
                "messages": [],
                "user_context": user_context,
                "user_query": user_query,
                "sql_query": None,
                "sql_result": None,
                "final_answer": None,
                "retry_count": 0,
                "error_log": [],
                "schema_metadata": self.db_manager.get_schema_metadata(),
                "validation_passed": True,
                "confidence_score": 1.0
            }
            
            # Run graph (THIS is where API calls happen - 2-3 calls total)
            final_state = self.graph.invoke(initial_state)
            
            # Save interaction to memory
            self.memory.add_interaction(
                query=user_query,
                sql_query=final_state["sql_query"],
                result=final_state["sql_result"],
                answer=final_state["final_answer"] or ""
            )
            
            # Prepare response
            response = {
                "success": final_state["final_answer"] is not None,
                "answer": final_state["final_answer"] or "I apologize, but I couldn't generate an answer. Please try rephrasing your question.",
                "sql_query": final_state["sql_query"],
                "retry_count": final_state["retry_count"],
                "errors": final_state["error_log"],
                "validation_passed": final_state.get("validation_passed", True),
                "confidence": final_state.get("confidence_score", 1.0)
            }
            
            return response
            
        except Exception as e:
            # Graceful error handling - NO additional API calls here
            return self._handle_query_error(e, user_query)
    
    def _handle_query_error(self, error: Exception, user_query: str) -> Dict[str, Any]:
        """Handle errors with user-friendly messages (NO API calls)"""
        error_msg = str(error)
        
        # API Quota
        if "RESOURCE_EXHAUSTED" in error_msg or "429" in error_msg or "quota" in error_msg.lower():
            friendly_msg = "I've reached my API usage limit. Please try again in a minute or contact your administrator for a higher quota tier."
            error_type = "API_QUOTA"
        # API Key
        elif "API_KEY" in error_msg or "authentication" in error_msg.lower() or "401" in error_msg:
            friendly_msg = "I'm having trouble connecting to my AI service. Please contact your administrator to verify the API key configuration."
            error_type = "API_AUTH"
        # Network
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            friendly_msg = "I'm having trouble connecting to my AI service. Please check your internet connection and try again in a moment."
            error_type = "NETWORK"
        # Database
        elif "database" in error_msg.lower() or "sqlite" in error_msg.lower():
            friendly_msg = "I'm having trouble accessing the database. Please ensure the database file exists."
            error_type = "DATABASE"
        # Generic
        else:
            friendly_msg = f"I encountered an unexpected error while processing your question. Please try rephrasing or contact your administrator."
            error_type = "GENERAL"
        
        return {
            "success": False,
            "answer": friendly_msg,
            "sql_query": None,
            "retry_count": 0,
            "errors": [error_type],
            "validation_passed": True,
            "confidence": 0.0,
            "error_type": error_type,
            "technical_details": error_msg if os.getenv("DEBUG_MODE", "false").lower() == "true" else None
        }
    
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation memory statistics"""
        return self.memory.get_statistics()
    
    def clear_conversation(self) -> None:
        """Clear conversation memory"""
        self.memory.clear_history()
