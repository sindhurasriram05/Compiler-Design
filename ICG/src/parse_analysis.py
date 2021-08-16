import ply.yacc as yacc
from lex_analysis import tokens
from code import ThreeAddressCode
import symbol_table
import ast

threeAddressCode = ThreeAddressCode()
symbolTable = symbol_table.symbol_table('global', 'global')
scope_name = "1"
scopes = {'if':0, 'else': 0, 'while': 0, 'for':0, 'loop':0} 

def initSymbolTable(st):
	global symbolTable
	symbolTable = st
	threeAddressCode.symbolTable = symbolTable

def p_program(p):
	'''program : FN MAIN LPAREN RPAREN compoundStmt'''
	p[0] = p[5]

def p_compoundStmt_Stmt(p):
	'''compoundStmt : LBRACE tablePush Stmt moreStmt tablePop RBRACE
					| LBRACE tablePush Decl moreStmt tablePop RBRACE'''
	if p[1] == '{':
		p[0] = p[2]
	elif p[1] == 'if':
		p[0] = p[1]

def p_moreStmt(p):
	'''moreStmt : Stmt moreStmt
				| Decl moreStmt
				| empty'''
	p[0] = p[1]

def p_decl_Stmt(p):
	'''Decl : LET VarList
			| LET AssignExpr'''
	p[0] = p[2]

def p_varlist(p):
	'''VarList : VarList COMMA ID
				| ID SEMICOLON'''
	if p[2] == ',':
		p[0] = p[3]
	else:
		p[0] = p[1]

def p_assignExpr(p):
	'''AssignExpr : ID EQUALS expression COMMA AssignExpr
					| ID EQUALS expression SEMICOLON'''
	p[1] = [p[1], ast.newLeaf(p[1])]
	p[0] = [p[3][0], ast.newNode('=', p[3][1], p[1][1])]
	threeAddressCode.generate_icg('=', p[3][0], '', p[1][0])
	p[0][1].printAST()

def p_Stmt(p):
	'''Stmt : print_text SEMICOLON
			| expression SEMICOLON
			| AssignExpr
			| if
			| if_else
			| loop'''
	p[0] = p[1]

def p_print(p):
	'''print_text : PRINTMAC LPAREN text RPAREN
					| PRINTLNMAC LPAREN text RPAREN'''
	p[0] = p[3][1:-1]
	threeAddressCode.generate_icg("print", "","", p[3][1:-1])
def p_text(p):
	'''text : STRINGZ '''
	p[0] = p[1]

def p_if_else(p):
	'''if_else : IF setScopeNameIf condition   compoundStmt generateGoto  ELSE setScopeNameElse putLabelResult compoundStmt putLabelArg'''
	if p[2] == "True":
		p[0] = p[3]
	else:
		p[0] = p[6]

def p_if_cond(p):
	'''if : IF setScopeNameIf condition   compoundStmt putLabelResult'''
	if p[2] == "True":
		p[0] = p[3]
	else:
		pass

def p_loop(p):
	'''loop : WHILE setScopeNameWhile condition compoundStmt generateGotoLoop putLabelResult
			| LOOP setScopeNameLoop compoundStmt generateGotoLoop putLabelResult
			| FOR setScopeNameFor ID IN ellipsis compoundStmt putLabelResult loopEnd''' 
	if p[1] == 'while':
		if p[2] == 'True':
			p[0] = p[3]
		else:
			pass
	elif p[1] == 'loop':
		p[0] = p[2]

	else:
		p[0] = p[5]

def p_ellipsis(p):
	'''ellipsis : term DOTDOT term '''
	threeAddressCode.loop_begin()
	threeAddressCode.generate_icg("FOR", p[1][0], p[3][0], "goto S")
	
def p_expression_plus(p):
	'''expression : expression PLUS term'''
	p[0] = [None, 0]
	flag = True
	if type(p[1][0]) == int and type(p[3][0]) == int:
		flag = False
		p[0][0] = p[1][0] + p[3][0]
	threeAddressCode.generate_icg('+', p[1][0], p[3][0], p[0][0])
	if flag:
		p[0][0] = threeAddressCode.getLatestTemp()
	p[0][1] = ast.newNode('+', p[1][1], p[3][1])

def p_expression_minus(p):
	'''expression : expression MINUS term'''
	p[0] = [None, 0]
	flag = True
	if type(p[1][0]) == int and type(p[3][0]) == int:
		flag = False
		p[0][0] = p[1][0] - p[3][0]
	threeAddressCode.generate_icg('-', p[1][0], p[3][0], p[0][0])
	if flag:
		p[0][0] = threeAddressCode.getLatestTemp()
	p[0][1] = ast.newNode('-', p[1][1], p[3][1])

