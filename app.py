"""
Streamlit Web UI for Property Management Chatbot
"""
import os
import sys
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

from agent import PropertyManagementAgent, UserContext, DatabaseManager


# Load environment variables from .env file in current directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_welcome_message(role: str, owner_id: int = None) -> str:
    """Generate personalized welcome message based on role"""
    if role == "admin":
        return """👋 **Welcome, Administrator!**

You have **full access** to all property data. You can:
- ✅ View all properties across all owners
- ✅ Get detailed property information and addresses
- ✅ Query any owner's data (LLC1-LLC5)
- ✅ Access financial data (rent, profitability, etc.)
- ✅ View aggregate statistics

**Example questions:**
- "How many total properties are in the database?"
- "What is the most profitable property?"
- "List all properties in Arizona"
- "What's the average rent across all properties?"
"""
    elif role == "owner":
        owner_name = f"LLC{owner_id}" if owner_id else "Owner"
        return f"""👋 **Welcome, {owner_name}!**

You have access to **your properties only**. You can:
- ✅ View your properties and their details
- ✅ Get counts and statistics for your portfolio
- ✅ Query rent and profitability of your properties
- ❌ Cannot view other owners' detailed property information

**Example questions:**
- "How many properties do I have?"
- "What is my most profitable property?"
- "What's my average rent?"
- "List my properties in California"

*Note: All queries are automatically filtered to show only your properties.*
"""
    else:  # viewer
        return """👋 **Welcome, Viewer!**

You have **read-only access to aggregated data**. You can:
- ✅ View property counts and totals
- ✅ Get average statistics (rent, etc.)
- ✅ Query aggregate data by location or type
- ❌ Cannot view specific property addresses
- ❌ Cannot view detailed owner information

**Example questions:**
- "How many properties are in the database?"
- "What's the average rent across all properties?"
- "How many properties are in Texas?"
- "What's the total count by state?"

*Note: You can only access summarized data, not individual property details.*
"""


