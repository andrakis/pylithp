import re

class LithpConstants(object):
	ReplaceNumberAtEnd = r'\d+$'
	ParseStringEscape = r'(.*?)(\\.)'
	ClassifyAtom = r'^[a-z][a-zA-Z0-9_]*$'
	ClassifyVariable = r'^[A-Z][A-Za-z0-9_]*$'
	ClassifyNumberInteger = r'^-?[0-9e][0-9e]*$'
	ClassifyNumberFloat = r'^-?[0-9e][0-9e.]*$'
	ClassifyStringSingle = r'^\".*\"$'
	ClassifyStringDouble = r"^'.*'$"
	FunctionDefinitionMatch = r'^([^A-Z][^/]*)(?:/([0-9]+|\*))$'