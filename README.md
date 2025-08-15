# Calendar and Notion Sync Tool

This repository contains a set of productivity tools to manage your schedule. It includes a web application (built with Flask) for local calendar management and a command-line tool to sync with Notion.

## Features

1.  **Flask Web Application**
    *   Add/manage calendar events and tasks in a local `calendar.json` file.
    *   Generate and download printable monthly or weekly calendars in PDF and DOCX formats.
    *   Provides instructions for using the command-line tools.

2.  **Notion Sync (CLI Tool)**
    *   Syncs events from a calendar (via an `.ics` link) to a Notion database.
    *   Creates study plans in Notion based on your schedule.
    *   Implements a spaced repetition schedule for studying.
    *   Generates weekly review pages in Notion.

## Installation

This project uses Conda/Mamba for environment management.

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create the Conda environment:**
    Use `mamba` (recommended for faster dependency resolution) or `conda` to create the environment.
    ```bash
    # For regular use
    mamba env create -f environment.yml -n calendar

    # For development (includes testing/linting tools)
    mamba env create -f environment.dev.yml -n notion_calendar_sync-dev
    ```
    You can also use the `make setup` command which does the same as the first command.

3.  **Activate the environment:**
    ```bash
    conda activate calendar
    # or for development:
    # conda activate notion_calendar_sync-dev
    ```

## Usage

All applications should be run from the root of the project directory.

### Flask Web App (Recommended)

The Flask app is the primary interface for the local calendar features.

1.  **Run the development server:**
    ```bash
    make run-flask
    ```
    Or run the command directly:
    ```bash
    python -m notion_calendar_sync.apps.flask.app
    ```
    Open your browser to `http://127.0.0.1:5000`.

2.  **Run in production:**
    For production use, it's recommended to use a proper WSGI server like `waitress`.
    ```bash
    make run-flask-prod
    ```

### Notion Sync CLI

The Notion-related tools are available via the command line. For instructions on how to configure your `.env` file with your Notion API keys, please see the "CLI Instructions" page in the Flask web app.

*   **Sync with Notion:**
    ```bash
    make run-cli-sync
    ```
*   **Get help on all commands:**
    ```bash
    make run-cli-help
    ```

### Legacy Tkinter App

A legacy Tkinter-based GUI is still available but is no longer the primary interface.
```bash
make run-tk
```

## Tailscale Integration (Future)

This application is designed to be easily exposed to your private Tailscale network (a "tailnet").

**Checklist for exposing the Flask app:**

*   [ ] **Install Tailscale** on the server running this application and on your client devices.
*   [ ] **Run the Flask App on `0.0.0.0`**: Set the `HOST` environment variable to `0.0.0.0` so the app is accessible from the tailnet IP.
*   [ ] **Expose the port**: Use `tailscale up --advertise-routes=...` or similar to expose the port (e.g., 5000) to your tailnet.
*   [ ] **Use HTTPS**: Use Tailscale's built-in HTTPS feature (`tailscale cert`) or a reverse proxy like Caddy to secure the connection.
*   [ ] **Authentication**: For added security, consider using Tailscale's ACLs to restrict access to specific users or groups, or add an authentication layer to the Flask app itself.
