from threading import Thread, Lock
import lstore.bufferpool as bufferpool
from queue import Queue
import time
import copy
from lstore.parser import get_physical_page_offset
 
class MergeWorkerThread(Thread):

    def __init__(self, lock, queue):
        Thread.__init__(self)
        self.lock = lock
        self.queue = queue

    """
    Start the merging process
    """

    def run(self):
        while True:
            logical_base_page, arr_of_tail_pages = self.queue.get() # block and wait
#           print('merging', logical_base_page.path)
#           print('merge starting...')
            base_tps = logical_base_page.tps
            base_path = logical_base_page.path
            num_columns = logical_base_page.num_columns
            num_user_columns = logical_base_page.num_user_columns
#           arr_of_tail_pages = copy.deepcopy(arr_of_tail_pages)

            # array of physical pages
            base_pages = bufferpool.shared.merge_get_logical_pages(base_path, num_columns, True)

            if base_pages is None:
                # bufferpool doesn't have the page, something is wrong
                print('bufferpool doesnt have base page for merge')
                logical_base_page.merging = False
                self.queue.task_done()
                continue

            merged_base_pages = copy.deepcopy(base_pages)
            del base_pages

            logical_tail_pages = [
                bufferpool.shared.merge_get_logical_pages(tail_page.path, tail_page.num_columns)
                for tail_page in arr_of_tail_pages
            ]

            start_rid, end_rid = merged_base_pages[1].get(0), merged_base_pages[1].get(510)

            latest_tps = 0
            finished_merging = False
            merged_base_rid = set()
            merged_records = 0

            page_number = len(arr_of_tail_pages) - 1 
            for tail_page in reversed(logical_tail_pages):
                # from arr_of_tail_pages[page_number].num_records - 1 to 0
                for i in range(arr_of_tail_pages[page_number].num_records - 1 , -1, -1):
                    tail_rid = tail_page[1].get(i)
                    base_rid = tail_page[4].get(i)
                    schema = tail_page[3].get(i)

                    if latest_tps == 0:
                        latest_tps = tail_rid

                    if tail_rid <= base_tps:
                        # finished merging
                        finished_merging = True
                        break
#                   if base_path == 'Grades/page_range_0_b/base_0':
#                       print(logical_tail_pages)
#                       input()
#                       print(base_rid)

                    if start_rid <= base_rid <= end_rid and base_rid not in merged_base_rid:
                        # merge this page
                        offset = get_physical_page_offset(base_rid)
                        indirection = merged_base_pages[0].get(offset)
                        if indirection != 200000000:
                            merged_base_pages[3].set(offset, 0)
                            for j in range(num_user_columns):
                                if (schema & (1 << (num_user_columns - j - 1))):
                                    merged_base_pages[j + 4].set(
                                        offset, tail_page[j + 5].get(i)
                                    )

                        merged_records += 1
                        merged_base_rid.add(base_rid)

                page_number -= 1
                if finished_merging:
                    # finished merging
                    break

            if merged_records > 0:
                # need to save the pages
#               print('merged', merged_records)
#               print(latest_tps)
                bufferpool.shared.merge_save_logical_pages(logical_base_page.path, num_columns, merged_base_pages)

            if logical_base_page.tps < latest_tps:
                logical_base_page.tps = latest_tps

            logical_base_page.merging = False
            self.queue.task_done()

class MergeWorker:
    def __init__(self):
        self.queue = Queue()
        self.lock = Lock()
        self.thread = MergeWorkerThread(self.lock, self.queue)
        self.thread.daemon = True
        self.thread.start()
        