"""Runtime value helpers shared by the interpreter and the standard library."""


class JapyFunction(object):
    """A function written in Japy (def / fn)."""

    def __init__(self, name, params, body, closure, filename=None):
        self.name = name
        self.params = params      # list of (name, default_node_or_None)
        self.body = body
        self.closure = closure
        self.file = filename

    def __repr__(self):
        return "<function %s>" % self.name


class JapyPlugin(object):
    """Handle returned by engineloadplugin(). Any method call on it is simulated."""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<plugin %s>" % self.name


def type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, JapyPlugin):
        return "plugin"
    if isinstance(value, JapyFunction) or callable(value):
        return "function"
    return type(value).__name__


def to_text(value, nested=False):
    """Convert any Japy value to the text print() shows."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return '"%s"' % value if nested else value
    if isinstance(value, float):
        if value != value:
            return "nan"
        if value in (float("inf"), float("-inf")):
            return "inf" if value > 0 else "-inf"
        if value.is_integer() and abs(value) < 1e16:
            return str(int(value))
        return repr(value)
    if isinstance(value, list):
        return "[" + ", ".join(to_text(v, True) for v in value) + "]"
    if isinstance(value, dict):
        return "{" + ", ".join("%s: %s" % (to_text(k, True), to_text(v, True))
                               for k, v in value.items()) + "}"
    if isinstance(value, JapyFunction):
        return "<function %s>" % value.name
    if isinstance(value, JapyPlugin):
        return "<plugin %s>" % value.name
    if callable(value):
        return "<builtin function>"
    return str(value)
