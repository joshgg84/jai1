"""JAI - Currency Conversion
Handles African and international currency conversion.
"""

import re

class JAICurrency:
    """Currency conversion for African and world currencies"""
    
    # African and world currencies
    CURRENCIES = {
        # West Africa
        'NGN': {'name': 'Nigerian Naira', 'symbol': '₦', 'rate_to_usd': 1500},
        'GHS': {'name': 'Ghanaian Cedi', 'symbol': '₵', 'rate_to_usd': 12},
        'XOF': {'name': 'West African CFA Franc', 'symbol': 'CFA', 'rate_to_usd': 600},
        
        # East Africa
        'KES': {'name': 'Kenyan Shilling', 'symbol': 'KSh', 'rate_to_usd': 130},
        'UGX': {'name': 'Ugandan Shilling', 'symbol': 'USh', 'rate_to_usd': 3800},
        'TZS': {'name': 'Tanzanian Shilling', 'symbol': 'TSh', 'rate_to_usd': 2600},
        'RWF': {'name': 'Rwandan Franc', 'symbol': 'FRw', 'rate_to_usd': 1300},
        
        # Southern Africa
        'ZAR': {'name': 'South African Rand', 'symbol': 'R', 'rate_to_usd': 18},
        'BWP': {'name': 'Botswana Pula', 'symbol': 'P', 'rate_to_usd': 13},
        'ZMW': {'name': 'Zambian Kwacha', 'symbol': 'ZK', 'rate_to_usd': 22},
        'NAD': {'name': 'Namibian Dollar', 'symbol': 'N$', 'rate_to_usd': 18},
        
        # Central Africa
        'XAF': {'name': 'Central African CFA Franc', 'symbol': 'FCFA', 'rate_to_usd': 600},
        'CDF': {'name': 'Congolese Franc', 'symbol': 'FC', 'rate_to_usd': 2800},
        
        # North Africa
        'EGP': {'name': 'Egyptian Pound', 'symbol': 'E£', 'rate_to_usd': 48},
        'MAD': {'name': 'Moroccan Dirham', 'symbol': 'DH', 'rate_to_usd': 10},
        'TND': {'name': 'Tunisian Dinar', 'symbol': 'DT', 'rate_to_usd': 3.1},
        'DZD': {'name': 'Algerian Dinar', 'symbol': 'DA', 'rate_to_usd': 135},
        
        # Major world currencies
        'USD': {'name': 'US Dollar', 'symbol': '$', 'rate_to_usd': 1},
        'EUR': {'name': 'Euro', 'symbol': '€', 'rate_to_usd': 1.08},
        'GBP': {'name': 'British Pound', 'symbol': '£', 'rate_to_usd': 1.26}
    }
    
    # Currency aliases for user input
    CURRENCY_ALIASES = {
        'usd': 'USD', 'dollar': 'USD', 'dollars': 'USD',
        'eur': 'EUR', 'euro': 'EUR', 'euros': 'EUR',
        'gbp': 'GBP', 'pound': 'GBP', 'pounds': 'GBP', 'sterling': 'GBP',
        'ngn': 'NGN', 'naira': 'NGN', 'nairas': 'NGN',
        'kes': 'KES', 'shilling': 'KES', 'shillings': 'KES', 'kenyan shilling': 'KES',
        'zar': 'ZAR', 'rand': 'ZAR', 'rands': 'ZAR', 'south african rand': 'ZAR',
        'ghs': 'GHS', 'cedi': 'GHS', 'cedis': 'GHS',
        'ugx': 'UGX', 'ugandan shilling': 'UGX',
        'tzs': 'TZS', 'tanzanian shilling': 'TZS',
        'xof': 'XOF', 'cfa': 'XOF', 'west african cfa': 'XOF',
        'xaf': 'XAF', 'central african cfa': 'XAF',
        'bwp': 'BWP', 'pula': 'BWP',
        'egp': 'EGP', 'egyptian pound': 'EGP',
        'mad': 'MAD', 'moroccan dirham': 'MAD'
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
        
        # Different formatting for different currencies
        if currency.upper() in ['NGN', 'GHS', 'KES', 'UGX', 'TZS', 'ZAR']:
            return f"{symbol}{formatted}"
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
        
        # Find currencies in message
        from_curr = None
        to_curr = None
        
        for alias, code in JAICurrency.CURRENCY_ALIASES.items():
            if alias in msg_lower:
                if from_curr is None:
                    from_curr = code
                else:
                    to_curr = code
        
        # If only one currency found, assume converting to NGN
        if from_curr and not to_curr:
            to_curr = 'NGN'
        
        if from_curr and to_curr:
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