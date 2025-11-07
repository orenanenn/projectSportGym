from decimal import Decimal, InvalidOperation
from django import template

register = template.Library()

try:
    from bson.decimal128 import Decimal128
except Exception:
    class Decimal128:
        pass

@register.filter(name="money2")
def money2(value):
    if value is None or value == "":
        return ""
    if isinstance(value, Decimal128):
        try:
            value = value.to_decimal()
        except Exception:
            return ""
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)
    return f"{dec:.2f}"
