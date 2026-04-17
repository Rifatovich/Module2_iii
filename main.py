import argparse
import os
import sys
from pathlib import Path
from src.link_analyzer import LinkAnalyzer
from src.crawler import WebCrawler
from src.stats_collector import StatsCollector

# Определяем папку, где находится main.py
SCRIPT_DIR = Path(__file__).parent.absolute()

def main():
    parser = argparse.ArgumentParser(description="Веб-краулер для сбора статистики сайта")
    parser.add_argument("--url", default="https://spbu.ru", help="Стартовый URL (по умолчанию https://spbu.ru)")
    parser.add_argument("--depth", type=int, default=2, help="Максимальная глубина обхода (по умолчанию 2)")
    parser.add_argument("--max-pages", type=int, default=500, help="Максимальное количество обрабатываемых страниц (по умолчанию 500)")
    parser.add_argument("--delay", type=float, default=1.0, help="Задержка между запросами в секундах")
    parser.add_argument("--output", default="output/stats.json", help="Путь для сохранения JSON-файла со статистикой (относительно папки со скриптом)")
    parser.add_argument("--browser-path", default=None, help="Путь к браузеру для JS-рендера (например, C:/Program Files/Google/Chrome/Application/chrome.exe)")
    args = parser.parse_args()

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = SCRIPT_DIR / output_path
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Запуск краулера для {args.url} (глубина={args.depth}, макс. страниц={args.max_pages})")
    print(f"Результат будет сохранён в: {output_path}")
    if args.browser_path:
        print(f"Используется браузер: {args.browser_path}")
    
    analyzer = LinkAnalyzer(args.url)
    crawler = WebCrawler(analyzer, delay=args.delay, browser_path=args.browser_path)
    crawler.crawl(args.url, max_depth=args.depth, max_pages=args.max_pages)

    collector = StatsCollector(args.url)
    stats = collector.collect(analyzer, crawler.get_visited_count())
    collector.save_to_json(stats, str(output_path))

    print(f"\nОбход завершён. Обработано страниц: {crawler.get_visited_count()}")
    print(f"Статистика сохранена в {output_path}")
    
    s = stats['statistics']
    print("\nКраткая статистика:")
    print(f"  Всего обработано страниц: {s['total_pages_processed']}")
    print(f"  Всего найдено ссылок: {s['total_links_found']}")
    print(f"  Уникальных внутренних страниц: {s['internal_pages']}")
    print(f"  Неработающих ссылок: {s['broken_links']}")
    print(f"  Внутренних поддоменов: {s['internal_subdomains']}")
    print(f"  Ссылок на внешние ресурсы (всего): {s['external_links_total']}")
    print(f"  Уникальных внешних ресурсов: {s['unique_external_resources']}")
    print(f"  Уникальных ссылок на файлы (doc/docx/pdf): {s['unique_file_links_doc_docx_pdf']}")

if __name__ == "__main__":
    main()