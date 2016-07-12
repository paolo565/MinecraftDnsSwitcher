# How frequently should we check the status of all servers?
STATUS_CHECK_DELAY = 10
# The minimum time a server needs to be online before it can be added again to cloudflare
MINIMUM_STABILITY_TIME = 1000 * 60 * 15
# How frequently should we update the list of servers on cloudflare?
TIME_BETWEEN_CLOUDFLARE_UPDATES = 1000 * 60 * 10

# The telegram chat were you want to send notifications
TELEGRAM_CHAT_ID = 0
# The api token of your telegram bot
TELEGRAM_TOKEN = "TELEGRAM_TOKEN"

# The headers required in any cloudflare api request
CLOUDFLARE_API_HEADERS = {
    # Your cloudflare api key (you can generate it at https://www.cloudflare.com/a/account/my-account)
    'x-auth-key': "CLOUDFLARE_API_KEY",
    # The email address of your cloudflare account
    'x-auth-email': "CLOUDFLARE_EMAIL_ADDRESS",
    # Do not edit
    'content-type': "application/json"
}

# The zone id on cloudflare
ZONE_ID = "CLOUDFLARE_ZONE_ID"
# The dns record used to connect to your server
DNS_RECORD = "play.example.com"
