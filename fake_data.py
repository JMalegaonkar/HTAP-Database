import unittest
from lstore.db import Database
from lstore.table import Table
from lstore.query import Query
from lstore.pageRange import PageRange
from lstore.basepage import BasePage
from lstore.record import Record
from lstore.page import Page
from lstore.parser import *
import time
import random

class TestPages(unittest.TestCase):

	def test_one_basepage(self):
		start = time.time()
		basepage = BasePage(2) # create two columns

		# Test First Record
		self.assertEqual(basepage.get_next_rec_num(), 0)
		basepage.write(Record(0, 0, [123, 321])) # set first column to 123 and second to 321
		self.assertTrue(abs(basepage.get(0, 2) - int(start)) <= 1) # check internal column (timestamp)
		self.assertEqual(basepage.get(0, 4), 123)
		self.assertEqual(basepage.get(0, 5), 321)
		
		self.assertEqual(basepage.get_cols(0, [1, 0]), [123, None])
		self.assertEqual(basepage.get_cols(0, [0, 1]), [None, 321])
		self.assertEqual(basepage.get_cols(0, [1, 1]), [123, 321])
		
		# Insert invalid record, should raise error
		with self.assertRaises(Exception):
			basepage.write(Record(0, 0, [123]))

		# Test 2nd to 512th
		for i in range(1, 512):
			self.assertEqual(basepage.get_next_rec_num(), i)
			
			basepage.write(Record(i, 0, [i * 2, i * 3])) # set first column to 123 and second to 321
			self.assertEqual(basepage.get(i, 2), int(start)) # check internal column (timestamp)
			self.assertEqual(basepage.get(i, 4), i * 2)
			self.assertEqual(basepage.get(i, 5), i * 3)
			
			self.assertEqual(basepage.get_cols(i, [1, 0]), [i * 2, None])
			self.assertEqual(basepage.get_cols(i, [0, 1]), [None, i * 3])
			self.assertEqual(basepage.get_cols(i, [1, 1]), [i * 2, i * 3])

		# Page is full and insert new record, should raise error
		with self.assertRaises(Exception):
			basepage.write(Record(512, 0, [123, 321]))


	def test_parser(self):
		self.assertEqual(get_physical_page_offset(123456789), 789)
		self.assertEqual(get_page_type(123456789), 1)
		self.assertEqual(get_page_range_number(123456789), 23)
		self.assertEqual(get_page_number(123456789), 456)
		
		self.assertEqual(get_page_type(create_rid(1, 0, 0, 0)), 1)
		self.assertEqual(get_page_range_number(create_rid(0, 23, 0, 0)), 23)
		self.assertEqual(get_page_number(create_rid(0, 0, 456, 0)), 456)
		self.assertEqual(get_physical_page_offset(create_rid(0, 0, 0, 789)), 789)
		self.assertEqual(create_rid(1, 23, 456, 789), 123456789)


	def test_page_range(self):
		rids = []
		
		page_range_0 = PageRange(2, 0) # 2 col, id = 0
		page_range_1 = PageRange(2, 1) # 2 col, id = 1
		
		self.assertEqual(page_range_0.write(1, 2), 0) # PageRange 0 first record ID should be 0
		self.assertEqual(page_range_1.write(1, 2), 1000000) # PageRange 1 first record ID should be 1000000
		self.assertEqual(page_range_0.write(3, 4), 1) # PageRange 0 second record ID should be 1
		self.assertEqual(page_range_1.write(3, 4), 1000001) # PageRange 1 second record ID should be 1000001
		
		self.assertEqual(page_range_0.get(0, 0,[1,1]), [1, 2])
		self.assertEqual(page_range_0.get(0, 1,[1,1]), [3, 4])
		
		# page range has 2 records, it should create a new base page if we insert 511 more records
		for i in range(2, 512):
			self.assertEqual(page_range_0.write(i, i ** 2), i)
			rids.append(i)
	
		# we have 512 records now, but it should only have 1 page
		self.assertEqual(len(page_range_0.arr_of_base_pages), 1)
		# next should triggle a new page, 513 records
		self.assertEqual(page_range_0.write(512, 262144), 1000)
		rids.append(1000)
		# check if length of base page array is 2
		self.assertEqual(len(page_range_0.arr_of_base_pages), 2)
		
		for i in range(513, 4096):
			rids.append(page_range_0.write(i, i ** 2))
		
		for i in range(2, 4096):
			self.assertEqual(page_range_0.get(i // 512, i % 512,[1,1]), [i, i ** 2])

		for i, rid in enumerate(rids):
			self.assertEqual(page_range_0.get_withRID(rid,[1,1]), [(i+2), (i+2) ** 2])
		
		with self.assertRaises(Exception):
			# pagerange is full
			page_range_0.write(0, 0)
			
		# awesome, all data are correct!


	def test_tail(self):
		# test summary
		# create two pages of tails the most recent update
		# for col 0 and 1 are in the last two tail places.
		# the most recent update in col 3 is buried below 514 
		# calls to traverse id
		page_range_0 = PageRange(3, 0) # 2 col, id = 0

		self.assertEqual(page_range_0.write(1, 2, 10), 0) # PageRange 0 first record ID should be 0
		#page_range_0.update(0, *[10000,None,3])
		for i in range(1, 512):
			page_range_0.update(0, *[i ** 2,None, i])
		# quick test to see that tail holds x update and that base page now points to tail rid
		page_range_0.update(0, *[1,25,None])
		page_range_0.update(0, *[10000,None,None])
		#page_range_0.traverse_ind(page_range_0.get_withRID(0),0,0)
		#page_range_0.arr_of_base_pages[0].phys_pages[0].get(0)
#		print('\n' + str(page_range_0))
#		print(page_range_0.get_withRID(0))


	def test_delete(self):
		page_range_0 = PageRange(3, 0) # 2 col, id = 0
		self.assertEqual(page_range_0.write(1, 2, 3), 0) # PageRange 0 first record ID should be 0
		self.assertEqual(page_range_0.get_withRID(0,[1,1,1]), [1, 2, 3])
	
		page_range_0.update(0, 4, 5, 6)
		self.assertEqual(page_range_0.get_withRID(0,[1,1,1]), [4, 5, 6])
	
		page_range_0.update(0, 7, 8, None)
		self.assertEqual(page_range_0.get_withRID(0,[1,1,1]), [7, 8, 6])
		page_range_0.delete_withRID(0)
		
		self.assertEqual(page_range_0.write(10, 20, 30), 1)
		self.assertEqual(page_range_0.get_withRID(1,[1,1,1]), [10, 20, 30])
		
		page_range_0.update(1, 40, 50, 60)
		self.assertEqual(page_range_0.get_withRID(1,[1,1,1]), [40, 50, 60])
		
		page_range_0.delete_withRID(1)
		self.assertEqual(page_range_0.get_withRID(0,[1,1,1]), None)
		self.assertEqual(page_range_0.get_withRID(1,[1,1,1]), None)
		
		rids = []
		for i in range(4094):
			rids.append(page_range_0.write(i, i+1, i+2))
		
		for rid in rids:
			self.assertNotEqual(page_range_0.get_withRID(rid,[1,1,1]), None)
			
		for rid in rids:
			page_range_0.delete_withRID(rid)
			
		for rid in rids:
			self.assertEqual(page_range_0.get_withRID(rid,[1,1,1]), None)
			
		with self.assertRaises(Exception):
			page_range_0.write(0, 0, 0)


	def test_query_insert_select(self):
		db = Database()
		grades_table = db.create_table('Grades', 5, 0)
		query = Query(grades_table)
		
		for i in range(10000):
			self.assertEqual(query.insert(i, i+1, i+2, i+3, i+4), True)

		for i in range(10000):
			results = query.select(i, 0, [1] * 5)
			self.assertEqual(len(results), 1)
			self.assertEqual(results[0].columns, [i, i+1, i+2, i+3, i+4])
		
		for i in range(10000):
			results = query.select(i+2, 2, [1] * 5)
			self.assertEqual(len(results), 1)
			self.assertEqual(results[0].columns, [i, i+1, i+2, i+3, i+4])

	def test_query_delete(self):
		db = Database()
		db.create_table('Test', 3, 0)
		table = db.get_table('Test')
		query = Query(table)
		
		keys = random.sample(range(-100000000, 100000000), 10000)
		
		# insert
		for key in keys:
			self.assertEqual(query.insert(key, key * 2, key * 3), True)
		
		# select should return a valid record
		for key in keys:
			self.assertEqual(query.select(key, 0, [1, 1, 1])[0].columns, [key, key * 2, key * 3])
		
		# delete should return True
		for key in keys:
			self.assertEqual(query.delete(key), True)
		
		# delete a invalid key should return False
		self.assertEqual(query.delete(1000000001), False)
		
		# select deleted keys should return None
		for key in keys:
			self.assertEqual(query.select(key, 0, [1, 1, 1]), [])
		
		# delete deleted keys should return False
		for key in keys:
			self.assertEqual(query.delete(key), False)

	def test_query_update(self):
		db = Database()
		db.create_table('Test', 3, 0)
		table = db.get_table('Test')
		query = Query(table)
		
		self.assertFalse(query.update(0, 1, 1, 1))
		
		self.assertTrue(query.insert(1, 2, 3))
		self.assertEqual(query.select(1, 0, [1, 1, 1])[0].columns, [1, 2, 3])
		
		self.assertFalse(query.update(0, 1, 1, 1))
		
		self.assertTrue(query.update(1, None, 9, None))
		self.assertEqual(query.select(1, 0, [1, 1, 1])[0].columns, [1, 9, 3])
		
		self.assertTrue(query.update(1, None, None, 10))
		self.assertEqual(query.select(1, 0, [1, 1, 1])[0].columns, [1, 9, 10])
		
		self.assertTrue(query.increment(1, 1))
		self.assertEqual(query.select(1, 0, [1, 1, 1])[0].columns, [1, 10, 10])
	
		self.assertTrue(query.update(1, 8, None, None))
		self.assertEqual(query.select(8, 0, [1, 1, 1])[0].columns, [8, 10, 10])
		self.assertEqual(query.select(1, 0, [1, 1, 1]), [])

	def test_query_sum(self):
		db = Database()
		db.create_table('Test', 3, 0)
		table = db.get_table('Test')
		query = Query(table)
		
		keys = random.sample(range(-100000000, 100000000), 10000)
		
		sum_first_col = 0
		sum_second_col = 0
		sum_third_col = 0
		
		for key in keys:
			self.assertEqual(query.insert(key, key * 2, key * 3), True)
			if -100000 <= key <= 100000:
				sum_first_col += key
				sum_second_col += key * 2
				sum_third_col += key * 3
		
		self.assertEqual(query.sum(-100000, 100000, 0), sum_first_col)
		self.assertEqual(query.sum(-100000, 100000, 1), sum_second_col)
		self.assertEqual(query.sum(-100000, 100000, 2), sum_third_col)
		
		table2 = db.create_table('Test2', 3, 0)
		query2 = Query(table2)
		
		self.assertEqual(query2.insert(100, 200, 300), True)
		self.assertEqual(query2.insert(1000, 2000, 3000), True)
		self.assertEqual(query2.sum(100, 1000, 2), 3300)
		
		self.assertEqual(query2.update(1000, None, 1000, None), True)
		self.assertEqual(query2.sum(100, 1000, 2), 3300)
		
		self.assertEqual(query2.update(1000, None, None, 2000), True)
		self.assertEqual(query2.sum(100, 1000, 2), 2300)
		
		self.assertEqual(query2.update(1000, 3000, None, None), True)
		self.assertEqual(query2.sum(100, 1000, 2), 300)
		
		self.assertEqual(query2.sum(100, 3000, 2), 2300)
	
	def test_select_duplicate(self):
		db = Database()
		db.create_table('Test', 3, 0)
		table = db.get_table('Test')
		query = Query(table)
		
		self.assertEqual(query.insert(0, 1000, 2000), True)
		self.assertEqual(query.insert(1, 100, 200), True)
		self.assertEqual(query.insert(1, 100, 200), False)
		self.assertEqual(query.insert(2, 100, 300), True)
		self.assertEqual(query.insert(3, 300, 3000), True)
		
		records = query.select(100, 1, [1, 1, 1])
		self.assertEqual(len(records), 2)
		
		for record in records:
			self.assertTrue(record.columns == [1, 100, 200] or record.columns == [2, 100, 300])
		
		self.assertEqual(query.update(3, None, 100, None), True)
		
		records = query.select(100, 1, [1, 1, 1])
		self.assertEqual(len(records), 3)
		
		for record in records:
			if record.rid == 1:
				self.assertEqual(record.columns, [1, 100, 200])
			elif record.rid == 2:
				self.assertEqual(record.columns, [2, 100, 300])
			else:
				self.assertEqual(record.columns, [3, 100, 3000])
		
		self.assertEqual(query.sum(1, 3, 1), 300)
		self.assertEqual(query.sum(1, 3, 2), 3500)
		
		
		
		records = query.select(4, 0, [1, 1, 1])
		self.assertEqual(len(records), 0)
		
		records = query.select(5, 0, [1, 1, 1])
		self.assertEqual(len(records), 0)
		
		self.assertEqual(query.insert(4, 44, 444), True)
		
		records = query.select(4, 0, [1, 1, 1])
		self.assertEqual(len(records), 1)
		
		self.assertNotEqual(query.sum(1, 4, 2), 3500)
		
		
		self.assertEqual(query.update(4, 5, None, None), True)
		
		records = query.select(4, 0, [1, 1, 1])
		self.assertEqual(len(records), 0)
		
		records = query.select(5, 0, [1, 1, 1])
		self.assertEqual(len(records), 1)
		
		self.assertEqual(query.sum(1, 3, 1), 300)
		self.assertEqual(query.sum(1, 3, 2), 3500)
		self.assertEqual(query.sum(1, 4, 2), 3500)
		self.assertNotEqual(query.sum(1, 5, 2), 3500)
		self.assertEqual(query.sum(1, 5, 2), 3500 + 444)
		
		self.assertEqual(query.update(5, None, None, None), True)
		self.assertEqual(query.sum(1, 3, 2), 3500)
		self.assertEqual(query.sum(1, 4, 2), 3500)
		self.assertNotEqual(query.sum(1, 5, 2), 3500)
		self.assertEqual(query.sum(1, 5, 2), 3500 + 444)
		
		self.assertEqual(query.update(5, None, None, 12345), True)
		self.assertEqual(query.sum(1, 5, 2), 3500 + 12345)
		
	
	def test_select_duplicate(self):
		db = Database()
		db.create_table('Test', 3, 0)
		table = db.get_table('Test')
		query = Query(table)
		query.insert(1, 2, 3)
		query.insert(4, 5, 6)
		
		self.assertFalse(query.update(1, 4, None, None))
		self.assertTrue(query.update(1, 7, None, None))
		
		self.assertFalse(query.insert(7, 8, 9))
		self.assertTrue(query.insert(-10, -11, -12))
		
		self.assertFalse(query.update(-10, 7, None, None))
		self.assertFalse(query.update(-10, 4, 1, 1))
		self.assertFalse(query.update(4, -10, None, None))
		self.assertTrue(query.update(4, -11, None, None))
		self.assertTrue(query.update(-10, 4, 1, 1))
		self.assertTrue(query.update(-11, -10, None, None))
	
		self.assertEqual(query.select(-10, 0, [1,1,1])[0].columns, [-10,5,6])
		self.assertEqual(query.select(4, 0, [1,1,1])[0].columns, [4,1,1])
		self.assertEqual(query.select(7, 0, [1,1,1])[0].columns, [7,2,3])

	def test_1M(self):
		db = Database()
		db.create_table('Test', 3, 0)
		table = db.get_table('Test')
		query = Query(table)
		for i in range(409601):
			query.insert(i, i, i)

if __name__ == '__main__':
	unittest.main()
	