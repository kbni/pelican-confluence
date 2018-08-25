#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals
from pathlib import Path
import json
data_dir = Path(__file__).parent.resolve()

AUTHOR = 'KBNi'
SITENAME = 'KBNi'
SITEURL = 'https://kbni.net.au'
TIMEZONE = 'Australia/Sydney'
DEFAULT_DATE_FORMAT = '%Y-%m-%d'

PLUGIN_PATHS = [str(Path(data_dir, 'pelican_plugins')), ]
PLUGINS = ['page_hierarchy']
THEME = str(Path(data_dir, 'theme'))
PATH = str(Path(data_dir, 'exports'))
OUTPUT_PATH = str(Path(data_dir, 'output'))
STATIC_PATHS = [PATH, ]
ARTICLE_URL = 'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}/'
ARTICLE_SAVE_AS = 'posts/{date:%Y}/{date:%m}/{date:%d}/{slug}/index.html'
TAGS_SAVE_AS = 'tags/index.html'
TAGS_URL = 'tags/'
TAG_SAVE_AS = 'tags/{slug}/index.html'
TAG_URL = 'tags/{slug}/'
DELETE_OUTPUT_DIRECTORY =True

CATEGORY_URL = 'category/{slug}/'
CATEGORY_SAVE_AS = 'category/{slug}/index.html'
YEAR_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/index.html'
MONTH_ARCHIVE_SAVE_AS = 'posts/{date:%Y}/{date:%m}/index.html'
CATEGORIES_SAVE_AS = 'categories/index.html'	
CATEGORIES_URL = 'categories/'
AUTHOR_URL = 'author/{slug}/'
AUTHOR_SAVE_AS = 'author/{slug}/index.html'
ARCHIVES_SAVE_AS = 'archives/index.html'
ARCHIVES_URL = 'archives/'
AUTHORS_SAVE_AS = ''

PORT = 8000
BIND = '127.0.0.1'

# This file is created by confluence2pelican/export.json
# Contains stuff like MENU_HIERARCHY, HIERARCHY_MENU_MAP and HIERARCHY_MENUS
extra_settings = Path(data_dir, 'per_export_settings.json')
if extra_settings.exists():
    with extra_settings.open('rb') as fh:
        for k, v in json.load(fh).items():
            locals()[k] = v
