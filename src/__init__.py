"""JapyScript - a mobile-first scripting language for 2D/3D games."""
from .version import VERSION, VERSION_LABEL
from .errors import JapyError, JapySyntaxError, JapyRuntimeError, JapyThrow, JapyExit, format_error
from .lexer import JapyLexer
from .parser import JapyParser
from .interpreter import JapyInterpreter

__version__ = VERSION
__all__ = ["VERSION", "VERSION_LABEL", "JapyError", "JapySyntaxError", "JapyRuntimeError",
           "JapyThrow", "JapyExit", "format_error", "JapyLexer", "JapyParser", "JapyInterpreter"]
