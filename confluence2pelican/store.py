import os
import logging
import uuid
import shutil
from pathlib import Path
from json import dumps
import pendulum
from slugify import slugify
from .dal import setup_database

logger = logging.getLogger(f'{__package__}.{__name__}')


class Store:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir).absolute()
        self.instance_id = str(uuid.uuid4())  # Use this string as a reference for cleanup_content()
        self.db = setup_database(self.data_dir, 'store_db', 'store.sqlite3', {
            'content': {
                'id_': 'string',
                'json': 'string',
                'run': 'string',
                'version': 'integer',
                'created': 'datetime',
                'modified': 'datetime',
                'title': 'string',
                'slug': 'string',
                'parent': 'reference content',
                'level': 'integer',
                'labels': 'list:string',
                'deleted': 'boolean',
                'type': 'string'
            },
            'attachment': {
                'id_': 'string',
                'json': 'string',
                'run': 'string',
                'version': 'integer',
                'created': 'datetime',
                'modified': 'datetime',
                'title': 'string',
                'path_all': 'string',
                'path_current': 'string',
                'parent': 'reference content',
                'deleted': 'boolean'
            }
        })

    def validate_dict(self, item):
        return isinstance(item, dict) and 'json' in item

    def commit(self):
        self.db(self.db.content.run != self.instance_id).delete()
        self.db(self.db.attachment.run != self.instance_id).delete()
        return self.db.commit()

    def iter_pages(self, min_level=0, max_level=1000):
        query = self.db(
            (self.db.content.type=='page')&
            (self.db.content.level >= min_level)&
            (self.db.content.level <= max_level)
        )
        for record in query.select(orderby=self.db.content.level):
            yield (record, list(self.db(self.db.attachment.parent==record.id).select()))

    def iter_blog(self):
        query = self.db((self.db.content.type=='blogpost'))
        for record in query.select(orderby=self.db.content.level):
            yield (record, list(self.db(self.db.attachment.parent==record.id).select()))

    def store_content(self, content):
        if not self.validate_dict(content):
            raise ValueError('expecting a dictionary from Slurp')
        record = self.db(self.db.content.id_==content['id']).select().first()
        if record is None:
            logger.debug('creating new record for %s (%s)', content['id'], content['title'])
            record = self.db.content[self.db.content.insert(id_=content['id'])]
        else:
            logger.debug('record id is %s for %s (%s)', record.id, content['id'], content['title'])
        record.update_record(
            run=self.instance_id,
            json=dumps(content['json']),
            level=content.get('level', None),
            title=content['title'],
            slug=slugify(content['title']),
            version=content['version'],
            created=pendulum.parse(content['json']['history']['createdDate']),
            modified=pendulum.parse(content['json']['version']['when']),
            parent=self.db(self.db.content.id_==content.get('parent', None)).select().first(),
            labels=content['labels'],
            deleted=False,
            type=content['json']['type']
        )

    def store_attachment(self, content, attachment):
        if not self.validate_dict(content) or not self.validate_dict(attachment):
            raise ValueError('expecting two dictionaries from Slurp')
        path_all = Path(self.data_dir, 'attachments', attachment['id'])
        path_version = Path(path_all, str(attachment['version']))
        path_current = Path(path_version, attachment['title'])
        path_version.mkdir(exist_ok=True, parents=True)

        if path_current.exists():
            if path_current.stat().st_size != attachment['json']['extensions']['fileSize']:
                logger.debug('deleting %s (%s) because it is the wrong size', attachment['id'], attachment['title'])
                path_current.unlink()

        if not path_current.exists():
            with open(path_current, 'wb') as f:
                for chunk in attachment['stream']().iter_content(chunk_size=1024): 
                    if chunk: # filter out keep-alives
                        f.write(chunk)
            logger.info('downloaded attachment: %s', path_current.relative_to(self.data_dir))

        record = self.db(self.db.attachment.id_==attachment['id']).select().first()
        if record is None:
            logger.debug('creating new record for %s (%s)', attachment['id'], attachment['title'])
            record = self.db.attachment[self.db.attachment.insert(id_=attachment['id'])]
        record.update_record(
            run=self.instance_id,
            json=dumps(attachment['json']),
            title=attachment['title'],
            version=attachment['version'],
            created=pendulum.parse(attachment['json']['history']['createdDate']),
            modified=pendulum.parse(attachment['json']['version']['when']),
            parent=self.db(self.db.content.id_==content['id']).select().first(),
            path_all=path_all.relative_to(self.data_dir),
            path_current=path_current.relative_to(self.data_dir),
            deleted=False
        )