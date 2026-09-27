import decimal
from typing import Dict, Union


# Hardcoded exchange rates for demonstration purposes based on base EUR.
# In a real application, this would fetch from a live API or database.
_EXCHANGE_RATES: Dict[str, decimal.Decimal] = {
    'EUR': decimal.Decimal('1.0000'),
    'USD': decimal.Decimal('1.0850'),
    'GBP': decimal.Decimal('0.8550'),
    'NGN': decimal.Decimal('1600.0000'),
}


class CurrencyValidationError(Exception):
    """Exception raised when currency validation fails."""
    pass


def validate_currency_code(currency_code: str) -> None:
    """
    Validates that a currency code is supported.

    Args:
        currency_code: The 3-letter ISO currency code.

    Raises:
        CurrencyValidationError: If the currency code is not supported.
    """
    if currency_code not in _EXCHANGE_RATES:
        raise CurrencyValidationError(f"Unsupported currency: {currency_code}")


def validate_amount(amount: Union[int, float, decimal.Decimal]) -> decimal.Decimal:
    """
    Validates and converts an amount to decimal.Decimal.

    Args:
        amount: Input amount as int, float or Decimal.

    Returns:
        decimal.Decimal: The validated amount.

    Raises:
        CurrencyValidationError: If amount is negative.
    """
    try:
        dec_amount = decimal.Decimal(str(amount))
    except (decimal.InvalidOperation, ValueError):
        raise CurrencyValidationError(f"Invalid amount format: {amount}")

    if dec_amount < 0:
        raise CurrencyValidationError("Amount cannot be negative.")
    
    return dec_amount


def convert_currency(
    amount: Union[int, float, decimal.Decimal],
    from_currency: str,
    to_currency: str
) -> decimal.Decimal:
    """
    Converts amount from one currency to another using fixed exchange rates.

    Args:
        amount: The original amount.
        from_currency: ISO code of original currency.
        to_currency: ISO code of target currency.

    Returns:
        decimal.Decimal: The converted amount.

    Raises:
        CurrencyValidationError: If currencies are unsupported or amount invalid.
    """
    validate_currency_code(from_currency)
    validate_currency_code(to_currency)
    validated_amount = validate_amount(amount)

    if from_currency == to_currency:
        return validated_amount

    # Convert to base (EUR) then to target currency
    rate_from = _EXCHANGE_RATES[from_currency]
    rate_to = _EXCHANGE_RATES[to_currency]
    
    amount_in_eur = validated_amount / rate_from
    converted_amount = amount_in_eur * rate_to
    
    # Round to standard 2 decimal places or appropriate precision for currency
    # For NGN example, precision might differ, but using 2 for standardisation.
    return converted_amount.quantize(decimal.Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)