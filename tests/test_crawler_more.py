import pytest
from src.link_analyzer import LinkAnalyzer
from src.stats_collector import StatsCollector

def test_internal_pages_count():
    """测试 internal_pages 统计（唯一内部链接数）"""
    base_url = "http://test.com"
    analyzer = LinkAnalyzer(base_url)
    analyzer.analyze_page(base_url, [
        "http://test.com/internal1",
        "http://test.com/internal2",
        "http://external.com",
        "http://test.com/internal1"  # 重复链接
    ])
    collector = StatsCollector(base_url)
    stats = collector.collect(analyzer, 1)
    assert stats['statistics']['internal_pages'] == 2

def test_file_links_extraction():
    """测试文档链接提取"""
    base_url = "http://test.com"
    analyzer = LinkAnalyzer(base_url)
    analyzer.analyze_page(base_url, [
        "http://test.com/doc.pdf",
        "http://test.com/file.docx",
        "http://test.com/data.doc",
        "http://test.com/normal.html"
    ])
    collector = StatsCollector(base_url)
    stats = collector.collect(analyzer, 1)
    assert stats['statistics']['unique_file_links_doc_docx_pdf'] == 3

def test_broken_links_count():
    """测试死链统计"""
    base_url = "http://test.com"
    analyzer = LinkAnalyzer(base_url)
    
    analyzer._link_status_cache["http://test.com/bad"] = True
    analyzer.broken_urls.add("http://test.com/bad")
    
    collector = StatsCollector(base_url)
    stats = collector.collect(analyzer, 1)
    assert stats['statistics']['broken_links'] == 1