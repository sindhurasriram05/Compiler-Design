import json
from ast import parse
from ast2json import ast2json

ast = ast2json(parse(open('/Users/deeksha/Desktop/MyPythonCompiler/ast/for.py').read()))
print (json.dumps(ast, indent=4))
