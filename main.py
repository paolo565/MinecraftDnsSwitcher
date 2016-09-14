import json
import time
import requests
from mcstatus import MinecraftServer
from config import *

NEXT_CLOUDFLARE_UPDATE = 0


def time_millis():
    return int(round(time.time() * 1000))


def send_telegram_message(text):
    requests.post("https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage", data={
        'chat_id': TELEGRAM_CHAT_ID,
        'text': "[MinecraftDnsSwitcher] " + text
    })


def list_cloudflare_ips(content=None):
    url = "https://api.cloudflare.com/client/v4/zones/" + ZONE_ID + "/dns_records"
    querystring = {
        "type": "A",
        "name": DNS_RECORD,
        "per_page": "100",
    }
    if content is not None:
        querystring['content'] = content

    response = requests.request("GET", url, data="{}", headers=CLOUDFLARE_API_HEADERS, params=querystring)
    resp = json.loads(response.text)
    if resp['success']:
        return resp['result']
    else:
        return None


def add_to_cloudflare(server_ip):
    print("Adding server " + server_ip + " to cloudflare")

    url = "https://api.cloudflare.com/client/v4/zones/" + ZONE_ID + "/dns_records"
    body = {
        "type": "A",
        "name": DNS_RECORD,
        "content": server_ip,
        "ttl": 120
    }
    response = requests.request("POST", url, data=json.dumps(body), headers=CLOUDFLARE_API_HEADERS)

    resp = json.loads(response.text)
    if resp['success']:
        print("Successfully added server " + server_ip + " to cloudflare")
    else:
        print("Failed adding server " + server_ip + " to cloudflare")
    return resp['success']


def remove_from_cloudflare(server_ip):
    print("Removing server " + server_ip + " from cloudflare")
    cloudflare_results = list_cloudflare_ips(server_ip)
    if cloudflare_results is not None:
        for result in cloudflare_results:
            url = "https://api.cloudflare.com/client/v4/zones/" + ZONE_ID + "/dns_records/" + result['id']

            response = requests.request("DELETE", url, data="{}", headers=CLOUDFLARE_API_HEADERS)
            resp = json.loads(response.text)
            if not resp['success']:
                print("Failed to remove server " + server_ip + " from cloudflare")
                return False
        print("Successfully removed server " + server_ip + " from cloudflare")
        return True
    print("Failed to remove server " + server_ip + " from cloudflare (dns records listing error)")
    return False


def check_all_servers():
    sent_notification = False
    with open('data.json') as data_file:
        data = json.load(data_file)

    now = time_millis()
    global NEXT_CLOUDFLARE_UPDATE
    if NEXT_CLOUDFLARE_UPDATE < now:
        print("Updating things on cloudflare")
        NEXT_CLOUDFLARE_UPDATE = now + TIME_BETWEEN_CLOUDFLARE_UPDATES
        cloudflare_ips = list_cloudflare_ips()
        if cloudflare_ips is not None:
            for server in data['servers']:
                found = False

                for cloudflare_ip in cloudflare_ips:
                    if cloudflare_ip['content'] == server['server_ip']:
                        found = True
                server['on_cloudflare'] = found

    online = 0
    online_on_cloudflare = 0
    on_cloudflare = 0
    for server in data['servers']:
        server_ip = server['server_ip']
        offline = False
        success, latency_or_error = get_latency_or_offline(server_ip)
        if not success or latency_or_error > 1500:
            if server['first_online'] is not None:
                time.sleep(5)
                success, latency_or_error = get_latency_or_offline(server_ip)
                if not success or latency_or_error > 1500:
                    offline = True
            else:
                offline = True
        server['last_latency_or_error'] = latency_or_error
        if not offline and server['first_online'] is None:
            server['first_online'] = now
        elif offline:
            server['first_online'] = None

        if not offline:
            online += 1
        if server['on_cloudflare']:
            on_cloudflare += 1
            if not offline:
                online_on_cloudflare += 1

    print("Online: " + str(online))
    print("On Cloudflare: " + str(on_cloudflare))
    print("Online on CloudFlare: " + str(online_on_cloudflare))

    for server in data['servers']:
        if server['first_online'] is None and server['on_cloudflare']:
            if on_cloudflare > 1:
                if remove_from_cloudflare(server['server_ip']):
                    sent_notification = True
                    send_telegram_message("Removed server " + server['server_ip'] +
                                          " from cloudflare, i wasn't able to ping it\nError: " +
                                          str(server['last_latency_or_error']))
                    server['on_cloudflare'] = False
                    on_cloudflare -= 1
        elif server['allow_on_cloudflare'] and not server['on_cloudflare'] and server['first_online'] is not None and\
                (online_on_cloudflare == 0 or (server['first_online'] + MINIMUM_STABILITY_TIME) < now):
            if add_to_cloudflare(server['server_ip']):
                sent_notification = True
                send_telegram_message("Added server " + server['server_ip'] + " to cloudflare, " +
                                      ("there weren't any servers online on cloudflare!" if online_on_cloudflare == 0
                                       else "it was stable for 15 minutes!"))
                server['on_cloudflare'] = True
                on_cloudflare += 1
                online_on_cloudflare += 1

    with open('data.json', 'w') as outfile:
        json.dump(data, outfile, sort_keys=True, indent=4)

    if sent_notification:
        send_telegram_message("Online Servers: " + str(online) + "\n" +
                              "Online Servers on CloudFlare: " + str(online_on_cloudflare) + "\n" +
                              "Servers on CloudFlare: " + str(on_cloudflare))


def get_latency_or_offline(server_ip):
    print("Checking server " + server_ip)
    # noinspection PyBroadException
    try:
        server = MinecraftServer(server_ip)
        # MinecraftServer.lookup(server_ip)
        latency = server.status(retries=1).latency
        print("Server " + server_ip + " is online (latency: " + str(latency) + "ms)")
        return True, latency
    except Exception as e:
        print("Server " + server_ip + " is offline " + str(e))
        return False, str(e)


while True:
    print("-------------------------------------------------------------------------")
    check_all_servers()
    time.sleep(STATUS_CHECK_DELAY)
