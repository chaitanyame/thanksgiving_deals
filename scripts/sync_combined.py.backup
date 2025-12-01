#!/usr/bin/env python3
"""
Combined Sync Script
Merges deals from Google Sheets with new deals from RSS feed
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import feedparser

FEED_URL = 'https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1'
DATA_DIR = Path(__file__).parent.parent / 'data'
DEALS_FILE = DATA_DIR / 'deals.json'


def normalize_link(raw_link):
    """Normalize a Slickdeals link to include sdtrk=bfsheet."""
    if not raw_link:
        return ''
    
    link = str(raw_link).strip()
    if not link:
        return ''
    
    if 'sdtrk=bfsheet' in link:
        return link
    
    if '?' in link:
        return link + '&sdtrk=bfsheet'
    else:
        return link + '?sdtrk=bfsheet'


def extract_price(title):
    """Extract the first price from a string."""
    if not title:
        return ''
    
    match = re.search(r'\$[\d,]+(?:\.\d{2})?', title)
    return match.group(0) if match else ''


def extract_deal_id(url):
    """Extract deal ID from Slickdeals URL."""
    if not url:
        return ''
    
    match = re.search(r'/f/(\d+)', url)
    if match:
        return f'slickdeals-f{match.group(1)}'
    return ''


def categorize_item(title, link):
    """Keyword-based categorization for a deal."""
    text = (str(title) + ' ' + str(link or '')).lower()
    
    def has_any(keywords):
        for kw in keywords:
            if kw.lower() in text:
                return True
        return False
    
    # === BABIES & KIDS ===
    if has_any(['kids toy', 'children toy', 'toy car', 'toy truck', 'atv', 'go kart', 
                'hoverboard', 'kids bike', 'baby toy', 'toddler toy']):
        return {'main': 'Babies & Kids', 'sub': 'Kids Toys'}
    if has_any(['baby', 'infant', 'toddler', 'diaper', 'baby food', 'formula', 
                'crib', 'stroller', 'car seat', 'baby monitor']):
        return {'main': 'Babies & Kids', 'sub': 'Baby Products'}
    
    # === VIDEO GAMES ===
    if has_any(['ps5', 'playstation 5', 'ps4', 'playstation 4', 'xbox series x',
                'xbox series s', 'xbox one', 'nintendo switch', 'switch oled']):
        return {'main': 'Video Games', 'sub': 'Video Game Consoles'}
    if has_any(['xbox game pass', 'game pass ultimate', 'playstation plus', 'ps plus',
                'ps+', 'nintendo switch online', 'ea play', 'ubisoft+']):
        return {'main': 'Video Games', 'sub': 'Video Game Memberships'}
    if has_any(['steam game', 'steam key', 'epic games store', 'origin game',
                'pc game', 'battle.net', 'gog.com']):
        return {'main': 'Video Games', 'sub': 'Computer & PC Games'}
    if has_any(['switch game', 'nintendo switch game']):
        return {'main': 'Video Games', 'sub': 'Nintendo Switch'}
    if has_any(['ps5 game', 'ps4 game']):
        return {'main': 'Video Games', 'sub': 'PlayStation'}
    if has_any(['xbox game']):
        return {'main': 'Video Games', 'sub': 'Xbox'}
    
    # === COMPUTERS ===
    if has_any(['rtx ', 'gtx ', 'rx ', 'graphics card', 'geforce', 'radeon', 'gpu']):
        return {'main': 'Computers', 'sub': "GPU's"}
    if has_any(['ssd', 'solid state drive', 'nvme', 'm.2', 'hard drive', 'hdd']):
        return {'main': 'Computers', 'sub': "SSD's & Hard Drives"}
    if has_any(['ram ', 'ddr4', 'ddr5', 'memory kit']):
        return {'main': 'Computers', 'sub': 'Memory'}
    if has_any(['laptop', 'notebook', 'chromebook', 'macbook']):
        return {'main': 'Computers', 'sub': 'Laptops'}
    if has_any(['desktop pc', 'gaming desktop', 'prebuilt pc', 'imac']):
        return {'main': 'Computers', 'sub': 'Desktop Computers'}
    if has_any(['router', 'wi-fi', 'wifi 6', 'mesh system', 'ethernet switch', 'network adapter']):
        return {'main': 'Computers', 'sub': 'Computer Networking'}
    if has_any(['printer', 'inkjet', 'laser printer', 'toner', 'ink cartridge']):
        return {'main': 'Computers', 'sub': 'Printers'}
    if has_any(['monitor', 'gaming monitor', 'curved monitor', 'ultrawide']):
        return {'main': 'Computers', 'sub': 'Monitors'}
    if has_any(['mouse', 'keyboard', 'gaming mouse', 'gaming keyboard']):
        return {'main': 'Computers', 'sub': 'Mice & Keyboards'}
    if has_any(['vpn', 'domain', 'hosting', 'web hosting']):
        return {'main': 'Computers', 'sub': "Internet, Websites & VPN's"}
    
    # === ELECTRONICS ===
    if has_any(['4k tv', 'hdr tv', 'oled tv', 'qled tv', 'uhd tv', 'smart tv']):
        return {'main': 'Electronics', 'sub': "TV's"}
    if has_any(['soundbar', 'sound bar']):
        return {'main': 'Electronics', 'sub': 'Sound Bars'}
    if has_any(['bluetooth speaker', 'smart speaker']):
        return {'main': 'Electronics', 'sub': 'Speakers'}
    if has_any(['headphones', 'earbuds', 'earphones', 'headset', 'gaming headset']):
        return {'main': 'Electronics', 'sub': 'Headphones, Headsets & Earbuds'}
    if has_any(['projector', 'home theater projector']):
        return {'main': 'Electronics', 'sub': 'Projectors'}
    if has_any(['smartwatch', 'apple watch', 'fitbit', 'wearable']):
        return {'main': 'Electronics', 'sub': 'Smart Watches & Wearables'}
    if has_any(['power bank', 'portable charger']):
        return {'main': 'Electronics', 'sub': 'Chargers & Power Banks'}
    if has_any(['ups ', 'surge protector', 'power strip']):
        return {'main': 'Electronics', 'sub': 'UPS, Surge Protectors & Powerstrips'}
    
    # === GROCERY ===
    if has_any(['paper towel', 'toilet paper', 'tissues', 'cleaning supplies', 'detergent',
                'dish soap', 'laundry', 'trash bags', 'household', 'cleaning']):
        return {'main': 'Grocery', 'sub': 'Household Goods'}
    if has_any(['chips', 'doritos', 'cheetos', 'pringles', 'snack', 'snacks',
                'trail mix', 'mixed nuts', 'almonds', 'cashews', 'pistachios']):
        return {'main': 'Grocery', 'sub': 'Snacks, Nuts & Chips'}
    if has_any(['soda', 'cola', 'sparkling water', 'energy drink', 'coffee', 'tea', 'juice']):
        return {'main': 'Grocery', 'sub': 'Drinks & Beverages'}
    if has_any(['cereal', 'oatmeal', 'granola', 'pancake mix']):
        return {'main': 'Grocery', 'sub': 'Breakfast Foods'}
    if has_any(['pasta', 'spaghetti', 'macaroni']):
        return {'main': 'Grocery', 'sub': 'Pasta'}
    if has_any(['rice', 'quinoa', 'brown rice']):
        return {'main': 'Grocery', 'sub': 'Rice & Grains'}
    if has_any(['frozen dinner', 'soup', 'canned soup', 'canned', 'microwave meal']):
        return {'main': 'Grocery', 'sub': 'Soups, Sauces, Packaged Meals & Canned Goods'}
    if has_any(['ketchup', 'mustard', 'hot sauce', 'spice', 'seasoning', 'sauce']):
        return {'main': 'Grocery', 'sub': 'Condiments & Spices'}
    
    # === HOME & HOME IMPROVEMENT ===
    if has_any(['grill', 'gas grill', 'charcoal grill', 'pellet grill', 'smoker', 'vertical smoker',
                'griddle', 'grilling', 'bbq accessories']):
        return {'main': 'Home & Home Improvement', 'sub': 'Grills & Grilling Accessories'}
    if has_any(['stove', 'oven', 'range', 'cooktop']):
        return {'main': 'Home & Home Improvement', 'sub': 'Stoves'}
    if has_any(['gardening', 'lawn mower', 'trimmer', 'outdoor equipment', 'patio furniture',
                'garden tools', 'outdoor living', 'deck', 'yard']):
        return {'main': 'Home & Home Improvement', 'sub': 'Gardening & Outdoor'}
    if has_any(['mattress', 'memory foam mattress', 'bedding', 'sheet set', 'duvet', 'comforter', 'pillow']):
        return {'main': 'Home & Home Improvement', 'sub': 'Mattresses, Sheets & Bedding'}
    if has_any(['vacuum', 'stick vac', 'robot vacuum', 'robovac', 'floor cleaner', 'steam mop']):
        return {'main': 'Home & Home Improvement', 'sub': 'Vacuums & Floor Cleaners'}
    if has_any(['air fryer', 'blender', 'toaster', 'microwave', 'coffee maker',
                'espresso machine', 'slow cooker', 'instant pot']):
        return {'main': 'Home & Home Improvement', 'sub': 'Small Appliances'}
    if has_any(['refrigerator', 'fridge', 'freezer']):
        return {'main': 'Home & Home Improvement', 'sub': 'Refrigerators & Freezers'}
    if has_any(['washer', 'washing machine', 'dryer']):
        return {'main': 'Home & Home Improvement', 'sub': 'Washers & Dryers'}
    if has_any(['sofa', 'couch', 'office chair', 'desk', 'dining table', 'bookshelf']):
        return {'main': 'Home & Home Improvement', 'sub': 'Furniture'}
    if has_any(['drill', 'saw', 'tool set', 'tool kit', 'wrench set', 'socket set']):
        return {'main': 'Home & Home Improvement', 'sub': 'Tool Sets'}
    if has_any(['ladder']):
        return {'main': 'Home & Home Improvement', 'sub': 'Ladders'}
    if has_any(['air purifier', 'space heater', 'air conditioner', 'portable ac', 'dehumidifier']):
        return {'main': 'Home & Home Improvement', 'sub': 'Air Conditioners, Heaters, Purifiers & More'}
    
    # === CLOTHING & ACCESSORIES ===
    if has_any(['sneakers', 'running shoes', 'sandals', 'boots', 'shoe', 'clogs', 'athletic shoes']):
        return {'main': 'Clothing & Accessories', 'sub': 'Shoes'}
    if has_any(['t-shirt', 'hoodie', 'jacket', 'jeans', 'pants', 'shorts', 'dress', 'sweater',
                'fleece', 'flannel', 'outerwear', 'apparel', 'clothes', 'clothing']):
        return {'main': 'Clothing & Accessories', 'sub': 'Apparel'}
    if has_any(['watch', 'chronograph']):
        return {'main': 'Clothing & Accessories', 'sub': 'Watches'}
    if has_any(['sunglasses', 'sunglass']):
        return {'main': 'Clothing & Accessories', 'sub': 'Sunglasses'}
    if has_any(['necklace', 'bracelet', 'ring', 'earring']):
        return {'main': 'Clothing & Accessories', 'sub': 'Jewelry'}
    
    # === HEALTH & BEAUTY ===
    if has_any(['vitamin', 'multivitamin', 'supplement', 'collagen', 'omega-3']):
        return {'main': 'Health & Beauty', 'sub': 'Vitamins'}
    if has_any(['protein powder', 'whey', 'casein', 'protein shake']):
        return {'main': 'Health & Beauty', 'sub': 'Protein Powder & Shakes'}
    if has_any(['shampoo', 'conditioner', 'hair care']):
        return {'main': 'Health & Beauty', 'sub': 'Shampoo & Hair Care'}
    if has_any(['toothpaste', 'toothbrush', 'mouthwash', 'oral care']):
        return {'main': 'Health & Beauty', 'sub': 'Toothpaste, Toothbrushes & Oral Care'}
    if has_any(['razor', 'shaving cream', 'shaver']):
        return {'main': 'Health & Beauty', 'sub': 'Razors & Shaving Supplies'}
    if has_any(['face cream', 'moisturizer', 'skin care', 'lotion']):
        return {'main': 'Health & Beauty', 'sub': 'Skin Care'}
    
    # === SPORTING GOODS ===
    if has_any(['gun safe', 'ammo', 'ammunition', '9mm', '.22lr', '5.56mm', 'brass', 'firearm']):
        return {'main': 'Sporting Goods', 'sub': 'Guns, Ammo & Accessories'}
    if has_any(['hunting', 'trail camera', 'camo', 'camouflage', 'hunting boots', 'deer', 'optics',
                'rifle scope', 'binoculars']):
        return {'main': 'Sporting Goods', 'sub': 'Hunting'}
    if has_any(['fishing', 'fish finder', 'fishing rod', 'fishing reel', 'tackle', 'lure']):
        return {'main': 'Sporting Goods', 'sub': 'Fishing'}
    if has_any(['golf', 'golf ball', 'golf club', 'putter', 'driver', 'iron set']):
        return {'main': 'Sporting Goods', 'sub': 'Golf'}
    if has_any(['knife', 'pocket knife', 'hunting knife', 'blade']):
        return {'main': 'Sporting Goods', 'sub': 'Knives'}
    if has_any(['basketball hoop', 'baseball bat', 'soccer ball', 'football', 'sports ball',
                'volleyball', 'tennis', 'badminton']):
        return {'main': 'Sporting Goods', 'sub': 'Sports Equipment'}
    if has_any(['yoga mat', 'resistance band', 'foam roller', 'fitness tracker', 'fitness',
                'wellness', 'pilates', 'heavy bag', 'boxing']):
        return {'main': 'Sporting Goods', 'sub': 'Fitness & Wellness'}
    if has_any(['bike', 'bicycle', 'mountain bike', 'road bike']):
        return {'main': 'Sporting Goods', 'sub': 'Bicycles & Bike Accessories'}
    if has_any(['treadmill', 'elliptical', 'rowing machine', 'dumbbell', 'kettlebell', 'weight set', 
                'home gym', 'smith cage', 'walking pad', 'weight bench']):
        return {'main': 'Sporting Goods', 'sub': 'Exercise Equipment'}
    if has_any(['pickleball', 'paddle', 'pickle ball']):
        return {'main': 'Sporting Goods', 'sub': 'Pickleball'}
    if has_any(['cooler', 'ice chest']):
        return {'main': 'Sporting Goods', 'sub': 'Coolers'}
    if has_any(['water bottle', 'hydro flask', 'yeti bottle']):
        return {'main': 'Sporting Goods', 'sub': 'Water Bottles'}
    
    # === AUTOS ===
    if has_any(['motor oil', 'engine oil', 'synthetic oil']):
        return {'main': 'Autos', 'sub': 'Motor Oil'}
    if has_any(['car wash', 'car wax', 'tire shine', 'detail spray']):
        return {'main': 'Autos', 'sub': 'Auto Detailing & Car Care'}
    if has_any(['jump starter', 'jumper starter', 'jump box']):
        return {'main': 'Autos', 'sub': 'Jump Starter'}
    if has_any(['car battery charger', 'battery maintainer']):
        return {'main': 'Autos', 'sub': 'Automotive Battery Chargers'}
    if has_any(['ev charger', 'level 2 charger']):
        return {'main': 'Autos', 'sub': 'EV Chargers'}
    
    # === TRAVEL & VACATIONS ===
    if has_any(['hotel', 'resort', 'vacation rental', 'airbnb']):
        return {'main': 'Travel & Vacations', 'sub': 'Hotels'}
    if has_any(['flight', 'airfare', 'round-trip flights', 'airline tickets']):
        return {'main': 'Travel & Vacations', 'sub': 'Flights'}
    if has_any(['car rental', 'rental car']):
        return {'main': 'Travel & Vacations', 'sub': 'Car Rentals'}
    if has_any(['cruise']):
        return {'main': 'Travel & Vacations', 'sub': 'Cruises'}
    if has_any(['theme park', 'disney', 'universal studios', 'six flags']):
        return {'main': 'Travel & Vacations', 'sub': 'Theme Parks & Attractions'}
    
    # === FLOWERS & GIFTS ===
    if has_any(['gift card', 'e-gift', 'egift']):
        return {'main': 'Flowers & Gifts', 'sub': 'Gift Cards'}
    if has_any(['greeting card', 'invitation']):
        return {'main': 'Flowers & Gifts', 'sub': 'Greeting Cards & Invitations'}
    
    # === RESTAURANTS ===
    if has_any(['pizza hut', "domino's", 'little caesars']):
        return {'main': 'Restaurants', 'sub': 'Pizza'}
    if has_any(['uber eats', 'doordash', 'grubhub', 'postmates']):
        return {'main': 'Restaurants', 'sub': 'Delivery & Take Out'}
    if has_any(["mcdonald's", 'burger king', "wendy's", 'taco bell', 'kfc', 'popeyes', 'fast food']):
        return {'main': 'Restaurants', 'sub': 'Fast Food'}
    
    # === OFFICE & SCHOOL SUPPLIES ===
    if has_any(['printer paper', 'copy paper', 'notebook paper']):
        return {'main': 'Office & School Supplies', 'sub': 'Paper'}
    if has_any(['pen', 'pencil', 'marker', 'highlighter']):
        return {'main': 'Office & School Supplies', 'sub': 'Pencils, Pens & Markers'}
    
    # === PETS ===
    if has_any(['dog food', 'dog treats', 'puppy food']):
        return {'main': 'Pets', 'sub': 'Dog Food & Treats'}
    if has_any(['cat food', 'cat treats', 'kitten food']):
        return {'main': 'Pets', 'sub': 'Cat Food & Treats'}
    if has_any(['pet toy', 'dog toy', 'cat toy']):
        return {'main': 'Pets', 'sub': 'Pet Toys'}
    
    # === ENTERTAINMENT / BOOKS ===
    if has_any(['blu-ray', 'dvd', 'movie']):
        return {'main': 'Entertainment', 'sub': 'Movies'}
    if has_any(['tv series', 'tv show', 'season 1', 'season 2']):
        return {'main': 'Entertainment', 'sub': 'TV Series & TV Shows'}
    if has_any(['board game', 'card game', 'tabletop']):
        return {'main': 'Entertainment', 'sub': 'Games, Board Games & Card Games'}
    if has_any(['ebook', 'kindle book']):
        return {'main': 'Books & Magazines', 'sub': 'eBooks'}
    if has_any(['hardcover', 'paperback', 'novel']):
        return {'main': 'Books & Magazines', 'sub': 'Books'}
    if has_any(['magazine']):
        return {'main': 'Books & Magazines', 'sub': 'Magazines'}
    
    return {'main': 'Uncategorized', 'sub': ''}


def fetch_rss_feed(url):
    """Fetch and parse RSS feed."""
    try:
        feed = feedparser.parse(url)
        items = []
        
        for entry in feed.entries:
            title = entry.get('title', '').strip()
            link = entry.get('link', '').strip()
            
            pub_date = None
            if 'published_parsed' in entry and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6]).isoformat() + 'Z'
            elif 'updated_parsed' in entry and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6]).isoformat() + 'Z'
            
            if title and link:
                items.append({
                    'title': title,
                    'link': link,
                    'pubDate': pub_date
                })
        
        return items
    except Exception as e:
        print(f'Error fetching RSS feed: {e}', file=sys.stderr)
        return []


def detect_store(title):
    """Detect store name from title."""
    title_lower = title.lower()
    if 'prime' in title_lower or 'amazon' in title_lower:
        return 'Amazon'
    return ''


def load_existing_deals():
    """Load existing deals from JSON file."""
    if DEALS_FILE.exists():
        try:
            with open(DEALS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('deals', [])
        except:
            pass
    return []


def merge_deals(existing_deals, new_rss_deals):
    """
    Merge existing deals with new RSS deals.
    - Keep ALL existing deals unchanged (they have proper URLs from Excel)
    - Only add NEW RSS deals that don't already exist
    - Never replace existing deals (Excel URLs are better than RSS search URLs)
    """
    # Normalize title for comparison
    def normalize_title(title):
        # Remove price, special chars, extra spaces
        normalized = re.sub(r'\$[\d,\.]+', '', title.lower())
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = ' '.join(normalized.split())
        return normalized
    
    # Create map of existing deals by ID (preserve all existing deals)
    existing_map = {deal['id']: deal for deal in existing_deals}
    
    # Create title index for duplicate detection
    existing_titles = set()
    for deal in existing_deals:
        norm_title = normalize_title(deal['title'])
        existing_titles.add(norm_title)
    
    # Only add RSS deals that are truly NEW (not already in existing deals)
    new_count = 0
    for rss_deal in new_rss_deals:
        norm_title = normalize_title(rss_deal['title'])
        
        # Skip if this title already exists (keep the existing deal with better URL)
        if norm_title in existing_titles:
            continue
        
        # Skip if this deal ID already exists
        if rss_deal['id'] in existing_map:
            continue
        
        # This is a truly new deal - add it
        existing_map[rss_deal['id']] = rss_deal
        existing_titles.add(norm_title)
        new_count += 1
        print(f"  Added new deal: {rss_deal['title'][:60]}...")
    
    print(f"Added {new_count} new deals from RSS feed")
    
    # Return all deals sorted by pubDate (newest first)
    all_deals = list(existing_map.values())
    all_deals.sort(key=lambda x: x.get('pubDate', ''), reverse=True)
    
    return all_deals


def main():
    """Main function: merge Google Sheets deals with RSS deals."""
    print('Syncing deals...')
    
    # Load existing deals (from Google Sheets import)
    existing_deals = load_existing_deals()
    print(f'Loaded {len(existing_deals)} existing deals')
    
    # Fetch new deals from RSS
    print('Fetching new deals from Slickdeals RSS feed...')
    rss_items = fetch_rss_feed(FEED_URL)
    
    if not rss_items:
        print('No new items found in RSS feed')
        return
    
    print(f'Found {len(rss_items)} items in RSS feed')
    
    # Process RSS items
    new_rss_deals = []
    for item in rss_items:
        title = item['title']
        link = normalize_link(item['link'])
        pub_date = item['pubDate']
        
        category = categorize_item(title, link)
        sale_price = extract_price(title)
        store = detect_store(title)
        deal_id = extract_deal_id(link)
        
        deal = {
            'id': deal_id,
            'title': title,
            'link': link,
            'mainCategory': category.get('main', 'Uncategorized'),
            'subCategory': category.get('sub', ''),
            'salePrice': sale_price,
            'originalPrice': '',
            'store': store,
            'salePeriod': '',
            'notes': '',
            'pubDate': pub_date
        }
        new_rss_deals.append(deal)
    
    # Merge deals
    all_deals = merge_deals(existing_deals, new_rss_deals)
    print(f'Total deals after merge: {len(all_deals)}')
    
    # Save to file
    data = {
        'lastUpdated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'deals': all_deals
    }
    
    DEALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DEALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'Successfully saved {len(all_deals)} deals to {DEALS_FILE}')


if __name__ == '__main__':
    main()
