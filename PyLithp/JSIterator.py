class JSListIterator(object):
	def __init__(self, l):
		assert isinstance(l, list)
		self.list = l
		self.index = -1
		self.length = len(self.list)
		if self.length > 0:
			self.index = 0

	def rewind(self):
		self.index = 0

	def next(self):
		if self.index >= len(self.list):
			return None
		val = self.get(self.index)
		self.index += 1
		return val

	def prev(self):
		if self.index == -1:
			raise IndexError()
		self.index -= 1

	def get(self, index = None):
		if index == None:
			index = self.index
		return self.list[index]

	def refresh(self):
		self.length = len(self.list)
