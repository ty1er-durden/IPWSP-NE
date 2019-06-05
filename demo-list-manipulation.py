import sys

f = lambda y : chr(y)
mylist = map(f,range(65,73))

expressions = []
expressions.append('mylist')
expressions.append('len(mylist)')
expressions.append('mylist[0]')
expressions.append('mylist[7]')
expressions.append('mylist[-1]')
expressions.append('mylist[8]')
expressions.append('mylist[:3]')
expressions.append('mylist[2:4]')
expressions.append('mylist[2:7:2]')
expressions.append('mylist[:len(mylist) - 1]')
expressions.append('mylist[-1:-(len(mylist) + 1):-1]')
expressions.append('mylist.append("I")')
expressions.append('mylist')
expressions.append('mylist.pop(0)')
expressions.append('mylist')
expressions.append('mylist.remove("B")')
expressions.append('mylist')

for expression in expressions:
	print('EXPRESSION: ' + expression)
	try:
		print('    RESULT: ' + str(eval(expression)))
	except:
		print('    RESULT: ' + str(sys.exc_info()[0]))
	print('')
