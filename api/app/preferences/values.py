"""Tidying what the owner types: one name per city, rupees from lakhs."""

from decimal import Decimal

LAKH = 100_000

# Old and informal names of Indian cities, each mapped to the one name that is stored.
CITY_NAMES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "blr": "Bengaluru",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
    "bombay": "Mumbai",
    "mumbai": "Mumbai",
    "navi mumbai": "Navi Mumbai",
    "madras": "Chennai",
    "chennai": "Chennai",
    "calcutta": "Kolkata",
    "kolkata": "Kolkata",
    "poona": "Pune",
    "pune": "Pune",
    "hyderabad": "Hyderabad",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "noida": "Noida",
    "trivandrum": "Thiruvananthapuram",
    "thiruvananthapuram": "Thiruvananthapuram",
    "cochin": "Kochi",
    "kochi": "Kochi",
    "mysore": "Mysuru",
    "mysuru": "Mysuru",
    "baroda": "Vadodara",
    "vadodara": "Vadodara",
    "ahmedabad": "Ahmedabad",
    "remote": "Remote (India)",
    "remote india": "Remote (India)",
    "remote (india)": "Remote (India)",
    "wfh": "Remote (India)",
    "work from home": "Remote (India)",
}


def normalise_place(place: str) -> str:
    key = " ".join(place.casefold().replace(",", " ").replace("-", " ").split())
    key = key.removesuffix(" india") if key not in CITY_NAMES else key
    return CITY_NAMES.get(key, " ".join(place.split()))


def clean_list(values: list[str]) -> list[str]:
    """Spaces tidied and repeats removed, whatever their capitals."""
    seen: dict[str, str] = {}
    for value in values:
        tidy = " ".join(value.split())
        if tidy:
            seen.setdefault(tidy.casefold(), tidy)
    return list(seen.values())


def rupees(lakhs: Decimal) -> int:
    return int(lakhs * LAKH)


def lakhs(amount: int) -> Decimal:
    value = (Decimal(amount) / LAKH).quantize(Decimal("0.01"))
    return value.quantize(Decimal(1)) if value == value.to_integral_value() else value.normalize()
