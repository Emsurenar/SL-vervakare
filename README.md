# SL Public Transport Delay Monitor (SL-övervakare)

This project monitors specific routes in the SL (Stockholm Public Transport) system every 5 minutes using GitHub Actions. If delays or interruptions are detected, it sends an automated Telegram notification directly to your phone. 

The primary use case is documenting and obtaining proof of delays exceeding 20 minutes to claim the [SL Delay Compensation](https://sl.se/kundservice/forseningsersattning).

The script utilizes the free and open **SL Deviations API** provided by Trafiklab. It does not require an API key to run.

## Configured Routes
The script currently filters deviations affecting the following modes of transport:
- **Red Line** (13, 14)
- **Green Line** (17, 18, 19)
- **Bus 2**

*You can easily modify this by changing the `RELEVANT_LINES` array in `sl_monitor.py`.*

## Setup Instructions

### 1. Create a Telegram Bot
1. Download Telegram and search for `@BotFather`.
2. Send the command `/newbot` and follow the instructions to name your bot (e.g., `SL_Delay_Monitor`).
3. Copy the **API Token** provided by BotFather. This token is your `TELEGRAM_BOT_TOKEN`.
4. Locate your new bot in the chat list and click "Start". Send a random message to initialize the chat.
5. Search for `@userinfobot` in Telegram, click "Start", and copy your **Chat ID** (a numeric string, e.g., `12345678`). This is your `TELEGRAM_CHAT_ID`.

### 2. Configure GitHub Repository
1. Push this entire project folder (including `.github`, `sl_monitor.py`, and this `README.md`) to a new repository on your GitHub account.
2. In your GitHub repository, navigate to **Settings** -> **Secrets and variables** -> **Actions**.
3. Click **"New repository secret"** and add your Telegram credentials:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

### 3. Usage & Anti-spam mechanism
Once your repository is configured, the `.github/workflows/sl-scraper.yml` file will ensure the monitor script runs automatically every 5 minutes. 

To prevent spamming the user with repeated notifications for the same ongoing delay, the script maintains a state file (`sent_deviations.txt`). Each time a new event triggers an alarm, its unique ID is stored here, and the file is automatically pushed back to the GitHub repository. This guarantees exactly one notification per incident.

**Note:** The Telegram message includes the official timestamp and deviation ID directly from SL's internal system. This information can be directly included in your delay compensation request for fast processing.
