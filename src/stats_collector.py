import json
from datetime import datetime, timezone
from datetime import datetime
from src.link_analyzer import LinkAnalyzer

class StatsCollector:
    def __init__(self, target_url: str):
        self.target_url = target_url
        self.crawl_date = None

    def collect(self, link_analyzer: LinkAnalyzer, pages_processed: int) -> dict:
        stats = link_analyzer.get_statistics()
        result = {
            "target_site": self.target_url,
            "crawl_date": datetime.now(timezone.utc).isoformat(),
            "statistics": {
                "total_pages_processed": pages_processed,
                "total_links_found": stats['total_links_found'],
                "internal_pages": stats['internal_pages'],
                "broken_links": stats['broken_links'],
                "internal_subdomains": stats['internal_subdomains'],
                "external_links_total": stats['external_links_total'],
                "unique_external_resources": stats['unique_external_resources'],
                "unique_file_links_doc_docx_pdf": stats['unique_file_links_doc_docx_pdf']
            }
        }
        self.crawl_date = result["crawl_date"]
        return result

    def save_to_json(self, data: dict, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)