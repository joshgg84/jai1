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
    _cache_duration = timedelta(hours=6)
    _cache_lock = Lock()
    
    # Free API endpoints
    API_ENDPOINTS = [
        "https://api.exchangerate-api.com/v4/latest/USD",
        "https://api.frankfurter.app/latest?from=USD",
        "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.min.json"
    ]
    
    # Fallback static rates (accurate as of April 2025)
    FALLBACK_RATES = {
        'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 154.50, 'CNY': 7.24,
        'INR': 83.60, 'RUB': 92.50, 'CHF': 0.91, 'CAD': 1.38, 'AUD': 1.53,
        'NZD': 1.66, 'SGD': 1.35, 'HKD': 7.83, 'KRW': 1355.0, 'BRL': 5.15,
        'MXN': 16.90, 'TRY': 32.80, 'SEK': 10.70, 'NOK': 10.80, 'DKK': 6.88,
        'PLN': 4.02, 'THB': 36.80, 'MYR': 4.78, 'IDR': 15900.0, 'PHP': 56.80,
        'VND': 25500.0, 'AED': 3.67, 'SAR': 3.75, 'ILS': 3.74,
        
        # African currencies
        'NGN': 1550.0,   # Nigerian Naira
        'ZAR': 18.90,    # South African Rand
        'KES': 136.0,    # Kenyan Shilling
        'EGP': 48.80,    # Egyptian Pound
        'GHS': 13.80,    # Ghanaian Cedi
        'UGX': 3880.0,   # Ugandan Shilling
        'TZS': 2680.0,   # Tanzanian Shilling
        'RWF': 1330.0,   # Rwandan Franc
        'BWP': 13.60,    # Botswana Pula
        'ZMW': 24.50,    # Zambian Kwacha
        'NAD': 18.90,    # Namibian Dollar
        'MAD': 10.15,    # Moroccan Dirham
        'TND': 3.15,     # Tunisian Dinar
        'DZD': 134.80,   # Algerian Dinar
        'XOF': 612.0,    # West African CFA
        'XAF': 612.0,    # Central African CFA
        'CDF': 2880.0,   # Congolese Franc
        'MUR': 47.0,     # Mauritian Rupee
        'SCR': 14.50,    # Seychellois Rupee
        'ETB': 57.50,    # Ethiopian Birr
        'MZN': 65.0,     # Mozambican Metical
        'AOA': 840.0,    # Angolan Kwanza
        'LSL': 18.90,    # Lesotho Loti
        'SZL': 18.90,    # Swazi Lilangeni
    }
    
    # Currency information with correct symbols
    CURRENCIES = {
        'USD': {'name': 'US Dollar', 'symbol': '$', 'flag': '🇺🇸'},
        'EUR': {'name': 'Euro', 'symbol': '€', 'flag': '🇪🇺'},
        'GBP': {'name': 'British Pound', 'symbol': '£', 'flag': '🇬🇧'},
        'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'flag': '🇯🇵'},
        'CNY': {'name': 'Chinese Yuan', 'symbol': '¥', 'flag': '🇨🇳'},
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
        'EGP': {'name': 'Egyptian Pound', 'symbol': 'E£', 'flag': '🇪🇬'},
        'GHS': {'name': 'Ghanaian Cedi', 'symbol': '₵', 'flag': '🇬🇭'},
        'UGX': {'name': 'Ugandan Shilling', 'symbol': 'USh', 'flag': '🇺🇬'},
        'TZS': {'name': 'Tanzanian Shilling', 'symbol': 'TSh', 'flag': '🇹🇿'},
        'RWF': {'name': 'Rwandan Franc', 'symbol': 'FRw', 'flag': '🇷🇼'},
        'BWP': {'name': 'Botswana Pula', 'symbol': 'P', 'flag': '🇧🇼'},
        'ZMW': {'name': 'Zambian Kwacha', 'symbol': 'ZK', 'flag': '🇿🇲'},
        'NAD': {'name': 'Namibian Dollar', 'symbol': 'N$', 'flag': '🇳🇦'},
        'MAD': {'name': 'Moroccan Dirham', 'symbol': 'DH', 'flag': '🇲🇦'},
        'TND': {'name': 'Tunisian Dinar', 'symbol': 'DT', 'flag': '🇹🇳'},
        'DZD': {'name': 'Algerian Dinar', 'symbol': 'DA', 'flag': '🇩🇿'},
        'XOF': {'name': 'West African CFA', 'symbol': 'CFA', 'flag': '🌍'},
        'XAF': {'name': 'Central African CFA', 'symbol': 'FCFA', 'flag': '🌍'},
    }
    
    # Currency aliases
    CURRENCY_ALIASES = {
        'usd': 'USD', 'dollar': 'USD', 'dollars': 'USD',
        'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
        'gbp': 'GBP', 'pound': 'GBP', 'pounds': 'GBP',
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
        'ngn': 'NGN', 'naira': 'NGN',
        'zar': 'ZAR', 'rand': 'ZAR', 'rands': 'ZAR',
        'kes': 'KES', 'shilling': 'KES', 'ksh': 'KES',
        'egp': 'EGP', 'egyptian pound': 'EGP',
        'ghs': 'GHS', 'cedi': 'GHS',
        'mad': 'MAD', 'dirham': 'MAD',
        'bwp': 'BWP', 'pula': 'BWP',
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
                    response = requests.get(api_url, timeout=15)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'rates' in data:
                            rates = data['rates']
                        elif 'usd' in data and isinstance(data['usd'], dict):
                            rates = {}
                            for currency, rate in data['usd'].items():
                                rates[currency.upper()] = 1 / rate if rate > 0 else 0
                            rates['USD'] = 1.0
                        else:
                            continue
                        
                        for currency in cls.CURRENCIES.keys():
                            if currency in rates:
                                cls._rate_cache[currency] = rates[currency]
                            elif currency in cls.FALLBACK_RATES:
                                cls._rate_cache[currency] = cls.FALLBACK_RATES[currency]
                        
                        cls._last_update = datetime.now()
                        logger.info(f"Live rates fetched")
                        return True
                        
                except Exception as e:
                    logger.warning(f"Failed to fetch: {e}")
                    continue
            
            cls._rate_cache = cls.FALLBACK_RATES.copy()
            cls._last_update = datetime.now()
            return True
    
    @classmethod
    def get_rate(cls, currency):
        """Get exchange rate for a currency (USD base)"""
        currency = currency.upper()
        
        if not cls._rate_cache or not cls._last_update:
            cls.fetch_live_rates()
        
        return cls._rate_cache.get(currency, cls.FALLBACK_RATES.get(currency, 1.0))
    
    @classmethod
    def convert(cls, amount, from_curr, to_curr):
        """Convert between currencies using USD as base"""
        try:
            from_rate = cls.get_rate(from_curr)
            to_rate = cls.get_rate(to_curr)
            
            if from_rate and to_rate:
                usd_amount = amount / from_rate
                result = usd_amount * to_rate
                return result
            return amount
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return amount
    
    @classmethod
    def format(cls, amount, currency):
        """Format currency with proper symbol and flag"""
        currency_info = cls.CURRENCIES.get(currency.upper(), {})
        symbol = currency_info.get('symbol', currency)
        flag = currency_info.get('flag', '💰')
        
        # Format amount
        if currency.upper() in ['JPY', 'KRW', 'RUB', 'IDR', 'VND', 'UGX', 'TZS', 'RWF']:
            formatted_amount = f"{int(amount):,}"
        else:
            formatted_amount = f"{amount:,.2f}"
        
        # Put symbol before or after based on currency
        if currency.upper() in ['EUR', 'GBP', 'USD', 'CAD', 'AUD', 'NZD', 'SGD', 'NGN', 'KES', 'ZAR', 'EGP']:
            return f"{flag} {symbol}{formatted_amount}"
        else:
            return f"{flag} {formatted_amount} {symbol}"
    
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
        
        # Find currencies
        found_currencies = []
        for alias, code in cls.CURRENCY_ALIASES.items():
            if alias in msg_lower:
                if code not in found_currencies:
                    found_currencies.append(code)
        
        # Also check 3-letter codes
        code_pattern = r'\b([A-Z]{3})\b'
        code_matches = re.findall(code_pattern, msg_lower.upper())
        for code in code_matches:
            if code in cls.CURRENCIES and code not in found_currencies:
                found_currencies.append(code)
        
        if len(found_currencies) < 2:
            return None
        
        # Determine from/to based on "to" keyword
        from_curr = None
        to_curr = None
        
        if 'to' in msg_lower:
            parts = msg_lower.split('to')
            before = parts[0]
            after = parts[1] if len(parts) > 1 else ''
            
            for code in found_currencies:
                if code.lower() in before and from_curr is None:
                    from_curr = code
                elif code.lower() in after and to_curr is None:
                    to_curr = code
        else:
            # First currency is from, last is to
            if len(found_currencies) >= 2:
                from_curr = found_currencies[0]
                to_curr = found_currencies[-1]
        
        if from_curr and to_curr and from_curr != to_curr:
            result = cls.convert(amount, from_curr, to_curr)
            formatted_amount = cls.format(amount, from_curr)
            formatted_result = cls.format(result, to_curr)
            rate = cls.convert(1, from_curr, to_curr)
            
            return f"💱 {formatted_amount} = {formatted_result}\n\n📊 Rate: 1 {from_curr} = {rate:,.4f} {to_curr}"
        
        return None