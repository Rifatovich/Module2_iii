import requests
from urllib.parse import urlparse
from collections import defaultdict
from src.utils import get_domain, is_internal_link, is_subdomain, extract_file_extension

class LinkAnalyzer:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.base_domain = get_domain(base_url)
        self.total_links_found = 0
        self.internal_urls = set()
        self.broken_urls = set()
        self.internal_subdomains = set()
        self.external_links_total = 0
        self.unique_external_domains = set()
        self.unique_file_links = set()
        self._link_status_cache = {}

    def analyze_page(self, page_url: str, links: list):
        for link in links:
            self.total_links_found += 1
            
            is_internal = is_internal_link(link, self.base_url)
            
            if is_internal:
                self.internal_urls.add(link)
                
                if is_subdomain(link, self.base_domain):
                    self.internal_subdomains.add(get_domain(link))
                
                ext = extract_file_extension(link)
                if ext in ('doc', 'docx', 'pdf'):
                    self.unique_file_links.add(link)
                
                if link not in self._link_status_cache:
                    is_broken = self._check_link_status(link)
                    self._link_status_cache[link] = is_broken
                    if is_broken:
                        self.broken_urls.add(link)
            else:
                self.external_links_total += 1
                self.unique_external_domains.add(get_domain(link))
                
                ext = extract_file_extension(link)
                if ext in ('doc', 'docx', 'pdf'):
                    self.unique_file_links.add(link)

    def _check_link_status(self, url: str, timeout: int = 10):
        urls_to_try = [url]
        
        if url.startswith('http://'):
            urls_to_try.append(url.replace('http://', 'https://'))
        elif url.startswith('https://'):
            urls_to_try.append(url.replace('https://', 'http://'))
        
        for test_url in urls_to_try:
            try:
                resp = requests.head(test_url, timeout=timeout, allow_redirects=True)
                
                if resp.status_code == 403:
                    return False
                
                if resp.status_code == 405:
                    resp = requests.get(test_url, timeout=timeout, stream=True)
                    if resp.status_code >= 400 and resp.status_code != 403:
                        return True
                    resp.close()
                    return False
                
                if resp.status_code >= 400:
                    if resp.status_code == 403:
                        return False
                    return True
                
                return False
                
            except (requests.Timeout, requests.ConnectionError, requests.RequestException):
                continue
        
        return True

    def get_statistics(self):
        return {
            'total_links_found': self.total_links_found,
            'internal_pages': len(self.internal_urls),
            'broken_links': len(self.broken_urls),
            'internal_subdomains': len(self.internal_subdomains),
            'external_links_total': self.external_links_total,
            'unique_external_resources': len(self.unique_external_domains),
            'unique_file_links_doc_docx_pdf': len(self.unique_file_links),
        }