"""Which network address a request came from, without believing what the visitor says."""

from ipaddress import ip_address, ip_network

from starlette.requests import Request

UNKNOWN = "unknown"


def client_ip(request: Request, trusted_proxy_count: int) -> str:
    """The visitor's address.

    Forwarding servers append the address they saw to `X-Forwarded-For`. Only the entries
    added by our own servers (counted from the right) are believed; anything further left
    was supplied by the visitor and could be invented.
    """
    if trusted_proxy_count > 0:
        header = request.headers.get("x-forwarded-for", "")
        entries = [entry.strip() for entry in header.split(",") if entry.strip()]
        if len(entries) >= trusted_proxy_count:
            candidate = entries[-trusted_proxy_count]
            try:
                return str(ip_address(candidate))
            except ValueError:
                pass
    return request.client.host if request.client else UNKNOWN


def ip_hint(ip: str) -> str | None:
    """A shortened address for the list of signed-in devices: enough to recognise, no more."""
    try:
        address = ip_address(ip)
    except ValueError:
        return None
    prefix = 24 if address.version == 4 else 48
    return str(ip_network(f"{address}/{prefix}", strict=False))
