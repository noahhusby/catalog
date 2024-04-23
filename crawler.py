import logging
import warnings
from urllib.parse import urlparse

import scrapy
import spacy
import argparse

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
