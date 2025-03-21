# Promotion!!
A discord bot that sends a message whenever a certain role is given.

---

# Setup
## Local setup
You need to create an application in the [Discord Developer Portal](https://discord.com/developers/applications). Go to the "Bot" section, scroll down to **Privileged Gateway Intents** and enable **Server Members Intent**. Download this repository.
### Windows
1. Download Python. Check the box that says "Add Python to PATH" during the installation process.
2. Unzip the file if it's zipped, then open Command Prompt and `cd` to the folder where `promotion.py` is.
3. Run `python -m venv venv`, then `venv\Scripts\activate` and `pip install --upgrade py-cord dotenv`.
4. Edit the .env file (with Notepad, for example) to include your bot's token (`DISCORD_TOKEN=YourBotsTokenHere`).
5. Run `python promotion.py
### Linux
1. Install `python` using your package manager.
2. Unzip the file if it's zipped, then `cd` to the folder where `promotion.py` is.
3. Run `python -m venv .`, then `source bin/activate` and `pip install --upgrade py-cord dotenv`.
4. Edit the .env file to include your bot's token (`DISCORD_TOKEN=YourBotsTokenHere`).
5. Run `python promotion.py`.

## Easy method (not recommended)
[Invite the bot to your server.](https://discord.com/oauth2/authorize?client_id=1349861779521404959)
You cannot change the profile picture of the bot using this method, and if too many people use it, I will have to verify the bot, which I don't really want to do, so if you can, set it up locally instead.
# Usage
Use the `/assign` command and select a role. You can select a channel. If you don't, the channel you run the command in will be used. You can type a custom message, if you don't, a default one will be used. You can insert tokens in the message to use data about the user or the role. To access a list of all tokens, use the `/help` command.

Use the `/view_assignments` to view all the assignments in a server.

Use the `/remove_assignment` command to remove assignments. The parameters and how to combine them is explained in the `/help` command.
