import os
import logging
import uuid
import shutil
import itertools
from pathlib import Path
from json import dumps, loads
from slugify import slugify
from .massage import Massage
import itertools

logger = logging.getLogger(f'{__package__}.{__name__}')


class Export:
    def __init__(self, data_dir, pelican_settings={}):
        self.data_dir = Path(data_dir).absolute()
        self.export_dir = Path(self.data_dir, 'exports')
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.content_paths = {}
        self.export_files = {}
        self.convert_to_index_html = True
        self.remove_pages_from_url = True
        self.hierarchy_menus = {}
        self.hierarchy_menu_map = {}
    
    def recurse_titles(self, record):
        titles = [record.title, ]
        while record.parent:
            titles.append(record.parent.title)
            record = record.parent
        return ' -> '.join(reversed(titles))

    def build_menu(self, all_content, level=None, parent=None, grandparent=None):
        menu_tier = []
        for content in all_content:
            if parent is None and level is None:
                grandparent = content.id_
            if (parent is None and content.level == 1) or (parent and content.parent.id_ == parent):
                url = self.export_files[content.id_]
                if self.convert_to_index_html and url.endswith('.html'):
                    url = f'/{url[0:-5]}/'
                if self.remove_pages_from_url and url.startswith('/pages/'):
                    url = url[6:]
                
                sub_menu = self.build_menu(all_content, parent=content.id_, grandparent=grandparent)
                if 'hidden' not in content.labels and ('menu' in content.labels or content.level > 1):
                    menu_tier.append([content.title, url, sub_menu])
                self.hierarchy_menu_map[url] = grandparent
                if content.level == 1:
                    self.hierarchy_menus[grandparent] = [[content.title, url, sub_menu], ]
        return menu_tier

    def export(self, store):
        logger.debug('Removing old exports: %s', self.export_dir)
        shutil.rmtree(self.export_dir)
        exports = []
        pages = []

        # Doing all this in memory so we can resolve links
        for content, attachments in itertools.chain(store.iter_pages(min_level=1), store.iter_blog()):
            logger.debug('Processing [%s] %s', content.id, self.recurse_titles(content))
            export_dir = None
            if content.type == 'blogpost':
                export_dir = Path('articles', content.created.strftime('%Y'), content.slug)
            if content.type == 'page':
                pages.append(content)
                if content.parent not in self.content_paths:
                    export_dir = Path('pages', content.slug)
                else:
                    export_dir = Path(self.content_paths[content.parent], content.slug)
                self.content_paths[content.id] = export_dir
            if content.type in ('blogpost', 'page'):
                export_file = str(export_dir) + '.html'
                self.export_files[str(content.id_)] = export_file

            for attachment in attachments:
                attach_file = Path(export_dir, attachment.title)
                exports.append(('file', attach_file, attachment))
                self.export_files[attachment.id_] = attach_file
                self.export_files[attachment.title] = attach_file
                self.export_files[f'{content.id_}/{attachment.title}'] = attach_file
            exports.append(('page', export_file, content))

        for export_type, dest, record in exports:
            if export_type == 'file':
                real_path = Path(self.data_dir, record.path_current)
                link_path = Path(self.export_dir, dest)
                link_path.parent.mkdir(parents=True, exist_ok=True)
                if link_path.exists():
                    link_path.unlink()
                os.link(real_path, link_path)
            else:
                m = Massage(
                    loads(record.json),
                    record.labels,
                    export_files=self.export_files,
                    destination=dest,
                )
                m.remove_styles()
                m.convert_page_links(convert_to_index_html=self.convert_to_index_html)
                m.convert_attachment_links()
                m.convert_code_to_prettyprint()
                m.replace_embedded_images()

                exp_path = Path(self.export_dir, dest)
                exp_path.parent.mkdir(parents=True, exist_ok=True)
                with open(exp_path, 'w') as fh:
                    logger.debug('Writing %s', exp_path)
                    fh.write(m.generate_html())

        menu = self.build_menu(pages)
        export_settings = {
            'MENU_HIERARCHY': menu,
            'HIERARCHY_MENU_MAP': self.hierarchy_menu_map,
            'HIERARCHY_MENUS': self.hierarchy_menus
        }
        with Path(self.data_dir, 'per_export_settings.json').open('wb') as fh:
            fh.write(dumps(export_settings, indent=2).encode('utf-8'))