import sys
import asyncio
from crawl import get_html, crawl_page, crawl_site_async
from json_report import write_json_report

async def main():
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    if len(sys.argv) > 4:
        print("too many arguments provided")
        sys.exit(1)

    base_url = sys.argv[1]
    max_concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    print(f"starting crawl of: {base_url} (max_concurrency: {max_concurrency}, max_pages: {max_pages})")

    page_data = await crawl_site_async(base_url, max_concurrency=max_concurrency, max_pages=max_pages)

    write_json_report(page_data)

    print("\n--- Crawl Complete ---")
    print(f"Total pages crawled: {len(page_data)}\n")
    print("Report written to report.json")


if __name__ == "__main__":
    asyncio.run(main())
