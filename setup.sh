#!/bin/bash
# setup.sh - Initialize virtual environment and install dependencies

set -e

echo "Setting up STATSports extraction tool..."

# Find Python executable (try python3 first, then python)
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check if it's Python 3
    PYTHON_VERSION=$(python --version 2>&1)
    if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
        PYTHON_CMD="python"
    else
        echo "ERROR: Found Python 2, but need Python 3.8+"
        echo "Please install Python 3 or try: brew install python3"
        exit 1
    fi
else
    echo "ERROR: No Python found. Please install Python 3.8+ first."
    echo "On macOS: brew install python3"
    echo "On Ubuntu: sudo apt-get install python3 python3-venv"
    exit 1
fi

echo "Found Python: $($PYTHON_CMD --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        echo "Try: $PYTHON_CMD -m pip install --user virtualenv"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Verify activation worked
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "Virtual environment activated: $VIRTUAL_ENV"

# Upgrade pip first
echo "Upgrading pip..."
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    echo "pip not found, trying to install it..."
    $PYTHON_CMD -m ensurepip --default-pip
    if [ $? -ne 0 ]; then
        echo "ERROR: Could not install pip. Try:"
        echo "  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py"
        echo "  $PYTHON_CMD get-pip.py"
        exit 1
    fi
fi

$PYTHON_CMD -m pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
$PYTHON_CMD -m pip install -r requirements.txt

echo "Setup complete. Ready to use."
echo ""
echo "To run extractions:"
echo "  ./run.sh 2024-01-01 2024-01-31"