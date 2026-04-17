import time
import requests
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from src.utils import normalize_url, get_domain
from src.link_analyzer import LinkAnalyzer

class WebCrawler:
    def __init__(self, link_analyzer: LinkAnalyzer, delay: float = 1.0, user_agent: str = "StatsCrawler/1.0", browser_path: str = None):
        self.link_analyzer = link_analyzer
        self.delay = delay
        self.user_agent = user_agent
        self.browser_path = browser_path
        self.visited_pages = set()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        self.robots_parsers = {}
        self.driver = None
        self.selenium_used = False

    def _get_driver(self):
        if self.driver is None:
            try:
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument(f"user-agent={self.user_agent}")
                
                if self.browser_path:
                    chrome_options.binary_location = self.browser_path
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("[INFO] Selenium WebDriver инициализирован")
            except Exception as e:
                print(f"[ERROR] Не удалось инициализировать Selenium: {e}")
                self.driver = None
        return self.driver

    def _get_robot_parser(self, url: str):
        domain = get_domain(url)
        if domain in self.robots_parsers:
            return self.robots_parsers[domain]
        rp = RobotFileParser()
        robots_url = f"{urlparse(url).scheme}://{domain}/robots.txt"
        rp.set_url(robots_url)
        try:
            rp.read()
        except Exception:
            rp = None
        self.robots_parsers[domain] = rp
        return rp

    def _is_allowed(self, url: str) -> bool:
        rp = self._get_robot_parser(url)
        if rp is None:
            return True
        return rp.can_fetch(self.user_agent, url)

    def _fetch_page_static(self, url: str):
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200 and 'text/html' in resp.headers.get('Content-Type', ''):
                return resp.text
            return None
        except requests.RequestException:
            return None

    def _fetch_page_with_selenium(self, url: str):
        driver = self._get_driver()
        if driver is None:
            return None
        try:
            driver.get(url)
            time.sleep(2)
            return driver.page_source
        except Exception as e:
            print(f"[WARNING] Selenium не смог загрузить {url}: {e}")
            return None

    def _looks_like_csr(self, soup):
        html = str(soup)
        csr_signals = [
            '<div id="app"',
            '<div id="root"',
            'data-reactroot',
            'data-reactid',
            '_nuxt',
            'ng-app',
            'ng-version',
            'v-cloak',
            'data-v-',
            '__NEXT_DATA__',
            'data-server-rendered'
        ]
        return any(signal in html for signal in csr_signals)

    def _fetch_page(self, url: str):
        """Всегда возвращает tuple (html, soup) или (None, None)"""
        html = self._fetch_page_static(url)
        
        if html is None:
            html = self._fetch_page_with_selenium(url)
            if html is None:
                return None, None
            return html, BeautifulSoup(html, 'lxml')
        
        soup = BeautifulSoup(html, 'lxml')
        links = soup.find_all('a', href=True)
        
        # Условия для включения Selenium:
        # 1. Нет ссылок совсем
        # 2. Меньше 3 ссылок И есть признаки CSR
        needs_selenium = False
        
        if len(links) == 0:
            needs_selenium = True
        elif len(links) < 3 and self._looks_like_csr(soup):
            needs_selenium = True
            print(f"[INFO] Страница {url} имеет признаки CSR (ссылок: {len(links)}), пробуем Selenium...")
        
        if needs_selenium:
            if not self.selenium_used:
                print("[INFO] Обнаружены страницы с динамическим контентом, включаю Selenium...")
                self.selenium_used = True
            selenium_html = self._fetch_page_with_selenium(url)
            if selenium_html:
                return selenium_html, BeautifulSoup(selenium_html, 'lxml')
        
        return html, soup

    def _extract_links_from_soup(self, soup, base_url: str):
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            absolute_url = urljoin(base_url, href)
            normalized = normalize_url(absolute_url)
            if normalized.startswith(('http://', 'https://')):
                links.append(normalized)
        return links

    def crawl(self, start_url: str, max_depth: int = 2, max_pages: int = 500):
        queue = [(start_url, 0)]
        queued = {start_url}
        processed = 0

        print(f"[INFO] Начинаем обход {start_url}")
        print(f"[INFO] Глубина: {max_depth}, максимум страниц: {max_pages}, задержка: {self.delay}с")

        try:
            while queue and processed < max_pages:
                url, depth = queue.pop(0)
                if url in self.visited_pages or depth > max_depth:
                    continue
                if not self._is_allowed(url):
                    continue

                html, soup = self._fetch_page(url)
                if html is None or soup is None:
                    continue

                self.visited_pages.add(url)
                processed += 1
                
                if processed % 100 == 0:
                    print(f"[INFO] Обработано страниц: {processed}, в очереди: {len(queue)}")
                
                links = self._extract_links_from_soup(soup, url)
                self.link_analyzer.analyze_page(url, links)

                for link in links:
                    if (link not in self.visited_pages and 
                        link not in queued and 
                        link.startswith(('http://', 'https://'))):
                        if get_domain(link) == get_domain(start_url) or link.startswith(start_url):
                            queue.append((link, depth + 1))
                            queued.add(link)

                time.sleep(self.delay)
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("[INFO] Браузер закрыт")
                except Exception:
                    pass

        print(f"[INFO] Обход завершён. Обработано страниц: {processed}")

    def get_visited_count(self):
        return len(self.visited_pages)