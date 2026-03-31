"""JAI - Currency Conversion
Handles African, international, and major world currencies.
"""

import re

class JAICurrency:
    """Currency conversion for all major currencies"""
    
    # Complete currency list with symbols and rates (USD as base)
    CURRENCIES = {
        # Major World Currencies
        'USD': {'name': 'US Dollar', 'symbol': '$', 'rate_to_usd': 1},
        'EUR': {'name': 'Euro', 'symbol': '€', 'rate_to_usd': 1.08},
        'GBP': {'name': 'British Pound', 'symbol': '£', 'rate_to_usd': 1.26},
        'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'rate_to_usd': 150},
        'CNY': {'name': 'Chinese Renminbi', 'symbol': '¥', 'rate_to_usd': 7.25},
        'INR': {'name': 'Indian Rupee', 'symbol': '₹', 'rate_to_usd': 83},
        'RUB': {'name': 'Russian Ruble', 'symbol': '₽', 'rate_to_usd': 92},
        'CHF': {'name': 'Swiss Franc', 'symbol': 'Fr', 'rate_to_usd': 0.88},
        'CAD': {'name': 'Canadian Dollar', 'symbol': '$', 'rate_to_usd': 1.35},
        'AUD': {'name': 'Australian Dollar', 'symbol': '$', 'rate_to_usd': 1.52},
        'NZD': {'name': 'New Zealand Dollar', 'symbol': '$', 'rate_to_usd': 1.65},
        'SGD': {'name': 'Singapore Dollar', 'symbol': '$', 'rate_to_usd': 1.34},
        'HKD': {'name': 'Hong Kong Dollar', 'symbol': 'HK$', 'rate_to_usd': 7.82},
        'KRW': {'name': 'South Korean Won', 'symbol': '₩', 'rate_to_usd': 1330},
        'BRL': {'name': 'Brazilian Real', 'symbol': 'R$', 'rate_to_usd': 5.00},
        'MXN': {'name': 'Mexican Peso', 'symbol': '$', 'rate_to_usd': 17.00},
        'TRY': {'name': 'Turkish Lira', 'symbol': '₺', 'rate_to_usd': 32},
        'SEK': {'name': 'Swedish Krona', 'symbol': 'kr', 'rate_to_usd': 10.50},
        'NOK': {'name': 'Norwegian Krone', 'symbol': 'kr', 'rate_to_usd': 10.80},
        'DKK': {'name': 'Danish Krone', 'symbol': 'kr', 'rate_to_usd': 6.90},
        'PLN': {'name': 'Polish Zloty', 'symbol': 'zł', 'rate_to_usd': 4.00},
        'THB': {'name': 'Thai Baht', 'symbol': '฿', 'rate_to_usd': 36},
        'MYR': {'name': 'Malaysian Ringgit', 'symbol': 'RM', 'rate_to_usd': 4.70},
        'IDR': {'name': 'Indonesian Rupiah', 'symbol': 'Rp', 'rate_to_usd': 15600},
        'PHP': {'name': 'Philippine Peso', 'symbol': '₱', 'rate_to_usd': 56},
        'VND': {'name': 'Vietnamese Dong', 'symbol': '₫', 'rate_to_usd': 25400},
        'AED': {'name': 'UAE Dirham', 'symbol': 'د.إ', 'rate_to_usd': 3.67},
        'SAR': {'name': 'Saudi Riyal', 'symbol': '﷼', 'rate_to_usd': 3.75},
        'ILS': {'name': 'Israeli Shekel', 'symbol': '₪', 'rate_to_usd': 3.70},
        
        # African Currencies
        'NGN': {'name': 'Nigerian Naira', 'symbol': '₦', 'rate_to_usd': 1500},
        'ZAR': {'name': 'South African Rand', 'symbol': 'R', 'rate_to_usd': 18},
        'KES': {'name': 'Kenyan Shilling', 'symbol': 'KSh', 'rate_to_usd': 130},
        'GHS': {'name': 'Ghanaian Cedi', 'symbol': '₵', 'rate_to_usd': 12},
        'UGX': {'name': 'Ugandan Shilling', 'symbol': 'USh', 'rate_to_usd': 3800},
        'TZS': {'name': 'Tanzanian Shilling', 'symbol': 'TSh', 'rate_to_usd': 2600},
        'RWF': {'name': 'Rwandan Franc', 'symbol': 'FRw', 'rate_to_usd': 1300},
        'BWP': {'name': 'Botswana Pula', 'symbol': 'P', 'rate_to_usd': 13},
        'ZMW': {'name': 'Zambian Kwacha', 'symbol': 'ZK', 'rate_to_usd': 22},
        'NAD': {'name': 'Namibian Dollar', 'symbol': 'N$', 'rate_to_usd': 18},
        'EGP': {'name': 'Egyptian Pound', 'symbol': 'E£', 'rate_to_usd': 48},
        'MAD': {'name': 'Moroccan Dirham', 'symbol': 'DH', 'rate_to_usd': 10},
        'TND': {'name': 'Tunisian Dinar', 'symbol': 'DT', 'rate_to_usd': 3.1},
        'DZD': {'name': 'Algerian Dinar', 'symbol': 'DA', 'rate_to_usd': 135},
        'XOF': {'name': 'West African CFA Franc', 'symbol': 'CFA', 'rate_to_usd': 600},
        'XAF': {'name': 'Central African CFA Franc', 'symbol': 'FCFA', 'rate_to_usd': 600},
        'CDF': {'name': 'Congolese Franc', 'symbol': 'FC', 'rate_to_usd': 2800},
        'MUR': {'name': 'Mauritian Rupee', 'symbol': '₨', 'rate_to_usd': 46},
        'SCR': {'name': 'Seychellois Rupee', 'symbol': '₨', 'rate_to_usd': 14},
        'ETB': {'name': 'Ethiopian Birr', 'symbol': 'Br', 'rate_to_usd': 56},
        'MZN': {'name': 'Mozambican Metical', 'symbol': 'MT', 'rate_to_usd': 64},
        'AOA': {'name': 'Angolan Kwanza', 'symbol': 'Kz', 'rate_to_usd': 830},
        'LSL': {'name': 'Lesotho Loti', 'symbol': 'L', 'rate_to_usd': 18},
        'SZL': {'name': 'Swazi Lilangeni', 'symbol': 'E', 'rate_to_usd': 18},
        'ZWL': {'name': 'Zimbabwean Dollar', 'symbol': '$', 'rate_to_usd': 360},
        'LYD': {'name': 'Libyan Dinar', 'symbol': 'LD', 'rate_to_usd': 4.8},
        'SDG': {'name': 'Sudanese Pound', 'symbol': '£', 'rate_to_usd': 600},
        'SOS': {'name': 'Somali Shilling', 'symbol': 'Sh', 'rate_to_usd': 570},
        'DJF': {'name': 'Djiboutian Franc', 'symbol': 'Fdj', 'rate_to_usd': 178},
        'KMF': {'name': 'Comorian Franc', 'symbol': 'CF', 'rate_to_usd': 490},
        'GMD': {'name': 'Gambian Dalasi', 'symbol': 'D', 'rate_to_usd': 70},
        'LRD': {'name': 'Liberian Dollar', 'symbol': '$', 'rate_to_usd': 190},
        'SLL': {'name': 'Sierra Leonean Leone', 'symbol': 'Le', 'rate_to_usd': 21000},
        'MRU': {'name': 'Mauritanian Ouguiya', 'symbol': 'UM', 'rate_to_usd': 38},
        'ERN': {'name': 'Eritrean Nakfa', 'symbol': 'Nfk', 'rate_to_usd': 15},
        'BIF': {'name': 'Burundian Franc', 'symbol': 'FBu', 'rate_to_usd': 2850},
        'MWK': {'name': 'Malawian Kwacha', 'symbol': 'MK', 'rate_to_usd': 1700},
        'MGA': {'name': 'Malagasy Ariary', 'symbol': 'Ar', 'rate_to_usd': 4500},
        'STN': {'name': 'São Tomé and Príncipe Dobra', 'symbol': 'Db', 'rate_to_usd': 23},
        'CVE': {'name': 'Cape Verdean Escudo', 'symbol': 'Esc', 'rate_to_usd': 103}
    }
    
    # Currency aliases for user input
    CURRENCY_ALIASES = {
        'usd': 'USD', 'dollar': 'USD', 'dollars': 'USD', 'us dollars': 'USD',
        'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
        'gbp': 'GBP', 'pound': 'GBP', 'pounds': 'GBP', 'sterling': 'GBP', 'british pound': 'GBP',
        'jpy': 'JPY', 'yen': 'JPY', 'japanese yen': 'JPY',
        'cny': 'CNY', 'yuan': 'CNY', 'renminbi': 'CNY', 'chinese yuan': 'CNY',
        'inr': 'INR', 'rupee': 'INR', 'indian rupee': 'INR',
        'rub': 'RUB', 'ruble': 'RUB', 'russian ruble': 'RUB',
        'chf': 'CHF', 'swiss franc': 'CHF', 'franc': 'CHF',
        'cad': 'CAD', 'canadian dollar': 'CAD',
        'aud': 'AUD', 'australian dollar': 'AUD',
        'nzd': 'NZD', 'new zealand dollar': 'NZD',
        'sgd': 'SGD', 'singapore dollar': 'SGD',
        'hkd': 'HKD', 'hong kong dollar': 'HKD',
        'krw': 'KRW', 'won': 'KRW', 'south korean won': 'KRW',
        'brl': 'BRL', 'real': 'BRL', 'brazilian real': 'BRL',
        'mxn': 'MXN', 'peso': 'MXN', 'mexican peso': 'MXN',
        'try': 'TRY', 'lira': 'TRY', 'turkish lira': 'TRY',
        
        # African currencies
        'ngn': 'NGN', 'naira': 'NGN', 'nigerian naira': 'NGN',
        'zar': 'ZAR', 'rand': 'ZAR', 'south african rand': 'ZAR', 'rands': 'ZAR',
        'kes': 'KES', 'shilling': 'KES', 'kenyan shilling': 'KES', 'kenya shilling': 'KES',
        'ghs': 'GHS', 'cedi': 'GHS', 'ghanaian cedi': 'GHS',
        'ugx': 'UGX', 'ugandan shilling': 'UGX',
        'tzs': 'TZS', 'tanzanian shilling': 'TZS',
        'bwp': 'BWP', 'pula': 'BWP', 'botswana pula': 'BWP',
        'egp': 'EGP', 'egyptian pound': 'EGP',
        'mad': 'MAD', 'dirham': 'MAD', 'moroccan dirham': 'MAD',
        'xof': 'XOF', 'cfa': 'XOF', 'west african cfa': 'XOF',
        'xaf': 'XAF', 'central african cfa': 'XAF'
    }
    
    @staticmethod
    def convert(amount, from_curr, to_curr):
        """Convert between currencies using USD as base"""
        from_rate = JAICurrency.CURRENCIES.get(from_curr.upper(), {}).get('rate_to_usd')
        to_rate = JAICurrency.CURRENCIES.get(to_curr.upper(), {}).get('rate_to_usd')
        
        if from_rate and to_rate:
            usd_amount = amount / from_rate
            result = usd_amount * to_rate
            return result
        return None
    
    @staticmethod
    def format(amount, currency):
        """Format currency with proper symbol"""
        currency_info = JAICurrency.CURRENCIES.get(currency.upper(), {})
        symbol = currency_info.get('symbol', currency)
        
        formatted = f"{amount:,.2f}"
        
        # Special formatting for certain currencies
        if currency.upper() in ['NGN', 'GHS', 'KES', 'UGX', 'TZS', 'ZAR']:
            return f"{symbol}{formatted}"
        elif currency.upper() in ['JPY', 'KRW', 'RUB']:
            return f"{symbol}{int(amount):,}"
        else:
            return f"{formatted} {symbol}"
    
    @staticmethod
    def detect_and_convert(message):
        """Detect currency conversion in message and return result"""
        msg_lower = message.lower()
        
        # Extract amount
        amount_match = re.search(r'(\d+(?:\.\d+)?)', msg_lower)
        if not amount_match:
            return None
        
        amount = float(amount_match.group(1))
        
        # Find all currency codes mentioned
        found_currencies = []
        for alias, code in JAICurrency.CURRENCY_ALIASES.items():
            if alias in msg_lower:
                if code not in found_currencies:
                    found_currencies.append(code)
        
        # If we found two currencies, determine from/to
        if len(found_currencies) >= 2:
            # Look for direction indicators
            to_pos = float('inf')
            if 'to' in msg_lower:
                to_pos = msg_lower.find('to')
            if 'in' in msg_lower:
                in_pos = msg_lower.find('in')
                if in_pos < to_pos:
                    to_pos = in_pos
            
            to_curr = None
            from_curr = None
            for code in found_currencies:
                code_lower = code.lower()
                if code_lower in msg_lower and msg_lower.find(code_lower) > to_pos:
                    to_curr = code
                else:
                    if from_curr is None:
                        from_curr = code
                    elif to_curr is None:
                        to_curr = code
            
            if not to_curr and len(found_currencies) >= 2:
                from_curr, to_curr = found_currencies[0], found_currencies[1]
            
            if from_curr and to_curr:
                result = JAICurrency.convert(amount, from_curr, to_curr)
                if result:
                    formatted_amount = JAICurrency.format(amount, from_curr)
                    formatted_result = JAICurrency.format(result, to_curr)
                    return f"💰 {formatted_amount} = {formatted_result}"
        
        # If only one currency found, assume converting to NGN
        elif len(found_currencies) == 1:
            from_curr = found_currencies[0]
            to_curr = 'NGN'
            result = JAICurrency.convert(amount, from_curr, to_curr)
            if result:
                formatted_amount = JAICurrency.format(amount, from_curr)
                formatted_result = JAICurrency.format(result, to_curr)
                return f"💰 {formatted_amount} = {formatted_result}"
        
        return None
    
    @staticmethod
    def get_supported_currencies():
        """Return list of supported currencies"""
        return list(JAICurrency.CURRENCIES.keys())
    
    @staticmethod
    def get_currency_info(currency_code):
        """Get information about a specific currency"""
        return JAICurrency.CURRENCIES.get(currency_code.upper(), None)