@st.cache_resource
def initialize_agent():
    """Initialize agent (cached)"""
    db_path = os.getenv("DATABASE_PATH", "property_management.db")
    if not Path(db_path).exists():
        st.error(f"Database not found: {db_path}")
        st.info("Please run: `python scripts/generate_mock_db.py`")
        st.stop()
    
    if not os.getenv("GOOGLE_API_KEY"):
        st.error("GOOGLE_API_KEY not found in environment")
        st.info("Please run: `python scripts/setup_env.py`")
        st.stop()
    
    try:
        db_manager = DatabaseManager(db_path)
        max_retries = int(os.getenv("MAX_RETRIES", "3"))
        agent = PropertyManagementAgent(db_manager, max_retries)
        return agent
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Property Management Chatbot",
        page_icon="🏠",
        layout="wide"
    )
    
    # Header
    st.title("🏠 Property Management Chatbot")
    st.markdown("---")
    
    # Initialize agent
    agent = initialize_agent()
    
    # Sidebar - User authentication
    with st.sidebar:
        st.header("🔐 Authentication")
        
        st.info("🔒 All users have READ-ONLY access. No data modifications allowed.")
        
        # Step 1: Role selection
        st.subheader("Step 1: Select Role")
        selected_role = st.radio(
            "Choose your role:",
            ["admin", "owner", "viewer"],
            help="Select the role you want to log in as",
            format_func=lambda x: {
                "admin": "👤 Administrator",
                "owner": "🏢 Property Owner",
                "viewer": "👁️ Viewer"
            }[x]
        )
        
        # Owner selection (if role is owner)
        selected_owner = None
        if selected_role == "owner":
            selected_owner = st.selectbox(
                "Select Owner:",
                ["LLC1", "LLC2", "LLC3", "LLC4", "LLC5"],
                help="Choose which property owner you are"
            )
        
        st.markdown("---")
        
        # Step 2: Password input with role-specific hint
        st.subheader("Step 2: Enter Password")
        
        # Show password hint based on selected role
        if selected_role == "admin":
            password_hint = "Password: `admin`"
        elif selected_role == "owner" and selected_owner:
            password_hint = f"Password: `{selected_owner.lower()}`"
        else:
            password_hint = "Password: `viewer`"
        
        st.caption(password_hint)
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder=f"Enter password for {selected_role}"
        )
        
        # Validate password matches selected role
        role = None
        owner_id = None
        user_id = None
        
        if password:
            password_lower = password.lower().strip()
            
            # Validate based on selected role
            if selected_role == "admin":
                if password_lower == "admin":
                    role = "admin"
                    user_id = 999
                    owner_id = None
                    st.success(f"✅ Authenticated as: ADMIN")
                else:
                    st.error(f"❌ Incorrect password for admin")
                    st.stop()
                    
            elif selected_role == "owner":
                expected_password = selected_owner.lower() if selected_owner else ""
                if password_lower == expected_password:
                    role = "owner"
                    owner_id = int(selected_owner[-1])
                    user_id = owner_id
                    st.success(f"✅ Authenticated as: OWNER ({selected_owner})")
                else:
                    st.error(f"❌ Incorrect password for {selected_owner}")
                    st.stop()
                    
            elif selected_role == "viewer":
                if password_lower == "viewer":
                    role = "viewer"
                    user_id = 998
                    owner_id = None
                    st.success(f"✅ Authenticated as: VIEWER")
                else:
                    st.error(f"❌ Incorrect password for viewer")
                    st.stop()
        else:
            st.warning("⚠️ Please enter password to continue")
            st.info("🔐 **Authentication Required**\n\nPlease enter your password in the sidebar to access the chatbot.")
            st.stop()
        
        st.markdown("---")
        st.header("ℹ️ About")
        st.markdown("""
        This chatbot uses:
        - **LangGraph** for agent orchestration
        - **Google Gemini** for natural language understanding
        - **SQLite** for data storage
        - **RBAC** for security
        """)
        
        st.markdown("---")
        st.header("💡 Example Questions")
        st.markdown("""
        - How many properties do I have?
        - How many active properties?
        - What is the most profitable property?
        - What is the average rent?
        - List properties in Arizona
        """)
    
    # Initialize session state for role tracking
    if "current_role" not in st.session_state:
        st.session_state.current_role = None
    if "current_owner_id" not in st.session_state:
        st.session_state.current_owner_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Detect role change and clear conversation history
    role_changed = (
        st.session_state.current_role != role or 
        st.session_state.current_owner_id != owner_id
    )
    
    if role_changed:
        # Clear conversation history (for both role change and first login)
        st.session_state.messages = []
        agent.clear_conversation()
        
        # Show role change notification (only if switching, not first login)
        if st.session_state.current_role is not None:
            prev_role = st.session_state.current_role
            prev_owner = f" (LLC{st.session_state.current_owner_id})" if st.session_state.current_owner_id else ""
            new_owner = f" (LLC{owner_id})" if owner_id else ""
            
            st.sidebar.success(f"✅ Switched from {prev_role}{prev_owner} to {role}{new_owner}")
            st.sidebar.info("💬 Conversation history cleared")
    
    # Update current role in session
    st.session_state.current_role = role
    st.session_state.current_owner_id = owner_id
    
    # Create user context
    user_context = UserContext(user_id=user_id, role=role, owner_id=owner_id)
    
    # Show welcome message if no conversation yet
    if len(st.session_state.messages) == 0:
        welcome_msg = get_welcome_message(role, owner_id)
        st.info(welcome_msg)
        st.markdown("---")
    
    # Display chat history
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sql" in message and st.checkbox(f"Show SQL", key=f"sql_{idx}"):
                st.code(message["sql"], language="sql")
    
    # Chat input
    if prompt := st.chat_input("Ask about your properties..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = agent.query(prompt, user_context)
            
            if response["success"]:
                st.markdown(response["answer"])
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["answer"],
                    "sql": response["sql_query"]
                })
                
                # Show SQL query in expander (if generated)
                if response["sql_query"]:
                    with st.expander("View SQL Query"):
                        st.code(response["sql_query"], language="sql")
                        if response["retry_count"] > 0:
                            st.info(f"Query was refined {response['retry_count']} time(s)")
            else:
                # Show user-friendly warning instead of scary error
                st.warning(response["answer"])
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"⚠️ {response['answer']}"
                })
                
                # Show technical details if DEBUG_MODE enabled
                if os.getenv("DEBUG_MODE", "false").lower() == "true" and response.get("technical_details"):
                    with st.expander("🔍 Technical Details (Debug Mode)"):
                        st.code(response["technical_details"])


if __name__ == "__main__":
    main()
