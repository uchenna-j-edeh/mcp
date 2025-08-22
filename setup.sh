#!/bin/bash

# This script automates the setup process for the mcp application.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Create and Activate Virtual Environment ---
echo "Creating and activating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# --- Install Dependencies ---
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# --- Create Log Directory ---
echo "Creating log directory..."
sudo mkdir -p /var/log/mcp-server-gemini-cli
sudo chown $USER:$USER /var/log/mcp-server-gemini-cli

# --- Create .env File ---
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "*****************************************************************"
    echo "*** .env file created. Please edit it to add your secret keys. ***"
    echo "*****************************************************************"
else
    echo ".env file already exists."
fi

echo "
Setup complete. To run the application, use the following command:

gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
"