"""
safe_eval safely evaluates constant expressions, lists, dicts, and tuples

safe_eval uses the abstract syntax tree created by compiler.parse. Since
compiler does the work, handling arbitrarily nested structures is transparent.

From the Python Cookbook
Submitter:        Michael Spencer
Date downloaded:  2006/01/09

@version: $Revision$
"""
__version__ = "$Revision$"[11:-2]


import compiler


class UnsafeSourceError(Exception):
    """
    Error for safe_eval to raise for unsafe constructs
    """

    def __init__(self,error,descr = None,node = None):
        self.error = error
        self.descr = descr
        self.node = node
        self.lineno = getattr(node,"lineno",None)

    def __repr__(self):
        return "Line %d.  %s: %s" % (self.lineno, self.error, self.descr)
    __str__ = __repr__

class AbstractVisitor(object):
    """
    ABS for the SafeEval class
    """

    def __init__(self):
        self._cache = {} # dispatch table

    def visit(self, node,**kw):
        cls = node.__class__
        meth = self._cache.setdefault(cls,
            getattr(self,'visit'+cls.__name__,self.default))
        return meth(node, **kw)

    def default(self, node, **kw):
        for child in node.getChildNodes():
            return self.visit(child, **kw)
    visitExpression = default


class SafeEval(AbstractVisitor):
    """
    A visitor for safe_eval to use
    """

    def visitConst(self, node, **kw):
        return node.value

    def visitDict(self,node,**kw):
        return dict([(self.visit(k),self.visit(v)) for k,v in node.items])

    def visitTuple(self,node, **kw):
        return tuple([self.visit(i) for i in node.nodes])

    def visitList(self,node, **kw):
        return [self.visit(i) for i in node.nodes]


class SafeEvalWithErrors(SafeEval):
    """
    A visitor for safe_eval that raises for disallowed names
    """

    def default(self, node, **kw):
        raise UnsafeSourceError("Unsupported source construct",
                                  node.__class__,node)

    def visitName(self,node, **kw):
        allowed = ['None', 'True', 'False']
        if node.name in allowed:
            return eval(node.name)
        else:
            raise UnsafeSourceError("Strings must be quoted",
                                      node.name, node)

    # Add more specific errors if desired


def safe_eval(source, fail_on_error=True):
    """
    safe_eval safely evaluates constant expressions, lists, dicts, and tuples
    using the abstract syntax tree created by compiler.parse. Since compiler
    does the work, handling arbitrarily nested structures is transparent.
    """
    walker = fail_on_error and SafeEvalWithErrors() or SafeEval()
    try:
        ast = compiler.parse(source,"eval")
    except SyntaxError, err:
        raise
    try:
        return walker.visit(ast)
    except UnsafeSourceError, err:
        raise

