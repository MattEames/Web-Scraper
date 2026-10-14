import unittest
from crawl import normalise_url, get_first_paragraph_from_html, get_heading_from_html, get_images_from_html, get_urls_from_html, extract_page_data

class TestCrawl(unittest.TestCase):
    def test_normlaise_url_https(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalise_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_http(self):
        input_url = "http://www.boot.dev/blog/path"
        actual = normalise_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_strip_trailing_slash(self):
        input_url = "https://www.boot.dev/blog/path/"
        actual = normalise_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_capitalization(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalise_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

class TestCrawlHTML(unittest.TestCase):
    # --- get_heading_from_html Tests ---

    def test_get_heading_from_html_h1(self):
        input_body = "<html><body><h1>Test Title</h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_h2_fallback(self):
        input_body = "<html><body><h2>Fallback Title</h2></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Fallback Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_missing(self):
        input_body = "<html><body><p>No headings here</p></body></html>"
        actual = get_heading_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    # --- get_first_paragraph_from_html Tests ---

    def test_get_first_paragraph_from_html_main_priority(self):
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_fallback(self):
        input_body = "<html><body><p>First paragraph without main</p></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = "First paragraph without main"
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_missing(self):
        input_body = "<html><body><h1>Only Heading</h1></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

class TestCrawlExtractors(unittest.TestCase):
    # --- get_urls_from_html Tests ---

    def test_get_urls_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/path/one">Link 1</a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/path/one"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_multiple_and_missing_href(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <a href="/path/one">Link 1</a>
            <a>No href link</a>
            <a href="https://other.com/path">Link 2</a>
        </body></html>"""
        actual = get_urls_from_html(input_body, input_url)
        expected = [
            "https://crawler-test.com/path/one",
            "https://other.com/path"
        ]
        self.assertEqual(actual, expected)

    # --- get_images_from_html Tests ---

    def test_get_images_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="https://images.com/pic.jpg"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://images.com/pic.jpg"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_missing_src(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img alt="No src attribute"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = []
        self.assertEqual(actual, expected)

class TestExtractPageData(unittest.TestCase):
    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_empty(self):
        input_url = "https://crawler-test.com"
        input_body = "<html><body></body></html>"
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "",
            "first_paragraph": "",
            "outgoing_links": [],
            "image_urls": [],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_multiple(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <main>
                <h2>Fallback Heading</h2>
                <p>Main body text.</p>
            </main>
            <a href="/page1">P1</a>
            <a href="https://external.com">External</a>
            <img src="https://images.com/a.png">
            <img src="/b.png">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Fallback Heading",
            "first_paragraph": "Main body text.",
            "outgoing_links": [
                "https://crawler-test.com/page1",
                "https://external.com",
            ],
            "image_urls": [
                "https://images.com/a.png",
                "https://crawler-test.com/b.png",
            ],
        }
        self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()
