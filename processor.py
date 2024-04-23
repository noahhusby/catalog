import argparse
import json
import logging
import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from flask import Flask, render_template, request, template_rendered

app = Flask(__name__)

# Init the CLI parser
parser = argparse.ArgumentParser(
    prog='catalog - processor',
    description='A web API for searching the index catalog'
)

# Set the CLI arguments (required args will prevent program from running if not included)
parser.add_argument('-i', '--input', help='The indexed input file', required=True)

# Parse the arguments
args = parser.parse_args()
input = args.input

# Configure logging
logging.basicConfig()
logging.root.setLevel(logging.NOTSET)
logging.basicConfig(level=logging.NOTSET)
logger = logging.getLogger('catalog')

# Print current configuration
logger.info("catalog - processor\n-----------------\n")
logger.info("Input: %s", input)

f = open(input)
data = json.load(f)
f.close()


@app.route('/')
def index():
    if 'query' not in request.args.keys():
        return render_template('index.html')
    query = request.args.get('query', '')
    k = int(request.args.get('k', 10))
    results = get_top_k_results(query, k)
    request.args.keys()
    return render_template('index.html', query=query, results=results)  # Display results


@app.route('/api/v1/search', methods=['GET'])
def search_api():
    # TODO: In production env, these would be automated to http res. For class, this should suffice
    query = request.args.get('query', '')
    k = int(request.args.get('k', 10))  # How many results to return
    results = get_top_k_results(query, k)
    return {
        'status': 'success',
        'timestamp': datetime.now(),
        'statusCode': '200',
        'path': '/api/v1/search',
        'result': results
    }


def get_top_k_results(query, k):
    terms = query.lower().split()
    scores = {}

    # Aggregate scores for each URL based on query terms
    for term in terms:
        if term in data:
            for url, score in data[term].items():
                if url in scores:
                    scores[url] += score
                else:
                    scores[url] = score

    # Sort URLs by score in descending order and return the top k
    sorted_urls = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return sorted_urls[:k]


if __name__ == '__main__':
    app.run(port=8080, debug=True)


@contextmanager
def captured_templates(app):
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


class TestProcessorApp(unittest.TestCase):
    def setUp(self):
        # Patch sys.argv for every test to simulate the input file argument
        self.patcher = patch('sys.argv', ['program', '-i', 'input.json'])
        self.mock_argv = self.patcher.start()

        # Patch opening and reading the file
        self.mock_file = patch('builtins.open', mock_open(read_data='{"example": {"http://example.com": 1.0}}'))
        self.mock_file.start()

        # Setup Flask test client
        self.app = app.test_client()
        self.app.testing = True

    def tearDown(self):
        self.patcher.stop()
        self.mock_file.stop()

    def test_index_no_query(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('index.html', response.get_data(as_text=True))

    def test_search_api(self):
        response = self.app.get('/api/v1/search?query=example&k=1')
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(len(json_data['result']), 1)
        self.assertEqual(json_data['result'][0][0], 'http://example.com')

    def test_get_top_k_results(self):
        results = get_top_k_results("example", 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0], "http://example.com")

    def test_index_with_query(self):
        response = self.app.get('/?query=example&k=1')
        self.assertEqual(response.status_code, 200)

    def test_api_with_missing_query(self):
        response = self.app.get('/api/v1/search')
        json_data = response.get_json()
        self.assertEqual(json_data['status'], 'success')
        self.assertEqual(len(json_data['result']), 0)
