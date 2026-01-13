"""
Architecture Diagram Generator
==============================
Generates a visual architecture diagram from Mermaid syntax using mmdc (mermaid-cli).

Prerequisites:
    npm install -g @mermaid-js/mermaid-cli

Usage:
    python generate_architecture_diagram.py
"""

import subprocess
import sys
from pathlib import Path

MERMAID_CONTENT = """
graph TB
    Start([User Query]) --> Auth[Password Authentication<br/>Role Selection]
    
    Auth -->|Authenticated| RoleCheck{Role Change?}
    Auth -->|Failed| AuthFail([Login Failed])
    
    RoleCheck -->|Yes| ClearMem[Clear Conversation<br/>Show Welcome Message]
    RoleCheck -->|No| Memory
    
    ClearMem --> Memory[Conversation Memory<br/>Track Context & History]
    
    Memory --> Router{Query Type?}
    
    Router -->|Data Query| AuthCheck[Authorization Check<br/>RBAC Intent Validation]
    Router -->|Conversational| DirectAnswer[Direct Response<br/>No SQL needed]
    
    AuthCheck -->|Allowed| SQLGen[SQL Generation Node<br/>LLM: Gemini + Schema]
    AuthCheck -->|Denied| BlockedEnd([Access Denied])
    
    SQLGen --> SQLVal[SQL Validation Node<br/>DML + Injection Detection]
    
    SQLVal -->|Valid| RBAC[Apply RBAC Filters<br/>Strip Semicolons<br/>Detect JOIN Aliases]
    SQLVal -->|Invalid| ErrorHandler[Error Handler Node<br/>Sanitize & Log]
    
    RBAC --> SQLExec[SQL Execution Node<br/>SQLite Database]
    
    SQLExec -->|Success| AnswerGen[Answer Generation Node<br/>LLM: Gemini]
    SQLExec -->|Error| ErrorHandler
    
    ErrorHandler --> RetryCheck{Retry Count<br/>< MAX_RETRIES?}
    RetryCheck -->|Yes| SQLGen
    RetryCheck -->|No| GracefulError[Graceful Error Handler<br/>User-Friendly Message]
    
    GracefulError --> FailEnd([Error Response])
    
    AnswerGen --> AnswerVal[Answer Validation Node<br/>Hallucination Detection<br/>Filter Street Addresses]
    
    AnswerVal -->|High Confidence| SaveMemory[Save to Memory<br/>Extract Context]
    AnswerVal -->|Low Confidence < 25%| WarnUser[Add Warning<br/>Show Confidence Score]
    
    WarnUser --> SaveMemory
    
    SaveMemory --> FinalAnswer([Final Answer])
    DirectAnswer --> FinalAnswer
    BlockedEnd --> UserResponse([Return to User])
    FailEnd --> UserResponse
    FinalAnswer --> UserResponse
    AuthFail --> UserResponse
    
    style Auth fill:#e3f2fd,stroke:#1565c0,stroke-width:3px
    style Memory fill:#e1f5fe,stroke:#01579b,stroke-width:3px
    style AnswerVal fill:#fff3e0,stroke:#e65100,stroke-width:3px
    style AuthCheck fill:#ffebee,stroke:#c62828,stroke-width:3px
    style SQLVal fill:#ffebee,stroke:#c62828,stroke-width:3px
    style RBAC fill:#fce4ec,stroke:#c2185b,stroke-width:3px
    style SQLGen fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style AnswerGen fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style ErrorHandler fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    style GracefulError fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style SaveMemory fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style ClearMem fill:#f1f8e9,stroke:#558b2f,stroke-width:2px
    style UserResponse fill:#e0f2f1,stroke:#00695c,stroke-width:4px
    style Start fill:#e0f2f1,stroke:#00695c,stroke-width:4px
"""

