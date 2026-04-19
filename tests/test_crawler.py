import pytest
from bs4 import BeautifulSoup
from src.link_analyzer import LinkAnalyzer
from src.crawler import WebCrawler
from src.stats_collector import StatsCollector


def mock_fetch_page(self, url):
    """模拟 _fetch_page，直接返回构造的 HTML 和 soup"""
    if url == "http://test-site.com":
        html = '''<html><body>
            <a href="/internal1">内链1</a>
            <a href="/internal2">内链2</a>
            <a href="http://external.com">外链</a>
            <a href="/doc.pdf">PDF文件</a>
            <a href="/broken">死链</a>
        </body></html>'''
    elif url == "http://test-site.com/internal1":
        html = "<html>page1</html>"
    elif url == "http://test-site.com/internal2":
        html = "<html>page2</html>"
    elif url == "http://external.com":
        html = "<html>external</html>"
    else:
        html = None
    if html is None:
        return None, None
    soup = BeautifulSoup(html, 'lxml')
    return html, soup


def test_crawler_with_mock(monkeypatch):
    # 替换 _fetch_page 方法
    monkeypatch.setattr(WebCrawler, '_fetch_page', mock_fetch_page)
    # 同时禁用 Selenium 相关方法（以防万一）
    monkeypatch.setattr(WebCrawler, '_get_driver', lambda self: None)
    monkeypatch.setattr(WebCrawler, '_fetch_page_with_selenium', lambda self, url: None)

    base_url = "http://test-site.com"
    analyzer = LinkAnalyzer(base_url)
    crawler = WebCrawler(analyzer, delay=0)
    crawler.crawl(base_url, max_depth=1, max_pages=10)

    collector = StatsCollector(base_url)
    visited_count = crawler.get_visited_count()
    stats = collector.collect(analyzer, visited_count)

    # 根据你的爬虫逻辑调整预期值
    assert stats['statistics']['total_pages_processed'] >= 1
    assert stats['statistics']['total_links_found'] >= 1
    print("测试通过")