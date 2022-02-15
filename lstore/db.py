import os
from lstore.table import Table
import lstore.bufferpool as bufferpool

class Database():

    __slots__ = ('tables', 'path')

    def __init__(self):
        bufferpool.shared.start()
        self.tables = {}

    # Not required for milestone1
    def open(self, path):
        bufferpool.shared.db_path(path) 
        
        if bufferpool.shared.db_exists():
            data = bufferpool.shared.read_metadata('database.db')
            if data is not None:
                for table in data:
                    self.create_table(table, None, None, True)

    def close(self):
        for table in self.tables.values():
            table.close()

        bufferpool.shared.write_metadata('database.db', (
            list(self.tables.keys())
        ))

    """
    # Creates a new table
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """
    def create_table(self, name, num_columns, key_index, open_from_db=False):
        table = Table(name, num_columns, key_index, open_from_db)
        self.tables[name] = table

        bufferpool.shared.create_folder(name)

        return table

    """
    # Deletes the specified table
    """
    def drop_table(self, name):
        del self.tables[name]

    """
    # Returns table with the passed name
    """
    def get_table(self, name):
        if name in self.tables:
            return self.tables[name]
        return None
    