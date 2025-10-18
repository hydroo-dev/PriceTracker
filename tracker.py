# tracker.py - Simple Auto Price Tracker with Telegram Alerts

import json
import time
import requests
from datetime import datetime
from scraper import scrape_product
from config import *

def send_telegram_message(message):
    """Send alert message to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Support both single chat ID (string) and multiple chat IDs (list)
    chat_ids = TELEGRAM_CHAT_ID if isinstance(TELEGRAM_CHAT_ID, list) else [TELEGRAM_CHAT_ID]
    
    success_count = 0
    for chat_id in chat_ids:
        data = {
            "chat_id": str(chat_id),
            "text": message,
            "parse_mode": "HTML"
        }
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                success_count += 1
            else:
                print(f"⚠️  Telegram API error for {chat_id}: {response.status_code}")
        except Exception as e:
            print(f"❌ Telegram error for {chat_id}: {e}")
    
    return success_count > 0


def load_products():
    """Load tracked products from JSON database."""
    try:
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("⚠️  Database corrupted, creating new one...")
        return []


def save_products(products):
    """Save tracked products to JSON database."""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)


def add_product():
    """Add new product to tracking list."""
    products = load_products()
    
    print("\n" + "="*60)
    print("📦 ADD PRODUCT TO TRACK")
    print("="*60)
    
    url = input("\n🔗 Enter product URL: ").strip()
    if not url:
        print("❌ Invalid URL!")
        return False
    
    # Check if already tracking
    for p in products:
        if p['url'] == url:
            print("⚠️  This product is already being tracked!")
            return False
    
    # Get target price with validation
    while True:
        target = input("💰 Enter target price (in ₹): ").strip()
        try:
            target = float(target)
            if target <= 0:
                print("❌ Price must be greater than 0!")
                continue
            break
        except ValueError:
            print("❌ Invalid price! Please enter a number.")
    
    # Fetch initial product data
    print("\n🔍 Fetching product details...")
    result = scrape_product(url)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    product = {
        "url": url,
        "name": result['name'],
        "target_price": target,
        "current_price": result['price'],
        "initial_price": result['price'],
        "last_checked": datetime.now().isoformat(),
        "alert_sent": False,
        "added_on": datetime.now().isoformat()
    }
    
    products.append(product)
    save_products(products)
    
    print("\n✅ Product Added Successfully!")
    print("="*60)
    print(f"📦 Name: {result['name'][:60]}")
    print(f"💰 Current Price: ₹{result['price']}")
    print(f"🎯 Target Price: ₹{target}")
    print("="*60)
    
    return True


def check_prices():
    """Check prices for all tracked products."""
    products = load_products()
    
    if not products:
        return
    
    print("\n" + "="*60)
    print(f"🔍 CHECKING PRICES - {datetime.now().strftime('%d %b %Y, %I:%M:%S %p')}")
    print("="*60)
    
    updated = False
    summary_message = f"📊 <b>Price Check Report</b>\n{datetime.now().strftime('%d %b %Y, %I:%M %p')}\n\n"
    
    for i, product in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] {product['name'][:50]}...")
        
        result = scrape_product(product['url'])
        
        if "error" in result:
            print(f"   ❌ Error: {result['error']}")
            summary_message += f"❌ {product['name'][:30]}...\n   Error: {result['error']}\n\n"
            continue
        
        old_price = product['current_price']
        new_price = result['price']
        
        if new_price is None:
            print(f"   ⚠️  Price not found!")
            summary_message += f"⚠️ {product['name'][:30]}...\n   Price not found\n\n"
            continue
        
        product['current_price'] = new_price
        product['last_checked'] = datetime.now().isoformat()
        updated = True
        
        print(f"   💰 Current: ₹{new_price} | Target: ₹{product['target_price']}")
        
        # Price change indicator
        if old_price and new_price < old_price:
            change = old_price - new_price
            trend = f"📉 -{change:.0f}"
            print(f"   📉 Price dropped by ₹{change:.2f}")
        elif old_price and new_price > old_price:
            change = new_price - old_price
            trend = f"📈 +{change:.0f}"
            print(f"   📈 Price increased by ₹{change:.2f}")
        else:
            trend = "➡️ No change"
        
        # Add to summary message with clickable link
        summary_message += f"📦 <a href='{product['url']}'>{product['name'][:35]}...</a>\n"
        summary_message += f"   💰 ₹{new_price} (Target: ₹{product['target_price']})\n"
        summary_message += f"   {trend}\n\n"
        
        # Check if price dropped below target - SPECIAL ALERT
        if new_price <= product['target_price'] and not product['alert_sent']:
            discount = ((product['initial_price'] - new_price) / product['initial_price']) * 100
            
            special_alert = (
                f"🎉🎉🎉 <b>PRICE ALERT!</b> 🎉🎉🎉\n\n"
                f"📦 <b>{product['name']}</b>\n\n"
                f"💰 Current Price: <b>₹{new_price}</b>\n"
                f"🎯 Your Target: ₹{product['target_price']}\n"
                f"📉 Discount: {discount:.1f}% OFF\n\n"
                f"🔗 <a href='{product['url']}'>BUY NOW!</a>"
            )
            
            print(f"   🔔 Sending SPECIAL alert...")
            if send_telegram_message(special_alert):
                print(f"   ✅ Special alert sent!")
                product['alert_sent'] = True
            else:
                print(f"   ❌ Failed to send special alert")
        
        elif new_price <= product['target_price'] and product['alert_sent']:
            print(f"   ✅ Still below target (special alert already sent)")
        
        # Delay between requests
        if i < len(products):
            time.sleep(REQUEST_DELAY)
    
    if updated:
        save_products(products)
    
    # Send summary notification for this check
    print(f"\n🔔 Sending check summary to Telegram...")
    if send_telegram_message(summary_message):
        print(f"✅ Summary notification sent!")
    else:
        print(f"❌ Failed to send summary")
    
    print("\n" + "="*60)
    print("✅ PRICE CHECK COMPLETE!")
    print("="*60)


def start_monitoring():
    """Start continuous automatic monitoring."""
    products = load_products()
    
    print("\n" + "="*60)
    print("🚀 AUTO PRICE MONITORING STARTED")
    print("="*60)
    print(f"⏱️  Check Interval: Every {CHECK_INTERVAL//60} minute(s)")
    print(f"📦 Tracking: {len(products)} product(s)")
    print(f"\n💡 Press Ctrl+C to stop\n")
    print("="*60)
    
    try:
        run_count = 0
        while True:
            run_count += 1
            print(f"\n{'='*60}")
            print(f"🔄 RUN #{run_count}")
            check_prices()
            
            next_check = datetime.now().timestamp() + CHECK_INTERVAL
            next_time = datetime.fromtimestamp(next_check).strftime('%I:%M %p')
            
            print(f"\n⏳ Next check at {next_time}...")
            print("💤 Sleeping...\n")
            
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("⏹️  MONITORING STOPPED")
        print("="*60)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 E-COMMERCE PRICE TRACKER")
    print("="*60)
    
    # Check if products exist
    products = load_products()
    
    if not products:
        print("\n⚠️  No products found in database!")
        print("Let's add your first product...\n")
        
        if not add_product():
            print("\n❌ Failed to add product. Exiting...")
            exit()
        
        # Ask if want to add more
        while True:
            another = input("\n➕ Add another product? (y/n): ").strip().lower()
            if another == 'y':
                if not add_product():
                    break
            else:
                break
    else:
        print(f"\n✅ Found {len(products)} product(s) in database")
        for i, p in enumerate(products, 1):
            print(f"   {i}. {p['name'][:50]} - Target: ₹{p['target_price']}")
        
        # Ask if want to add more
        add_more = input("\n➕ Add more products? (y/n): ").strip().lower()
        if add_more == 'y':
            while True:
                if not add_product():
                    break
                another = input("\n➕ Add another? (y/n): ").strip().lower()
                if another != 'y':
                    break
    
    # Start monitoring
    print("\n" + "="*60)
    input("Press ENTER to start monitoring...")
    start_monitoring()