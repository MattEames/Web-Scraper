from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup, Tag
from typing import TypedDict
import requests
import asyncio
import aiohttp

def normalise_url(url: str) -> str:
    parsed = urlsplit(url)
    full_path = f"{parsed.netloc}{parsed.path}"

    if full_path.endswith("/"):
        full_path = full_path[:-1]
    return full_path

def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h_tag = soup.find("h1") or soup.find("h2")

    if isinstance(h_tag, Tag):
        return h_tag.get_text(strip=True)
    return ""

def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main_tag = soup.find("main")
    p_tag = None
    if isinstance(main_tag, Tag):
        p_tag = main_tag.find("p")
    if not p_tag:
        p_tag = soup.find("p")
    if isinstance(p_tag, Tag):
        return p_tag.get_text(strip=True)
    return ""

def get_urls_from_html(html: str, base_url: str) -> list[str]:
    urls = []
    soup = BeautifulSoup(html, "html.parser")
    for a_tag in soup.find_all("a"):
        href = a_tag.get("href")
        if href:
            urls.append(urljoin(base_url, href))
    return urls

def get_images_from_html(html: str, base_url: str) -> list[str]:
    image_urls = []
    soup = BeautifulSoup(html, "html.parser")
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src")
        if src:
            image_urls.append(urljoin(base_url, src))
    return image_urls

class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

def extract_page_data(html: str, page_url: str) -> PageData:
    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }

def get_html(url: str) -> str:
    headers = {"User-Agent": "BootCrawler/1.0"}

    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        raise Exception(f"Network error while fetching {url}: {e}")

    if response.status_code >= 400:
        raise Exception(f"HTTP error {response.status_code} fetching {url}")

    content_type = response.headers.get("Content-Type", "")
    if "text/html" not in content_type:
        raise Exception(f"Invalid Content-Type '{content_type}' for {url}, expected 'text/html'")

    return response.text

def crawl_page(base_url: str, current_url: str = None, page_data: dict = None) -> dict:

    if current_url is None:
        current_url = base_url
    if page_data is None:
        page_data = {}

    base_domain = urlsplit(base_url).netloc
    current_domain = urlsplit(current_url).netloc
    if base_domain != current_domain:
        return page_data

    normalised_current = normalise_url(current_url)

    if normalised_current in page_data:
        return page_data

    print(f"crawling: {current_url}")
    try:
        html = get_html(current_url)
    except Exception as e:
        print(f"Error fetching {current_url}: {e}")
        return page_data

    data = extract_page_data(html, current_url)
    page_data[normalised_current] = data

    for next_url in data["outgoing_links"]:
        crawl_page(base_url, next_url, page_data)

    return page_data

class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrency: int = 5, max_pages: int = 100):
        self.base_url = base_url
        self.base_domain = urlsplit(base_url).netloc
        self.page_data = {}
        self.visited = set()
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None
        self.max_pages = max_pages
        self.should_stop = False
        self.all_tasks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def add_page_visit(self, normalised_url: str) -> bool:
        async with self.lock:
            if self.should_stop:
                return False
            if normalised_url in self.visited:
                return False

            self.visited.add(normalised_url)
            return True

    async def get_html(self, url: str) -> str:
        headers = {"User-Agent": "BootCrawler/1.0"}
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status >= 400:
                    raise Exception(f"HTTP error {response.status} fetching {url}")

                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    raise Exception(
                        f"Invalid Content-Type '{content_type}' for {url}, expected 'text/html'"
                    )

                return await response.text()
        except Exception as e:
            raise Exception(f"Error fetching {url}: {e}")

    async def crawl_page(self, current_url: str):

        if self.should_stop:
            return
        # 1. Ensure current_url is on the same domain as base_domain
        current_domain = urlsplit(current_url).netloc
        if current_domain != self.base_domain:
            return

        # 2. Check and record visit safely
        normalised_current = normalise_url(current_url)
        if not await self.add_page_visit(normalised_current):
            return

        # 3. Limit concurrency using the semaphore
        async with self.semaphore:
            if self.should_stop:
                return
            print(f"crawling: {current_url}")
            try:
                html = await self.get_html(current_url)
            except Exception as e:
                print(e)
                return

        # 4. Extract page data and update page_data dictionary safely
        data = extract_page_data(html, current_url)
        async with self.lock:
            self.page_data[normalised_current] = data
            if len(self.page_data) >= self.max_pages:
                if not self.should_stop:
                    print("Reached maximum number of pages to crawl.")
                    self.should_stop = True
        if self.should_stop:
            return

        # 5. Create concurrent tasks for outgoing links
        tasks = []
        for next_url in data["outgoing_links"]:
            if self.should_stop:
                break

            async def task_wrapper(url):
                current_task = asyncio.current_task()
                self.all_tasks.add(current_task)
                try:
                    await self.crawl_page(url)
                finally:
                    self.all_tasks.remove(current_task)

            task = asyncio.create_task(self.crawl_page(next_url))
            tasks.append(task)

        if tasks:
            await asyncio.gather(*tasks)

    async def crawl(self) -> dict:
        await self.crawl_page(self.base_url)
        return self.page_data


async def crawl_site_async(base_url: str, max_concurrency: int = 5, max_pages: int = 100) -> dict:
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()
