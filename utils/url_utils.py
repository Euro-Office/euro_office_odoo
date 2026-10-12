import ipaddress
import logging
import socket
from urllib.parse import urlparse

from odoo.addons.euro_office_odoo.utils import config_utils

_logger = logging.getLogger(__name__)


class InvalidURLError(ValueError):
    """Raised when a URL must not be fetched server-side."""


def replace_public_url_to_internal(env, url):
    public_url = config_utils.get_doc_server_public_url(env)
    inner_url = config_utils.get_doc_server_inner_url(env)
    if inner_url and inner_url != public_url:
        _logger.info("Replace public url %s to internal url %s", public_url, inner_url)
        url = url.replace(public_url, inner_url)
    return url


def _hostname_is_publicly_routable(hostname):
    try:
        address_infos = socket.getaddrinfo(hostname, None)
    except OSError:
        return False
    for address_info in address_infos:
        try:
            address = ipaddress.ip_address(address_info[4][0])
        except ValueError:
            return False
        if not address.is_global:
            return False
    return True


def validate_public_http_url(
    env,
    url,
    allow_document_server=True,
    allow_odoo_base=False,
    extra_allowed_hosts=(),
):
    """Check that ``url`` is safe to fetch server-side.

    Only absolute http(s) URLs are accepted. Hosts that resolve to
    private, loopback, link-local, or other non-routable addresses are
    rejected unless the URL targets the configured Document Server (or,
    optionally, the configured Odoo base URL), which legitimately live on
    internal networks in many deployments.

    Note: DNS is resolved once here and again by the HTTP client, so a
    DNS-rebinding adversary with a public domain can still pivot; an
    allowlist on the Document Server hostname plus egress filtering is
    recommended for high-security deployments.

    Raises InvalidURLError when the URL must not be fetched.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise InvalidURLError("only absolute http(s) URLs are allowed")

    allowed_hosts = set(extra_allowed_hosts)
    if allow_document_server:
        for configured_url in (config_utils.get_doc_server_public_url(env), config_utils.get_doc_server_inner_url(env)):
            configured_host = urlparse(configured_url).hostname
            if configured_host:
                allowed_hosts.add(configured_host.lower())
    if allow_odoo_base:
        odoo_host = urlparse(config_utils.get_base_or_odoo_url(env)).hostname
        if odoo_host:
            allowed_hosts.add(odoo_host.lower())

    hostname = parsed.hostname.lower()
    if hostname in allowed_hosts:
        return

    if not _hostname_is_publicly_routable(hostname):
        raise InvalidURLError("hostname resolves to a non-public address and may not be fetched")
