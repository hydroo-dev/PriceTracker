import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        " AppleWebKit/537.36 (KHTML, like Gecko)"
        " Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def parse_price(text):
    """Extract number from price string."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text)
    if cleaned:
        try:
            return float(cleaned)
        except:
            return None
    return None


# ------------ AMAZON ------------
def scrape_amazon(url):
    res = requests.get(url, headers=HEADERS, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "lxml")

    # Title
    title = soup.select_one("#productTitle")
    
    # Price - multiple fallbacks
    price = (
        soup.select_one(".a-price-whole") or
        soup.select_one("#priceblock_dealprice") or
        soup.select_one("#priceblock_ourprice") or
        soup.select_one(".a-offscreen") or
        soup.select_one("#corePriceDisplay_desktop_feature_div .a-price-whole")
    )

    name = title.get_text(strip=True) if title else "Unknown Product"
    price_text = price.get_text(strip=True) if price else None
    price_val = parse_price(price_text)
    
    if not price_val:
        all_prices = soup.select(".a-price .a-offscreen")
        if all_prices:
            price_val = parse_price(all_prices[0].get_text())
    
    return {"name": name, "price": price_val}


# ------------ FLIPKART ------------
def scrape_flipkart(url):
    res = requests.get(url, headers=HEADERS, timeout=15)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "lxml")

    # Title - updated selectors
    title = (
        soup.select_one("span.VU-ZEz") or
        soup.select_one("span.B_NuCI") or
        soup.select_one("h1.yhB1nd")
    )
    
    # Price - updated selectors
    price = (
        soup.select_one("div.Nx9bqj.CxhGGd") or
        soup.select_one("div._30jeq3._16Jk6d") or
        soup.select_one("div._30jeq3")
    )

    name = title.get_text(strip=True) if title else "Unknown Product"
    price_text = price.get_text(strip=True) if price else None
    price_val = parse_price(price_text)
    return {"name": name, "price": price_val}


# ------------ MAIN FUNCTION ------------
def scrape_product(url):
    """Detect site and use correct scraper."""
    try:
        if "amazon." in url:
            data = scrape_amazon(url)
        elif "flipkart." in url:
            data = scrape_flipkart(url)
        else:
            return {"error": "Unsupported site"}
        
        if not data.get("price"):
            return {"name": data.get("name"), "price": None, "warning": "Price not found"}
        
        return data
    except requests.exceptions.Timeout:
        return {"error": "Request timeout - try again"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection failed - check internet"}
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP Error {e.response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    print("📦 E-commerce Price Tracker")
    print("=" * 50)
    
    url = input("\n🔗 Enter product URL: ").strip()
    
    if not url:
        print("❌ No URL entered!")
        exit()
    
    print("\n🔍 Fetching product data...\n")
    
    result = scrape_product(url)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Product Found!")
        print("=" * 50)
        print(f"📦 Name: {result['name']}")
        
        if result['price']:
            print(f"💰 Price: ₹{result['price']}")
        else:
            print(f"💰 Price: Not found ⚠️")
        
        print("=" * 50)