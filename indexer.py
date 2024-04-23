import argparse
import json
import logging
from pathlib import Path
from alive_progress import alive_bar

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def start():
    """Starts the crawler workflow. The command line argument parser is initialized here."""

    # Init the CLI parser
    parser = argparse.ArgumentParser(
        prog='catalog - indexer utility',
        description='A set of tools to index a catalog of crawled websites'
    )

    # Set the CLI arguments (required args will prevent program from running if not included)
    parser.add_argument('-i', '--input', help='An input file from the crawler', required=True)
    parser.add_argument('-o', '--output', help='A output file of indexed data', default='output.json')

    # Parse the arguments
    args = parser.parse_args()
    input = args.input
    output = args.output

    # Configure logging
    logging.basicConfig()
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    logger = logging.getLogger('catalog')

    # Print current configuration
    logger.info("catalog - indexer utility\n-----------------\n")
    logger.info("Input: %s", input)
    logger.info("Output: %s", output)

    # Start indexing data
    index_data(input, output)


def index_data(input: str, output: str):
    logger = logging.getLogger('catalog')

    # Load the documents from the crawler
    documents = load_data(input)
    doc_keys = list(documents.keys())
    doc_values = list(documents.values())

    # Vectorize the documents using sklearn
    # I added stop_words at this step as well, regardless of whether stop words were already addressed
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(doc_values)

    # Get feature names
    feature_names = vectorizer.get_feature_names_out()

    # create inverted index for provided terms
    logger.info('Generating inverted index for provided terms')
    with alive_bar(sum(1 for _ in enumerate(feature_names))) as bar:
        # Inverted index using string keys
        inverted_index = {}
        for idx, feature in enumerate(feature_names):
            inverted_index[feature] = {}
            for doc_idx in range(tfidf_matrix.shape[0]):
                score = tfidf_matrix[doc_idx, idx]
                if score > 0:
                    inverted_index[feature][doc_keys[doc_idx]] = score
            bar()

    # Cosine similarity matrix
    cosine_sim_matrix = cosine_similarity(tfidf_matrix)

    def get_similar_documents(doc_key, cosine_sim_matrix):
        doc_id = doc_keys.index(doc_key)
        similar_docs = cosine_sim_matrix[doc_id]
        return [(doc_keys[i], score) for i, score in enumerate(similar_docs) if i != doc_id and score > 0]

    print(7)
    # Outputs
    Path("data/indexer").mkdir(parents=True, exist_ok=True)
    with open('data/indexer/' + output, "w") as outfile:
        json.dump(inverted_index, outfile)
    print(8)


def load_data(dataset):
    # Initialize empty dictionary
    data_dict = {}

    # Import jsonl file
    # the size of a standard json file was giving python some trouble,
    # so I opted for using jsonl and just parsing it line by line
    with open(dataset, 'r') as file:
        for line in file:
            # Parse each line as JSON and update the dictionary
            json_data = json.loads(line)
            data_dict.update(json_data)
    return data_dict


if __name__ == '__main__':
    start()
