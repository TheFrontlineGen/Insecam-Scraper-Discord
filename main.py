from urllib.request import urlopen, Request
import urllib.request
import re
import json
import os
import time
import ipinfo
import shlex, subprocess
import requests

webhook_url = os.environ['webhook_url']
access_token = os.environ['access_token']
handler = ipinfo.getHandler(access_token)

regex = re.compile(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})")

headers = {
    'User-Agent':
    'Mozilla/5.0 (X11; Linux x86_64) '
    'AppleWebKit/537.11 (KHTML, like Gecko) '
    'Chrome/23.0.1271.64 Safari/537.11',
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset':
    'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding':
    'none',
    'Accept-Language':
    'en-US,en;q=0.8',
    'Connection':
    'keep-alive'
}

requests_sent = 0

for i in range(1, 1000):

    if requests_sent == 30:
        print("Waiting for 1 minute...")
        time.sleep(60)
        requests_sent = 0

    reg_url = f"http://www.insecam.org/en/bynew/?page={i}"

    req = Request(url=reg_url, headers=headers)

    with urllib.request.urlopen(req) as response:
        html = response.read().decode('utf-8')

    ip_list = re.findall(regex, html)
    if ip_list:
        for ip, port in ip_list:

            details = handler.getDetails(ip)

            region_name = details.all.get("region_name", "db")
            directory = f"{region_name}"
            if not os.path.exists(directory):
                os.makedirs(directory)

            thumbnail_regex = re.compile(r'<img[^>]*?src="(.*?\.(?:jpg|jpeg|png|gif)).*?"')
            thumbnail_match = thumbnail_regex.search(html)
            if thumbnail_match:
                thumbnail_url = thumbnail_match.group(1)

                with open(f"{directory}/list.json", "a") as f:
                    data = {"ip": ip, "port": port, "geolocation": details.all, "thumbnail_url": thumbnail_url}
                    f.write(json.dumps(data) + "\n")

                embed_data = {
                    "title": f"New IP Found on insecam.org (Page {i})",
                    "description":
                    f"**IP:** [{ip}](http://{ip}:{port})\n**Port:** {port}\n**Region Name:** {region_name}\n**Geolocation Info:** {json.dumps(details.all)}",
                    "color": 16711680,
                    "image": {"url": f"{thumbnail_url}"}
                }
                data = {"embeds": [embed_data]}
                requests.post(webhook_url, json=data)

                print(f"IP Info sent to Discord for {ip}:{port}")
                requests_sent += 1
    else:
        print(f"No IP Found on page {i}")
