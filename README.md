# Beekeeler
Custom Discord server bot, originally intended as a bitrate reduction prank, now evolved into a multipurpose assistant.

Not production ready. Updated rarely, whenever we see fit for new features and have spare time.

Create an instance on replit!
[![Run on Repl.it](https://replit.com/badge/github/xveiga/beekeeler)](https://repl.it/github/xveiga/beekeeler)

## Dependencies
- `discord.py`
- `aiosqlite`
- `roman`
- `black` as code formatter, with the default options.

## Setup
1. Create a bot first, using the Discord developer dashboard. Set the scope as *Bot* and check the permission box for *Administrator*
2. Install the required modules, with `pip install -r requirements.txt`.
3. Copy the file `config.json.def` as `config.json` and paste the bot token.
4. Optionally, enter your user ID to access some privileged commands (hot module reloading). You can find it easily using the Developer Mode on the Discord client. (*Options -> Advanced -> Developer mode*, then right click on your profile, and *Copy ID*
5. Run `main.py` (`python3 main.py`).
6. Send the command `invite` via private message to the bot, it'll reply with an URL. Follow the prompts, select the desired server and confirm.