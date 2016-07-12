## MinecraftDnsSwitcher
This program automatically updates your cloudflare dns records when your minecraft server goes offline and when it comes back up.
It can also send messages on telegram when your server goes offline and it comes back up.

### Installation

    $ pip3 install -r requirements.txt

### Creating the telegram bot
You can find all the information to create a new telegram bot here: https://core.telegram.org/bots#6-botfather

### Configuration
Open config.py and set your telegram chat id, the telegram bot token, your cloudflare email and api key, your zone id and the dns used to connect to your minecraft server.
Then add every server inside data.json