def check_mermaid_cli():
    """Check if mermaid-cli is installed"""
    try:
        result = subprocess.run(
            ["mmdc", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print(f"[OK] Mermaid CLI found: {result.stdout.strip()}")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    return False

def install_instructions():
    """Print installation instructions"""
    print("\n" + "="*70)
    print("Mermaid CLI Not Found")
    print("="*70)
    print("\nTo generate the architecture diagram, you need to install mermaid-cli:")
    print("\n1. Install Node.js from https://nodejs.org/")
    print("\n2. Install mermaid-cli:")
    print("   npm install -g @mermaid-js/mermaid-cli")
    print("\n3. Re-run this script:")
    print("   python generate_architecture_diagram.py")
    print("\n" + "="*70)
    print()

def generate_diagram():
    """Generate diagram from Mermaid syntax"""
    # Check if mermaid-cli is available
    if not check_mermaid_cli():
        install_instructions()
        
        # Try alternative: create HTML file with Mermaid
        print("Creating HTML alternative instead...")
        create_html_alternative()
        return
    
    # Create temp mermaid file
    mermaid_file = Path("docs/architecture_diagram.mmd")
    output_file = Path("docs/architecture_diagram.png")
    
    # Write mermaid content
    with open(mermaid_file, 'w') as f:
        f.write(MERMAID_CONTENT.strip())
    
    print(f"\n[OK] Created {mermaid_file}")
    
    # Generate PNG
    print(f"\nGenerating diagram...")
    try:
        result = subprocess.run(
            [
                "mmdc",
                "-i", str(mermaid_file),
                "-o", str(output_file),
                "-t", "default",
                "-b", "white"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"[OK] Generated {output_file}")
            print(f"\n[OK] Architecture diagram created successfully!")
            print(f"\nView the diagram: {output_file}")
        else:
            print(f"[ERROR] Error generating diagram:")
            print(result.stderr)
            create_html_alternative()
    
    except subprocess.TimeoutExpired:
        print("[ERROR] Diagram generation timed out")
        create_html_alternative()
    
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        create_html_alternative()

def create_html_alternative():
    """Create HTML file with embedded Mermaid diagram"""
    html_file = Path("docs/architecture_diagram.html")
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Property Management Chatbot - Architecture</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 20px auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        .mermaid {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .instructions {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 4px;
            padding: 15px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <h1>🏠 Property Management Chatbot - System Architecture</h1>
    
    <div class="instructions">
        <strong>📝 Note:</strong> This is an interactive HTML version of the architecture diagram.
        To generate a PNG image, install mermaid-cli:
        <code>npm install -g @mermaid-js/mermaid-cli</code>
    </div>
    
    <div class="mermaid">
{MERMAID_CONTENT.strip()}
    </div>
    
    <div style="background: #f8f9fa; padding: 20px; margin-top: 30px; border-radius: 8px;">
        <h3 style="color: #333; margin-top: 0;">Key Components:</h3>
        <ul style="color: #555;">
            <li><strong>Password Authentication:</strong> Role-based login (admin/owner/viewer)</li>
            <li><strong>Conversation Memory:</strong> Tracks context and history (last 10 turns)</li>
            <li><strong>RBAC Filters:</strong> Strips semicolons, detects JOIN aliases, applies owner_id filters</li>
            <li><strong>Answer Validation:</strong> Hallucination detection with confidence scoring</li>
            <li><strong>Graceful Error Handling:</strong> User-friendly messages for API/network/DB errors</li>
            <li><strong>Self-Correction Loop:</strong> Max 3 retries with error feedback</li>
        </ul>
    </div>
    
    <p style="text-align: center; color: #666; margin-top: 20px;">
        Property Management Chatbot - Version 1.0.0
    </p>
</body>
</html>
"""
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n[OK] Created HTML alternative: {html_file}")
    print(f"\nOpen {html_file} in your browser to view the interactive diagram.")
    print(f"To generate PNG, install mermaid-cli and re-run this script.")

def main():
    """Main entry point"""
    print("="*70)
    print("Architecture Diagram Generator")
    print("="*70)
    
    # Ensure docs directory exists
    Path("docs").mkdir(exist_ok=True)
    
    # Generate diagram
    generate_diagram()
    
    print("\n" + "="*70)
    print("Done!")
    print("="*70)
    print()

if __name__ == "__main__":
    main()
