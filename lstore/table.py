from lstore.index import Index
from time import time

INDIRECTION_COLUMN = 0
RID_COLUMN = 1
TIMESTAMP_COLUMN = 2
SCHEMA_ENCODING_COLUMN = 3

# We are storing RID as int probably 9 digits, it will be assigned
# based on where the actualy key is stored and will be linked to the key via
# index
class Record:

    def __init__(self, rid, key, columns):
        self.rid = rid
        self.key = key
        self.columns = columns

class Table:



    #Patrick's comments/thoughts

    #S2 implment page directory here to mape the index(RID) that matches to said page
    #RID is given by key, which is the column of the table where the RID is stored.
    #See m1_tester.py where column one stores studentid our key

    #So page directory here should map that RID to the page it belongs too

    #Optional:
    
    #Index is not needed in milestone one but I would Like to get to it if we have time.
    #But it basically maps the queried value to the RID 
    #which then uses the page directory.

    #We also do not quite need a traditional bufferpool as described in class just yet
    #as for this milestone everything is in main memory and that buffferpool is for dragging
    #data from disk to RAM and persistentning it for quicker access if reused

    #How should we init the Page.py here? We need to index on Key actually so
    #match the key to a page So how are we storing our pages? in an array? Linked list?
    #array of linked lists maybe im thinking?

    """
    :param name: string         #Table name
    :param num_columns: int     #Number of Columns: all columns are integer
    :param key: int             #Index of table key in columns
    """

    
    def __init__(self, name, num_columns, key):
        self.name = name
        self.key = key
        self.num_columns = num_columns
        self.page_directory = {}
        self.index = Index(self)
        pass

    def __merge(self):
        print("merge is happening")
        pass
 
