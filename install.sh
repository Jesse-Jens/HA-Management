#!/bin/bash
set -e

wait_for_dpkg() {
    # wait if another apt or dpkg process is running
    while sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; do
        echo "Waiting for package manager lock..."
        sleep 5
    done
}

if [ "$1" = "cleaninstall" ]; then
    echo "Performing clean installation..."
    sudo systemctl stop ha-management.service 2>/dev/null || true
    pkill -f "python.*run.py" 2>/dev/null || true
    rm -rf venv management.db
fi

# Basic Ubuntu install script for HA-Management

# update package list and install system dependencies
wait_for_dpkg
sudo apt-get update
wait_for_dpkg
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
