"""Japy error types and readable error formatting."""


class JapyError(Exception):
    """Base class for every error the Japy engine reports to the script author."""
    kind = "Error"

    def __init__(self, message, line=None, col=None, filename=None):
        Exception.__init__(self, message)
        self.message = message
        self.line = line
        self.col = col
        self.filename = filename


class JapySyntaxError(JapyError):
    kind = "SyntaxError"


class JapyRuntimeError(JapyError):
    kind = "RuntimeError"


class JapyThrow(JapyError):
    """Raised by the `throw` statement. `value` is the thrown Japy value."""
    kind = "Uncaught throw"

    def __init__(self, value, text, line=None):
        JapyError.__init__(self, text, line)
        self.value = value


class JapyExit(Exception):
    """Raised by exit(). Not an error: stops the script with a status code."""

    def __init__(self, code=0):
        Exception.__init__(self, code)
        self.code = code


def format_error(err, sources=None):
    """Return a readable multi-line description of a JapyError."""
    where = err.filename or "<script>"
    head = "[Japy %s] %s" % (err.kind, where)
    if err.line:
        head += ":%d" % err.line
    lines = [head]
    source = (sources or {}).get(err.filename)
    if source and err.line:
        src_lines = source.split("\n")
        if 1 <= err.line <= len(src_lines):
            lines.append("  %4d | %s" % (err.line, src_lines[err.line - 1].rstrip("\r")))
            if err.col:
                lines.append("       | " + " " * (err.col - 1) + "^")
    lines.append("  " + str(err.message))
    return "\n".join(lines)
