"""Small helpers for request-scoped security decisions.

Centralizes the "which IP address should the application log / rate-limit
on?" question so that trusted-proxy configuration applies consistently.

Default behaviour (no TRUSTED_PROXIES configured): trust
``request.remote_addr`` only, ignore X-Forwarded-For.  This is the safe
default when the app is directly reachable on a private network.

When TRUSTED_PROXIES is configured (a tuple of hostnames/CIDRs), the
leftmost (outermost) X-Forwarded-For entry that is NOT listed as a
trusted proxy is used as the client IP.  This lets a WSGI deployment
behind a trusted reverse proxy record real client addresses without
trusting spoofable headers from untrusted hops.
"""
from flask import current_app, request


def _trusted_proxies():
    proxies = getattr(current_app.config, 'TRUSTED_PROXIES', None)
    if not proxies:
        return ()
    if isinstance(proxies, str):
        return tuple(p.strip() for p in proxies.split(',') if p.strip())
    return tuple(proxies)


def client_ip():
    """Return the best-known client IP address for the current request.

    Honors ``TRUSTED_PROXIES``: when set, walks the X-Forwarded-For chain
    from right to left (server-side → client-side) and picks the first
    entry that is not a trusted proxy.  When no trusted proxies are
    configured, returns ``request.remote_addr`` — the safe default.
    """
    proxies = _trusted_proxies()
    if not proxies:
        return request.remote_addr

    remote = request.remote_addr
    if remote in proxies:
        forwarded = request.headers.get('X-Forwarded-For', '')
        entries = [e.strip() for e in forwarded.split(',') if e.strip()]
        for entry in reversed(entries):
            if entry not in proxies:
                return entry
        return remote
    return remote


def user_agent_string():
    return request.headers.get('User-Agent')
