# -*- coding: utf-8 -*-
import logging
import parsererror as PErr

# TODO isfilter is (probably) not used anymore, delete from code


class Operator:
    """ A class for representing complete and incomplet elasticsearch objects
        Construct an object by giving te expressiontype and the operator.
        Complete it by giving it field name(s) and operand(s) using (one or
        many calls to) the string or multiple_fields_string methods, possibly
        incrementally.
    """

    operator = ''  # The name of the operator
    query = ''     # The resulting query string
    isfilter = False  # Should the query be expressed as an filter?

    def __init__(self, etype, op, isfilter=False):
        """ Creates an elasticObject object from
            etype, a string defining the expression type ("and","not")
            op,    a string defining the operation ("equals","missing"...)
            filter, a bool stating whether a filter should be constructed
        """
        self.ok_in_filter = True
        self.set_etype(etype, op)
        self.set_op(op, isfilter)


    def string(self, field=None, query=None):
        """ Method for adding the field and/or operand name to the question
            Updates the query object
            field is a string
            query is a string
            returns a string
        """
        self.query = self.make_string(self.query, field, query)
        return self.query

    def make_string(self, q_obj, field=None, query=None, other_op=None):
        """ Similar to the string method, but does not update the self.query
            q_obj is a query string (such as self.query)
            field is a string
            query is a string
            other_op is a tuple of two strings
            returns a string
        """
        # Creates, but does not set the query string
        if field is not None:
            q_obj = q_obj.replace('FIELD', field)
        if query is not None:
            q_obj = q_obj.replace('QUERY', query)
        if other_op is not None:
            q_obj = q_obj.replace(other_op[0], other_op[1])
        return q_obj

    def multiple_fields_string(self, fields='', query=None, constraints=''):
        """ Similar to the string method but handles multiple field search.
            Updates the self.query
            fields is a list of strings
            query  is a string
            returns a string
        """
        # Combine the fields in a bool query
        queries = []
        for f in fields:
            queries.append(self.make_string(self.query, f, query))
        # Normally, the fields should be in a disjunction;
        # find X in either this or that field
        combinator = 'should'
        if self.operator == 'missing':
            # If the operator is missing, we instead want to ask for documents
            # containing none of the fields (conjunction)
            combinator = 'must'

        fieldquery = '"bool" : {"%s" : [' % (combinator) + \
                     ','.join('{' + q + '}' for q in queries) + ']}'

        if constraints:
            nestedquery = '"match_phrase": {"%s": "%s"}' % (constraints[1],
                                                            constraints[2])
            self.query = '"nested": {"path": "%s", "query": {"bool": {"must":[{%s},{%s}]}}}'\
                         % (constraints[0], fieldquery, nestedquery)
        else:
            self.query = fieldquery

        return self.query

    def set_etype(self, etype, op):
        "Sets the expression type"
        if op == "missing":
            # missing filter is deprecated, use negated 'exists' instead
            etype = "and" if etype == "not" else "not"
        self.etype = etype

    def construct_query(self, operands):
        """ Constructs a query corresponding to the information given so far
            operands is a list of strings, the query
            returns a string
        """
        ops = []
        no_opers = len(operands)
        logging.debug('operand %s ' % self.operator)
        if no_opers > self.max_operands or no_opers < self.min_operands:
            raise PErr.QueryError('Wrong number of operands given. \
                                   Permitted range: %d-%d'
                                  % (self.min_operands, self.max_operands))

        for index, operand in enumerate(operands):
            # If the operand is within the range of what the operator needs,
            # fill up its slots (eg. range)
            if index > 0 and index < self.min_operands:
                ops[-1] = self.make_string(ops[-1], other_op=('OP%d' % index, operand))
            # If there are more than the minimum number of operands we prepare
            # them one by one here, and save the list to be coordinated by 'or'
            # och 'and not'
            else:
                ops.append('{%s}' % self.make_string(self.query, query=operand))

        if not operands:
            # if there are no operands (an unary operator), the query is
            # complete already
            ops = ['{%s}' % self.query]

        if self.etype == "and":  # prepare conjunctions
            # Two special cases:
            # No operand (missing, exists) means we're done
            if len(operands) == 0:
                return self.string()
            # Just one operand => no disjunction
            if len(operands) == 1:
                # don't use ops, they contain to many curly brackets
                return self.string(query=operands[0])

            # Several operands here means disjunction, the 'and' tells us that
            # the result should later be conjuncted with the rest of the
            # queries.
            return '"bool" : {"should" : [%s]}' % ','.join(ops)

        if self.etype == "not":
            return '"bool" : {"must_not" : [%s]}' % ','.join(ops)

    def set_op(self, op, isfilter=False):
        """ Method for setting the operator, called when an object is
            initialized. Sets all relevant object fields
        """
        self.operator = op
        self.max_operands = 100  # could be infinite...
        self.min_operands = 1
        self.ok_in_filter = True
        operators = ["equals", "contains", "missing", "exists", "regexp",
                     "startswith", "endswith", "lte", "gte"]

        if op == "equals":
            # Always use match_phrase, works better with tokenization.
            # (Eg. "gälla..5" in comment won't be found with term
            # self.operator =  "term" if max_words<=1 else "match_phrase"
            self.operator = "match_phrase"
            self.query = '"%s" : {"FIELD" : "QUERY"}' % self.operator
            # Set to false to make sure this query is never put
            # directly inside a filter
            self.ok_in_filter = False

        elif op == "strictequals":
            # This could be useful for searching in some "strict" (no
            # full-text) fields, like pos and might, in theory, be faster. In
            # practice, it is not (as of July 2015).
            self.operator = "term"
            self.query = '"%s" : {"FIELD" : "QUERY"}' % self.operator
            self.isfilter = True

        elif op == "contains":
            self.operator = "match"
            self.query = '"%s": {"FIELD": {"query": "QUERY", "operator": "and"}}' % self.operator
            # Set to false to make sure this query is never put
            # directly inside a filter (might be possible, not tested)
            self.ok_in_filter = False

        elif op == "missing":
            # This filter consider empty strings (but not empty lists) to be an
            # existing value
            # missing is deprecated in ES, use negated 'exists' instead
            self.max_operands = 0  # allows no operands
            self.min_operands = 0
            self.operator = "exist"  # "missing"
            # self.isfilter = True
            self.query = '"exists" : {"field" : "FIELD"}'
        elif op == "exists":
            # This filter consider empty strings (but not empty lists) to be an
            # existing value
            self.max_operands = 0  # allows no operands
            self.min_operands = 0
            self.operator = "exist"
            # self.isfilter = True
            self.query = '"exists" : {"field" : "FIELD"}'
        elif op == "regexp":
            self.operator = "regexp"
            self.query = '"regexp" : {"FIELD" : "QUERY"}'
        elif op == "startswith":
            self.operator = "startswith"
            op = 'regexp'
            self.query = '"%s" : {"FIELD" : "QUERY.*"}' % op
        elif op == "endswith":
            self.operator = "endswith"
            op = 'regexp'
            self.query = '"%s" : {"FIELD" : ".*QUERY"}' % op
        elif op == "lte":
            self.operator = "lte"
            op = 'range'
            self.query = '"%s" : {"FIELD" : {"lte" : "QUERY"}}' % op
        elif op == "gte":
            self.operator = "gte"
            op = 'range'
            self.query = '"%s" : {"FIELD" : {"gte" : "QUERY"}}' % op
        elif op == "range":
            self.operator = "range"
            op = 'range'
            self.max_operands = 2  # allows exactly two operands
            self.min_operands = 2
            self.query = '"%s" : {"FIELD" : {"lte" : "OP1", "gte": "QUERY"}}' % op
        else:
            raise PErr.QueryError('Operator "%s" not recognized.\
                                   Valid options %s'
                                  % (op, ','.join(operators)))
