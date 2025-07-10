#!/bin/bash
set -e

if [ "$1" = "cleaninstall" ]; then
    echo "Performing clean installation..."
    sudo systemctl stop ha-management.service 2>/dev/null || true
    pkill -f "python.*run.py" 2>/dev/null || true
    rm -rf venv management.db
fi

# Basic Ubuntu install script for HA-Management

# update package list and install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip sqlite3

# create python virtual environment if not existing
if [ ! -d venv ]; then
    python3 -m venv venv
fi

# activate venv and install requirements
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# initialize the database and create the admin user
python run.py init

echo "Setup complete. You can now run the server with: source venv/bin/activate && python run.py"
