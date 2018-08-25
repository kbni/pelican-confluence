import os
import sys
import json
import logging
import argparse
from .massage import Massage
from .slurp import Slurp
from .store import Store
from .export import Export


logger = logging.getLogger(f'{__package__}.{__name__}')
DEFAULT_CONFIG = {
    "confluence_url": "https://conf.example.com/",
    "confluence_space": "HOME",
    "confluence_username": "admin",
    "confluence_password": "hunter2",
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', metavar='DATA_DIR', default='./data')
    parser.add_argument('-d', '--debug', action='store_true', default=False)
    parser.add_argument('-c', '--create', action='store_true', default=False)
    parser.add_argument('-s', '-1', '--slurp', action='store_true', default=False)
    parser.add_argument('-e', '-2', '--export', action='store_true', default=False)
    parser.add_argument('-p', '-3', '--pelican', action='store_true', default=False)
    args = parser.parse_args()

    logging.basicConfig(
        format='%(levelname)s:%(message)s',
        level=logging.DEBUG if args.debug else logging.INFO
    )

    # Load our configuration file
    config_file = os.path.join(args.data_dir, 'settings.json')
    logger.debug(f'config_file is {config_file}')
    if not os.path.exists(config_file):
        if not args.create:
            logger.critical(f'{config_file} does not exist, use --create to create file')
            sys.exit(1)
        else:
            if not os.path.exists(args.data_dir):
                os.mkdir(args.data_dir)
            if not os.path.exists(config_file):
                config = DEFAULT_CONFIG
                with open(config_file, 'w') as fh:
                    fh.write(json.dumps(config, indent=2, sort_keys=True))
    else:
        with open(config_file, 'r') as fh:
            config = json.loads(fh.read())

    # Setup the Slurp object (used to retrieve pages from Confluence)
    store = Store(args.data_dir)
    export = Export(args.data_dir, config.get('pelican_settings', {}))
    slurp = Slurp(
        url=config['confluence_url'],
        username=config['confluence_username'],
        password=config['confluence_password'],
        space_key=config['confluence_space']
    )

    if args.slurp:
        slurp.slurp(store=store)

    if args.export:
        export.export(store=store)