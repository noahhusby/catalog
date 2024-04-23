import logging
import sys
import unittest
import warnings
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import scrapy
import spacy
import argparse

from scrapy import crawler
from scrapy.crawler import CrawlerProcess


def start():
    """Starts the crawler workflow. The command line argument parser is initialized here."""

    # Init the CLI parser
    parser = argparse.ArgumentParser(
        prog='catalog - crawler utility',
        description='A set of tools to crawl and compile data from the internet'
    )

    # Set the CLI arguments (required args will prevent program from running if not included)
    parser.add_argument('-u', '--url', help='A list of URLs to crawl (comma separated)', required=True)
    parser.add_argument('-d', '--depth', help='Set the depth of the crawl', choices=range(1, 3), default=1, type=int)
    parser.add_argument('-p', '--pages', help='Set the max number of pages for the crawl', default=100, type=int)
    parser.add_argument('-o', '--output', help='Set the name of the output file', default='output.jsonl')

    # Parse the arguments
    args = parser.parse_args()
    url = args.url
    depth = args.depth
    pages = args.pages
    output = args.output

    # Configure logging
    logging.basicConfig()
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger('catalog')
    logging.getLogger('scrapy').propagate = False
    warnings.filterwarnings("ignore", category=scrapy.exceptions.ScrapyDeprecationWarning)

    # Print current configuration
    logger.info("catalog - crawler utility\n-----------------\n")
    logger.info("URL: %s", url)
    logger.info("Max Depth: %d", depth)
    logger.info("Max Pages: %d", pages)
    logger.info("Output: %s", output)

    # Start crawling
    crawl(url, depth, pages, output)


def crawl(urls: str, depth, pages, output):
    """
    Initializes the crawler process.

    :param urls: A list of URLs to crawl (comma separated)
    :param depth: Set the depth of the crawl
    :param pages: Set the max number of pages for the crawl
    :param output: Set the name of the output file
    :return: Nil
    """

    logger = logging.getLogger('catalog')

    # Initialize new crawler process with output destination, depth limit, and page limit
    # User Agent is set to google crawler to avoid being rate limited
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'FEEDS': {
            'data/crawler/' + output: {
                "format": "jsonl"
            }
        },
        'DEPTH_LIMIT': depth,
        'PAGE_LIMIT': pages
    })

    # Start crawling
    logger.info('Crawling website! This could take a while...')
    process.crawl(WikiSpider, start_uri=urls.split(','))
    process.start()
    logger.info('Finished crawling website!')
    logger.info('The results have been compiled into: /data/crawler/%s', output)


class WikiSpider(scrapy.Spider):
    def __init__(self, start_uri, *args, **kwargs):
        """
        Initialize the spider for crawly
        :param start_uri: A list of URLs to crawl (comma separated)
        :param args: A list of additional arguments to pass to the spider
        :param kwargs: A list of additional arguments to pass to the spider
        """
        super(WikiSpider, self).__init__(*args, **kwargs)
        self.start_urls = start_uri
        self.allowed_domains = [urlparse(u).netloc for u in start_uri]
        # Set up NLP to remove stop words (reduce total space in output)
        self.nlp = spacy.load("en_core_web_sm")

    name = 'scraper'

    def parse(self, response):
        response.selector.remove_namespaces()
        # Remove all CSS / HTML from text
        all_text = response.xpath('//*[not(self::script or self::style)]/text()').getall()
        clean_text = ' '.join([text.strip() for text in all_text if text.strip()])

        # Remove all stop words (spacy was simplier to implement that NTLK in this instance)
        doc = self.nlp(clean_text)
        filtered_words = [token.text for token in doc if not token.is_stop]
        clean_text = ' '.join(filtered_words)

        # Return KV pair of website URL (Document ID going forward) and the cleaned text
        yield {
            response.url: clean_text,
        }

        # Extract all links and follow them up to the defined depth
        links = response.css('a::attr(href)').re(r'^/wiki/[^:#]*$')  # Filter for valid article links
        for link in links:
            yield response.follow(link, self.parse)


if __name__ == '__main__':
    start()


class TestCrawlerUtility(unittest.TestCase):
    def test_required_url_argument(self):
        """
        Checks to ensure the program exits when no valid URL is attached
        """
        with self.assertRaises(SystemExit):
            sys.argv = ['program', '-d', '2', '-p', '50', '-o', 'test.jsonl']
            start()

    @patch('crawler.crawl')
    def test_default_values(self, mock_crawl):
        """
        Checks to make sure crawl was called with the proper arguments
        """
        sys.argv = ['program', '-u', 'https://example.com']
        start()
        # Assuming crawl() is mocked, verify the call with default arguments
        mock_crawl.assert_called_with('https://example.com', 1, 100, 'output.jsonl')

    @patch('crawler.crawl')
    def test_all_arguments(self, mock_crawl):
        sys.argv = ['program', '-u', 'https://example.com', '-d', '2', '-p', '50', '-o', 'test.jsonl']
        start()
        # Again, assuming crawl() is mocked
        mock_crawl.assert_called_with('https://example.com', 2, 50, 'test.jsonl')


class TestCrawlFunction(unittest.TestCase):
    @unittest.mock.patch('crawler.CrawlerProcess')
    def test_crawler_initialization(self, mock_process):
        crawl('https://example.com', 1, 100, 'output.jsonl')
        spacy.load = MagicMock()
        # Make sure all the scrapy process methods were called
        mock_process.assert_called_once()
        process_instance = mock_process.return_value
        process_instance.crawl.assert_called_once()
        process_instance.start.assert_called_once()


class TestWikiSpider(unittest.TestCase):
    def setUp(self):
        self.spider = WikiSpider(start_uri=['https://example.com'])

    @unittest.mock.patch('scrapy.spiders.Spider.start_requests')
    def test_initial_urls(self, mock_start):
        self.assertEqual(self.spider.start_urls, ['https://example.com'])
        self.assertIn('example.com', self.spider.allowed_domains)

    def test_parse_function(self):
        # Mock the response object to provide necessary data for parsing
        response = MagicMock()
        response.url = 'https://example.com'
        response.xpath.return_value.getall.return_value = ['Example content']
        # Assuming spacy NLP is mocked too
        result = next(self.spider.parse(response))
        self.assertIn('https://example.com', result)