def p_term_times(p):
	'''term : term TIMES factor'''
	p[0] = [None, 0]
	flag = True
	if type(p[1][0]) == int and type(p[3][0]) == int:
		flag = False
		p[0][0] = p[1][0] * p[3][0]
	threeAddressCode.generate_icg('*', p[1][0], p[3][0], p[0][0])
	if flag:
		p[0][0] = threeAddressCode.getLatestTemp()
	p[0][1] = ast.newNode('*', p[1][1], p[3][1])

def p_term_div(p):
	'''term : term DIVIDE factor'''
	p[0] = [None, 0]
	flag = True
	if type(p[1][0]) == int and type(p[3][0]) == int:
		flag = False
		p[0][0] = p[1][0] / p[3][0]
	threeAddressCode.generate_icg('/', p[1][0], p[3][0], p[0][0])
	if flag:
		p[0][0] = threeAddressCode.getLatestTemp()
	p[0][1] = ast.newNode('/', p[1][1], p[3][1]) 

def p_condition_equequ(p):
	'''condition : term EQUALSEQUALS term'''
	p[0] = [None, ast.newNode('==', p[1][1], p[3][1])]
	threeAddressCode.generate_icg("==F", p[1][0], p[3][0], "goto S")

def p_condition_notequ(p):
	'''condition : term NOTEQUALS term'''
	p[0] = [None, ast.newNode('!=', p[1][1], p[3][1])]
	threeAddressCode.generate_icg("!=F", p[1][0], p[3][0], "goto S")

def p_condition_gthanequ(p):
	'''condition : term GTHANEQU term'''
	p[0] = [None, ast.newNode('>=', p[1][1], p[3][1])]
	threeAddressCode.generate_icg(">=F", p[1][0], p[3][0], "goto S")

def p_condition_lthanequ(p):
	'''condition : term LTHANEQU term'''
	p[0] = [None, ast.newNode('<=', p[1][1], p[3][1])]
	threeAddressCode.generate_icg("<=F", p[1][0], p[3][0], "goto S")

def p_condition_lthan(p):
	'''condition : term GTHAN term'''
	p[0] = [None, ast.newNode('>', p[1][1], p[3][1])]
	threeAddressCode.generate_icg(">F", p[1][0], p[3][0], "goto S")

def p_condition_gthan(p):
	'''condition : term LTHAN term'''
	p[0] = [None, ast.newNode('<', p[1][1], p[3][1])]
	threeAddressCode.generate_icg("<F", p[1][0], p[3][0], "goto S")

def p_expression_term(p):
	'expression : term'
	p[0] = p[1]

def p_term_factor(p):
	'term : factor'
	p[0] = p[1]

def p_factor_num(p):
	'''factor : NUMBER
				| ID '''
	p[0] = p[1]
	p[0] = [p[1], ast.newLeaf(p[1])]

def p_factor_expr(p):
	'''factor : LPAREN expression RPAREN'''
	p[0] = p[2]

def p_putLabelResult(p):
	'''putLabelResult : empty'''
	threeAddressCode.putLabel('result')

def p_putLabelArg(p):
	'''putLabelArg : empty'''
	threeAddressCode.putLabel('arg1')

def p_generateGoto(p):
	'''generateGoto : empty'''
	threeAddressCode.generate_icg("goto", "S", '', '')

def p_generateGotoLoop(p):
	'''generateGotoLoop : empty'''
	threeAddressCode.putLabel('loop')

def p_setScopeNameIf(p):
	'''setScopeNameIf : empty'''
	global scopes
	global scope_name
	scopes['if'] += 1
	scope_name = 'if'+str(scopes['if']) 

def p_setScopeNameElse(p):
	'''setScopeNameElse : empty'''
	global scopes
	global scope_name
	scopes['else'] += 1
	scope_name = 'else'+str(scopes['else'])

def p_setScopeNameWhile(p):
	'''setScopeNameWhile : empty'''
	global scopes
	global scope_name
	scopes['while'] += 1
	scope_name = 'while'+str(scopes['while'])

def p_setScopeNameLoop(p):
	'''setScopeNameLoop : empty'''
	global scopes
	global scope_name
	scopes['loop'] += 1
	scope_name = 'loop'+str(scopes['loop']) 

def p_setScopeNameFor(p):
	'''setScopeNameFor : empty'''
	global scopes
	global scope_name
	scopes['for'] += 1
	scope_name = 'for'+str(scopes['for']) 

def p_loopEnd(p):
	'''loopEnd :  empty'''
	threeAddressCode.loop_end()
	threeAddressCode.generate_icg("loop-end", "","","")

def p_tablePush(p):
	'''tablePush : empty'''
	global symbolTable
	symbolTable = symbolTable.get_child(scope_name)
	threeAddressCode.symbolTable = symbolTable

def p_tablePop(p):
	'''tablePop : empty'''
	global symbolTable
	symbolTable = symbolTable.get_parent()
	threeAddressCode.symbolTable = symbolTable

# Error rule for syntax errors
def p_error(p):
	print("Syntax error in input!")
	print(p)

def p_empty(p):
	'empty : '
	pass
	