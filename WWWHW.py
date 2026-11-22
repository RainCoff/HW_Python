from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup as bs
import re
base_url ="https://drozdovn.ru/"
r = requests.get(base_url)
r.encoding = r.apparent_encoding
soup = bs(r.text, "html.parser")
for a in soup.find_all("a", href=True):
    href = a["href"]
    full = urljoin(base_url, href)
    kind = "внешняя" if href.startswith("http") else "внутренняя"
    print(f"{a.text.strip():10} {kind:10} {full}")

email_pattern = r"[\w%+-]+(?:\.[\w%+-]+)*@(?:[^\W_](?:[\w-]*[^\W_])?\.)+[^\W_](?:[\w-]*[^\W_])?"
emails = sorted(set(re.findall(email_pattern, r.text)))
print(emails)

myIp= requests.get("https://api.ipify.org?format=json")
print(myIp.json())