import pytest
from src.link_analyzer import LinkAnalyzer
from src.stats_collector import StatsCollector

def test_internal_pages_count():
    """测试 internal_pages 统计（唯一内部链接数）"""
    base_url = "http://test.com"
    analyzer = LinkAnalyzer(base_url)
    # 模拟爬虫分析页面时发现的链接
    analyzer.analyze_page(base_url, [
        "http://test.com/internal1",
        "http://test.com/internal2",
        "http://external.com",
        "http://test.com/internal1"  # 重复链接
    ])
    collector = StatsCollector(base_url)
    # 注意：这里使用位置参数，不要用 visited_count=
    stats = collector.collect(analyzer, 1)  # 第二个参数是 visited_count
    assert stats['statistics']['internal_pages'] == 2

def test_file_links_extraction():
    """测试文档链接提取"""
    base_url = "http://test.com"
    analyzer = LinkAnalyzer(base_url)
    # 正确添加链接：调用 analyze_page
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
    # 手动模拟爬虫发现的死链集合（实际项目中死链由 LinkAnalyzer 内部标记）
    # 注意：broken_links 和 all_links 可能是内部属性，可能需要直接设置
    # 如果直接设置不行，我们可以模拟 analyze_page 时传入状态码信息，但为了简单，先这样尝试
    analyzer.broken_links = {"http://test.com/bad"}
    analyzer.all_links = {"http://test.com/good", "http://test.com/bad"}
    collector = StatsCollector(base_url)
    stats = collector.collect(analyzer, 1)
    assert stats['statistics']['broken_links'] == 1