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
    """Enhanced keyword-based categorization with 150+ new patterns and context-aware matching."""
    text = (str(title) + ' ' + str(link or '')).lower()
    
    def has_any(keywords):
        for kw in keywords:
            if kw.lower() in text:
                return True
        return False
    
    def has_context(primary_keywords, context_keywords):
        """Check if primary keywords exist WITH context keywords."""
        has_primary = any(kw.lower() in text for kw in primary_keywords)
        has_context_match = any(kw.lower() in text for kw in context_keywords)
        return has_primary and has_context_match
    
    def has_word(word):
        """Word boundary matching for precise matches."""
        import re
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        return bool(re.search(pattern, text))
    
    # === GROCERY - HOUSEHOLD GOODS (check early to catch cleaning products) ===
    if has_any(['paper towel', 'toilet paper', 'tissues', 'cleaning supplies', 'detergent',
                'dish soap', 'dish spray', 'dawn powerwash', 'dawn ', 'laundry', 'trash bags', 
                'cleaning wipes', 'lysol', 'clorox', 'all-purpose cleaner', 'spray cleaner', 'windex', 'mr clean']):
        return {'main': 'Grocery', 'sub': 'Household Goods'}
    
    # === BOOKS & MAGAZINES (check early to catch book, audiobook, audible) ===
    if has_any(['audible', 'audiobook', 'audio book']):
        return {'main': 'Books & Magazines', 'sub': 'Audiobooks'}
    if has_any(['ebook', 'kindle book', 'digital book']):
        return {'main': 'Books & Magazines', 'sub': 'eBooks'}
    if has_any(['hardcover', 'paperback']) or (has_word('book') and not has_any(['notebook', 'photo book', 'chromebook', 'macbook'])):
        return {'main': 'Books & Magazines', 'sub': 'Books'}
    if has_any(['magazine subscription', 'magazine']):
        return {'main': 'Books & Magazines', 'sub': 'Magazines'}
    
    # === BABIES & KIDS ===
    if has_any(['kids toy', 'children toy', 'toy car', 'toy truck', 'atv', 'go kart', 
                'hoverboard', 'kids bike', 'baby toy', 'toddler toy', 'ride-on', 'remote control car',
                'rc car', 'maisto', 'hot wheels', 'barbie', 'plush', 'stuffed animal', 'disney jr',
                'superkitties', 'paw patrol', 'peppa pig', 'bluey', 'cocomelon']):
        return {'main': 'Babies & Kids', 'sub': 'Kids Toys'}
    if has_any(['diaper', 'baby food', 'formula', 'crib', 'stroller', 'car seat', 'baby monitor', 'nursery', 
                'baby wipes', 'baby bottle', 'pacifier', 'infant', 'toddler']):
        return {'main': 'Babies & Kids', 'sub': 'Baby Products'}
    
    # === VIDEO GAMES ===
    if has_any(['ps5', 'playstation 5', 'ps4', 'playstation 4', 'xbox series x',
                'xbox series s', 'xbox one', 'nintendo switch', 'switch oled', 'playstation®5',
                'playstation bundle', 'ps5 bundle', 'ps5 disc', 'ps5 digital']):
        return {'main': 'Video Games', 'sub': 'Video Game Consoles'}
    if has_any(['game controller', 'xbox controller', 'playstation controller', 'ps5 controller',
                'switch controller', 'dualsense', 'dualshock', '8bitdo', 'scuf', 'mobile controller',
                'bluetooth controller', 'galileo']):
        return {'main': 'Video Games', 'sub': 'Controllers & Accessories'}
    if has_any(['xbox game pass', 'game pass ultimate', 'playstation plus', 'ps plus',
                'ps+', 'nintendo switch online', 'ea play', 'ubisoft+', 'neverwinter zen', 'tera coin']):
        return {'main': 'Video Games', 'sub': 'Video Game Memberships'}
    if has_any(['steam game', 'steam key', 'epic games store', 'origin game',
                'pc game', 'battle.net', 'gog.com', 'gaming pc', 'steam deck']):
        return {'main': 'Video Games', 'sub': 'Computer & PC Games'}
    if has_any(['switch game', 'nintendo switch game', 'nsw-', 'nsw2']):
        return {'main': 'Video Games', 'sub': 'Nintendo Switch'}
    if has_any(['ps5 game', 'ps4 game', 'playstation game']):
        return {'main': 'Video Games', 'sub': 'PlayStation'}
    if has_any(['xb1-', 'xbsx', 'xbox game']):
        return {'main': 'Video Games', 'sub': 'Xbox'}
    if has_any(['anbernic', 'rg557', 'rg556', 'retro handheld', 'rg7']):
        return {'main': 'Video Games', 'sub': 'Handheld Gaming'}
    if has_any(['pokemon tcg', 'pokemon card', 'pokemon trading', 'elite trainer box', 'booster box']):
        return {'main': 'Video Games', 'sub': 'Trading Card Games'}
    if has_any(['playmat', 'game mat', 'disney lorcana', 'lorc ']):
        return {'main': 'Video Games', 'sub': 'Trading Card Games'}
    # General video game titles - check common game keywords
    if has_any(['madden nfl', 'train sim', 'motorfest', 'five nights', 'tekken', 'oddballers',
                'red dead', 'the crew', 'the last of us', 'bendy and the ink', 'story of seasons',
                'agatha christie', 'timesplitters', 'exoprimal', 'hatsune miku', 'atelier', 
                'raccoon city', 'help wanted', 'motorcycle club', 'future perfect', 'abc murders',
                'enlisted', 'season pass', 'borderlands', 'wolfenstein', 'lords of the fallen',
                'ad infinitum', "assassin's creed", 'prince of persia', 'pure farming', 'warriors:',
                'kingdoms of amalur', 'persona 5', 'killing floor', 'bloodstained', 'starlink',
                'stardew valley', 'mutazione', 'warhammer', 'vermintide', 'sea of thieves',
                'dragon quest', 'rune factory', 'from dust', 'dancing in starlight',
                'deluxe edition', 'collectors edition', 'gold edition', 'ultimate edition', 'premium edition',
                'artful escape', 'make way', 'desperados', 'dynasty warriors', 'snowrunner', 
                'still wakes', 'kingdom come', 'custom mech', 'torchlight', 'dishonored', 
                'bratz', 'supercross', 'war thunder', 'far cry', 'greedfall', 'devil may cry',
                'dead by daylight', 'livelock', 'call of the wild', 'deus ex', 'paradize',
                'chip n clawz', 'brainoid']):
        return {'main': 'Video Games', 'sub': 'Video Games'}
    
    # === ELECTRONICS - TABLETS (check before Computers to avoid cellular/wifi false positives) ===
    if has_any(['ipad', 'ipad pro', 'ipad air', 'ipad mini', 'galaxy tab', 'surface pro', 'kindle fire', 'android tablet',
                'samsung tab']) or (has_word('tablet') and not has_any(['tablet stand', 'tablet case'])):
        return {'main': 'Electronics', 'sub': 'Tablets'}
    
    # === COMPUTERS ===
    # Check laptops FIRST - laptops often have SSD/RAM specs in title which shouldn't categorize them as components
    if has_any(['laptop', 'notebook', 'chromebook', 'macbook', 'gaming laptop', 'ultrabook', 'acer swift', 'lenovo ideapad', 'hp pavilion', 'dell xps', 'asus vivobook', 'thinkpad', 'acer aspire', 'hp envy', 'surface laptop']):
        return {'main': 'Computers', 'sub': 'Laptops'}
    if has_any(['rtx ', 'gtx ', 'rx 6', 'rx 7', 'graphics card', 'geforce', 'radeon', 'gpu',
                'gv-n5080', 'gv-r9070', '5070', '4090', '4080', '4070']):
        return {'main': 'Computers', 'sub': "GPU's"}
    if has_any(['motherboard', 'am5', 'lga 1700', 'b850', 'z890', 'x870', 'asrock', 'gigabyte z',
                'cpu motherboard', 'intel core ultra', 'memory combo']):
        return {'main': 'Computers', 'sub': 'Motherboards'}
    if has_any(['ssd', 'solid state drive', 'nvme', 'm.2', 'hard drive', 'hdd', 'external drive']):
        return {'main': 'Computers', 'sub': "SSD's & Hard Drives"}
    if has_any(['ram ', 'ddr4', 'ddr5', 'memory kit', 'corsair vengeance']):
        return {'main': 'Computers', 'sub': 'Memory'}
    if has_any(['desktop pc', 'gaming desktop', 'prebuilt pc', 'imac', 'desktop computer']):
        return {'main': 'Computers', 'sub': 'Desktop Computers'}
    if has_any(['router', 'wifi 6', 'wifi 7', 'mesh system', 'ethernet switch', 'network adapter', 'modem', 'access point', 'range extender']) or (has_word('wi-fi') and not has_any(['ipad', 'iphone', 'tablet'])):
        return {'main': 'Computers', 'sub': 'Computer Networking'}
    if has_any(['printer', 'inkjet', 'laser printer', 'toner', 'ink cartridge', 'all-in-one printer']):
        return {'main': 'Computers', 'sub': 'Printers'}
    if has_any(['monitor', 'gaming monitor', 'curved monitor', 'ultrawide', '4k monitor', 'display', 'flat gaming']):
        return {'main': 'Computers', 'sub': 'Monitors'}
    if has_any(['mouse', 'keyboard', 'gaming mouse', 'gaming keyboard', 'mechanical keyboard', 'wireless mouse',
                'wireless combo', 'logitech mk', 'keyboard combo']):
        return {'main': 'Computers', 'sub': 'Mice & Keyboards'}
    if has_any(['vpn', 'domain', 'hosting', 'web hosting', 'cloud storage', 'nord vpn', 'expressvpn']):
        return {'main': 'Computers', 'sub': "Internet, Websites & VPN's"}
    if has_any(['pc case', 'computer case', 'mid-tower', 'mini-itx', 'micro-atx', 'atx case', 
                'phanteks', 'nzxt', 'corsair case', 'h7 flow']):
        return {'main': 'Computers', 'sub': 'Computer Cases'}
    if has_any(['power supply', 'psu', '80 plus', '80+ gold', '1000w', '850w', '750w', '650w', 
                'atx 3.0', 'modular power', 'be quiet! pure power', 'asus prime']):
        return {'main': 'Computers', 'sub': 'Power Supplies'}
    if has_any(['ibuypower', 'prebuilt', 'gaming desktop', 'custom pc', 'skytech gaming']):
        return {'main': 'Computers', 'sub': 'Desktop Computers'}
    if has_any(['ubiquiti', 'unifi', 'dream machine', 'cloud gateway', 'udm-pro']):
        return {'main': 'Computers', 'sub': 'Computer Networking'}
    
    # === SOFTWARE ===
    if has_any(['norton 360', 'norton utilities', 'antivirus', 'mcafee', 'kaspersky', 'bitdefender']):
        return {'main': 'Software', 'sub': 'Security Software'}
    if has_any(['microsoft 365', 'office 365', 'microsoft office', 'windows 11', 'windows key']):
        return {'main': 'Software', 'sub': 'Office & Productivity'}
    if has_any(['adobe', 'photoshop', 'creative cloud', 'premiere pro', 'lightroom']):
        return {'main': 'Software', 'sub': 'Creative Software'}
    
    # === ELECTRONICS ===
    if has_any(['iphone', 'galaxy s', 'galaxy z', 'pixel phone', 'smartphone', 'cell phone',
                'mobile plan', 'wireless plan', 'us mobile', 'mint mobile', 'visible', 'cricket wireless',
                'pixel 10', 'pixel 9', 'pixel 8']):
        return {'main': 'Electronics', 'sub': 'Cell Phones & Plans'}
    if has_any(['phone case', 'iphone case', 'pixel case', 'screen protector', 'plyo', 'magsafe case',
                'monarch pro', 'civilian', 'iph16', 'iph 15']):
        return {'main': 'Electronics', 'sub': 'Phone Accessories'}
    if has_any(['camera', 'mirrorless', 'dslr', 'gopro', 'action camera', 'webcam', 'lens', 'canon', 'nikon', 'sony alpha',
                'tripod', 'camera tripod', 'travel tripod']):
        return {'main': 'Electronics', 'sub': 'Cameras & Photography'}
    if has_any(['airtag', 'air tag', 'tile tracker', 'tracker', 'bluetooth tracker', 'gps tracker']):
        return {'main': 'Electronics', 'sub': 'Tracking Devices'}
    if has_any(['4k tv', 'hdr tv', 'oled tv', 'qled tv', 'uhd tv', 'smart tv', 'tcl tv', 'samsung tv', 'lg tv', 'sony tv',
                'mini-led', 'fire tv', 'roku tv', 'hisense', 'vizio', 'tizen', 'frame tv', 'frame qled',
                'qned', 'webos tv', 'lg 65', 'lg 55', 'lg 75', 'samsung 65', 'samsung 55']):
        return {'main': 'Electronics', 'sub': "TV's"}
    if has_any(['soundbar', 'sound bar']):
        return {'main': 'Electronics', 'sub': 'Sound Bars'}
    if has_any(['bluetooth speaker', 'smart speaker', 'portable speaker', 'jbl', 'bose speaker', 'alexa', 'echo dot',
                'marshall speaker', 'acton', 'gigaworks', 'multimedia speaker', 'echo show', 'amazon echo', 'mag series']):
        return {'main': 'Electronics', 'sub': 'Speakers'}
    if has_any(['headphones', 'earbuds', 'earphones', 'headset', 'gaming headset', 'airpods', 'beats', 'sony wh',
                'sennheiser', 'momentum', 'wh1000xm', 'xm5', 'xm6']):
        return {'main': 'Electronics', 'sub': 'Headphones, Headsets & Earbuds'}
    if has_any(['projector', 'home theater projector', '4k projector']):
        return {'main': 'Electronics', 'sub': 'Projectors'}
    if has_any(['smartwatch', 'apple watch', 'fitbit', 'wearable', 'fitness tracker', 'garmin watch', 'charge 6']):
        return {'main': 'Electronics', 'sub': 'Smart Watches & Wearables'}
    if has_any(['power bank', 'portable charger', 'anker', 'charging cable', 'usb-c cable', 'usb adapter', 'usb-a adapter',
                'wall charger', '70w charger', '65w charger', 'retrak']):
        return {'main': 'Electronics', 'sub': 'Chargers & Power Banks'}
    if has_any(['ups ', 'surge protector', 'power strip', 'battery backup']):
        return {'main': 'Electronics', 'sub': 'UPS, Surge Protectors & Powerstrips'}
    if has_any(['blink', 'ring doorbell', 'ring floodlight', 'security camera', 'smart doorbell', 'nest cam', 'wyze cam']):
        return {'main': 'Electronics', 'sub': 'Smart Home Security'}
    if has_any(['theragun', 'massage gun', 'percussion massager']):
        return {'main': 'Electronics', 'sub': 'Wellness Devices'}
    if has_any(['dji', 'drone', 'gimbal', 'rs3', 'rs4', 'mavic', 'mini 3', 'mini 4']):
        return {'main': 'Electronics', 'sub': 'Drones & Gimbals'}
    if has_any(['elgato', 'game capture', 'stream deck', 'capture card', 'cam link']):
        return {'main': 'Electronics', 'sub': 'Streaming Equipment'}
    if has_any(['ecobee', 'nest thermostat', 'smart thermostat', 'thermostat']):
        return {'main': 'Electronics', 'sub': 'Smart Home'}
    if has_any(['solar panel', 'foldable solar', 'portable solar']):
        return {'main': 'Electronics', 'sub': 'Solar Panels'}
    if has_any(['vinyl record player', 'turntable', 'record player', 'phonograph']):
        return {'main': 'Electronics', 'sub': 'Audio Equipment'}
    
    # === ENTERTAINMENT (before Grocery to catch false positives) ===
    if has_any(['funko pop', 'funko', 'action figure', 'collectible', 'replica', 'lego', 'building set',
                'lego set', 'star wars', 'marvel legends', 'mcfarlane', 'model kit',
                'son goku', 'dragon ball', 'anime figure', 'db fig', 'daima']):
        return {'main': 'Entertainment', 'sub': 'Collectibles & Toys'}
    if has_any(['disney+', 'disney plus', 'netflix', 'hulu', 'paramount+', 'peacock', 'max ', 'hbo max',
                'apple tv+', 'prime video']):
        return {'main': 'Entertainment', 'sub': 'Streaming Services'}
    if has_any(['guitar', 'electric guitar', 'acoustic guitar', 'bass guitar', 'piano', 'keyboard', 'drum',
                'ukulele', 'violin', 'synthesizer', 'midi']):
        return {'main': 'Entertainment', 'sub': 'Musical Instruments'}
    if has_any(['blu-ray', 'dvd', 'movie', '4k blu-ray']):
        return {'main': 'Entertainment', 'sub': 'Movies'}
    if has_any(['tv series', 'tv show', 'season 1', 'season 2', 'complete series']):
        return {'main': 'Entertainment', 'sub': 'TV Series & TV Shows'}
    if has_any(['board game', 'card game', 'tabletop', 'dungeons', 'magic the gathering', 'pokemon cards', 
                'monopoly', 'uno', 'scrabble', 'trivial pursuit']):
        return {'main': 'Entertainment', 'sub': 'Games, Board Games & Card Games'}
    
    # === HEALTH & PERSONAL CARE ===
    if has_any(['dayquil', 'nyquil', 'vicks', 'cough', 'cold medicine', 'flu relief', 'tylenol', 'advil', 
                'ibuprofen', 'allergy relief', 'vitamin', 'supplement', 'multivitamin']):
        return {'main': 'Health & Personal Care', 'sub': 'Medicine & Supplements'}
    if has_any(['toothbrush', 'toothpaste', 'oral-b', 'sonicare', 'floss', 'mouthwash', 'waterpik']):
        return {'main': 'Health & Personal Care', 'sub': 'Oral Care'}
    if has_any(['razor', 'shaver', 'electric shaver', 'trimmer', 'beard trimmer', 'philips norelco', 'braun shaver']):
        return {'main': 'Health & Personal Care', 'sub': 'Shaving & Grooming'}
    if has_any(['shampoo', 'conditioner', 'body wash', 'deodorant', 'lotion', 'moisturizer', 'sunscreen']):
        return {'main': 'Health & Personal Care', 'sub': 'Personal Care'}
    if has_any(['massager', 'neck massager', 'shoulder massager', 'shiatsu', 'massage cushion', 'foot massager']):
        return {'main': 'Health & Personal Care', 'sub': 'Massage & Relaxation'}
    if has_any(['lip balm', "burt's bees", 'chapstick', 'lip gloss', 'lip care']):
        return {'main': 'Health & Personal Care', 'sub': 'Lip Care'}
    if has_any(['gift basket', 'gift set', 'spa set', 'bath set', 'beauty set', 'spa luxetique', 'body cream']):
        return {'main': 'Health & Personal Care', 'sub': 'Gift Sets'}
    if has_any(['feminine pad', 'flex foam', 'sanitary', 'always pad', 'tampons', 'menstrual']):
        return {'main': 'Health & Personal Care', 'sub': 'Feminine Care'}
    if has_any(['odor defense', 'odor eliminator', 'downy', 'fabric softener', 'dryer sheet']):
        return {'main': 'Grocery', 'sub': 'Household Goods'}
    if has_any(['pistachio cream', 'nut butter', 'hazelnut spread', 'chocolate spread']):
        return {'main': 'Grocery', 'sub': 'Spreads & Butters'}
    
    # === GROCERY (with context-aware matching) ===
    if has_any(['paper towel', 'toilet paper', 'tissues', 'cleaning supplies', 'detergent',
                'dish soap', 'dish spray', 'dawn powerwash', 'dawn ', 'laundry', 'trash bags', 'household', 
                'cleaning wipes', 'lysol', 'clorox', 'all-purpose cleaner', 'spray cleaner']):
        return {'main': 'Grocery', 'sub': 'Household Goods'}
    if has_any(['chips', 'doritos', 'cheetos', 'pringles', 'snack', 'snacks',
                'trail mix', 'mixed nuts', 'almonds', 'cashews', 'pistachios', 'crackers', 'popcorn']):
        return {'main': 'Grocery', 'sub': 'Snacks, Nuts & Chips'}
    if has_context(['coffee'], ['pod', 'k-cup', 'beans', 'ground', 'instant', 'nespresso', 'starbucks', 'folgers', 'keurig', 'java', 'roast']):
        return {'main': 'Grocery', 'sub': 'Drinks & Beverages'}
    if has_any(['soda', 'cola', 'sparkling water', 'energy drink', 'tea', 'juice', 'gatorade', 'vitamin water']):
        return {'main': 'Grocery', 'sub': 'Drinks & Beverages'}
    if has_any(['cereal', 'oatmeal', 'granola', 'pancake mix', 'breakfast']):
        return {'main': 'Grocery', 'sub': 'Breakfast Foods'}
    if has_any(['pasta', 'spaghetti', 'macaroni', 'penne', 'linguine']):
        return {'main': 'Grocery', 'sub': 'Pasta'}
    if has_any(['rice', 'quinoa', 'brown rice', 'wild rice']):
        return {'main': 'Grocery', 'sub': 'Rice & Grains'}
    if has_any(['frozen dinner', 'soup', 'canned soup', 'canned', 'microwave meal', 'ramen']):
        return {'main': 'Grocery', 'sub': 'Soups, Sauces, Packaged Meals & Canned Goods'}
    if has_any(['ketchup', 'mustard', 'hot sauce', 'spice', 'seasoning', 'sauce', 'mayo', 'sriracha']):
        return {'main': 'Grocery', 'sub': 'Condiments & Spices'}
    if has_any(['turkey', 'chicken breast', 'ground beef', 'steak', 'pork', 'salmon', 'frozen pizza', 'ice cream']):
        return {'main': 'Grocery', 'sub': 'Meat & Frozen Foods'}
    
    # === HOME & HOME IMPROVEMENT ===
    if has_any(['cookware', 'frying pan', 'skillet', 'pot set', 'dutch oven', 'bakeware', 'silverware',
                'flatware', 'utensil', 'knife set', 'cutting board', 'mixing bowl', 'calphalon', 'tefal',
                'cast iron', 'non-stick', 'parchment paper']):
        return {'main': 'Home & Home Improvement', 'sub': 'Kitchen & Cookware'}
    if has_any(['lamp', 'desk lamp', 'floor lamp', 'light bulb', 'led light', 'led strip', 'chandelier',
                'ceiling light', 'smart bulb', 'philips hue', 'string lights', 'solar lights', 'motion sensor light',
                'nanoleaf', 'govee', 'rope light', 'wall light panels', 'outdoor lights', 'led lights']):
        return {'main': 'Home & Home Improvement', 'sub': 'Lighting'}
    if has_any(['storage bin', 'storage container', 'organizer', 'shelving', 'closet organizer',
                'drawer organizer', 'garage storage', 'lunch box', 'insulated lunch']):
        return {'main': 'Home & Home Improvement', 'sub': 'Storage & Organization'}
    if has_any(['grill', 'gas grill', 'charcoal grill', 'pellet grill', 'smoker', 'vertical smoker',
                'griddle', 'grilling', 'bbq accessories', 'blackstone']):
        return {'main': 'Home & Home Improvement', 'sub': 'Grills & Grilling Accessories'}
    if has_word('stove') or has_word('oven') or has_any(['range', 'cooktop']):
        return {'main': 'Home & Home Improvement', 'sub': 'Stoves'}
    if has_any(['gardening', 'lawn mower', 'trimmer', 'weed eater', 'leaf blower', 'garden hose',
                'garden tools', 'patio furniture', 'patio set', 'yard tool']):
        return {'main': 'Home & Home Improvement', 'sub': 'Gardening & Outdoor'}
    if has_any(['mattress', 'memory foam mattress', 'bedding', 'sheet set', 'duvet', 'comforter', 'pillow', 'bed frame',
                'bath towel', 'bath sheet', 'towel set', 'throw blanket', 'heated blanket', 'electric blanket',
                'faux fur throw', 'fleece blanket', 'weighted blanket', 'sheets', 'microfiber sheet']):
        return {'main': 'Home & Home Improvement', 'sub': 'Mattresses, Sheets & Bedding'}
    if has_any(['vacuum', 'stick vac', 'robot vacuum', 'robovac', 'floor cleaner', 'steam mop', 'dyson', 'shark vacuum']):
        return {'main': 'Home & Home Improvement', 'sub': 'Vacuums & Floor Cleaners'}
    if has_any(['air fryer', 'blender', 'toaster', 'microwave', 'coffee maker',
                'espresso machine', 'slow cooker', 'instant pot', 'food processor', 'stand mixer',
                'rice cooker', 'pressure cooker', 'ninja', 'keurig', 'k-cup brewer', 'coffee brewer',
                'deep fryer', 'electric fryer', 'water filter', 'reverse osmosis', 'waterdrop']):
        return {'main': 'Home & Home Improvement', 'sub': 'Small Appliances'}
    if has_any(['refrigerator', 'fridge', 'freezer', 'mini fridge']):
        return {'main': 'Home & Home Improvement', 'sub': 'Refrigerators & Freezers'}
    if has_any(['washer', 'washing machine', 'dryer', 'washer dryer']):
        return {'main': 'Home & Home Improvement', 'sub': 'Washers & Dryers'}
    if has_any(['sofa', 'couch', 'office chair', 'gaming chair', 'desk', 'dining table', 'bookshelf',
                'recliner', 'sectional', 'futon', 'ottoman', 'nightstand', 'dresser', 'coffee table', 'end table']):
        return {'main': 'Home & Home Improvement', 'sub': 'Furniture'}
    if has_any(['drill', 'saw', 'circular saw', 'miter saw', 'tool set', 'tool kit', 'wrench set', 'socket set',
                'screwdriver', 'dewalt', 'milwaukee', 'ryobi', 'makita']):
        return {'main': 'Home & Home Improvement', 'sub': 'Tool Sets'}
    if has_any(['ladder', 'step ladder', 'extension ladder']):
        return {'main': 'Home & Home Improvement', 'sub': 'Ladders'}
    if has_any(['air purifier', 'space heater', 'air conditioner', 'portable ac', 'dehumidifier', 'humidifier', 'fan', 'hand warmer']):
        return {'main': 'Home & Home Improvement', 'sub': 'Air Conditioners, Heaters, Purifiers & More'}
    if has_any(['curtain', 'blackout curtain', 'sheer curtain', 'curtain rod', 'blinds', 'mini blind',
                'window shade', 'shower curtain', 'drapes']):
        return {'main': 'Home & Home Improvement', 'sub': 'Curtains & Window Treatments'}
    if has_any(['area rug', 'floor rug', 'rug ', 'bath rug', 'bath mat', 'door mat', 'doormat', 'floor mat',
                'carpet', 'runner rug', 'chenille']):
        return {'main': 'Home & Home Improvement', 'sub': 'Rugs & Mats'}
    if has_any(['mirror', 'wall mirror', 'floor mirror', 'full length mirror', 'vanity mirror']):
        return {'main': 'Home & Home Improvement', 'sub': 'Mirrors'}
    if has_any(['artificial plant', 'artificial tree', 'fake plant', 'faux plant', 'topiary', 
                'artificial olive', 'artificial ficus', 'artificial cedar']):
        return {'main': 'Home & Home Improvement', 'sub': 'Artificial Plants'}
    if has_any(['smoke alarm', 'smoke detector', 'carbon monoxide detector', 'fire alarm', 'fire extinguisher']):
        return {'main': 'Home & Home Improvement', 'sub': 'Safety & Security'}
    if has_any(['chafing dish', 'ice cube tray', 'water pitcher', 'serving platter', 'serving tray']):
        return {'main': 'Home & Home Improvement', 'sub': 'Kitchen & Cookware'}
    if has_any(['alarm clock', 'sunrise alarm', 'sound machine', 'white noise machine']):
        return {'main': 'Home & Home Improvement', 'sub': 'Clocks & Sleep Aids'}
    if has_any(['fire pit', 'propane fire pit', 'outdoor fireplace']):
        return {'main': 'Home & Home Improvement', 'sub': 'Outdoor Fire Pits'}
    if has_any(['generator', 'inverter generator', 'portable generator', 'predator', 'dual-fuel generator']):
        return {'main': 'Home & Home Improvement', 'sub': 'Generators'}
    if has_any(['candle', 'yankee candle', 'scented candle', 'wax melt']):
        return {'main': 'Home & Home Improvement', 'sub': 'Candles & Home Fragrance'}
    if has_any(['tv wall mount', 'tv mount', 'swivel mount', 'tilt mount']):
        return {'main': 'Home & Home Improvement', 'sub': 'TV Mounts'}
    if has_any(['flooring', 'laminate flooring', 'vinyl plank', 'hardwood flooring', 'tile flooring', 'herringbone']):
        return {'main': 'Home & Home Improvement', 'sub': 'Flooring'}
    if has_any(['vanity', 'vanities', 'bathroom vanity', 'bathroom sink']):
        return {'main': 'Home & Home Improvement', 'sub': 'Bathroom'}
    if has_any(['workbench', 'tool box', 'tool chest', 'pegboard', 'husky']):
        return {'main': 'Home & Home Improvement', 'sub': 'Tool Storage'}
    if has_any(['path light', 'garden light', 'landscape light', 'outdoor light', 'porch light']):
        return {'main': 'Home & Home Improvement', 'sub': 'Outdoor Lighting'}
    if has_any(['platform bed', 'bed with storage', 'bed frame with', 'wood bed']):
        return {'main': 'Home & Home Improvement', 'sub': 'Furniture'}
    if has_any(['raised garden bed', 'planter box', 'garden planter', 'flower pot', 'plant stand']):
        return {'main': 'Home & Home Improvement', 'sub': 'Gardening & Outdoor'}
    
    # === SEASONAL & HOLIDAY ===
    if has_any(['christmas tree', 'artificial christmas', 'pre-lit tree', 'xmas tree']):
        return {'main': 'Seasonal', 'sub': 'Christmas Trees'}
    if has_any(['christmas inflatable', 'christmas blow up', 'xmas inflatable', 'holiday inflatable',
                'nativity', 'santa inflatable', 'christmas outdoor', 'outdoor xmas', 'snowman decoration']):
        return {'main': 'Seasonal', 'sub': 'Christmas Decorations'}
    if has_any(['christmas lights', 'holiday lights', 'icicle lights', 'xmas lights']):
        return {'main': 'Seasonal', 'sub': 'Christmas Lights'}
    if has_any(['ornament', 'tree topper', 'wreath', 'garland', 'stocking']):
        return {'main': 'Seasonal', 'sub': 'Christmas Ornaments & Decor'}
    
    # === CLOTHING & ACCESSORIES ===
    if has_any(['sneakers', 'sneaker', 'running shoes', 'sandals', 'boots', 'shoe', 'clogs', 'athletic shoes', 
                'nike', 'adidas', 'skechers', 'new balance', 'puma', 'reebok', 'asics', 'crocs',
                'booties', 'journee', 'heels', 'flats', 'loafers', 'slippers']):
        return {'main': 'Clothing & Accessories', 'sub': 'Shoes'}
    if has_any(['backpack', 'luggage', 'suitcase', 'duffel bag', 'tote bag', 'messenger bag', 'laptop bag',
                'crossbody', 'lanyard']):
        return {'main': 'Clothing & Accessories', 'sub': 'Bags & Luggage'}
    if has_any(['socks', 'sock', 'ankle socks', 'crew socks', 'compression socks', 'goldtoe']):
        return {'main': 'Clothing & Accessories', 'sub': 'Socks'}
    if has_any(['pajamas', 'pj set', 'pjs', 'sleepwear', 'nightgown', 'robe', 'gap kids']):
        return {'main': 'Clothing & Accessories', 'sub': 'Sleepwear'}
    if has_any(['t-shirt', 'hoodie', 'jacket', 'jeans', 'pants', 'shorts', 'dress', 'sweater',
                'fleece', 'flannel', 'outerwear', 'apparel', 'clothes', 'clothing', 'polo', 'sweatshirt',
                "men's", "women's", 'under armour', 'champion', 'hanes', 'fruit of the loom', 'gildan',
                'levis', "levi's", 'wrangler', 'carhartt', 'columbia', 'north face', 'patagonia',
                'tank top', 'shirt', 'blouse', 'underwear', 'thong', 'boxer', 'brief', 'ruched', 'racerback',
                'ribbed', 'jersey', 'keyhole', 'scuba', 'jogger', 'lululemon']):
        return {'main': 'Clothing & Accessories', 'sub': 'Apparel'}
    if has_word('watch') or has_any(['chronograph', 'wristwatch', 'timepiece']):
        return {'main': 'Clothing & Accessories', 'sub': 'Watches'}
    if has_any(['sunglasses', 'sunglass', 'ray-ban', 'oakley']):
        return {'main': 'Clothing & Accessories', 'sub': 'Sunglasses'}
    if has_any(['necklace', 'bracelet', 'earring', 'engagement ring', 'wedding ring', 'diamond ring', 'gold ring']):
        return {'main': 'Clothing & Accessories', 'sub': 'Jewelry'}
    if has_any(['eyeglasses', 'prescription glasses', 'reading glasses', 'goggles', 'optical', 'goggles4u']):
        return {'main': 'Clothing & Accessories', 'sub': 'Eyewear'}
    
    # === HEALTH & BEAUTY ===
    if has_any(['cotton swab', 'q-tip', 'cotton ball', 'hair straightener', 'curling iron', 'hair dryer',
                'blow dryer', 'flat iron', 'hair styling']):
        return {'main': 'Health & Beauty', 'sub': 'Personal Care'}
    if has_any(['vitamin', 'multivitamin', 'supplement', 'collagen', 'omega-3', 'probiotics', 'magnesium']):
        return {'main': 'Health & Beauty', 'sub': 'Vitamins'}
    if has_any(['protein powder', 'whey', 'casein', 'protein shake', 'pre-workout', 'creatine']):
        return {'main': 'Health & Beauty', 'sub': 'Protein Powder & Shakes'}
    if has_any(['shampoo', 'conditioner', 'hair care', 'hair oil']):
        return {'main': 'Health & Beauty', 'sub': 'Shampoo & Hair Care'}
    if has_any(['toothpaste', 'toothbrush', 'mouthwash', 'oral care', 'floss', 'whitening']):
        return {'main': 'Health & Beauty', 'sub': 'Toothpaste, Toothbrushes & Oral Care'}
    if has_any(['razor', 'shaving cream', 'shaver', 'electric shaver', 'gillette']):
        return {'main': 'Health & Beauty', 'sub': 'Razors & Shaving Supplies'}
    if has_any(['face cream', 'moisturizer', 'skin care', 'lotion', 'serum', 'sunscreen', 'spf']):
        return {'main': 'Health & Beauty', 'sub': 'Skin Care'}
    if has_any(['perfume', 'cologne', 'fragrance', 'body spray']):
        return {'main': 'Health & Beauty', 'sub': 'Fragrances'}
    
    # === SPORTING GOODS ===
    if has_any(['gun safe', 'ammo', 'ammunition', '9mm', '.22lr', '5.56mm', 'brass', 'firearm']):
        return {'main': 'Sporting Goods', 'sub': 'Guns, Ammo & Accessories'}
    if has_any(['hunting', 'trail camera', 'camo', 'camouflage', 'hunting boots', 'deer', 'optics',
                'rifle scope', 'binoculars']):
        return {'main': 'Sporting Goods', 'sub': 'Hunting'}
    if has_any(['fishing', 'fish finder', 'fishing rod', 'fishing reel', 'tackle', 'lure', 'bait']):
        return {'main': 'Sporting Goods', 'sub': 'Fishing'}
    if has_any(['golf', 'golf ball', 'golf club', 'putter', 'driver', 'iron set', 'golf bag']):
        return {'main': 'Sporting Goods', 'sub': 'Golf'}
    if has_any(['knife', 'pocket knife', 'hunting knife', 'blade', 'swiss army']):
        return {'main': 'Sporting Goods', 'sub': 'Knives'}
    if has_any(['basketball hoop', 'baseball bat', 'soccer ball', 'football', 'sports ball',
                'volleyball', 'tennis', 'badminton', 'ping pong', 'table tennis']):
        return {'main': 'Sporting Goods', 'sub': 'Sports Equipment'}
    if has_any(['yoga mat', 'resistance band', 'foam roller', 'fitness tracker', 'fitness',
                'wellness', 'pilates', 'heavy bag', 'boxing', 'jump rope']):
        return {'main': 'Sporting Goods', 'sub': 'Fitness & Wellness'}
    if has_any(['bike', 'bicycle', 'mountain bike', 'road bike', 'e-bike', 'bike helmet']):
        return {'main': 'Sporting Goods', 'sub': 'Bicycles & Bike Accessories'}
    if has_any(['treadmill', 'elliptical', 'rowing machine', 'dumbbell', 'kettlebell', 'weight set', 
                'home gym', 'smith cage', 'walking pad', 'weight bench', 'barbell', 'exercise bike']):
        return {'main': 'Sporting Goods', 'sub': 'Exercise Equipment'}
    if has_any(['pickleball', 'paddle', 'pickle ball']):
        return {'main': 'Sporting Goods', 'sub': 'Pickleball'}
    if has_any(['cooler', 'ice chest', 'yeti cooler']):
        return {'main': 'Sporting Goods', 'sub': 'Coolers'}
    if has_any(['water bottle', 'hydro flask', 'yeti bottle', 'insulated bottle']):
        return {'main': 'Sporting Goods', 'sub': 'Water Bottles'}
    if has_any(['tent', 'sleeping bag', 'backpacking', 'hiking boots', 'trekking pole',
                'camping gear', 'hammock', 'camp stove']) or (has_word('camping') and not has_any(['camping chair'])):
        return {'main': 'Sporting Goods', 'sub': 'Camping & Outdoor'}
    
    # === AUTOS ===
    if has_any(['tire inflator', 'air compressor', 'car charger', 'dash cam', 'dashcam', 'car mount',
                'phone mount', 'car vacuum', 'seat cover', 'magsafe car']):
        return {'main': 'Autos', 'sub': 'Car Accessories'}
    if has_any(['motor oil', 'engine oil', 'synthetic oil', 'mobil 1', 'castrol']):
        return {'main': 'Autos', 'sub': 'Motor Oil'}
    if has_any(['car wash', 'car wax', 'tire shine', 'detail spray', 'car polish']):
        return {'main': 'Autos', 'sub': 'Auto Detailing & Car Care'}
    if has_any(['jump starter', 'jumper starter', 'jump box']):
        return {'main': 'Autos', 'sub': 'Jump Starter'}
    if has_any(['car battery charger', 'battery maintainer', 'battery tender']):
        return {'main': 'Autos', 'sub': 'Automotive Battery Chargers'}
    if has_any(['ev charger', 'level 2 charger', 'tesla charger']):
        return {'main': 'Autos', 'sub': 'EV Chargers'}
    if has_any(['car tire', 'all-season tire', 'winter tire', 'tire set']):
        return {'main': 'Autos', 'sub': 'Tires'}
    
    # === TRAVEL & VACATIONS ===
    if has_any(['hotel', 'resort', 'vacation rental', 'airbnb']):
        return {'main': 'Travel & Vacations', 'sub': 'Hotels'}
    if has_any(['flight', 'airfare', 'round-trip flights', 'airline tickets']):
        return {'main': 'Travel & Vacations', 'sub': 'Flights'}
    if has_any(['car rental', 'rental car']):
        return {'main': 'Travel & Vacations', 'sub': 'Car Rentals'}
    if has_any(['cruise', 'cruise line', 'caribbean cruise']):
        return {'main': 'Travel & Vacations', 'sub': 'Cruises'}
    if has_any(['theme park', 'disneyland', 'disney world', 'universal studios', 'six flags', 'seaworld']):
        return {'main': 'Travel & Vacations', 'sub': 'Theme Parks & Attractions'}
    
    # === FLOWERS & GIFTS ===
    if has_any(['gift card', 'e-gift', 'egift']):
        return {'main': 'Flowers & Gifts', 'sub': 'Gift Cards'}
    if has_any(['greeting card', 'invitation', 'birthday card']):
        return {'main': 'Flowers & Gifts', 'sub': 'Greeting Cards & Invitations'}
    
    # === RESTAURANTS ===
    if has_any(['pizza hut', "domino's", 'little caesars', 'papa johns']):
        return {'main': 'Restaurants', 'sub': 'Pizza'}
    if has_any(['uber eats', 'doordash', 'grubhub', 'postmates']):
        return {'main': 'Restaurants', 'sub': 'Delivery & Take Out'}
    if has_any(["mcdonald's", 'burger king', "wendy's", 'taco bell', 'kfc', 'popeyes', 'fast food',
                'chick-fil-a', 'subway', 'chipotle']):
        return {'main': 'Restaurants', 'sub': 'Fast Food'}
    
    # === OFFICE & SCHOOL SUPPLIES ===
    if has_any(['photo print', 'photo service', 'canvas print', 'photo book', 'walgreens photo']):
        return {'main': 'Office & School Supplies', 'sub': 'Photo Printing'}
    if has_any(['printer paper', 'copy paper', 'notebook paper', 'cardstock']):
        return {'main': 'Office & School Supplies', 'sub': 'Paper'}
    if has_any(['pen', 'pencil', 'marker', 'highlighter', 'crayons', 'colored pencils']):
        return {'main': 'Office & School Supplies', 'sub': 'Pencils, Pens & Markers'}
    if has_any(['binder', 'folder', 'notebook', 'planner', 'calendar', 'sticky notes']):
        return {'main': 'Office & School Supplies', 'sub': 'Office Supplies'}
    if has_any(['tape', 'packing tape', 'scotch tape', 'duct tape', 'packaging supplies']):
        return {'main': 'Office & School Supplies', 'sub': 'Tape & Packaging'}
    
    # === PETS ===
    if has_any(['dog food', 'dog treats', 'puppy food']):
        return {'main': 'Pets', 'sub': 'Dog Food & Treats'}
    if has_any(['cat food', 'cat treats', 'kitten food']):
        return {'main': 'Pets', 'sub': 'Cat Food & Treats'}
    if has_any(['pet toy', 'dog toy', 'cat toy', 'kong ', 'chew toy']):
        return {'main': 'Pets', 'sub': 'Pet Toys'}
    if has_any(['pet bed', 'dog bed', 'cat bed', 'pet carrier', 'leash', 'collar', 'dog crate', 
                'puppy pads', 'training pads', 'cat litter', 'litter box', 'pet kennel', 'dog kennel',
                'pet cage', 'cat tree', 'scratching post', 'pet water fountain', 'dockstream']):
        return {'main': 'Pets', 'sub': 'Pet Supplies'}
    
    # === BABIES & KIDS - ADDITIONAL ===
    if has_any(['bubble blaster', 'bubble machine', 'balloon pump', 'balloon inflator', 'bubble party',
                'sidewalk chalk', 'playsets', 'mga miniverse', 'harry potter', 'honeydukes']):
        return {'main': 'Babies & Kids', 'sub': 'Kids Toys'}
    if has_any(['sherpa lined', 'kids jacket', 'kids coat', 'girls sherpa', 'boys sherpa']):
        return {'main': 'Babies & Kids', 'sub': 'Kids Clothing'}
    
    # === SPORTING GOODS - ADDITIONAL ===
    if has_any(['trampoline', 'bounce pro', 'zupapa']):
        return {'main': 'Sporting Goods', 'sub': 'Outdoor Recreation'}
    if has_any(['inline skate', 'roller skate', 'skateboard', 'longboard', 'scooter', 
                'electric scooter', 'kick scooter', 'e-scooter']):
        return {'main': 'Sporting Goods', 'sub': 'Skating & Scooters'}
    if has_any(['basketball arcade', 'dart board', 'pool table', 'ping pong table', 
                'foosball', 'air hockey', 'arcade game', 'shooting game']):
        return {'main': 'Sporting Goods', 'sub': 'Game Room'}
    if has_any(['heated gloves', 'heated jacket', 'heated vest', 'heated socks']):
        return {'main': 'Sporting Goods', 'sub': 'Heated Apparel'}
    
    # === HOME - ADDITIONAL ===
    if has_any(['trash can', 'garbage can', 'waste bin', 'recycling bin']):
        return {'main': 'Home & Home Improvement', 'sub': 'Trash & Recycling'}
    if has_any(['spin scrubber', 'power scrubber', 'electric scrubber', 'mop pad', 'mopping pad', 
                'swiffer', 'wet jet', 'floor mop']):
        return {'main': 'Home & Home Improvement', 'sub': 'Cleaning Tools'}
    if has_any(['outdoor storage', 'storage shed', 'metal shed', 'patiowell', 'outdoor shed']):
        return {'main': 'Home & Home Improvement', 'sub': 'Outdoor Storage'}
    if has_any(['dehydrator', 'food dehydrator', 'slushie machine', 'slushy machine', 
                'ice maker', 'nugget ice', 'countertop ice', 'waffle maker', 'belgian waffle',
                'magic bullet', 'nutribullet', 'juicer', 'smoothie maker']):
        return {'main': 'Home & Home Improvement', 'sub': 'Small Appliances'}
    if has_any(['embroidery machine', 'sewing machine', 'serger', 'overlock']):
        return {'main': 'Home & Home Improvement', 'sub': 'Sewing & Embroidery'}
    if has_any(['espresso', 'latte', 'cappuccino', 'lavazza', 'nespresso', 'breville', 'opal']):
        return {'main': 'Home & Home Improvement', 'sub': 'Small Appliances'}
    if has_any(['vending machine', 'commercial ice', 'ice machine', 'beverage center', 'wine cooler',
                'beverage cooler', 'beer fridge', 'commercial refrigerator']):
        return {'main': 'Business & Industrial', 'sub': 'Commercial Equipment'}
    if has_any(['hiboy', 'e-scooter with seat', 'electric scooter with seat']):
        return {'main': 'Sporting Goods', 'sub': 'Electric Scooters'}
    if has_any(['m310', 'logitech m', 'wireless mouse']):
        return {'main': 'Computers', 'sub': 'Mice & Keyboards'}
    if has_any(['bk12', 'peak design']):
        return {'main': 'Electronics', 'sub': 'Cameras & Photography'}
    if has_any(['pepper grinder', 'salt grinder', 'spice grinder']):
        return {'main': 'Home & Home Improvement', 'sub': 'Kitchen & Cookware'}
    
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
