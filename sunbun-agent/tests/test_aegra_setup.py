"""
SunBun Aegra Setup Validation Script
Checks infrastructure, environment, and dependencies before implementation.
"""

from pathlib import Path
import sys
import os

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_status(message, status="info"):
    """Print colored status messages"""
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}
    color = colors.get(status, RESET)
    icon = {"success": "[SUCCESS]", "error": "[ERROR]", "warning": "[WARNING]", "info": "[INFO]"}
    
    # Use standard characters for cross-platform compatibility
    try:
        # If terminal supports emojis, try to print them
        real_icon = {"success": "✓", "error": "✗", "warning": "!", "info": "i"}[status]
        print(f"{color}{real_icon} {message}{RESET}")
    except UnicodeEncodeError:
        # Fallback to plain text ascii
        print(f"{color}{icon[status]} {message}{RESET}")

def check_python_version():
    """Verify Python 3.10+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", "success")
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} (requires 3.10+)", "error")
        return False

def check_required_packages():
    """Check if all required packages are installed"""
    required = {
        "aegra": "aegra",
        "langgraph": "langgraph",
        "langchain_core": "langchain-core",
        "langchain_openai": "langchain-openai",
        "psycopg": "psycopg[binary]",
        "pandas": "pandas",
        "fastapi": "fastapi"
    }
    
    all_installed = True
    for package, pip_name in required.items():
        try:
            __import__(package)
            print_status(f"{package} installed", "success")
        except ImportError:
            print_status(f"{package} NOT installed (run: pip install {pip_name})", "error")
            all_installed = False
    
    return all_installed

def check_env_file():
    """Verify .env file exists and has required variables"""
    env_path = Path(".env")
    
    if not env_path.exists():
        print_status(".env file not found", "error")
        print(f"{YELLOW}Create .env with:{RESET}")
        print("""
POSTGRES_USER=sunbun_agent
POSTGRES_PASSWORD=sunbun_secret_2025
POSTGRES_DB=sunbun_week2
DATABASE_URL=postgresql://sunbun_agent:sunbun_secret_2025@localhost:5433/sunbun_week2
GOOGLE_API_KEY=your-key-here
        """)
        return False
    
    # Read and check variables
    required_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]
    env_content = env_path.read_text()
    
    missing = []
    for var in required_vars:
        if var not in env_content:
            missing.append(var)
    
    if missing:
        print_status(f".env missing: {', '.join(missing)}", "error")
        return False
    
    print_status(".env file configured", "success")
    return True

def check_aegra_json():
    """Verify aegra.json exists and is valid"""
    aegra_path = Path("aegra.json")
    
    if not aegra_path.exists():
        print_status("aegra.json not found", "error")
        print(f"{YELLOW}Create aegra.json with:{RESET}")
        print("""
{
  "dependencies": ["."],
  "graphs": {
    "agent": "./graph/graph_aegra.py:compiled_graph"
  },
  "env": ".env"
}
        """)
        return False
    
    # Try to parse JSON
    import json
    try:
        config = json.loads(aegra_path.read_text())
        
        # Check required fields
        if "graphs" not in config:
            print_status("aegra.json missing 'graphs' field", "error")
            return False
        
        if "agent" not in config["graphs"]:
            print_status("aegra.json missing 'agent' graph definition", "error")
            return False
        
        print_status(f"aegra.json valid (graph: {config['graphs']['agent']})", "success")
        return True
        
    except json.JSONDecodeError as e:
        print_status(f"aegra.json invalid JSON: {e}", "error")
        return False

def check_docker_compose():
    """Check if docker-compose.yml exists"""
    docker_path = Path("docker-compose.yml")
    
    if not docker_path.exists():
        print_status("docker-compose.yml not found (optional but recommended)", "warning")
        return True  # Not critical
    
    print_status("docker-compose.yml found", "success")
    return True

def check_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        import psycopg
        from dotenv import load_dotenv
        
        load_dotenv()
        
        db_url = os.getenv("DATABASE_URL", "postgresql://sunbun_agent:sunbun_secret_2025@localhost:5433/sunbun_week2")
        
        # Try to connect
        conn = psycopg.connect(db_url, connect_timeout=3)
        conn.close()
        
        print_status("PostgreSQL connection successful", "success")
        return True
        
    except ImportError:
        print_status("psycopg not installed (run: pip install psycopg[binary])", "error")
        return False
    except Exception as e:
        print_status(f"PostgreSQL connection failed: {e}", "error")
        print(f"{YELLOW}Start PostgreSQL with: docker-compose up -d postgres{RESET}")
        print(f"{YELLOW}Hint: Detected local postgres.exe on 5432. Using Docker mapping on 5433.{RESET}")
        return False

def check_csv_data():
    """Verify CSV data files exist"""
    data_dir = Path("data")
    
    if not data_dir.exists():
        print_status("data/ directory not found", "error")
        return False
    
    required_csvs = [
        "customers.csv",
        "sites.csv",
        "proposals.csv",
        "proposal_template.csv",
        "agent_availability.csv"
    ]
    
    missing = []
    for csv_file in required_csvs:
        if not (data_dir / csv_file).exists():
            missing.append(csv_file)
    
    if missing:
        print_status(f"Missing CSV files: {', '.join(missing)}", "error")
        return False
    
    print_status(f"All {len(required_csvs)} required CSV files found", "success")
    return True

def check_graph_structure():
    """Verify graph module structure"""
    graph_dir = Path("graph")
    
    if not graph_dir.exists():
        print_status("graph/ directory not found", "error")
        return False
    
    required_files = [
        "graph/__init__.py",
        "graph/state_aegra.py",
        "graph/graph_aegra.py",
        "graph/nodes/__init__.py",
        "graph/nodes/auth_nodes.py",
        "graph/nodes/service_nodes.py",
        "graph/nodes/sales_nodes.py"
    ]
    
    missing = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print_status(f"Missing files: {', '.join(missing)}", "warning")
        print(f"{YELLOW}These will be created during Week 2 implementation{RESET}")
        return True  # Not critical for initial setup
    
    print_status("Graph module structure complete", "success")
    return True


def main():
    """Run all validation checks"""
    # Fix Windows console encoding if needed
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
    print("\n" + "="*70)
    print(f"{BLUE}SunBun Solar Assistant - Week 2 Aegra Setup Validation{RESET}")
    print("="*70 + "\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("Environment File", check_env_file),
        ("Aegra Configuration", check_aegra_json),
        ("Docker Compose", check_docker_compose),
        ("PostgreSQL Connection", check_postgres_connection),
        ("CSV Data Files", check_csv_data),
        ("Graph Module Structure", check_graph_structure)
    ]
    
    results = {}
    for name, check_func in checks:
        print(f"\n{BLUE}Checking {name}...{RESET}")
        results[name] = check_func()
    
    # Summary
    print("\n" + "="*70)
    print(f"{BLUE}SUMMARY{RESET}")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {name}")
    
    print("\n" + "="*70)
    if passed == total:
        print(f"{GREEN}[SUCCESS] ALL CHECKS PASSED! ({passed}/{total}){RESET}")
        print(f"{GREEN}You're ready to start Week 2 implementation!{RESET}")
        return 0
    else:
        print(f"{RED}[ERROR] {total - passed} CHECK(S) FAILED ({passed}/{total}){RESET}")
        print(f"{YELLOW}Fix the issues above before proceeding{RESET}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
