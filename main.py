"""
CLI Interface for Property Management Chatbot
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from colorama import init, Fore, Style
import getpass

from agent import PropertyManagementAgent, UserContext, DatabaseManager


# Initialize colorama for Windows support
init()


def print_header():
    """Print application header"""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}Property Management Chatbot")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")


def print_error(message: str):
    """Print error message"""
    print(f"{Fore.RED}[X] {message}{Style.RESET_ALL}")


def print_success(message: str):
    """Print success message"""
    print(f"{Fore.GREEN}[OK] {message}{Style.RESET_ALL}")


def print_info(message: str):
    """Print info message"""
    print(f"{Fore.YELLOW}[i] {message}{Style.RESET_ALL}")


def print_help():
    """Print help message with example questions"""
    print(f"\n{Fore.YELLOW}Example Questions:{Style.RESET_ALL}")
    print("  - How many properties do I have?")
    print("  - How many active properties do I have?")
    print("  - What is the most profitable property that I own?")
    print("  - What is the average rent I received?")
    print("  - List all properties in Arizona")
    print("  - Show me units with 3 bedrooms")
    print()


def print_welcome_message(role: str, owner_id: int = None):
    """Print role-specific welcome message"""
    print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}")
    
    if role == "admin":
        print(f"{Fore.GREEN}Welcome, Administrator!{Style.RESET_ALL}")
        print("\nYou have FULL ACCESS to all property data.")
        print("\nWhat you can do:")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} View all properties across all owners")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} Get detailed property information")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} Query any owner's data (LLC1-LLC5)")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} Access financial data")
        print("\nExample questions:")
        print("  - How many total properties are in the database?")
        print("  - What is the most profitable property?")
        print("  - List all properties in Arizona")
        
    elif role == "owner":
        owner_name = f"LLC{owner_id}" if owner_id else "Owner"
        print(f"{Fore.GREEN}Welcome, {owner_name}!{Style.RESET_ALL}")
        print("\nYou have access to YOUR PROPERTIES ONLY.")
        print("\nWhat you can do:")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} View your properties and details")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} Get counts and statistics for your portfolio")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} Query rent and profitability")
        print(f"{Fore.RED}  [X]{Style.RESET_ALL}  Cannot view other owners' properties")
        print("\nExample questions:")
        print("  - How many properties do I have?")
        print("  - What is my most profitable property?")
        print("  - What's my average rent?")
        
    else:  # viewer
        print(f"{Fore.GREEN}Welcome, Viewer!{Style.RESET_ALL}")
        print("\nYou have access to AGGREGATED DATA ONLY.")
        print("\nWhat you can do:")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} View property counts and totals")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} Get average statistics")
        print(f"{Fore.GREEN}  [OK]{Style.RESET_ALL} Query aggregate data by location")
        print(f"{Fore.RED}  [X]{Style.RESET_ALL}  Cannot view specific addresses")
        print(f"{Fore.RED}  [X]{Style.RESET_ALL}  Cannot view owner details")
        print("\nExample questions:")
        print("  - How many properties are in the database?")
        print("  - What's the average rent?")
        print("  - How many properties in Texas?")
    
    print(f"\n{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")


def select_role() -> tuple:
    """Role selection interface"""
    print(f"\n{Fore.CYAN}Role Selection{Style.RESET_ALL}")
    print("="*40)
    print()
    print("Available roles:")
    print("  1. admin   - Full access: all properties + detailed data")
    print("  2. owner   - Limited access: only YOUR properties")
    print("  3. viewer  - Summary access: aggregated data only")
    print()
    
    while True:
        role_input = input("Select role (1-3): ").strip()
        if role_input == "1":
            return "admin", None
        elif role_input == "2":
            # Owner selection
            print()
            print("Available owners:")
            for i in range(1, 6):
                print(f"  {i}. LLC{i}")
            print()
            while True:
                owner_input = input("Select owner (1-5): ").strip()
                if owner_input in ["1", "2", "3", "4", "5"]:
                    return "owner", int(owner_input)
                else:
                    print_error("Invalid selection. Please choose 1-5.")
        elif role_input == "3":
            return "viewer", None
        else:
            print_error("Invalid selection. Please choose 1, 2, or 3.")


def authenticate(role: str, owner_id: int | None) -> bool:
    """Password authentication"""
    print(f"\n{Fore.CYAN}Password Authentication{Style.RESET_ALL}")
    
    # Show expected password based on role
    if role == "admin":
        expected_password = "admin"
        hint = "admin"
    elif role == "owner":
        expected_password = f"llc{owner_id}"
        hint = f"llc{owner_id}"
    else:  # viewer
        expected_password = "viewer"
        hint = "viewer"
    
    print(f"Password hint: {hint}")
    
    attempts = 0
    while attempts < 3:
        password = getpass.getpass("Enter password: ").strip().lower()
        
        if password == expected_password:
            return True
        else:
            print_error("Incorrect password. Please try again.")
            attempts += 1
    
    print_error("Too many failed login attempts.")
    return False


def setup_user_context() -> UserContext:
    """Setup user authentication and role selection"""
    print(f"\n{Fore.CYAN}User Authentication{Style.RESET_ALL}")
    print("="*40)
    print()
    print(f"{Fore.YELLOW}NOTE:{Style.RESET_ALL} All users have READ-ONLY access. No data modifications allowed.")
    print()
    
    # Role selection
    role, owner_id = select_role()
    
    # Password authentication
    if not authenticate(role, owner_id):
        sys.exit(1)
    
    # Set user_id based on role
    if role == "admin":
        user_id = 999
    elif role == "owner":
        user_id = owner_id
    else:  # viewer
        user_id = 998
    
    print_success(f"Authenticated as: {role.upper()}" + (f" (LLC{owner_id})" if owner_id else ""))
    return UserContext(user_id=user_id, role=role, owner_id=owner_id)


def main():
    """Main CLI application"""
    # Load environment variables from .env file in current directory
    env_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=env_path)
    
    print_header()
    
    # Check database exists
    db_path = os.getenv("DATABASE_PATH", "property_management.db")
    if not Path(db_path).exists():
        print_error(f"Database not found: {db_path}")
        print_info("Please run: python scripts/generate_mock_db.py")
        sys.exit(1)
    
    # Check API key
    if not os.getenv("GOOGLE_API_KEY"):
        print_error("GOOGLE_API_KEY not found in environment")
        print_info("Please run: python scripts/setup_env.py")
        sys.exit(1)
    
    # Initialize components
    try:
        db_manager = DatabaseManager(db_path)
        max_retries = int(os.getenv("MAX_RETRIES", "3"))
        agent = PropertyManagementAgent(db_manager, max_retries)
        print_success("Agent initialized successfully\n")
    except Exception as e:
        print_error(f"Failed to initialize agent: {e}")
        sys.exit(1)
    
    # Setup user context
    user_context = setup_user_context()
    
    # Show welcome message
    print_welcome_message(user_context.role, user_context.owner_id)
    
    # Chat loop
    print()
    print("="*70)
    print("Ready to answer your questions!")
    print("Type 'quit' or 'exit' to end the session")
    print("Type 'help' for example questions")
    print("Type 'change role' to switch to a different role")
    print("="*70)
    print()
    
    while True:
        try:
            # Get user input
            user_input = input(f"{Fore.CYAN}You:{Style.RESET_ALL} ").strip()
            
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print()
                print("Goodbye!")
                break
            
            # Check for role change command
            if user_input.lower() == 'change role':
                print()
                print(f"{Fore.YELLOW}Switching roles...{Style.RESET_ALL}")
                agent.clear_conversation()
                user_context = setup_user_context()
                print_welcome_message(user_context.role, user_context.owner_id)
                print()
                print("="*70)
                print("Ready to answer your questions!")
                print("Type 'quit' or 'exit' to end the session")
                print("Type 'help' for example questions")
                print("Type 'change role' to switch to a different role")
                print("="*70)
                print()
                continue
            
            # Check for help command
            if user_input.lower() == 'help':
                print_help()
                continue
            
            # Process query
            print(f"{Fore.GREEN}Agent:{Style.RESET_ALL} ", end="", flush=True)
            response = agent.query(user_input, user_context)
            
            # Display response
            if response["success"]:
                print(response["answer"])
                print()
            else:
                # Show user-friendly warning
                print(f"{Fore.YELLOW}{response['answer']}{Style.RESET_ALL}")
                print()
                
                # Show technical details if DEBUG_MODE enabled
                if os.getenv("DEBUG_MODE", "false").lower() == "true" and response.get("technical_details"):
                    print(f"{Fore.RED}[DEBUG] {response['technical_details']}{Style.RESET_ALL}")
                    print()
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print_error(f"Unexpected error: {e}\n")


if __name__ == "__main__":
    main()
