# mcp

This is a Flask application that displays daily stock market snapshots.

## Running in Production (Ubuntu Server)

These instructions will guide you through deploying the application on an Ubuntu server in a production environment.

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

    Here are a few ways to set these variables:

    **a) For Development: `.env` file**

    You can create a `.env` file in the project root directory:

    ```
    DATABASE_URL="postgresql://your_user:your_password@localhost/stock_app_db"
    FMP_API_KEY="YOUR_API_KEY"
    ```

    To load these variables, you can install `python-dotenv` (`pip install python-dotenv`) and add the following to the top of `app.py`:

    ```python
    from dotenv import load_dotenv
    load_dotenv()
    ```

    **Important:** Add the `.env` file to your `.gitignore` file to avoid committing secrets to your repository.

    **b) For Production: Systemd `EnvironmentFile`**

    When running the application as a systemd service, you can specify an `EnvironmentFile` in the service definition. This file should contain the environment variables in the same format as the `.env` file.

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
