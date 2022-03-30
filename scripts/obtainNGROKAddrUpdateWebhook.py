import requests
from requests.exceptions import HTTPError


def get_ngrok_hostname():
    url = "http://127.0.0.1:4040/api/tunnels"
    try:
        response = requests.get(url)
        url_new_https = response.json()["tunnels"][0]["public_url"]
        print(url_new_https)
        return url_new_https
    except HTTPError as e:
        print(e.response.status_code)
        return None


def update_webex_webhook(ngrokAddr):
    url = "https://webexapis.com/v1/webhooks/{webhookId}"
    data = {
        "name": "DeeDee Webhook",
        "targetUrl": ngrokAddr,
        "secret": "SECRET",
        "ownedBy": "org",
        "status": "active",
    }
    response = requests.put(url, data)
    print(response.status_code)


update_webex_webhook(get_ngrok_hostname())
