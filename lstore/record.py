class Record:

	"""
	For query
	"""

	def __init__(self, rid, key, columns):
		self.rid = rid
		self.key = key
		self.columns = columns

	def __str__(self):
		return 'RID: {}, key: {}, data: {}'.format(self.rid, self.key, self.columns)

	"""
	Overload [] operator
	"""
	def __getitem__(self, key):
		return self.columns[key]
