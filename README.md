# mcp

This is a Flask application that displays daily stock market snapshots.

## Automated Setup

For a fast and easy setup, you can use the provided setup script. This script will automate the process of creating a virtual environment, installing dependencies, and creating the necessary directories and files.

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/uchenna-j-edeh/mcp.git
    cd mcp
    ```

2.  **Run the setup script:**

    ```bash
    ./setup.sh
    ```

3.  **Edit the `.env` file:**

    The setup script will create a `.env` file in the project root directory. You will need to edit this file to add your database connection string and your Financial Modeling Prep API key.

## Manual Setup (Ubuntu Server)

If you prefer to set up the application manually, you can follow these instructions.

### 1. Prerequisites

Before you begin, you will need:

*   An Ubuntu server (20.04 or later is recommended).
*   Python 3 and `pip` installed.
*   PostgreSQL installed and a database created for this application.
*   `git` installed.

### 2. Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/uchenna-j-edeh/mcp.git
    cd mcp
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required Python packages:**

    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

1.  **Set Environment Variables:**

    The application requires the following environment variables to be set:

    *   `DATABASE_URL`: The connection string for your PostgreSQL database.
    *   `FMP_API_KEY`: Your API key for the Financial Modeling Prep API.

    You can create a `.env` file in the project root directory with these variables. See the `.env.example` file for a template.

2.  **Create the Log Directory:**

    The application is configured to log to `/var/log/mcp-server-gemini-cli/app.log`. You will need to create this directory and set the appropriate permissions:

    ```bash
    sudo mkdir -p /var/log/mcp-server-gemini-cli
    sudo chown $USER:$USER /var/log/mcp-server-gemini-cli
    ```

### 4. Running with Gunicorn

For a production environment, it is recommended to use a production-ready web server like Gunicorn instead of the built-in Flask development server.

1.  **Install Gunicorn:**

    ```bash
    pip install gunicorn
    ```

2.  **Run the application with Gunicorn:**

    ```bash
    gunicorn --workers 3 --bind 0.0.0.0:5000 app:app
    ```

    This command will start Gunicorn with 3 worker processes, listening on port 5000.

### 5. Systemd Service (Recommended)

To ensure the application starts automatically on boot and is managed properly, you can run it as a systemd service.

1.  **Create a systemd service file:**

    ```bash
    sudo nano /etc/systemd/system/mcp.service
    ```

2.  **Add the following content to the file:**

    ```ini
    [Unit]
    Description=Gunicorn instance to serve mcp
    After=network.target

    [Service]
    User=<your_username>
    Group=<your_username>
    WorkingDirectory=/home/<your_username>/mcp
    EnvironmentFile=/home/<your_username>/mcp/.env
    ExecStart=/home/<your_username>/mcp/venv/bin/gunicorn --workers 3 --bind unix:mcp.sock -m 007 app:app

    [Install]
    WantedBy=multi-user.target
    ```

    **Note:** Make sure to replace `<your_username>` with your actual username and adjust the paths as necessary. The `ExecStart` path should point to the `gunicorn` executable inside your virtual environment.

3.  **Start and enable the service:**

    ```bash
    sudo systemctl start mcp
    sudo systemctl enable mcp
    ```

### 6. Firewall Configuration

If you have a firewall enabled, you will need to open the port that the application is running on (e.g., 5000):

```bash
sudo ufw allow 5000
```