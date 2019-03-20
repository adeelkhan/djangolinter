import re 

# class RuleViolation(object):
#     """
#     Base class representing a rule violation which can be used for reporting.
#     """

#     def __init__(self, rule):
#         """
#         Init method.

#         Arguments:
#             rule: The Rule which was violated.

#         """
#         self.rule = rule
#         self.full_path = ''
#         self.is_disabled = False



# class ExpressionRuleViolation(RuleViolation):
#     """
#     A class representing a particular rule violation for expressions which
#     contain more specific details of the location of the violation for reporting
#     purposes.

#     """

#     def __init__(self, rule, expression):
#         """
#         Init method.

#         Arguments:
#             rule: The Rule which was violated.
#             expression: The Expression that was in violation.

#         """
#         super(ExpressionRuleViolation, self).__init__(rule)
#         self.expression = expression
#         self.start_line = 0
#         self.start_column = 0
#         self.end_line = 0
#         self.end_column = 0
#         self.lines = []



class Expression(object):
	def __init__(self, full_expression, start, end, lineno, offset):
		self.full_expression = full_expression
		self.start = start
		self.end = end
		self.lineno = lineno
		self.offset = offset
		self.inner_expression = full_expression[2:-2]

class TransExpression(Expression):
	def __init__(self, *args, **kwargs):
		super(TransExpression, self).__init__(*args, **kwargs)

	def validate_expression(self, template_file, results):
		return 
		# from pdb import set_trace
		# set_trace()
		print str(self.start) + ':' + self.inner_expression
		trans_expr = self.inner_expression
		if 'as' not in trans_expr:
			results.append({'violation':'django-trans-missing-escape', 'expression':self})
			return 
		pos = trans_expr.find('as')
		if pos == -1:
			results.append({'violation':'django-trans-missing-escape', 'expression':self})
			return 
		trans_var_name_used = trans_expr[pos + len('as'):].strip()
		print trans_var_name_used
		
		escape_expr_start_pos = template_file.find('{{', self.end)
		if escape_expr_start_pos == -1:
			results.append({'violation':'django-trans-missing-escape', 'expression':self})
			return 
		escape_expr_end_pos = template_file.find('}}', escape_expr_start_pos)
		
		# couldn't find matching }}
		if escape_expr_end_pos == -1:
			results.append({'violation':'django-trans-missing-escape', 'expression':self})		
		escape_expr = template_file[escape_expr_start_pos+len('{{'):escape_expr_end_pos]
		 		
		# check escape expression has the right variable and its escaped properly
		# with force_escape filter 
		if '|' not in escape_expr \
			or len(escape_expr.split('|')) != 2:
			results.append({'violation':'django-trans-invalid-escape-filter', 'expression':self})
			return		
		escape_expr_var_used, escape_filter = escape_expr.split('|')[0], escape_expr.split('|')[1]
		if trans_var_name_used != escape_expr_var_used:
			results.append({'violation':'django-escape-variable-mismatch', 'expression':self})
			return
		if escape_filter != 'force_escape':
			results.append({'violation':'django-escape-invalid-filter', 'expression':self})
			return


class BlockTransExpression(Expression):
	def __init__(self, *args, **kwargs):
		super(BlockTransExpression, self).__init__(*args, **kwargs)

	def validate_expression(self, template_file, results):
		#pass
		# from pdb import set_trace
		# set_trace()
		print str(self.start) + ':' + self.inner_expression
		if self.offset == 0 and self.lineno == 0:
			results.append({'violation':'django-blocktrans-missing-escape-filter', 'expression':self})
			return
		if self.lineno != 0:
			prev_offset = self.start - self.offset
			force_filter_start_pos = template_file.rfind('{%', prev_offset)
			if force_filter_start_pos ==-1:
				results.append({'violation':'django-blocktrans-missing-escape-filter', 'expression':self})
				return
			force_filter_start_pos = template_file.rfind('%}', force_filter_start_pos)
			force_escape_filter = template_file[force_filter_start_pos:force_filter_end_pos]
			print force_escape_filter

			# now check if the blocktrans applied filter is correct

def find_translation_expression(django_template, expressions):	
	 
	te = None 
	#print data
	trans_iterator = re.finditer(r'{% trans .*%}', django_template, re.I)
	for trans in trans_iterator:
		expr =  trans.string[trans.start():trans.end()]

		start = trans.start()
		lineno = django_template.count('\n', 0, start) + 1
		offset = start - django_template.rfind('\n', 0, start)
	
		trans_expr = TransExpression(expr, 
						trans.start(),
						trans.end(), 
						lineno,
						offset)
		if trans_expr:
			expressions.append(trans_expr)

	block_trans_iterator = re.finditer(r'{% blocktrans .*?%}', django_template, re.I)
	for trans in block_trans_iterator:
		expr =  trans.string[trans.start():trans.end()]
		start = trans.start()
		
		lineno = django_template.count('\n', 0, start) + 1
		offset = start - django_template.rfind('\n', 0, start)

		blocktrans_expr = BlockTransExpression(expr, 
							trans.start(),
							trans.end(),
							lineno,
							offset)


		if blocktrans_expr:
			expressions.append(blocktrans_expr)


	# for line in data:
	# 	search_trans = re.search(r'{% trans .*%}', line, re.I)
	# 	block_trans = re.search(r'{% blocktrans .*%}', line, re.I)

	# 	if search_trans:
	# 		expr =  search_trans.string[search_trans.start():search_trans.end()]
	# 		trans_expr = TransExpression(expr, 
	# 						search_trans.start(),
	# 						search_trans.end())
	# 		if trans_expr:
	# 			expressions.append(trans_expr)

	# 	if block_trans:
	# 		expr  = block_trans.string[block_trans.start():block_trans.end()]
	# 		blocktrans_expr = BlockTransExpression(expr, 
	# 						block_trans.start(),
	# 						block_trans.end())
	# 		if blocktrans_expr:
	# 			expressions.append(blocktrans_expr)

def check_translation_filters(template_file, expressions, results):
	for expr in expressions:
		expr.validate_expression(template_file, results)

if __name__== '__main__':
	file = open('./djangotemplate.html','r')
	django_template = file.read()
	expressions = []
	results = []
	find_translation_expression(django_template, expressions)
	#file.seek(0)
	check_translation_filters(django_template, expressions, results)

	print '------violations-----'
	for r in results:
		print r['violation'] + ':' + r['expression'].full_expression + ':' + str(r['expression'].lineno) + ':' + str(r['expression'].offset)
