"""Direct, experiment-local lowering of finite scalar sums through local helpers.

This is not installed in Missing Link or SymPy. The sum path supports flat Symbol
arguments, the math backend, and nonempty ascending integer bounds. Other uses
retain native lambdify when CSE is disabled or no Sum occurs.
"""

import operator

import sympy as sy


def scoped_lambdify(args, expr, modules=None, **options):
    """Compile each sum body in its own argument scope, using native CSE there."""
    def has_sum(node):
        if isinstance(node, (list, tuple)):
            return any(has_sum(item) for item in node)
        return isinstance(node, sy.Basic) and node.has(sy.Sum)

    if options.get("cse", False) is not True or not has_sum(expr):
        return sy.lambdify(args, expr, modules=modules, **options)

    environment = list(args) if isinstance(args, (list, tuple)) else [args]
    if not all(isinstance(arg, sy.Symbol) for arg in environment):
        raise NotImplementedError("The direct sum prototype requires flat Symbol arguments")
    if len({str(arg) for arg in environment}) != len(environment):
        raise ValueError("Argument names must be distinct")
    backends = list(modules) if isinstance(modules, (list, tuple)) else [modules]
    if backends.count("math") != 1 or not all(
        isinstance(item, dict) or item == "math" for item in backends
    ):
        raise NotImplementedError("The direct sum prototype supports only the math backend")

    helpers = {}
    occupied = {str(arg) for arg in environment}
    for item in backends:
        if isinstance(item, dict):
            occupied.update(item)
    for node in sy.preorder_traversal(expr):
        if isinstance(node, sy.Symbol):
            occupied.add(str(node))
        elif isinstance(node, sy.Function):
            occupied.add(str(node.func))

    def compile_scope(scope_args, body):
        lowered = lower(body, scope_args)
        return sy.lambdify(scope_args, lowered, modules=[helpers, *backends], **options)

    def lower(node, scope_args):
        if isinstance(node, (list, tuple)):
            return type(node)(lower(item, scope_args) for item in node)
        if not isinstance(node, sy.Basic) or not node.args:
            return node
        if isinstance(node, sy.Sum):
            index, start, end = node.limits[-1]
            if not isinstance(index, sy.Symbol):
                raise NotImplementedError("Sum indices must be Symbols")
            captures = [arg for arg in scope_args if str(arg) != str(index)]
            inner = (node.function if len(node.limits) == 1 else
                     sy.Sum(node.function, *node.limits[:-1]))
            body = compile_scope([*captures, index], inner)

            def summed(*values):
                supplied, first, last = values[:-2], values[-2], values[-1]
                first, last = operator.index(first), operator.index(last)
                if last < first:
                    raise ValueError("The direct sum prototype requires nonempty ascending bounds")
                return sum(body(*supplied, position) for position in range(first, last + 1))

            number = len(helpers)
            name = f"_scope_sum_{number}"
            while name in occupied:
                number += 1
                name = f"_scope_sum_{number}"
            occupied.add(name)
            helpers[name] = summed
            return sy.Function(name)(*captures, lower(start, scope_args), lower(end, scope_args))
        if getattr(node, "bound_symbols", ()):
            raise NotImplementedError("Other symbolic binders are outside the direct sum prototype")
        return node.func(*(lower(arg, scope_args) for arg in node.args))

    return compile_scope(environment, expr)
