#!/bin/bash
# Bitcoin Whale Intelligence - Startup Script

echo "Bitcoin Whale Intelligence - Starting..."

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 1. Activate virtual environment
echo "Activating virtual environment..."

# Check if venv exists in project directory
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Using venv in project directory"
elif [ -d "/Users/roman/spark_project/py11_venv_project" ]; then
    source "/Users/roman/spark_project/py11_venv_project/bin/activate"
    echo "Using venv: py11_venv_project"
elif [ -d "$HOME/.venvs/bitcoin-whale" ]; then
    source "$HOME/.venvs/bitcoin-whale/bin/activate"
    echo "Using venv in $HOME/.venvs/bitcoin-whale"
else
    echo ""
    echo "ERROR: No virtual environment found!"
    echo ""
    echo "Please create one first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# 2. Set Java Home (for Spark)
echo "Setting Java environment..."

# Try to find Java 11
if command -v /usr/libexec/java_home &> /dev/null; then
    # macOS
    export JAVA_HOME=$(/usr/libexec/java_home -v 11 2>/dev/null)
    if [ -z "$JAVA_HOME" ]; then
        export JAVA_HOME=$(/usr/libexec/java_home 2>/dev/null)
    fi
elif [ -d "/usr/lib/jvm/java-11-openjdk-amd64" ]; then
    # Ubuntu
    export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
elif [ -d "/usr/lib/jvm/java-11-openjdk" ]; then
    # Other Linux
    export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
fi

if [ -z "$JAVA_HOME" ]; then
    echo ""
    echo "WARNING: Java not found!"
    echo "PySpark requires Java 11. Please install:"
    echo "  macOS: brew install openjdk@11"
    echo "  Ubuntu: sudo apt-get install openjdk-11-jdk"
    echo ""
else
    echo "Java Home: $JAVA_HOME"
fi

# 3. Check BigQuery credentials
if [ -f .env ] && [ -f .credentials/bigquery-credentials.json ]; then
    echo "BigQuery credentials found - Ready for live data"
else
    echo ""
    echo "Info: BigQuery not configured (optional)"
    echo "Notebook will run in DEMO MODE with sample data"
    echo "For BigQuery setup see: docs/BIGQUERY_SETUP.md"
    echo ""
fi

# 4. Display environment info
echo ""
echo "Environment ready!"
echo ""
echo "Project: $PROJECT_ROOT"
echo "Python: $(python --version)"
if [ -n "$JAVA_HOME" ]; then
    echo "Java: $(java -version 2>&1 | head -n 1)"
fi
echo "Spark: $(python -c 'import pyspark; print(pyspark.__version__)' 2>/dev/null || echo 'not installed')"
echo ""
echo "Open: notebooks/01_data_exploration.ipynb to get started"
echo ""

# 5. Start Jupyter Notebook
jupyter notebook
