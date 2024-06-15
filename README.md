# ProgrammingPartyDiscordBot
Bot made for discord programming party bot

## Setup:
1. Clone the repository
   - Do `git clone` in the terminal
2. Run Docker.
   - `docker-compose up -d` to start the database
3. Install all python dependencies
   - `pip install -r requirements.txt`
4. Create a `.env` file in the root directory and add the following
    - `DISCORD_TOKEN=YOUR_DISCORD_BOT_TOKEN`
5. Run the bot
    - `python bot.py`