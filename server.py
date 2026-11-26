
from http.server import SimpleHTTPRequestHandler, HTTPServer
import json
import urllib.request
import xml.etree.ElementTree as ET
import re
import html
import os
import urllib.parse

def load_env():
    try:
        with open(".env", "r") as file:
            for line in file:
                if line.startswith("FINNHUB_API_KEY="):
                    return line.strip().split("=", 1)[1]
    except FileNotFoundError:
        pass

    return ""

FINNHUB_API_KEY = load_env()
FEEDS = [
    {
        "url": "https://news.google.com/rss/search?q=US+Nonfarm+Payrolls+OR+NFP&hl=en-US&gl=US&ceid=US:en",
        "category": "Employment / NFP"
    },
    {
        "url": "https://news.google.com/rss/search?q=US+CPI+inflation+OR+consumer+prices&hl=en-US&gl=US&ceid=US:en",
        "category": "CPI / Inflation"
    },
    {
        "url": "https://news.google.com/rss/search?q=US+PPI+producer+prices&hl=en-US&gl=US&ceid=US:en",
        "category": "PPI / Producer Prices"
    }
]
def get_finnhub_news():
    if not FINNHUB_API_KEY:
        print("Finnhub API key belum terbaca")
        return []

    try:
        url = "https://finnhub.io/api/v1/news?category=general&token=" + FINNHUB_API_KEY
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))

        news = []

        keywords = (
            "federal reserve", "fed", "fomc",
            "fed rate", "interest rate", "rate hike",
            "rate cut", "inflation", "cpi",
            "core cpi", "ppi", "pce", "core pce",
            "nonfarm payroll", "nfp", "payrolls",
            "unemployment", "jobless claims",
            "treasury yield", "us yields",
            "dollar index", "us dollar", "usd",
            "gold price", "gold futures", "xauusd",
            "crude oil", "oil prices", "energy prices",
            "us economy", "us economic data",
            "tariffs", "trade war"
        )

        for item in data:
            text_news = (
                item.get("headline", "") + " " +
                item.get("summary", "")
            ).lower()

            if not any(word in text_news for word in keywords):
                continue

            news.append({
                "title": item.get("headline", ""),
                "source": item.get("source", "Finnhub"),
                "category": "US Economy",
                "description": clean_text(item.get("summary", "")),
                "url": item.get("url", ""),
                "image": item.get("image", ""),
                "date": item.get("datetime", "")
            })

        return news

    except Exception as error:
        print("Finnhub error:", error)
        return []


def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def get_rss_image(item):
    # Coba ambil gambar dari media:content
    image = item.find("{http://search.yahoo.com/mrss/}content")
    if image is not None and image.get("url"):
        return image.get("url")

    # Coba ambil gambar dari media:thumbnail
    image = item.find("{http://search.yahoo.com/mrss/}thumbnail")
    if image is not None and image.get("url"):
        return image.get("url")

    # Coba ambil gambar dari enclosure
    image = item.find("enclosure")
    if image is not None and image.get("type", "").startswith("image/"):
        return image.get("url", "")

    # Coba ambil gambar dari HTML description
    description = item.findtext("description", "")
    match = re.search(r"<img[^>]+src=[\\\"']([^\\\"']+)[\\\"']", description, re.I)
    if match:
        return html.unescape(match.group(1))

    return ""


def get_news():
    news = get_finnhub_news()

    for feed in FEEDS:
        try:
            request = urllib.request.Request(
                feed["url"],
                headers={
                    "User-Agent": "Mozilla/5.0"
                }
            )

            with urllib.request.urlopen(request, timeout=15) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)

            for item in root.findall(".//item"):
                title = item.findtext("title", "").strip()
                description = clean_text(
                    item.findtext("description", "")
                )
                link = item.findtext("link", "").strip()
                pub_date = item.findtext("pubDate", "").strip()

                if title:
                    news.append({
                        "title": title,
                        "source": "U.S. Bureau of Labor Statistics",
                        "category": feed["category"],
                        "description": description,
                        "url": link,
                        "date": pub_date
                    })

        except Exception as error:
            print("RSS error:", feed["category"], error)

    selected_news = []

    for category in [
        "CPI / Inflation",
        "PPI / Producer Prices",
        "Employment / NFP",
        "US Economy"
    ]:
        category_news = [
            x for x in news
            if x.get("category") == category
        ]

        selected_news.extend(category_news[:10])

    return selected_news

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/news":
            data = get_news()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )
            self.send_header(
                "Access-Control-Allow-Origin",
                "*"
            )
            self.end_headers()

            self.wfile.write(
                json.dumps(data).encode("utf-8")
            )

        else:
            super().do_GET()

HTTPServer(("0.0.0.0", 8001), Handler).serve_forever()

