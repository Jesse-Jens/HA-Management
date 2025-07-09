#!/bin/bash
set -e

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
