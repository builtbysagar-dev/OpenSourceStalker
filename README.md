# OpenSourceStalker 🕵️‍♂️💻

OpenSourceStalker is a Discord bot designed to help developers find "good first issues" and monitor repositories for new activity. Built with Python and `discord.py`.

## Features
- **🔎 Issue Hunter**: Find open-source issues to contribute to.
  - Command: `!findissue <language>` (e.g., `!findissue python`, `!findissue javascript`)
- **👀 Repo Stalker**: Get notified when a new issue is created in a repo.
  - Command: `!stalk <owner>/<repo>` (e.g., `!stalk facebook/react`)
  - Runs a background check every 10 minutes.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <your-repo-url>
    cd OpenSourceStalker
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration**:
    - Create a `.env` file in the root directory (or use the provided template).
    - Add your Discord Bot Token:
      ```env
      DISCORD_TOKEN=your_token_here
      ```

4.  **Run the Bot**:
    ```bash
    python main.py
    ```

## Tech Stack
- Python 3.10+
- `discord.py`
- `aiohttp` (for async API requests)
- `python-dotenv`

## License
MIT
