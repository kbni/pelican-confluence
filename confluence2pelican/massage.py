import os
import re
import logging
from pathlib import Path
import lxml.html
from lxml.html.builder import HTML, HEAD, BODY, META, TITLE
from bs4 import BeautifulSoup

logger = logging.getLogger(f'{__package__}.{__name__}')


class Massage:
    def __init__(self, content_json, label_list, destination, export_files):
        self.content = content_json
        self.export_files = export_files
        self.destination = destination
        self.document = self.document_from_json(content_json, label_list)
        self.soup = BeautifulSoup(lxml.html.tostring(self.document), 'lxml')

    def relative_path(self, path):
        # Why is os.path.relpath better than Path.relative_to ??
        return os.path.relpath(
            str(Path('/', path)),
            str(Path('/', self.destination))
        )

    def document_from_json(self, page_json, label_list):
        return HTML(
            HEAD(
                TITLE(page_json['title']),
                META(name='date', content=page_json['history']['createdDate']),
                META(name='modified', content=page_json['version']['when']),
                META(name='tags', content=','.join([l for l in label_list if l not in ('hidden', 'menu')])),
                META(name='authors', content=page_json['history']['createdBy']['username'])
            ),
            BODY(
                *lxml.html.fromstring(page_json['body']['export_view']['value'] or '<p>Nothing yet.</p>')
            )
        )

    def convert_code_to_prettyprint(self):
        for pre in self.soup.find_all('pre'):
            if 'syntaxhighlighter-pre' in pre['class']:
                replace_classes = ['']
                params = {
                    k: v for k, v in [re.split(': ?', s) for s in re.split('; ?', pre['data-syntaxhighlighter-params'])]
                }
                pre['class'] = ['prettyprint',]
                if 'brush' in params:
                    pre['class'].append(f'lang-{params["brush"]}')

    def convert_page_links(self, convert_to_index_html=False):
        '''
        Convert page links:
            <a href="https://conf.kbni.net.au/pages/viewpage.action?pageId=10518579">Sub Page</a>
        to:
            <a href="[base_dir]/test-page/sub-page">Sub Page</a>
        '''
        for a in self.soup.find_all('a'):
            if 'viewpage.action?pageId=' in a['href']:
                content_id = a['href'].split('pageId=')[-1].split('&')[0]
                a['href'] = str(Path('/', self.export_files[content_id]))
                if convert_to_index_html:
                    if a['href'].endswith('.html'):
                        a['href'] = a['href'][0:-5] + '/'
                    if a['href'].startswith('/pages/'):
                        a['href'] = a['href'][6:]
    
    def remove_styles(self):
        for style in self.soup.find_all('style'):
            style.decompose()

    def convert_attachment_links(self):
        '''
        Replace a link such as the one below:
            <a  data-linked-resource-container-id="10518571" data-linked-resource-container-version="3"
                data-linked-resource-content-type="application/zip"
                data-linked-resource-default-alias="openttd-1.8.0-macosx-universal.zip"
                data-linked-resource-id="10518574" data-linked-resource-type="attachment"
                data-linked-resource-version="1" data-nice-type="Zip Archive"
                href="https://conf.kbni.net.au/download/attachments/10518571/openttd-1.8.0-macosx-universal.
                    zip?version=1&amp;modificationDate=1534462241779&amp;api=v2">
                openttd-1.8.0-macosx-universal.zip</a>
        with a simple link:
            <a href="[base_dir]/openttd-1.8.0-macosx-universal.zip">openttd-1.8.0-macosx-universal.zip</a>
        '''

        cull_properties = [
            'data-linked-resource-container-id',
            'data-linked-resource-container-version',
            'data-linked-resource-content-type',
            'data-linked-resource-default-alias',
            'data-linked-resource-id',
            'data-linked-resource-type',
            'data-linked-resource-version',
            'data-nice-type'
        ]
        for a in self.soup.find_all('a'):
            if '/download/attachments/' in a['href']: # and a['data-linked-resource-id']:
                a['href'] = self.relative_path(Path(self.export_files[f'att{a["data-linked-resource-id"]}']))
            for cull_prop in cull_properties:
                try:
                    del a[cull_prop]
                except KeyError:
                    pass

    def replace_embedded_images(self):
        '''
        Convert images:
            <span class="confluence-embedded-file-wrapper confluence-embedded-manual-size">
                <img class="confluence-embedded-image" height="77" src="https://conf.kbni.net.au/download/attachments/embedded-page/WWW/Test%20Page/image2018-8-17_9-19-31.png?api=v2"/>
            </span>
        to 
            <span class="embedded-image">
                <img class="confluence-embedded-image" height="77" src="[base_dir]/image2018-8-17_9-19-31.png"/>
            </span>
        '''
        for span in self.soup.find_all('span'):
            if 'confluence-embedded-file-wrapper' in span.get('class', ''):
                images = span.find_all('img')
                if images:
                    span['class'] = 'embedded-image'
        for image in self.soup.find_all('img'):
            del image['class']
            if 'download/attachments' in image['src']:
                href = image['src'].split('/')[-1].split('?')[0]
                try_keys = [f'{self.content["id"]}/{href}', href]
                for try_replace in try_keys:
                    if try_replace in self.export_files:
                        image['src'] = str(Path('/', self.export_files[try_replace]))
                        if image['src'].startswith('/pages/'):
                            image['src'] = image['src'][6:]
                        break

    def generate_html(self):
        return str(self.soup)