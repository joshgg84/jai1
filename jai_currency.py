"""JAI - Live Currency Conversion
Handles African, international, and major world currencies with real-time rates.
"""

import re
import json
import logging
import requests
from datetime import datetime, timedelta
from threading import Lock

logger = logging.getLogger(__name__)

class JAICurrency:
    """Currency conversion with real-time rates and caching"""
    
    # Cache for live rates
    _rate_cache = {}
    _last_update = None
    _cache_duration = timedelta(hours=6)  # Update every 6 hours
    _cache_lock = Lock()
    
    # Free API endpoints (more reliable options)
    API_ENDPOINTS = [
        "https://api.exchangerate-api.com/v4/latest/USD",
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json",
        "https://api.frankfurter.app/latest?from=USD"
    ]
    
    # Updated fallback static rates (as of April 2025)
    FALLBACK_RATES = {
        'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 151.50, 'CNY': 7.25,
        'INR': 83.50, 'RUB': 92.0, 'CHF': 0.91, 'CAD': 1.37, 'AUD': 1.52,
        'NZD': 1.65, 'SGD': 1.34, 'HKD': 7.82, 'KRW': 1350.0, 'BRL': 5.10,
        'MXN': 16.80, 'TRY': 32.50, 'SEK': 10.60, 'NOK': 10.70, 'DKK': 6.85,
        'PLN': 3.98, 'THB': 36.50, 'MYR': 4.75, 'IDR': 15800.0, 'PHP': 56.50,
        'VND': 25450.0, 'AED': 3.67, 'SAR': 3.75, 'ILS': 3.72,
        
        # African currencies (updated)
        'NGN': 1550.0,   # Nigerian Naira
        'ZAR': 18.80,    # South African Rand
        'KES': 135.0,    # Kenyan Shilling
        'GHS': 13.50,    # Ghanaian Cedi
        'UGX': 3850.0,    # Ugandan Shilling
        'TZS': 2650.0,    # Tanzanian Shilling
        'RWF': 1320.0,    # Rwandan Franc
        'BWP': 13.50,     # Botswana Pula
        'ZMW': 24.0,      # Zambian Kwacha
        'NAD': 18.80,     # Namibian Dollar
        'EGP': 48.50,     # Egyptian Pound
        'MAD': 10.10,     # Moroccan Dirham
        'TND': 3.12,      # Tunisian Dinar
        'DZD': 134.50,    # Algerian Dinar
        'XOF': 610.0,     # West African CFA
        'XAF': 610.0,     # Central African CFA
        'CDF': 2850.0,    # Congolese Franc
        'MUR': 46.50,     # Mauritian Rupee
        'SCR': 14.20,     # Seychellois Rupee
        'ETB': 57.0,      # Ethiopian Birr
        'MZN': 64.50,     # Mozambican Metical
        'AOA': 835.0,     # Angolan Kwanza
        'LSL': 18.80,     # Lesotho Loti
        'SZL': 18.80,     # Swazi Lilangeni
        'ZWL': 370.0,     # Zimbabwean Dollar
        'LYD': 4.82,      # Libyan Dinar
        'SDG': 605.0,     # Sudanese Pound
        'SOS': 575.0,     # Somali Shilling
        'DJF': 178.50,    # Djiboutian Franc
        'KMF': 495.0,     # Comorian Franc
        'GMD': 71.0,      # Gambian Dalasi
        'LRD': 192.0,     # Liberian Dollar
        'SLL': 21500.0,   # Sierra Leonean Leone
        'MRU': 39.0,      # Mauritanian Ouguiya
        'ERN': 15.0,      # Eritrean Nakfa
        'BIF': 2900.0,    # Burundian Franc
        'MWK': 1750.0,    # Malawian Kwacha
        'MGA': 4600.0,    # Malagasy Ariary
        'STN': 23.50,     # São Tomé Dobra
        'CVE': 104.0      # Cape Verdean Escudo
    }
    
    # Currency information
    CURRENCIES = {
        'USD': {'name': 'US Dollar', 'symbol': '$', 'flag': '🇺🇸'},
        'EUR': {'name': 'Euro', 'symbol': '€', 'flag': '🇪🇺'},
        'GBP': {'name': 'British Pound', 'symbol': '£', 'flag': '🇬🇧'},
        'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'flag': '🇯🇵'},
        'CNY': {'name': 'Chinese Renminbi', 'symbol': '¥', 'flag': '🇨🇳'},
        'INR': {'name': 'Indian Rupee', 'symbol': '₹', 'flag': '🇮🇳'},
        'RUB': {'name': 'Russian Ruble', 'symbol': '₽', 'flag': '🇷🇺'},
        'CHF': {'name': 'Swiss Franc', 'symbol': 'Fr', 'flag': '🇨🇭'},
        'CAD': {'name': 'Canadian Dollar', 'symbol': '$', 'flag': '🇨🇦'},
        'AUD': {'name': 'Australian Dollar', 'symbol': '$', 'flag': '🇦🇺'},
        'NZD': {'name': 'New Zealand Dollar', 'symbol': '$', 'flag': '🇳🇿'},
        'SGD': {'name': 'Singapore Dollar', 'symbol': '$', 'flag': '🇸🇬'},
        'HKD': {'name': 'Hong Kong Dollar', 'symbol': 'HK$', 'flag': '🇭🇰'},
        'KRW': {'name': 'South Korean Won', 'symbol': '₩', 'flag': '🇰🇷'},
        'BRL': {'name': 'Brazilian Real', 'symbol': 'R$', 'flag': '🇧🇷'},
        'MXN': {'name': 'Mexican Peso', 'symbol': '$', 'flag': '🇲🇽'},
        'TRY': {'name': 'Turkish Lira', 'symbol': '₺', 'flag': '🇹🇷'},
        'SEK': {'name': 'Swedish Krona', 'symbol': 'kr', 'flag': '🇸🇪'},
        'NOK': {'name': 'Norwegian Krone', 'symbol': 'kr', 'flag': '🇳🇴'},
        'DKK': {'name': 'Danish Krone', 'symbol': 'kr', 'flag': '🇩🇰'},
        'PLN': {'name': 'Polish Zloty', 'symbol': 'zł', 'flag': '🇵🇱'},
        'THB': {'name': 'Thai Baht', 'symbol': '฿', 'flag': '🇹🇭'},
        'MYR': {'name': 'Malaysian Ringgit', 'symbol': 'RM', 'flag': '🇲🇾'},
        'IDR': {'name': 'Indonesian Rupiah', 'symbol': 'Rp', 'flag': '🇮🇩'},
        'PHP': {'name': 'Philippine Peso', 'symbol': '₱', 'flag': '🇵🇭'},
        'VND': {'name': 'Vietnamese Dong', 'symbol': '₫', 'flag': '🇻🇳'},
        'AED': {'name': 'UAE Dirham', 'symbol': 'د.إ', 'flag': '🇦🇪'},
        'SAR': {'name': 'Saudi Riyal', 'symbol': '﷼', 'flag': '🇸🇦'},
        'ILS': {'name': 'Israeli Shekel', 'symbol': '₪', 'flag': '🇮🇱'},
        'NGN': {'name': 'Nigerian Naira', 'symbol': '₦', 'flag': '🇳🇬'},
        'ZAR': {'name': 'South African Rand', 'symbol': 'R', 'flag': '🇿🇦'},
        'KES': {'name': 'Kenyan Shilling', 'symbol': 'KSh', 'flag': '🇰🇪'},
        'GHS': {'name': 'Ghanaian Cedi', 'symbol': '₵', 'flag': '🇬🇭'},
        'UGX': {'name': 'Ugandan Shilling', 'symbol': 'USh', 'flag': '🇺🇬'},
        'TZS': {'name': 'Tanzanian Shilling', 'symbol': 'TSh', 'flag': '🇹🇿'},
        'RWF': {'name': 'Rwandan Franc', 'symbol': 'FRw', 'flag': '🇷🇼'},
        'BWP': {'name': 'Botswana Pula', 'symbol': 'P', 'flag': '🇧🇼'},
        'ZMW': {'name': 'Zambian Kwacha', 'symbol': 'ZK', 'flag': '🇿🇲'},
        'NAD': {'name': 'Namibian Dollar', 'symbol': 'N$', 'flag': '🇳🇦'},
        'EGP': {'name': 'Egyptian Pound', 'symbol': 'E£', 'flag': '🇪🇬'},
        'MAD': {'name': 'Moroccan Dirham', 'symbol': 'DH', 'flag': '🇲🇦'},
        'TND': {'name': 'Tunisian Dinar', 'symbol': 'DT', 'flag': '🇹🇳'},
        'DZD': {'name': 'Algerian Dinar', 'symbol': 'DA', 'flag': '🇩🇿'},
        'XOF': {'name': 'West African CFA', 'symbol': 'CFA', 'flag': '🌍'},
        'XAF': {'name': 'Central African CFA', 'symbol': 'FCFA', 'flag': '🌍'},
        'CDF': {'name': 'Congolese Franc', 'symbol': 'FC', 'flag': '🇨🇩'},
        'MUR': {'name': 'Mauritian Rupee', 'symbol': '₨', 'flag': '🇲🇺'},
        'SCR': {'name': 'Seychellois Rupee', 'symbol': '₨', 'flag': '🇸🇨'},
        'ETB': {'name': 'Ethiopian Birr', 'symbol': 'Br', 'flag': '🇪🇹'},
        'MZN': {'name': 'Mozambican Metical', 'symbol': 'MT', 'flag': '🇲🇿'},
        'AOA': {'name': 'Angolan Kwanza', 'symbol': 'Kz', 'flag': '🇦🇴'},
        'LSL': {'name': 'Lesotho Loti', 'symbol': 'L', 'flag': '🇱🇸'},
        'SZL': {'name': 'Swazi Lilangeni', 'symbol': 'E', 'flag': '🇸🇿'},
        'ZWL': {'name': 'Zimbabwean Dollar', 'symbol': '$', 'flag': '🇿🇼'},
        'LYD': {'name': 'Libyan Dinar', 'symbol': 'LD', 'flag': '🇱🇾'},
        'SDG': {'name': 'Sudanese Pound', 'symbol': '£', 'flag': '🇸🇩'},
        'SOS': {'name': 'Somali Shilling', 'symbol': 'Sh', 'flag': '🇸🇴'},
        'DJF': {'name': 'Djiboutian Franc', 'symbol': 'Fdj', 'flag': '🇩🇯'},
        'KMF': {'name': 'Comorian Franc', 'symbol': 'CF', 'flag': '🇰🇲'},
        'GMD': {'name': 'Gambian Dalasi', 'symbol': 'D', 'flag': '🇬🇲'},
        'LRD': {'name': 'Liberian Dollar', 'symbol': '$', 'flag': '🇱🇷'},
        'SLL': {'name': 'Sierra Leonean Leone', 'symbol': 'Le', 'flag': '🇸🇱'},
        'MRU': {'name': 'Mauritanian Ouguiya', 'symbol': 'UM', 'flag': '🇲🇷'},
        'ERN': {'name': 'Eritrean Nakfa', 'symbol': 'Nfk', 'flag': '🇪🇷'},
        'BIF': {'name': 'Burundian Franc', 'symbol': 'FBu', 'flag': '🇧🇮'},
        'MWK': {'name': 'Malawian Kwacha', 'symbol': 'MK', 'flag': '🇲🇼'},
        'MGA': {'name': 'Malagasy Ariary', 'symbol': 'Ar', 'flag': '🇲🇬'},
        'STN': {'name': 'São Tomé Dobra', 'symbol': 'Db', 'flag': '🇸🇹'},
        'CVE': {'name': 'Cape Verdean Escudo', 'symbol': 'Esc', 'flag': '🇨🇻'}
    }
    
    # Currency aliases
    CURRENCY_ALIASES = {
        'usd': 'USD', 'dollar': 'USD', 'dollars': 'USD', 'us dollars': 'USD',
        'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
        'gbp': 'GBP', 'pound': 'GBP', 'pounds': 'GBP', 'sterling': 'GBP',
        'jpy': 'JPY', 'yen': 'JPY',
        'cny': 'CNY', 'yuan': 'CNY',
        'inr': 'INR', 'rupee': 'INR',
        'rub': 'RUB', 'ruble': 'RUB',
        'chf': 'CHF', 'swiss franc': 'CHF',
        'cad': 'CAD', 'canadian dollar': 'CAD',
        'aud': 'AUD', 'australian dollar': 'AUD',
        'nzd': 'NZD', 'new zealand dollar': 'NZD',
        'sgd': 'SGD', 'singapore dollar': 'SGD',
        'hkd': 'HKD', 'hong kong dollar': 'HKD',
        'krw': 'KRW', 'won': 'KRW',
        'brl': 'BRL', 'real': 'BRL',
        'mxn': 'MXN', 'peso': 'MXN',
        'try': 'TRY', 'lira': 'TRY',
        'ngn': 'NGN', 'naira': 'NGN', 'nigerian naira': 'NGN',
        'zar': 'ZAR', 'rand': 'ZAR', 'rands': 'ZAR', 'south african rand': 'ZAR',
        'kes': 'KES', 'shilling': 'KES', 'kenyan shilling': 'KES', 'ksh': 'KES',
        'ghs': 'GHS', 'cedi': 'GHS',
        'ugx': 'UGX', 'ugandan shilling': 'UGX',
        'tzs': 'TZS', 'tanzanian shilling': 'TZS',
        'bwp': 'BWP', 'pula': 'BWP',
        'egp': 'EGP', 'egyptian pound': 'EGP',
        'mad': 'MAD', 'dirham': 'MAD'
    }
    
    @classmethod
    def fetch_live_rates(cls):
        """Fetch live exchange rates from API"""
        with cls._cache_lock:
            # Check if cache is still valid
            if cls._last_update and datetime.now() - cls._last_update < cls._cache_duration:
                logger.debug("Using cached exchange rates")
                return True
            
            logger.info("Fetching live exchange rates...")
            
            for api_url in cls.API_ENDPOINTS:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle different API response formats
                        if 'rates' in data:
                            rates = data['rates']
                        elif 'usd' in data and isinstance(data['usd'], dict):
                            # Format from cdn.jsdelivr.net
                            rates = {}
                            for currency, rate in data['usd'].items():
                                rates[currency.upper()] = 1 / rate if rate > 0 else 0
                            rates['USD'] = 1.0
                        else:
                            continue
                        
                        # Update cache with live rates
                        for currency in cls.CURRENCIES.keys():
                            if currency in rates:
                                cls._rate_cache[currency] = rates[currency]
                            elif currency in cls.FALLBACK_RATES:
                                cls._rate_cache[currency] = cls.FALLBACK_RATES[currency]
                        
                        cls._last_update = datetime.now()
                        logger.info(f"✅ Live rates fetched from {api_url}")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch from {api_url}: {e}")
                    continue
            
            # If all APIs fail, use fallback rates
            logger.warning("Using fallback static rates")
            cls._rate_cache = cls.FALLBACK_RATES.copy()
            cls._last_update = datetime.now()
            return False
    
    @classmethod
    def get_rate(cls, currency):
        """Get exchange rate for a currency (USD base)"""
        currency = currency.upper()
        
        # Fetch rates if cache is empty or expired
        if not cls._rate_cache or not cls._last_update:
            cls.fetch_live_rates()
        elif datetime.now() - cls._last_update > cls._cache_duration:
            # Background refresh
            import threading
            threading.Thread(target=cls.fetch_live_rates, daemon=True).start()
        
        return cls._rate_cache.get(currency, cls.FALLBACK_RATES.get(currency))
    
    @classmethod
    def convert(cls, amount, from_curr, to_curr):
        """Convert between currencies using USD as base"""
        from_rate = cls.get_rate(from_curr)
        to_rate = cls.get_rate(to_curr)
        
        if from_rate and to_rate:
            usd_amount = amount / from_rate
            result = usd_amount * to_rate
            return result
        return None
    
    @classmethod
    def format(cls, amount, currency):
        """Format currency with proper symbol and flag"""
        currency_info = cls.CURRENCIES.get(currency.upper(), {})
        symbol = currency_info.get('symbol', currency)
        flag = currency_info.get('flag', '💰')
        
        if currency.upper() in ['JPY', 'KRW', 'RUB', 'IDR', 'VND', 'UGX', 'TZS', 'RWF']:
            return f"{flag} {symbol}{int(amount):,}"
        else:
            return f"{flag} {symbol}{amount:,.2f}"
    
    @classmethod
    def detect_and_convert(cls, message):
        """Detect currency conversion in message and return result"""
        if not message:
            return None
        
        msg_lower = message.lower().strip()
        
        # Extract amount
        amount_match = re.search(r'(\d+(?:\.\d+)?)', msg_lower)
        if not amount_match:
            return None
        
        amount = float(amount_match.group(1))
        
        # Find all currency codes mentioned
        found_currencies = []
        
        for alias, code in cls.CURRENCY_ALIASES.items():
            if alias in msg_lower:
                if code not in found_currencies:
                    found_currencies.append(code)
        
        # Also check for direct 3-letter codes
        code_pattern = r'\b([A-Z]{3})\b'
        code_matches = re.findall(code_pattern, msg_lower.upper())
        for code in code_matches:
            if code in cls.CURRENCIES and code not in found_currencies:
                found_currencies.append(code)
        
        if len(found_currencies) < 2:
            return None
        
        # Determine from/to based on position
        from_curr = None
        to_curr = None
        
        # Look for "to" keyword
        to_keywords = ['to', 'in', 'into', 'for']
        to_pos = len(msg_lower)
        found_keyword = None
        
        for kw in to_keywords:
            pos = msg_lower.find(kw)
            if pos != -1 and pos < to_pos:
                to_pos = pos
                found_keyword = kw
        
        if found_keyword:
            before = msg_lower[:to_pos]
            after = msg_lower[to_pos + len(found_keyword):]
            
            for code in found_currencies:
                code_lower = code.lower()
                if code_lower in before and from_curr is None:
                    from_curr = code
                elif code_lower in after and to_curr is None:
                    to_curr = code
        
        # If no keyword, use first as from, last as to
        if not from_curr or not to_curr:
            if len(found_currencies) >= 2:
                from_curr = found_currencies[0]
                to_curr = found_currencies[-1]
        
        if from_curr and to_curr and from_curr != to_curr:
            result = cls.convert(amount, from_curr, to_curr)
            if result:
                formatted_amount = cls.format(amount, from_curr)
                formatted_result = cls.format(result, to_curr)
                rate = cls.convert(1, from_curr, to_curr)
                
                return f"💱 {formatted_amount} = {formatted_result}\n\n📊 Rate: 1 {from_curr} = {rate:,.4f} {to_curr}"
        
        return None
    
    @classmethod
    def get_supported_currencies(cls):
        """Return list of supported currencies"""
        return list(cls.CURRENCIES.keys())
    
    @classmethod
    def get_currency_info(cls, currency_code):
        """Get information about a specific currency"""
        return cls.CURRENCIES.get(currency_code.upper(), None)
    
    @classmethod
    def get_last_update(cls):
        """Get last update time for rates"""
        if cls._last_update:
            return cls._last_update.strftime("%Y-%m-%d %H:%M:%S")
        return "Not updated yet"