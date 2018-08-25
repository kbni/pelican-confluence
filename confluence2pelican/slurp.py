import logging
import itertools
from pathlib import Path
from json import dumps
import requests


logger = logging.getLogger(f'{__package__}.{__name__}')


class Slurp:
    def __init__(self, url, username, password, space_key):
        self.space_key = space_key
        self.url = url if not url.endswith('/') else url[0:-1]
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.content_expands = ','.join([
            'version,metadata.labels,history,children.page,body.export_view',
            'children.attachment,children.attachment.version,children.attachment.history',
        ])
    
    def slurp(self, store=None):
        for content in itertools.chain(self.recurse_pages(self.get_homepage_id()), self.recurse_blogs()):
            logger.debug('Content: %s', {k: v for k, v in content.items() if k != 'json'})
            if store:
                store.store_content(content)
            for attachment in self.attachments_from_content(content['json']):
                logger.debug('Attachment: %s', {k: v for k, v in attachment.items() if k != 'json'})
                if store:
                    store.store_attachment(content, attachment)

        if store:
            store.commit()
    
    def get(self, path, **kwargs):
        path = path if not path.startswith('/') else path[1:]
        return self.session.get(f'{self.url}/{path}', **kwargs)

    def get_content(self, page_id):
        page_res = self.get(f'rest/api/content/{page_id}?expand=body.export_view,version,history,metadata.labels')
        if page_res.status_code < 300:
            return page_res.json()

    def get_homepage_id(self):
        res = self.get(f'rest/api/space/{self.space_key}?expand=homepage')
        if res.status_code == 200:
            homepage_id = res.json()['homepage']['id']
            logger.debug(f'homepage id is {homepage_id}')
            return homepage_id

    def recurse_pages(self, page_id, parent_id=None, level=0):
        res = self.get(f'rest/api/content/{page_id}?expand={self.content_expands}')
        if res.status_code == 200:
            page_json = res.json()
            yield {
                'id': page_id,
                'type': 'page',
                'level': level,
                'parent': parent_id,
                'title': page_json['title'],
                'version': page_json['version']['number'],
                'json': page_json,
                'labels': self.labels_from_content(page_json)
            }
            if page_json['children']['page']['size']:
                for child in page_json['children']['page']['results']:
                    yield from self.recurse_pages(child['id'], page_id, level+1)

    def recurse_blogs(self):
        params = {
            'cql': f'space.key = {self.space_key} AND type = blogpost',
            'expand': self.content_expands,
            'limit': 50,
            'start': 0
        }
        while True:
            res = self.get('rest/api/content/search', params=params)
            if res.status_code != 200:
                break
            res_json = res.json()
            for blog_json in res_json['results']:
                yield {
                    'id': blog_json['id'],
                    'type': 'blogpost',
                    'title': blog_json['title'],
                    'version': blog_json['version']['number'],
                    'json': blog_json,
                    'labels': self.labels_from_content(blog_json)
                }
            if res_json['size'] < params['limit']:
                break
            params['start'] += params['limit']

    def labels_from_content(self, content):
        labels = [l['name'] for l in content['metadata']['labels']['results']]
        if not content['metadata']['labels']['size'] < content['metadata']['labels']['limit']:
            logger.warning('Probably more labels for %s (%s)', content['id'], content['title'])
        return labels
    
    def attachments_from_content(self, content):
        attachments = content['children']['attachment']['results']
        if not content['children']['attachment']['size'] < content['children']['attachment']['limit']:
            logger.warning('Probably more attachments for %s (%s)', content['id'], content['title'])
        for attachment_json in attachments:
            yield {
                'id': attachment_json['id'],
                'type': 'file',
                'title': attachment_json['title'],
                'version': attachment_json['version']['number'],
                'size': attachment_json['extensions']['fileSize'],
                'json': attachment_json,
                'parent': content['id'],
                'stream': lambda: self.get(attachment_json['_links']['download'], stream=True)
            }
