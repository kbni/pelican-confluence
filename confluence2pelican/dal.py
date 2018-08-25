import logging
from pathlib import Path
from pydal import DAL, Field


logger = logging.getLogger(f'{__package__}.{__name__}')


def setup_database(data_dir, sub_dir, db_file, tables):
    # Figure out where our database should live
    db_folder = Path(data_dir, sub_dir).absolute()
    db_folder.mkdir(exist_ok=True, parents=True)
    db = DAL(f'sqlite://{db_folder}/store.sqlite', folder=db_folder)

    for table_name in tables:
        db.define_table(
            table_name,
            *[Field(f, tables[table_name][f]) for f in tables[table_name]],
            migrate=f'{table_name}.migrate'
        )

    return db