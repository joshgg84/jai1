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
    _cache_duration = timedelta(hours=1)
    _cache_lock = Lock()
    
    # Free API endpoints
    API_ENDPOINTS = [
        "https://api.exchangerate-api.com/v4/latest/USD",
        "https://api.exchangerate.host/latest?base=USD",
        "https://v6.exchangerate-api.com/v6/latest/USD"
    ]
    
    # Fallback static rates
    FALLBACK_RATES = {
        'USD': 1.0, 'EUR': 1.08, 'GBP': 1.26, 'JPY': 150.0, 'CNY': 7.25,
        'INR': 83.0, 'RUB': 92.0, 'CHF': 0.88, 'CAD': 1.35, 'AUD': 1.52,
        'NZD': 1.65, 'SGD': 1.34, 'HKD': 7.82, 'KRW': 1330.0, 'BRL': 5.00,
        'MXN': 17.00, 'TRY': 32.0, 'SEK': 10.50, 'NOK': 10.80, 'DKK': 6.90,
        'PLN': 4.00, 'THB': 36.0, 'MYR': 4.70, 'IDR': 15600.0, 'PHP': 56.0,
        'VND': 25400.0, 'AED': 3.67, 'SAR': 3.75, 'ILS': 3.70,
        
        # African currencies
        'NGN': 1500.0, 'ZAR': 18.0, 'KES': 130.0, 'GHS': 12.0, 'UGX': 3800.0,
        'TZS': 2600.0, 'RWF': 1300.0, 'BWP': 13.0, 'ZMW': 22.0, 'NAD': 18.0,
        'EGP': 48.0, 'MAD': 10.0, 'TND': 3.1, 'DZD': 135.0, 'XOF': 600.0,
        'XAF': 600.0, 'CDF': 2800.0, 'MUR': 46.0, 'SCR': 14.0, 'ETB': 56.0,
        'MZN': 64.0, 'AOA': 830.0, 'LSL': 18.0, 'SZL': 18.0, 'ZWL': 360.0,
        'LYD': 4.8, 'SDG': 600.0, 'SOS': 570.0, 'DJF': 178.0, 'KMF': 490.0,
        'GMD': 70.0, 'LRD': 190.0, 'SLL': 21000.0, 'MRU': 38.0, 'ERN': 15.0,
        'BIF': 2850.0, 'MWK': 1700.0, 'MGA': 4500.0, 'STN': 23.0, 'CVE': 103.0
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
        'XOF': {'name': 'West African CFA Franc', 'symbol': 'CFA', 'flag': '🌍'},
        'XAF': {'name': 'Central African CFA Franc', 'symbol': 'FCFA', 'flag': '🌍'}
    }
    
    # Currency aliases
    CURRENCY_ALIASES = {
        'usd': 'USD', 'dollar': 'USD', 'dollars': 'USD', 'us dollars': 'USD',
        'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
        'gbp': 'GBP', 'pound': 'GBP', 'pounds': 'GBP', 'sterling': 'GBP',
        'jpy': 'JPY', 'yen': 'JPY', 'japanese yen': 'JPY',
        'cny': 'CNY', 'yuan': 'CNY', 'renminbi': 'CNY',
        'inr': 'INR', 'rupee': 'INR', 'indian rupee': 'INR',
        'rub': 'RUB', 'ruble': 'RUB', 'russian ruble': 'RUB',
        'chf': 'CHF', 'swiss franc': 'CHF',
        'cad': 'CAD', 'canadian dollar': 'CAD',
        'aud': 'AUD', 'australian dollar': 'AUD',
        'nzd': 'NZD', 'new zealand dollar': 'NZD',
        'sgd': 'SGD', 'singapore dollar': 'SGD',
        'hkd': 'HKD', 'hong kong dollar': 'HKD',
        'krw': 'KRW', 'won': 'KRW', 'south korean won': 'KRW',
        'brl': 'BRL', 'real': 'BRL', 'brazilian real': 'BRL',
        'mxn': 'MXN', 'peso': 'MXN', 'mexican peso': 'MXN',
        'try': 'TRY', 'lira': 'TRY', 'turkish lira': 'TRY',
        'ngn': 'NGN', 'naira': 'NGN', 'nigerian naira': 'NGN',
        'zar': 'ZAR', 'rand': 'ZAR', 'south african rand': 'ZAR', 'rands': 'ZAR',
        'kes': 'KES', 'shilling': 'KES', 'kenyan shilling': 'KES', 'ksh': 'KES',
        'ghs': 'GHS', 'cedi': 'GHS', 'ghanaian cedi': 'GHS',
        'ugx': 'UGX', 'ugandan shilling': 'UGX',
        'tzs': 'TZS', 'tanzanian shilling': 'TZS',
        'bwp': 'BWP', 'pula': 'BWP', 'botswana pula': 'BWP',
        'egp': 'EGP', 'egyptian pound': 'EGP',
        'mad': 'MAD', 'dirham': 'MAD', 'moroccan dirham': 'MAD',
        'xof': 'XOF', 'cfa': 'XOF', 'west african cfa': 'XOF',
        'xaf': 'XAF', 'central african cfa': 'XAF'
    }
    
    @classmethod
    def fetch_live_rates(cls):
        """Fetch live exchange rates from API"""
        with cls._cache_lock:
            if cls._last_update and datetime.now() - cls._last_update < cls._cache_duration:
                return True
            
            logger.info("Fetching live exchange rates...")
            
            for api_url in cls.API_ENDPOINTS:
                try:
                    response = requests.get(api_url, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'rates' in data:
                            rates = data['rates']
                        elif 'quotes' in data:
                            rates = {k.replace('USD', ''): v for k, v in data['quotes'].items()}
                            rates['USD'] = 1.0
                        else:
                            continue
                        
                        for currency in cls.CURRENCIES.keys():
                            if currency in rates:
                                cls._rate_cache[currency] = rates[currency]
                            elif currency in cls.FALLBACK_RATES:
                                cls._rate_cache[currency] = cls.FALLBACK_RATES[currency]
                        
                        cls._last_update = datetime.now()
                        logger.info("Live rates fetched successfully")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch: {e}")
                    continue
            
            cls._rate_cache = cls.FALLBACK_RATES.copy()
            cls._last_update = datetime.now()
            return False
    
    @classmethod
    def get_rate(cls, currency):
        """Get exchange rate for a currency (USD base)"""
        currency = currency.upper()
        
        if not cls._rate_cache or not cls._last_update:
            cls.fetch_live_rates()
        
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
        
        # Pattern 1: "150dollars to ksh" (no space between number and currency)
        number_currency_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*([a-z]+)', re.IGNORECASE)
        match = number_currency_pattern.search(msg_lower)
        
        amount = None
        from_currency_alias = None
        
        if match:
            amount = float(match.group(1))
            from_currency_alias = match.group(2)
            logger.info(f"Found number+currency: {amount} {from_currency_alias}")
        else:
            amount_match = re.search(r'(\d+(?:\.\d+)?)', msg_lower)
            if amount_match:
                amount = float(amount_match.group(1))
        
        if not amount:
            return None
        
        # Find all currency codes mentioned
        found_currencies = []
        
        for alias, code in cls.CURRENCY_ALIASES.items():
            if alias in msg_lower:
                if code not in found_currencies:
                    found_currencies.append(code)
        
        if from_currency_alias:
            for alias, code in cls.CURRENCY_ALIASES.items():
                if alias == from_currency_alias:
                    if code not in found_currencies:
                        found_currencies.insert(0, code)
                    break
        
        # Determine from/to based on keywords
        from_curr = None
        to_curr = None
        
        to_keywords = ['to', 'in', 'into', 'for', '->']
        to_pos = len(msg_lower)
        
        for kw in to_keywords:
            pos = msg_lower.find(kw)
            if pos != -1 and pos < to_pos:
                to_pos = pos
        
        if to_pos < len(msg_lower):
            before = msg_lower[:to_pos]
            after = msg_lower[to_pos:]
            
            for code in found_currencies:
                code_lower = code.lower()
                if code_lower in before and from_curr is None:
                    from_curr = code
                elif code_lower in after and to_curr is None:
                    to_curr = code
        else:
            if len(found_currencies) >= 2:
                from_curr = found_currencies[0]
                to_curr = found_currencies[1]
            elif len(found_currencies) == 1:
                from_curr = found_currencies[0]
                to_curr = 'KES' if from_curr != 'KES' else 'NGN'
        
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