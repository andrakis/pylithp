
class LithpError(Exception, object):
	pass

class KeyNotFoundError(LithpError):
	def __init__(self, key):
		super(LithpError, self).__init__("Key not found: " + key)
		self.key = key

class FunctionNotFoundError(LithpError):
	def __init__(self, fn):
		super(LithpError, self).__init__("Function not found: " + fn)
		self.fn = fn

class InvalidEscapeCharacter(LithpError):
	def __init__(self, c):
		super(LithpError, self).__init__("Function not found: " + c)
		self.c = c

class InvalidArguemntError(LithpError):
	def __init__(self, arg = None):
		super(LithpError, self).__init__("Invalid argument")

class RuntimeError(LithpError):
	def __init__(self, error = "Unknown"):
		super(LithpError, self).__init__(error)