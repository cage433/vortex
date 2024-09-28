from env import AIRTABLE_TOKEN, VORTEX_DATABASE_ID
import requests
import logging

if __name__ == '__main__':
    # requests.packages.urllib3.util.connection.HAS_IPV6 = False
    import http.client
    http.client.HTTPConnection.debuglevel = 1

    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    r = requests.get(
        f"https://api.airtable.com/v0/{VORTEX_DATABASE_ID}/Contracts",
        headers={"Authorization": f"Bearer {AIRTABLE_TOKEN}"},
        stream=True,
    )
