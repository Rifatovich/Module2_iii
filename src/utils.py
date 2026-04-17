import re
from urllib.parse import urlparse, urljoin, urlunparse

def normalize_url(url: str, base_url: str = None) -> str:
    if base_url:
        url = urljoin(base_url, url)
    parsed = urlparse(url)
    parsed = parsed._replace(fragment='')
    query_params = sorted(parsed.query.split('&')) if parsed.query else []
    query = '&'.join(query_params)
    parsed = parsed._replace(query=query)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    return urlunparse(parsed._replace(scheme=scheme, netloc=netloc))

def get_domain(url: str) -> str:
    return urlparse(url).netloc

def is_same_domain(url1: str, url2: str) -> bool:
    return get_domain(url1) == get_domain(url2)

def is_internal_link(link_url: str, base_url: str) -> bool:
    link_domain = get_domain(link_url)
    base_domain = get_domain(base_url)
    return link_domain == base_domain or link_domain.endswith('.' + base_domain)

def is_subdomain(subdomain_url: str, base_domain: str) -> bool:

    sub_domain = get_domain(subdomain_url)
    if sub_domain == base_domain:
        return False
    return sub_domain.endswith('.' + base_domain)

def extract_file_extension(url: str) -> str:
    path = urlparse(url).path
    match = re.search(r'\.([a-z0-9]+)$', path, re.IGNORECASE)
    return match.group(1).lower() if match else ''