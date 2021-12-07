#!/usr/bin/env python3


# Basic
import re

# API request
import requests
import json


class Article:
    PATTERN_URL = r'(https?://)?(www.)?(steenwijkercourant\.nl)/(.+)/(.+)\.html'

    def __init__(self, source_url):
        assert self.validate_url(source_url), 'Not an Opregte URL.'
        self.source_url = source_url
        # Initiate article variables
        self.published = None
        self.updated = None
        self.section = None
        self.authors = None
        self.title = None
        self.lead = None
        self.paragraphs = None
        self.image = None
        # Get data from url
        self.cook_url = self.get_cook_url()
        self.cook_content = self.get_cook_content()
        self.get_article_data()

    def validate_url(self, url):
        return re.fullmatch(self.PATTERN_URL, url)

    def get_cook_url(self):
        match = re.fullmatch(self.PATTERN_URL, self.source_url)
        protocol, sub, domain, path1, path2 = match.groups()
        return f'https://{domain}/cook//{path1}/{path2}.html'

    def get_cook_content(self):
        response = requests.get(self.cook_url)
        if not 200 <= response.status_code < 300:
            raise ConnectionError(f'{self.cook_url} could not be reached.')
        content = json.loads(response.content)
        return content

    def get_article_data(self):
        info = self.cook_content['data']['context']
        content = info.get('fields')
        # Test whether this is an article
        assert content, 'Not an article URL.'
        # Basic info
        self.published = info['published']
        self.updated = info['updated']
        self.section = info['homeSection']['name']
        self.authors = [a['name'] for a in info['authors']]
        # Title and lead
        self.title = content['title']
        self.lead = content['leadtext_raw']
        # Paragraphs
        elements = content['body']
        self.paragraphs = []
        self.image = None
        header = None
        for el in elements:
            images = find_items_recursively(el, 'href_full')
            if images and not self.image:
                # Store image specification
                self.image = images[-1]
            else:
                el_type = el['type']
                text = ''.join(find_items_recursively(el, 'text'))
                if re.fullmatch(r'h\d', el_type):
                    # Store header for next paragraph
                    header = text
                elif el_type == 'p':
                    self.paragraphs.append(Paragraph(header, text))
                    header = None

    def __str__(self):
        items = [self.title, self.published, ', '.join(self.authors), self.lead]
        items += [str(p) for p in self.paragraphs]
        return '\n\n'.join(items)


class Paragraph:
    def __init__(self, header, text):
        self.header = header
        self.text = text

    def __str__(self):
        if self.header:
            return self.header + '\n\n' + self.text
        return self.text


def find_items_recursively(obj, key):
    results = []
    if key in obj:
        results.append(obj[key])
    for k, v in obj.items():
        if isinstance(v, list):
            for child in v:
                results_deep = find_items_recursively(child, key)
                results += results_deep
        elif isinstance(v, dict):
            results_deep = find_items_recursively(v, key)
            results += results_deep
    return results
