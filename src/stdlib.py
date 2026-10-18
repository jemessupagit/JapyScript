"""Japy standard library: core commands that are always available.

Every command is registered with a category, a signature and a one-line
description. That data feeds help(), listapis() and docs/api.md.
"""
import copy as _copy
import json
import math
import random
import sys
import time

from .errors import JapyRuntimeError, JapyExit
from .values import JapyFunction, JapyPlugin, type_name, to_text
from .version import VERSION

MAX_RANGE = 5000000


def _fail(message):
    return JapyRuntimeError(message)


def _is_num(v):
    return isinstance(v, (int, float))


def _num(v, fname):
    if not _is_num(v):
        raise _fail("%s() needs a number but got a %s" % (fname, type_name(v)))
    return v


def _whole(v, fname):
    v = _num(v, fname)
    if isinstance(v, float):
        if not v.is_integer():
            raise _fail("%s() needs a whole number but got %s" % (fname, to_text(v)))
        v = int(v)
    return v


def _need(v, cls, fname, label):
    if not isinstance(v, cls):
        raise _fail("%s() needs %s but got a %s" % (fname, label, type_name(v)))
    return v


def install(interp):
    methods = {"str": {}, "list": {}, "dict": {}}
    interp.methods = methods
    call = interp.call_value

    def reg(name, category, signature, description):
        def deco(fn):
            interp.register(name, category, signature, description, fn)
            return fn
        return deco

    def const(name, value, description):
        interp.builtins[name] = value
        interp.docs[name] = ("Constants", name, description)

    const("PI", math.pi, "3.14159... (half a turn in radians)")
    const("TAU", 2 * math.pi, "6.28318... (a full turn in radians)")
    const("E", math.e, "2.71828... (Euler's number)")
    const("INF", float("inf"), "Positive infinity")

    # ------------------------------------------------------------- output / input
    @reg("print", "Output", "print(...values)", "Print values separated by spaces, then start a new line.")
    def _print(*args):
        interp.write(" ".join(to_text(a) for a in args))

    @reg("write", "Output", "write(...values)", "Like print() but without the final new line.")
    def _write(*args):
        interp.write(" ".join(to_text(a) for a in args), end="")

    @reg("warn", "Output", "warn(...values)", "Print values with a [warn] prefix.")
    def _warn(*args):
        interp.write("[warn] " + " ".join(to_text(a) for a in args))

    @reg("input", "Output", "input(prompt = \"\")", "Ask the player for a line of text and return it.")
    def _input(prompt=""):
        interp.write(to_text(prompt), end="")
        interp.flush()
        stream = interp.stdin if interp.stdin is not None else sys.stdin
        return stream.readline().rstrip("\r\n")

    @reg("assert", "Output", "assert(condition, message = \"Assertion failed\")",
         "Stop with an error when condition is false.")
    def _assert(condition, message="Assertion failed"):
        if not condition:
            raise _fail(to_text(message))
        return True

    @reg("exit", "Output", "exit(code = 0)", "Stop the script immediately.")
    def _exit(code=0):
        raise JapyExit(code if isinstance(code, int) else 0)

    @reg("delay", "Time", "delay(ms)", "Pause for ms milliseconds (only really sleeps with --realtime).")
    def _delay(ms):
        _num(ms, "delay")
        interp.write("[Japy System] Slept for %s milliseconds" % to_text(ms))
        if interp.realtime:
            interp.flush()
            time.sleep(ms / 1000.0)

    interp.builtins["sleep"] = _delay
    interp.docs["sleep"] = ("Time", "sleep(ms)", "Same as delay(ms).")

    @reg("time", "Time", "time()", "Seconds since 1970 (with decimals).")
    def _time():
        return time.time()

    @reg("clock", "Time", "clock()", "Milliseconds since the script started.")
    def _clock():
        return (time.time() - interp.started) * 1000.0

    @reg("date", "Time", "date()", "Current local date and time as text.")
    def _date():
        return time.strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------------------------------------------- types
    @reg("type", "Types", "type(value)", "Type name: number, string, bool, list, dict, null, function or plugin.")
    def _type(v):
        return type_name(v)

    @reg("str", "Types", "str(value)", "Convert any value to text.")
    def _str(v):
        return to_text(v)

    @reg("int", "Types", "int(value)", "Convert text or a number to a whole number (cuts decimals).")
    def _int(v):
        if isinstance(v, (bool, int)):
            return int(v)
        if isinstance(v, float):
            if v != v or v in (float("inf"), float("-inf")):
                raise _fail("int() cannot convert %s" % to_text(v))
            return int(v)
        if isinstance(v, str):
            text = v.strip()
            try:
                return int(text)
            except ValueError:
                try:
                    return int(float(text))
                except (ValueError, OverflowError):
                    raise _fail("int() cannot convert \"%s\" to a number" % v)
        raise _fail("int() cannot convert a %s" % type_name(v))

    @reg("float", "Types", "float(value)", "Convert text or a number to a decimal number.")
    def _float(v):
        if isinstance(v, (bool, int, float)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v.strip())
            except ValueError:
                raise _fail("float() cannot convert \"%s\" to a number" % v)
        raise _fail("float() cannot convert a %s" % type_name(v))

    @reg("bool", "Types", "bool(value)", "true for non-empty / non-zero values, otherwise false.")
    def _bool(v):
        return bool(v)

    @reg("len", "Types", "len(value)", "Length of text, a list or a dict.")
    def _len(v):
        if isinstance(v, (str, list, dict)):
            return len(v)
        raise _fail("len() needs text, a list or a dict but got a %s" % type_name(v))

    @reg("isnull", "Types", "isnull(value)", "true when the value is null.")
    def _isnull(v):
        return v is None

    @reg("isnumber", "Types", "isnumber(value)", "true when the value is a number.")
    def _isnumber(v):
        return _is_num(v) and not isinstance(v, bool)

    @reg("isstring", "Types", "isstring(value)", "true when the value is text.")
    def _isstring(v):
        return isinstance(v, str)

    @reg("islist", "Types", "islist(value)", "true when the value is a list.")
    def _islist(v):
        return isinstance(v, list)

    @reg("isdict", "Types", "isdict(value)", "true when the value is a dict.")
    def _isdict(v):
        return isinstance(v, dict)

    @reg("copy", "Types", "copy(value)", "Independent deep copy of a list or dict.")
    def _copy_value(v):
        return _copy.deepcopy(v)

    # -------------------------------------------------------------------- math
    @reg("abs", "Math", "abs(x)", "Absolute value.")
    def _abs(x):
        return abs(_num(x, "abs"))

    def _list_or_args(args, fname):
        if len(args) == 1 and isinstance(args[0], list):
            args = args[0]
        if not args:
            raise _fail("%s() needs at least one value" % fname)
        for a in args:
            _num(a, fname)
        return args

    @reg("min", "Math", "min(a, b, ...) or min(list)", "Smallest value.")
    def _min(*args):
        return min(_list_or_args(args, "min"))

    @reg("max", "Math", "max(a, b, ...) or max(list)", "Largest value.")
    def _max(*args):
        return max(_list_or_args(args, "max"))

    @reg("sum", "Math", "sum(list)", "Add up all numbers in a list.")
    def _sum(lst):
        _need(lst, list, "sum", "a list")
        total = 0
        for v in lst:
            total += _num(v, "sum")
        return total

    @reg("avg", "Math", "avg(list)", "Average of the numbers in a list.")
    def _avg(lst):
        _need(lst, list, "avg", "a list")
        if not lst:
            raise _fail("avg() needs a list with at least one number")
        return _sum(lst) / len(lst)

    @reg("round", "Math", "round(x, digits = 0)", "Round to the nearest value (halves go up).")
    def _round(x, digits=0):
        _num(x, "round")
        digits = _whole(digits, "round")
        if digits <= 0:
            return int(math.floor(x + 0.5))
        factor = 10 ** digits
        return math.floor(x * factor + 0.5) / factor

    @reg("floor", "Math", "floor(x)", "Round down to a whole number.")
    def _floor(x):
        return int(math.floor(_num(x, "floor")))

    @reg("ceil", "Math", "ceil(x)", "Round up to a whole number.")
    def _ceil(x):
        return int(math.ceil(_num(x, "ceil")))

    @reg("sqrt", "Math", "sqrt(x)", "Square root.")
    def _sqrt(x):
        if _num(x, "sqrt") < 0:
            raise _fail("sqrt() cannot take a negative number")
        return math.sqrt(x)

    @reg("pow", "Math", "pow(base, exponent)", "base raised to exponent (same as base ** exponent).")
    def _pow(a, b):
        _num(a, "pow")
        _num(b, "pow")
        if isinstance(b, int) and b > 10000 and abs(a) > 1:
            raise _fail("pow() exponent is too large")
        try:
            return a ** b
        except ZeroDivisionError:
            raise _fail("pow() cannot raise 0 to a negative power")

    def _trig(name, fn, doc):
        def impl(x):
            return fn(_num(x, name))
        interp.register(name, "Math", "%s(x)" % name, doc, impl)

    _trig("sin", math.sin, "Sine (x in radians).")
    _trig("cos", math.cos, "Cosine (x in radians).")
    _trig("tan", math.tan, "Tangent (x in radians).")
    _trig("atan", math.atan, "Arc tangent, result in radians.")
    _trig("exp", math.exp, "e raised to x.")
    _trig("radians", math.radians, "Convert degrees to radians.")
    _trig("degrees", math.degrees, "Convert radians to degrees.")

    @reg("asin", "Math", "asin(x)", "Arc sine, x between -1 and 1.")
    def _asin(x):
        if not -1 <= _num(x, "asin") <= 1:
            raise _fail("asin() needs a number between -1 and 1")
        return math.asin(x)

    @reg("acos", "Math", "acos(x)", "Arc cosine, x between -1 and 1.")
    def _acos(x):
        if not -1 <= _num(x, "acos") <= 1:
            raise _fail("acos() needs a number between -1 and 1")
        return math.acos(x)

    @reg("atan2", "Math", "atan2(y, x)", "Angle of the point (x, y) in radians.")
    def _atan2(y, x):
        return math.atan2(_num(y, "atan2"), _num(x, "atan2"))

    @reg("log", "Math", "log(x, base = e)", "Logarithm (natural by default).")
    def _logm(x, base=None):
        if _num(x, "log") <= 0:
            raise _fail("log() needs a number greater than 0")
        if base is None:
            return math.log(x)
        if _num(base, "log") <= 0 or base == 1:
            raise _fail("log() base must be greater than 0 and not 1")
        return math.log(x, base)

    @reg("log10", "Math", "log10(x)", "Base-10 logarithm.")
    def _log10(x):
        if _num(x, "log10") <= 0:
            raise _fail("log10() needs a number greater than 0")
        return math.log10(x)

    @reg("sign", "Math", "sign(x)", "-1, 0 or 1 depending on the sign of x.")
    def _sign(x):
        _num(x, "sign")
        return (x > 0) - (x < 0)

    @reg("clamp", "Math", "clamp(x, low, high)", "Limit x to the range low..high.")
    def _clamp(x, low, high):
        _num(x, "clamp")
        _num(low, "clamp")
        _num(high, "clamp")
        if low > high:
            raise _fail("clamp() needs low <= high")
        return max(low, min(high, x))

    @reg("lerp", "Math", "lerp(a, b, t)", "Blend from a to b; t=0 gives a, t=1 gives b.")
    def _lerp(a, b, t):
        return _num(a, "lerp") + (_num(b, "lerp") - a) * _num(t, "lerp")

    @reg("dist", "Math", "dist(x1, y1, x2, y2)", "Distance between two 2D points.")
    def _dist(x1, y1, x2, y2):
        return math.hypot(_num(x2, "dist") - _num(x1, "dist"), _num(y2, "dist") - _num(y1, "dist"))

    @reg("random", "Math", "random()", "Random decimal from 0 up to (not including) 1.")
    def _random():
        return random.random()

    @reg("randint", "Math", "randint(low, high)", "Random whole number from low to high (both included).")
    def _randint(low, high):
        low, high = _whole(low, "randint"), _whole(high, "randint")
        if low > high:
            raise _fail("randint() needs low <= high")
        return random.randint(low, high)

    @reg("randchoice", "Math", "randchoice(list)", "Pick a random item from a list.")
    def _randchoice(lst):
        _need(lst, list, "randchoice", "a list")
        if not lst:
            raise _fail("randchoice() needs a list with at least one item")
        return random.choice(lst)

    @reg("shuffle", "Math", "shuffle(list)", "Shuffle a list in place and return it.")
    def _shuffle(lst):
        _need(lst, list, "shuffle", "a list")
        random.shuffle(lst)
        return lst

    @reg("seed", "Math", "seed(n)", "Make random numbers repeatable.")
    def _seed(n):
        random.seed(n)

    # ------------------------------------------------------------------- text
    @reg("upper", "Text", "upper(text)", "UPPERCASE copy of the text.")
    def _upper(s):
        return _need(s, str, "upper", "text").upper()

    @reg("lower", "Text", "lower(text)", "lowercase copy of the text.")
    def _lower(s):
        return _need(s, str, "lower", "text").lower()

    @reg("trim", "Text", "trim(text)", "Remove spaces from both ends.")
    def _trim(s):
        return _need(s, str, "trim", "text").strip()

    @reg("split", "Text", "split(text, separator = null)", "Split text into a list (by spaces when no separator).")
    def _split(s, sep=None):
        _need(s, str, "split", "text")
        if sep is None:
            return s.split()
        _need(sep, str, "split", "text as the separator")
        return list(s) if sep == "" else s.split(sep)

    @reg("join", "Text", "join(list, separator = \"\")", "Glue list items into one text.")
    def _join(lst, sep=""):
        _need(lst, list, "join", "a list")
        return to_text(sep).join(to_text(v) for v in lst)

    @reg("replace", "Text", "replace(text, old, new)", "Replace every old with new.")
    def _replace(s, old, new):
        _need(s, str, "replace", "text")
        return s.replace(to_text(old), to_text(new))

    @reg("startswith", "Text", "startswith(text, prefix)", "true when text begins with prefix.")
    def _startswith(s, prefix):
        return _need(s, str, "startswith", "text").startswith(to_text(prefix))

    @reg("endswith", "Text", "endswith(text, suffix)", "true when text ends with suffix.")
    def _endswith(s, suffix):
        return _need(s, str, "endswith", "text").endswith(to_text(suffix))

    @reg("substr", "Text", "substr(text, start, length = null)", "Part of a text starting at start.")
    def _substr(s, start, length=None):
        _need(s, str, "substr", "text")
        start = _whole(start, "substr")
        if length is None:
            return s[start:]
        length = _whole(length, "substr")
        if start < 0:
            start = max(len(s) + start, 0)
        return s[start:start + max(length, 0)]

    @reg("repeat", "Text", "repeat(text, times)", "Repeat the text several times.")
    def _repeat(s, times):
        _need(s, str, "repeat", "text")
        times = _whole(times, "repeat")
        if times < 0 or len(s) * times > 10000000:
            raise _fail("repeat() count is out of range")
        return s * times

    @reg("chr", "Text", "chr(code)", "Character for a character code.")
    def _chr(code):
        return chr(_whole(code, "chr"))

    @reg("ord", "Text", "ord(char)", "Character code of a single character.")
    def _ord(ch):
        if not isinstance(ch, str) or len(ch) != 1:
            raise _fail("ord() needs a single character")
        return ord(ch)

    @reg("format", "Text", "format(template, ...values)", "Fill each {} in template with a value.")
    def _format(template, *values):
        _need(template, str, "format", "text")
        parts = template.split("{}")
        if len(parts) - 1 != len(values):
            raise _fail("format() has %d {} placeholder(s) but %d value(s)" % (len(parts) - 1, len(values)))
        out = [parts[0]]
        for value, part in zip(values, parts[1:]):
            out.append(to_text(value))
            out.append(part)
        return "".join(out)

    # ------------------------------------------------ lists (and some text)
    @reg("push", "Lists", "push(list, ...values)", "Add values to the end of a list; returns the list.")
    def _push(lst, *values):
        _need(lst, list, "push", "a list").extend(values)
        return lst

    @reg("pop", "Lists", "pop(list, index = -1)", "Remove and return an item (the last one by default).")
    def _pop(lst, index=-1):
        _need(lst, list, "pop", "a list")
        index = _whole(index, "pop")
        if not lst or index < -len(lst) or index >= len(lst):
            raise _fail("pop() index %d is out of range (length is %d)" % (index, len(lst)))
        return lst.pop(index)

    @reg("insert", "Lists", "insert(list, index, value)", "Insert a value before index; returns the list.")
    def _insert(lst, index, value):
        _need(lst, list, "insert", "a list").insert(_whole(index, "insert"), value)
        return lst

    @reg("remove", "Lists", "remove(list, value)", "Remove the first matching value; returns true if found.")
    def _remove(lst, value):
        _need(lst, list, "remove", "a list")
        if value in lst:
            lst.remove(value)
            return True
        return False

    def _sort_in_place(lst, keyfn, fname):
        try:
            if keyfn is None:
                lst.sort()
            else:
                lst.sort(key=lambda v: call(keyfn, [v]))
        except TypeError:
            raise _fail("%s() cannot compare values of different types" % fname)

    @reg("sort", "Lists", "sort(list, keyfn = null)", "Sort a list in place (keyfn picks the sort key); returns the list.")
    def _sort(lst, keyfn=None):
        _need(lst, list, "sort", "a list")
        _sort_in_place(lst, keyfn, "sort")
        return lst

    @reg("sorted", "Lists", "sorted(list, keyfn = null)", "Sorted copy of a list.")
    def _sorted(lst, keyfn=None):
        _need(lst, list, "sorted", "a list")
        out = list(lst)
        _sort_in_place(out, keyfn, "sorted")
        return out

    @reg("reverse", "Lists", "reverse(list)", "Reverse a list in place (returns reversed text for text).")
    def _reverse(x):
        if isinstance(x, str):
            return x[::-1]
        _need(x, list, "reverse", "a list or text").reverse()
        return x

    @reg("reversed", "Lists", "reversed(list)", "Reversed copy of a list.")
    def _reversed(lst):
        return list(reversed(_need(lst, list, "reversed", "a list")))

    @reg("slice", "Lists", "slice(list_or_text, start, end = null)", "Part of a list or text from start up to end.")
    def _slice(x, start, end=None):
        _need(x, (list, str), "slice", "a list or text")
        start = _whole(start, "slice")
        return x[start:] if end is None else x[start:_whole(end, "slice")]

    @reg("contains", "Lists", "contains(list_text_or_dict, item)", "true when the item is inside.")
    def _contains(x, item):
        if isinstance(x, str):
            return to_text(item) in x
        if isinstance(x, (list, dict)):
            try:
                return item in x
            except TypeError:
                return False
        raise _fail("contains() needs a list, text or dict but got a %s" % type_name(x))

    @reg("indexof", "Lists", "indexof(list_or_text, item)", "Position of the item, or -1 when it is missing.")
    def _indexof(x, item):
        if isinstance(x, str):
            return x.find(to_text(item))
        _need(x, list, "indexof", "a list or text")
        return x.index(item) if item in x else -1

    @reg("clear", "Lists", "clear(list_or_dict)", "Remove everything; returns the emptied container.")
    def _clear(x):
        _need(x, (list, dict), "clear", "a list or dict").clear()
        return x

    @reg("range", "Lists", "range(stop) / range(start, stop, step = 1)", "List of whole numbers.")
    def _range(a, b=None, step=1):
        start, stop = (0, _whole(a, "range")) if b is None else (_whole(a, "range"), _whole(b, "range"))
        step = _whole(step, "range")
        if step == 0:
            raise _fail("range() step cannot be 0")
        if len(range(start, stop, step)) > MAX_RANGE:
            raise _fail("range() is too large (more than %d items)" % MAX_RANGE)
        return list(range(start, stop, step))

    @reg("enumerate", "Lists", "enumerate(list)", "List of [index, item] pairs; use with  for i, v in ...")
    def _enumerate(lst):
        return [[i, v] for i, v in enumerate(_need(lst, list, "enumerate", "a list"))]

    @reg("zip", "Lists", "zip(a, b, ...)", "Pair up items from several lists.")
    def _zip(*lists):
        for lst in lists:
            _need(lst, list, "zip", "lists")
        return [list(t) for t in zip(*lists)]

    @reg("map", "Lists", "map(list, fn)", "New list with fn applied to every item.")
    def _map(lst, fn):
        return [call(fn, [v]) for v in _need(lst, list, "map", "a list")]

    @reg("filter", "Lists", "filter(list, fn)", "New list with the items where fn returns true.")
    def _filter(lst, fn):
        return [v for v in _need(lst, list, "filter", "a list") if call(fn, [v])]

    @reg("reduce", "Lists", "reduce(list, fn, start = first item)", "Fold a list into one value with fn(total, item).")
    def _reduce(lst, fn, *start):
        _need(lst, list, "reduce", "a list")
        items = list(lst)
        if start:
            total = start[0]
        elif items:
            total = items.pop(0)
        else:
            raise _fail("reduce() of an empty list needs a start value")
        for v in items:
            total = call(fn, [total, v])
        return total

    @reg("each", "Lists", "each(list, fn)", "Call fn for every item.")
    def _each(lst, fn):
        for v in list(_need(lst, list, "each", "a list")):
            call(fn, [v])

    @reg("find", "Lists", "find(list, fn)", "First item where fn returns true (null if none).")
    def _find(lst, fn):
        for v in _need(lst, list, "find", "a list"):
            if call(fn, [v]):
                return v
        return None

    @reg("any", "Lists", "any(list)", "true when at least one item is true.")
    def _any(lst):
        return any(_need(lst, list, "any", "a list"))

    @reg("all", "Lists", "all(list)", "true when every item is true.")
    def _all(lst):
        return all(_need(lst, list, "all", "a list"))

    # ------------------------------------------------------------------ dicts
    @reg("keys", "Dicts", "keys(dict)", "List of the keys.")
    def _keys(d):
        return list(_need(d, dict, "keys", "a dict"))

    @reg("values", "Dicts", "values(dict)", "List of the values.")
    def _values(d):
        return list(_need(d, dict, "values", "a dict").values())

    @reg("items", "Dicts", "items(dict)", "List of [key, value] pairs.")
    def _items(d):
        return [[k, v] for k, v in _need(d, dict, "items", "a dict").items()]

    @reg("has", "Dicts", "has(dict, key)", "true when the key exists.")
    def _has(d, key):
        _need(d, dict, "has", "a dict")
        try:
            return key in d
        except TypeError:
            return False

    @reg("get", "Dicts", "get(dict, key, default = null)", "Value for key, or default when missing.")
    def _get(d, key, default=None):
        _need(d, dict, "get", "a dict")
        try:
            return d.get(key, default)
        except TypeError:
            return default

    @reg("delete", "Dicts", "delete(dict, key)", "Remove a key; returns its old value (null if missing).")
    def _delete(d, key):
        _need(d, dict, "delete", "a dict")
        try:
            return d.pop(key, None)
        except TypeError:
            return None

    # ------------------------------------------------------------------- json
    @reg("jsonencode", "JSON", "jsonencode(value, pretty = false)", "Convert a value to JSON text.")
    def _jsonencode(value, pretty=False):
        def default(obj):
            raise TypeError("a %s cannot be turned into JSON" % type_name(obj))
        return json.dumps(value, default=default, indent=2 if pretty else None, ensure_ascii=False)

    @reg("jsondecode", "JSON", "jsondecode(text)", "Parse JSON text into lists, dicts and numbers.")
    def _jsondecode(text):
        _need(text, str, "jsondecode", "text")
        try:
            return json.loads(text)
        except ValueError as exc:
            raise _fail("jsondecode(): %s" % exc)

    # ---------------------------------------------------------------- engine
    @reg("engineloadplugin", "Engine", "engineloadplugin(name)",
         "Attach a plugin (simulated) and return a handle whose methods can be called.")
    def _loadplugin(name):
        interp.write("[Japy Engine] Plugin successfully attached: %s" % to_text(name))
        interp.plugins.append(to_text(name))
        return JapyPlugin(to_text(name))

    @reg("engineplugins", "Engine", "engineplugins()", "List of plugin names attached so far.")
    def _plugins():
        return list(interp.plugins)

    @reg("japyversion", "Engine", "japyversion()", "Version text of the Japy engine.")
    def _japyversion():
        return VERSION

    @reg("apicount", "Engine", "apicount()", "How many commands are available right now.")
    def _apicount():
        return len(interp.builtins)

    @reg("listapis", "Engine", "listapis(prefix = \"\")", "Sorted list of command names starting with prefix.")
    def _listapis(prefix=""):
        return sorted(n for n in interp.builtins if n.startswith(to_text(prefix)))

    @reg("help", "Engine", "help(name)", "Show the signature and description of a command.")
    def _help(name):
        key = to_text(name)
        if key not in interp.docs:
            raise _fail("No command named '%s'. Try listapis() to see them." % key)
        category, signature, description = interp.docs[key]
        interp.write("%s  [%s]\n    %s" % (signature, category, description))

    # --------------------------------------------- methods:  "text".upper() etc.
    b = interp.builtins
    methods["str"].update(dict((n, b[n]) for n in (
        "upper", "lower", "trim", "split", "replace", "startswith", "endswith", "substr",
        "repeat", "format", "slice", "reverse", "contains", "indexof")))
    methods["list"].update(dict((n, b[n]) for n in (
        "push", "pop", "insert", "remove", "sort", "sorted", "reverse", "reversed", "join",
        "slice", "contains", "indexof", "clear", "copy", "map", "filter", "reduce", "each",
        "find", "any", "all", "sum", "avg")))
    methods["dict"].update(dict((n, b[n]) for n in (
        "keys", "values", "items", "has", "get", "clear", "copy")))
    methods["dict"]["remove"] = b["delete"]
