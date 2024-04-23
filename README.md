<!--suppress HtmlDeprecatedAttribute -->
<div align="center">

# catalog

<p>
  <b>A scraper & information retrieval system utilizing an inverted index. </b>
  <br/>
  ⚠️ This is part of a <a href="https://github.com/noahhusby/university"><strong>larger collection of projects</strong></a> for university. ⚠️
  <br/><br/>
</p>

[![](https://img.shields.io/github/license/noahhusby/catalog)](https://github.com/noahhusby/catalog/blob/main/LICENSE)
</div>

## Table of Contents
- [Abstract](https://github.com/noahhusby/catalog#abstract)
- [Project Overview](https://github.com/noahhusby/catalog/tree/main/#overview)
  - [Component Workflow](https://github.com/noahhusby/catalog/tree/main/#component-workflow)
- [Design](https://github.com/noahhusby/rent/blob/main/#design)
  - [Crawling & Indexing](https://github.com/noahhusby/catalog/tree/main/#crawling--indexing)
  - [Processing](https://github.com/noahhusby/catalog/tree/main/#processing)
- [Relational Schema](https://github.com/noahhusby/rent/blob/main/relational_schema.pdf)
- [Sample Data](https://github.com/noahhusby/rent/tree/main#sql-scripts)
  - [As SQL File](https://github.com/noahhusby/rent/blob/main/sample_data.sql)
- Application
  - [Backend (/src)](https://github.com/noahhusby/rent/tree/main/src)
  - [Frontend (/web)](https://github.com/noahhusby/rent/tree/main/web)
- [Video Walkthrough](https://youtu.be/dTSDwB6lwqI)

## Abstract

This project contains a processor and two utilities (crawler and indexer) for building and hosting an information retrieval system. The goal is to crawl specified wikipedia pages and build an inverted index that can then be served to the end user as a search engine. The processor is powered by Flask and hosts a static webpage that the end user can interact with to make search queries. A REST API is also exposed for returning the search results in JSON format. 

## Overview

The utilities for building the inverted index should be able to be called through the CLI and require no other tools or programs to use. As such, all utilities were designed to use the `argparse` library to simplify the process for handling arguments. Each of the components should logically integrate with each other to build the inverted index.

### Component Workflow
1. **Crawler:** Specify web sources (wikipedia pages) to scrape. The crawler should build a file that the indexer can parse.
2. **Indexer:** Open crawler build file and create an inverted index and output it to the local directory.
3. **Processor:** Open indexed file and host a webpage for searching through the index.

At the end of the workflow, only the processor should need to be running to handle incoming requests. The index should have already been built with the crawler and indexer.

## Design

The following guidelines were created for the project:

### Crawling & Indexing
1. The crawler must be able to handle multiple URLs at once.
2. The crawler must be able to have the depth and max pages variables assigned from the CLI.
3. All files between components must use a common format (json, xml) in place of a more efficient binary format. This is for readability / expandability of the system.
4. The indexer should display the current status of building large indexes. (logs, progress bar, etc.)

### Processing
1. A web interface must be exposed for the end user to interact with the search engine.
2. A REST API must be exposed for returning the direct search results.
3. The processor must have an argument for defining the target index file.

## Architecture

### Overview

![Architecture Overview](https://raw.githubusercontent.com/noahhusby/catalog/main/docs/catalog_infra.png)

The architecture is composed of three major components:
1. Crawler
   2. Based on `scrapy` library
   3. Implements `spacy` to remove stop words from compiled results
3. Indexer
   4. Based on `scikit-learn` library
5. Processor
   6. Based on `flask` library
   7. Implements user interface & REST API

### Web Interface

The web interface is exposed on the root (`/`) of the web server. By default, the port of the processor is 8080. It has been adjusted from the default due to conflicts with a service on newer releases of MacOS.

### REST API


## Operation

### Setting up the dev environment

1. Run `pip install -r requirements.txt` to install the required packages.
2. Run `python -m spacy download en_core_web_sm` to manually install the stop word package.

⚠️ **Note:** It may be necessary to replace `pip` and `python` with `pip3` and `python3` in certain installations.

### Run the crawler

This example will create a new crawler file for the topic of Formula SAE race cars. The source will come from two wikipedia pages. **Note:** This file has been pre-generated and is available at [data/crawler/formula.jsonl]().

```shell
python crawler.py -u https://en.wikipedia.org/wiki/Formula_Hybrid,https://en.wikipedia.org/wiki/Formula_SAE -o formula.jsonl 
```

### Run the indexer
This example will run the indexer using the file generated from the crawler example above. 

```shell
python indexer.py -i data/crawler/formula.jsonl -o formula.json
```

### Run the processor
This example will start the processor using the file built with the indexer.
```shell
python indexer.py -i data/crawler/formula.jsonl -o formula.json     
```


