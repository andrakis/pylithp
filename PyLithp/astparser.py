import json
import re

from lithptypes import *
from excepts import *

SUPPORTED_ESCAPES = {
	"n": "\n",
	"r": "\r",
	"t": "\t",
	"\\": "\\\\"
}

class ASTParser(object):
	pass

	@staticmethod
	def ParseEscapes(s):
		match = re.match(r'(.*?)(\\.)', s)
		if match != None:
			pre    = match.group(1)
			symbol = match.group(2)[1:]
			if symbol in SUPPORTED_ESCAPES.keys():
				s = pre + SUPPORTED_ESCAPES[symbol]
			else:
				raise InvalidEscapeCharacter(symbol)
		return s
	
	@staticmethod
	def Classify(phrase):
		result = 0
		char = phrase[0]
		if char in ["\t", " ", "\r", "\n"]:
			result = ASTParser.EX_PARAM_SEPARATOR
		elif char == "(":
			result = ASTParser.EX_OPCHAIN | ASTParser.EX_FUNCTIONCALL
		elif char == ")":
			result = ASTParser.EX_CALL_END | ASTParser.EX_OPCHAIN_END
		elif char == "'":
			result = ASTParser.EX_STRING_SINGLE
		elif char == '"':
			result = ASTParser.EX_STRING_DOUBLE
		elif char == "%":
			result = ASTParser.EX_COMMENT
		elif char == ",":
			result = ASTParser.EX_FUNCTION_BODY
		else:
			if re.match(r'^[a-z][a-zA-Z0-9_]*$', phrase) != None:
				result = ASTParser.EX_ATOM
			elif re.match(r'^[A-Z][A-Za-z0-9_]*$', phrase) != None:
				result = ASTParser.EX_VARIABLE
			elif re.match(r'^-?[0-9e][0-9e]*$', phrase) != None:
				result = ASTParser.EX_NUMBER | ASTParser.EX_ATOM | ASTParser.NUMBER
			elif re.match(r'^-?[0-9e][0-9e.]*$', phrase) != None:
				result = ASTParser.EX_NUMBER | ASTParser.EX_ATOM | ASTParser.NUMBER
			elif len(phrase) > 1 and re.test(r'^\".*\"$', phrase) != None:
				result = ASTParser.EX_STRING_DOUBLE
			elif len(phrase) > 1 and re.test(r"^'.*'$", phrase) != None:
				result = ASTParser.EX_STRING_SINGLE
			else:
				result = ASTParser.EX_ATOM
			result |= ASTParser.EX_STRING_CHARACTER
		return result
	
	@staticmethod
	def Classified(n):
		parts = []
		for k in ASTParser.EX_TABLE:
			if ASTParser.EX_TABLE[k] & n:
				parts.append(k)
		return " | ".join(parts)

ASTParser.EX_LITERAL = 1 << 0              # Literal (1  2  "test")
ASTParser.EX_OPCHAIN = 1 << 1              # opening OpChain '('
ASTParser.EX_FUNCTIONCALL = 1 << 2         # opening FunctionCall '('
ASTParser.EX_NUMBER  = 1 << 3              # Collect number (whole or float: [0-9.]+f?$)
ASTParser.EX_ATOM    = 1 << 4              # Collect atom
ASTParser.EX_VARIABLE= 1 << 5              # Variables
ASTParser.EX_STRING_CHARACTER  = 1 << 6    # Collect character
ASTParser.EX_STRING_SINGLE = 1 << 7        # Expecting a single quote to end '
ASTParser.EX_STRING_DOUBLE = 1 << 8        # Expecting a double quote to end "
ASTParser.EX_PARAM_SEPARATOR   = 1 << 9    # Expecting a space
ASTParser.EX_CALL_END          = 1 << 10   # Expected a )  end of call
ASTParser.EX_OPCHAIN_END       = 1 << 11   # Expect a )  end of opchain
ASTParser.EX_COMMENT           = 1 << 12   # Comments
ASTParser.EX_COMPILED          = 1 << 13   # Already compiled
ASTParser.EX_FUNCTION_MARKER   = 1 << 14   # #     next: Arg1 Arg2 :: (...)
ASTParser.EX_FUNCTION_PARAM    = 1 << 15   # #     this: Arg1
ASTParser.EX_FUNCTION_PARAM_SEP= 1 << 16   # #Arg1 this:  
ASTParser.EX_FUNCTION_BODY     = 1 << 17;  # #Arg1 Arg2  this: ::

ASTParser.EX_TABLE = {
	"EX_LITERAL": ASTParser.EX_LITERAL,
	"EX_OPCHAIN": ASTParser.EX_OPCHAIN,
	"EX_FUNCTIONCALL": ASTParser.EX_FUNCTIONCALL,
	"EX_NUMBER": ASTParser.EX_NUMBER,
	"EX_ATOM": ASTParser.EX_ATOM,
	"EX_VARIABLE": ASTParser.EX_VARIABLE,
	"EX_STRING_CHARACTER": ASTParser.EX_STRING_CHARACTER,
	"EX_STRING_SINGLE": ASTParser.EX_STRING_SINGLE,
	"EX_STRING_DOUBLE": ASTParser.EX_STRING_DOUBLE,
	"EX_PARAM_SEPARATOR": ASTParser.EX_PARAM_SEPARATOR,
	"EX_CALL_END": ASTParser.EX_CALL_END,
	"EX_OPCHAIN_END": ASTParser.EX_OPCHAIN_END,
	"EX_COMMENT": ASTParser.EX_COMMENT,
	"EX_COMPILED": ASTParser.EX_COMPILED,
	"EX_FUNCTION_MARKER": ASTParser.EX_FUNCTION_MARKER,
	"EX_FUNCTION_PARAM": ASTParser.EX_FUNCTION_PARAM,
	"EX_FUNCTION_PARAM_SEP": ASTParser.EX_FUNCTION_PARAM_SEP,
	"EX_FUNCTION_BODY": ASTParser.EX_FUNCTION_BODY
}

class JSONParser(ASTParser):
	def __init__(self, path):
		self.path = path
		with open(self.path) as fileData:
			asJson = json.load(fileData)
			self.ops = self.unexport(asJson)
	
	def unexport(self, ast):
		if isinstance(ast, dict):
			obj = {}
			code = self.unexport(ast["code"])
			obj["code"] = code
			obj["_fndef"] = ast["_fndef"]
			obj["_fnparams"] = ast["_fnparams"]
			return obj
		elif isinstance(ast, list):
			res = []
			for a in ast:
				res.append(self.unexport(a))
			return res
		else:
			return ast
	
	def finalize(self):
		chain = OpChain()
		for x in self.ops:
			c = self.convert(chain, x)
			chain.append(c)
		return chain
	
	def classify(self, x):
		if not isinstance(x, basestring):
			return ASTParser.EX_COMPILED
		return ASTParser.Classify(str(x))
	
	def mapParam(self, P, chain, fnName):
		result = self.mapParamInner(P, chain, fnName)
		return result
	
	def mapParamInner(self, P, chain, fnName):
		if isinstance(P, list):
			return convert(chain, P)
		cls = self.classify(P)
		strV= str(P)
		print "Classified: ", ASTParser.Classification(cls)

