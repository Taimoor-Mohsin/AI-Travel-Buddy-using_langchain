from currency import CurrencyConverter

_cc = None


def convert(amount: float, to: str) -> float:
    global _cc
    if _cc is None:
        _cc = CurrencyConverter(
            fallback_on_missing_rate=True, fallback_on_wrong_date=True
        )
    try:
        return float(_cc.convert(amount, "USD", to.upper()))
    except Exception:
        return amount  # fallback
