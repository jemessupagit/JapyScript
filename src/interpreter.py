"""Japy interpreter: walks the AST produced by japy.parser."""
import difflib
import functools
import os
import sys
import time

from .errors import JapyError, JapyRuntimeError, JapyThrow, JapyExit
from .lexer import JapyLexer
from .parser import (JapyParser, VarDecl, Assign, FuncDef, FuncExpr, Call, Index, Member,
                     Ident, Literal, ListLit, DictLit, Binary, Unary, If, While, For,
                     Break, Continue, Return, Try, Throw, Import)
from .values import JapyFunction, JapyPlugin, type_name, to_text

# Nodes whose value the REPL echoes when they are the last statement.
_EXPR_NODES = (Ident, Literal, ListLit, DictLit, FuncExpr, Call, Index, Member, Binary, Unary)

DEFAULT_MAX_LOOPS = 1000000     # safety net: stops runaway while-loops
DEFAULT_MAX_DEPTH = 200         # safety net: stops runaway recursion


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value


class Env(object):
    """One variable scope. Blocks and function calls each get their own."""
    __slots__ = ('vars', 'consts', 'parent')

    def __init__(self, parent=None):
        self.vars = {}
        self.consts = None
        self.parent = parent

    def define(self, name, value, const=False):
        self.vars[name] = value
        if const:
            if self.consts is None:
                self.consts = set()
            self.consts.add(name)
        elif self.consts is not None:
            self.consts.discard(name)

    def find(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env
            env = env.parent
        return None


class PluginMethod(object):
    """A simulated method call on a plugin handle."""

    def __init__(self, interp, plugin, name):
        self.interp, self.plugin, self.name = interp, plugin, name

    def __call__(self, *args):
        self.interp.write("[Japy Plugin Trigger] Object: %s -> Executed Method: %s with parameters: %s"
                          % (self.plugin.name, self.name, to_text(list(args))))
        return None


class JapyInterpreter(object):
    def __init__(self, stdout=None, stdin=None, base_dir=None, max_loops=DEFAULT_MAX_LOOPS,
                 max_depth=DEFAULT_MAX_DEPTH, realtime=False, frames=1):
        self.stdout = stdout
        self.stdin = stdin
        self.base_dir = base_dir or os.getcwd()
        self.max_loops = max_loops
        self.max_depth = max_depth
        self.realtime = realtime
        self.frames = frames

        self.globals = Env()
        self.builtins = {}
        self.docs = {}              # name -> (category, signature, description)
        self.methods = {}
        self.plugins = []
        self.save_data = {}
        self.imported = set()
        self.sources = {}           # filename -> source text (for error display)
        self.cur_file = None
        self.depth = 0
        self.loop_depth = 0
        self.frame = 0
        self.started = time.time()

        if sys.getrecursionlimit() < 6000:
            sys.setrecursionlimit(6000)

        self._dispatch = {
            Literal: self._literal, Ident: self._ident, ListLit: self._list, DictLit: self._dict,
            FuncExpr: self._funcexpr, Call: self._call, Index: self._index, Member: self._member,
            Binary: self._binary, Unary: self._unary, VarDecl: self._vardecl, Assign: self._assign,
            FuncDef: self._funcdef, If: self._if, While: self._while, For: self._for,
            Break: self._break, Continue: self._continue, Return: self._return,
            Try: self._try, Throw: self._throw, Import: self._import,
        }

        from . import stdlib, api_db
        stdlib.install(self)
        api_db.install(self)
        # Backwards-compatible alias for tools written against v1.0.x.
        self.custom_apis = self.builtins

    # --------------------------------------------------------------- output
    def write(self, text, end="\n"):
        out = self.stdout if self.stdout is not None else sys.stdout
        out.write(text + end)

    def flush(self):
        out = self.stdout if self.stdout is not None else sys.stdout
        if hasattr(out, "flush"):
            out.flush()

    # ----------------------------------------------------------- registration
    def register(self, name, category, signature, description, fn):
        self.builtins[name] = fn
        self.docs[name] = (category, signature, description)

    @staticmethod
    def to_text(value, nested=False):
        return to_text(value, nested)

    # ------------------------------------------------------------ running code
    def execute_source(self, source, filename="<script>", want_value=False):
        """Parse and run source in the global scope. Returns the last value
        (only when want_value is set and the last statement is an expression)."""
        self.sources[filename] = source
        saved = self.cur_file
        self.cur_file = filename
        try:
            tokens = JapyLexer().tokenize(source)
            program = JapyParser(tokens).parse()
            for st in program.statements:          # functions can be used before their definition
                if st.__class__ is FuncDef:
                    self._funcdef(st, self.globals)
            result = self.exec_block(program.statements, self.globals)
            if want_value and program.statements and isinstance(program.statements[-1], _EXPR_NODES):
                return result
            return None
        except RecursionError:
            raise JapyRuntimeError("Maximum recursion depth exceeded", filename=filename)
        except JapyError as err:
            if err.filename is None:
                err.filename = filename
            raise
        finally:
            self.cur_file = saved

    def run_entry_points(self):
        """Call setup() once, then loop() for each frame (see --frames)."""
        setup = self.globals.vars.get("setup")
        if isinstance(setup, JapyFunction):
            self.call_function(setup, [])
        loop = self.globals.vars.get("loop")
        if isinstance(loop, JapyFunction):
            for i in range(self.frames):
                self.frame = i + 1
                self.call_function(loop, [])

    def run_script(self, source, filename="<script>"):
        self.execute_source(source, filename)
        self.run_entry_points()

    def run_function(self, func_name):
        fn = self.globals.vars.get(func_name)
        if isinstance(fn, JapyFunction):
            return self.call_function(fn, [])
        return None

    # --------------------------------------------------------------- evaluation
    def eval(self, node, env):
        return self._dispatch[node.__class__](node, env)

    def exec_block(self, statements, env):
        result = None
        dispatch = self._dispatch
        for st in statements:
            try:
                result = dispatch[st.__class__](st, env)
            except JapyError as err:
                if err.line is None:
                    err.line = st.line
                if err.filename is None:
                    err.filename = self.cur_file
                raise
        return result

    # literals and names
    def _literal(self, node, env):
        return node.value

    def _ident(self, node, env):
        name = node.name
        scope = env
        while scope is not None:
            values = scope.vars
            if name in values:
                return values[name]
            scope = scope.parent
        if name in self.builtins:
            return self.builtins[name]
        raise JapyRuntimeError(self._undefined_message(name, env), node.line)

    def _undefined_message(self, name, env):
        names = set(self.builtins)
        scope = env
        while scope is not None:
            names.update(scope.vars)
            scope = scope.parent
        msg = "Undefined variable or function '%s'" % name
        close = difflib.get_close_matches(name, names, n=1, cutoff=0.7)
        if close:
            msg += ". Did you mean '%s'?" % close[0]
        return msg

    def _list(self, node, env):
        return [self.eval(item, env) for item in node.items]

    def _dict(self, node, env):
        return dict((key, self.eval(value, env)) for key, value in node.pairs)

    def _funcexpr(self, node, env):
        return JapyFunction("<fn>", node.params, node.body, env, self.cur_file)

    def _funcdef(self, node, env):
        env.define(node.name, JapyFunction(node.name, node.params, node.body, env, self.cur_file))
        return None

    # variables
    def _vardecl(self, node, env):
        value = self.eval(node.value, env)
        env.define(node.name, value, node.const)
        return value

    def _assign(self, node, env):
        target, op = node.target, node.op
        cls = target.__class__
        if cls is Ident:
            value = self.eval(node.value, env)
            if op:
                value = self._binop(op, self._ident(target, env), value, node)
            owner = env.find(target.name)
            if owner is None:
                owner = self.globals           # assigning an unknown name creates a global
            elif owner.consts and target.name in owner.consts:
                raise JapyRuntimeError("Cannot change '%s' because it was declared with const" % target.name,
                                       node.line)
            owner.vars[target.name] = value
            return value
        if cls is Index:
            obj = self.eval(target.obj, env)
            idx = self.eval(target.index, env)
            value = self.eval(node.value, env)
            if op:
                value = self._binop(op, self._get_index(obj, idx, node), value, node)
            self._set_index(obj, idx, value, node)
            return value
        obj = self.eval(target.obj, env)                      # Member
        value = self.eval(node.value, env)
        if op:
            value = self._binop(op, self._get_member(obj, target.name, node), value, node)
        if obj.__class__ is not dict:
            raise JapyRuntimeError("Cannot set property '%s' on a %s" % (target.name, type_name(obj)), node.line)
        obj[target.name] = value
        return value

    # indexing and members
    def _index(self, node, env):
        return self._get_index(self.eval(node.obj, env), self.eval(node.index, env), node)

    def _get_index(self, obj, idx, node):
        cls = obj.__class__
        if cls is list or cls is str:
            if idx.__class__ is float and idx.is_integer():
                idx = int(idx)
            if idx.__class__ is not int:
                raise JapyRuntimeError("A %s index must be a whole number, got %s"
                                       % (type_name(obj), type_name(idx)), node.line)
            n = len(obj)
            if idx < -n or idx >= n:
                raise JapyRuntimeError("Index %d is out of range (length is %d)" % (idx, n), node.line)
            return obj[idx]
        if cls is dict:
            try:
                return obj.get(idx)
            except TypeError:
                raise JapyRuntimeError("Dict keys must be numbers, text or bool", node.line)
        raise JapyRuntimeError("Cannot use [ ] on a %s" % type_name(obj), node.line)

    def _set_index(self, obj, idx, value, node):
        cls = obj.__class__
        if cls is list:
            if idx.__class__ is float and idx.is_integer():
                idx = int(idx)
            if idx.__class__ is not int:
                raise JapyRuntimeError("A list index must be a whole number, got %s" % type_name(idx), node.line)
            n = len(obj)
            if idx < -n or idx >= n:
                raise JapyRuntimeError("Index %d is out of range (length is %d)" % (idx, n), node.line)
            obj[idx] = value
        elif cls is dict:
            if not isinstance(idx, (str, int, float, bool)):
                raise JapyRuntimeError("Dict keys must be numbers, text or bool", node.line)
            obj[idx] = value
        else:
            raise JapyRuntimeError("Cannot change items of a %s" % type_name(obj), node.line)

    def _member(self, node, env):
        return self._get_member(self.eval(node.obj, env), node.name, node)

    def _get_member(self, obj, name, node):
        cls = obj.__class__
        if cls is dict:
            if name in obj:
                return obj[name]
            method = self.methods["dict"].get(name)
            if method is not None:
                return functools.partial(method, obj)
            if name == "length":
                return len(obj)
            return None
        if cls is JapyPlugin:
            return PluginMethod(self, obj, name)
        if cls is list or cls is str:
            if name == "length":
                return len(obj)
            method = self.methods["list" if cls is list else "str"].get(name)
            if method is None:
                raise JapyRuntimeError("A %s has no method '%s'" % (type_name(obj), name), node.line)
            return functools.partial(method, obj)
        raise JapyRuntimeError("Cannot read '%s' of a %s" % (name, type_name(obj)), node.line)

    # calls
    @staticmethod
    def _callee_name(callee):
        if callee.__class__ is Ident:
            return callee.name
        if callee.__class__ is Member:
            return "." + callee.name
        return "value"

    def _call(self, node, env):
        callee = node.callee
        if callee.__class__ is Member:
            fn = self._get_member(self.eval(callee.obj, env), callee.name, node)
        else:
            fn = self.eval(callee, env)
        args = [self.eval(arg, env) for arg in node.args]
        return self.call_value(fn, args, node)

    def call_value(self, fn, args, node=None):
        """Call any Japy function value (user-defined or built in)."""
        if fn.__class__ is JapyFunction:
            return self.call_function(fn, args, node)
        if callable(fn):
            try:
                return fn(*args)
            except (TypeError, ValueError, KeyError, IndexError, OverflowError,
                    ZeroDivisionError, AttributeError, OSError) as exc:
                name = getattr(fn, "__name__", None) or getattr(fn, "name", "function")
                if node is not None and node.callee.__class__ is Ident:
                    name = node.callee.name
                raise JapyRuntimeError("%s(): %s" % (name, exc), node.line if node is not None else None)
        what = self._callee_name(node.callee) if node is not None else "value"
        raise JapyRuntimeError("'%s' is not a function (it is a %s)" % (what, type_name(fn)),
                               node.line if node is not None else None)

    def call_function(self, fn, args, node=None):
        params = fn.params
        line = node.line if node is not None else None
        if len(args) > len(params):
            raise JapyRuntimeError("%s() takes at most %d argument(s) but %d were given"
                                   % (fn.name, len(params), len(args)), line)
        local = Env(fn.closure)
        for i, (pname, default) in enumerate(params):
            if i < len(args):
                local.vars[pname] = args[i]
            elif default is not None:
                local.vars[pname] = self.eval(default, local)
            else:
                raise JapyRuntimeError("%s() is missing the argument '%s'" % (fn.name, pname), line)
        if self.depth >= self.max_depth:
            raise JapyRuntimeError("Too many nested calls (%d) - is a function calling itself forever?"
                                   % self.max_depth, line)
        saved_file, saved_loops = self.cur_file, self.loop_depth
        self.cur_file, self.loop_depth = fn.file, 0
        self.depth += 1
        try:
            self.exec_block(fn.body, local)
        except ReturnSignal as ret:
            return ret.value
        finally:
            self.depth -= 1
            self.cur_file, self.loop_depth = saved_file, saved_loops
        return None

    # operators
    def _unary(self, node, env):
        value = self.eval(node.operand, env)
        if node.op == '!':
            return not value
        if not isinstance(value, (int, float)):
            raise JapyRuntimeError("Cannot use '-' with a %s" % type_name(value), node.line)
        return -value

    def _binary(self, node, env):
        op = node.op
        if op == '&&':
            return bool(self.eval(node.left, env)) and bool(self.eval(node.right, env))
        if op == '||':
            return bool(self.eval(node.left, env)) or bool(self.eval(node.right, env))
        return self._binop(op, self.eval(node.left, env), self.eval(node.right, env), node)

    def _binop(self, op, a, b, node):
        if op == '==':
            return a == b
        if op == '!=':
            return a != b
        nums = isinstance(a, (int, float)) and isinstance(b, (int, float))
        try:
            if op == '+':
                if a.__class__ is str or b.__class__ is str:
                    return to_text(a) + to_text(b)
                if nums or (a.__class__ is list and b.__class__ is list):
                    return a + b
            elif op == '-':
                if nums:
                    return a - b
            elif op == '*':
                if nums or (isinstance(a, (str, list)) and b.__class__ is int) or \
                        (a.__class__ is int and isinstance(b, (str, list))):
                    return a * b
            elif op == '/':
                if nums:
                    if b == 0:
                        raise JapyRuntimeError("Division by zero", node.line)
                    if isinstance(a, int) and isinstance(b, int) and a % b == 0:
                        return a // b
                    return a / b
            elif op == '%':
                if nums:
                    if b == 0:
                        raise JapyRuntimeError("Modulo by zero", node.line)
                    return a % b
            elif op == '**':
                if nums:
                    if isinstance(b, int) and b > 10000 and abs(a) > 1:
                        raise JapyRuntimeError("Exponent is too large", node.line)
                    return a ** b
            elif op in ('<', '>', '<=', '>='):
                if nums or (a.__class__ is str and b.__class__ is str):
                    if op == '<':
                        return a < b
                    if op == '>':
                        return a > b
                    if op == '<=':
                        return a <= b
                    return a >= b
            elif op == 'in':
                if b.__class__ in (list, dict) or (a.__class__ is str and b.__class__ is str):
                    return a in b
        except OverflowError:
            raise JapyRuntimeError("The number is too large", node.line)
        except TypeError:
            pass
        raise JapyRuntimeError("Cannot use '%s' with %s and %s" % (op, type_name(a), type_name(b)), node.line)

    # control flow
    def _if(self, node, env):
        if self.eval(node.condition, env):
            return self.exec_block(node.then_body, Env(env))
        if node.else_body is not None:
            return self.exec_block(node.else_body, Env(env))
        return None

    def _while(self, node, env):
        count = 0
        self.loop_depth += 1
        try:
            while self.eval(node.condition, env):
                try:
                    self.exec_block(node.body, Env(env))
                except BreakSignal:
                    break
                except ContinueSignal:
                    pass
                count += 1
                if count >= self.max_loops:
                    raise JapyRuntimeError("Loop stopped after %d rounds (possible infinite loop). "
                                           "Raise the limit with --max-loops." % self.max_loops, node.line)
        finally:
            self.loop_depth -= 1
        return None

    def _for(self, node, env):
        iterable = self.eval(node.iterable, env)
        names = node.names
        cls = iterable.__class__
        if cls is list or cls is str:
            items = list(iterable)
        elif cls is dict:
            items = list(iterable.items()) if len(names) == 2 else list(iterable)
        else:
            raise JapyRuntimeError("Cannot loop over a %s (use a list, dict, text or range())"
                                   % type_name(iterable), node.line)
        self.loop_depth += 1
        try:
            for item in items:
                scope = Env(env)
                if len(names) == 1:
                    scope.vars[names[0]] = item
                else:
                    if item.__class__ not in (list, tuple) or len(item) != len(names):
                        raise JapyRuntimeError("Cannot split each item into %d variables" % len(names), node.line)
                    for n, v in zip(names, item):
                        scope.vars[n] = v
                try:
                    self.exec_block(node.body, scope)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
        finally:
            self.loop_depth -= 1
        return None

    def _break(self, node, env):
        if self.loop_depth == 0:
            raise JapyRuntimeError("'break' can only be used inside a loop", node.line)
        raise BreakSignal()

    def _continue(self, node, env):
        if self.loop_depth == 0:
            raise JapyRuntimeError("'continue' can only be used inside a loop", node.line)
        raise ContinueSignal()

    def _return(self, node, env):
        if self.depth == 0:
            raise JapyRuntimeError("'return' can only be used inside a function", node.line)
        raise ReturnSignal(self.eval(node.value, env) if node.value is not None else None)

    def _try(self, node, env):
        try:
            try:
                self.exec_block(node.body, Env(env))
            except JapyError as exc:
                if node.catch_body is None:
                    raise
                scope = Env(env)
                if node.catch_name:
                    scope.vars[node.catch_name] = exc.value if isinstance(exc, JapyThrow) else exc.message
                self.exec_block(node.catch_body, scope)
        finally:
            if node.finally_body is not None:
                self.exec_block(node.finally_body, Env(env))
        return None

    def _throw(self, node, env):
        value = self.eval(node.value, env)
        raise JapyThrow(value, to_text(value), node.line)

    def _import(self, node, env):
        path = self._resolve_import(node.path, node)
        if path in self.imported:
            return None
        self.imported.add(path)
        with open(path, "r", encoding="utf-8-sig") as handle:
            source = handle.read()
        self.execute_source(source, path)
        return None

    def _resolve_import(self, name, node):
        here = self.base_dir
        if self.cur_file and not self.cur_file.startswith("<"):
            here = os.path.dirname(os.path.abspath(self.cur_file))
        for folder in (here, self.base_dir, os.getcwd()):
            for candidate in (name, name + ".japy"):
                full = os.path.abspath(os.path.join(folder, candidate))
                if os.path.isfile(full):
                    return full
        raise JapyRuntimeError("Cannot find the file to import: '%s'" % name, node.line)
