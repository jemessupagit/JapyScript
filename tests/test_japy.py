"""JapyScript test suite. Run with:  python -m unittest discover -s tests -v"""
import ast
import glob
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from japy import (JapyInterpreter, JapyLexer, JapyParser, JapyError, JapySyntaxError,  # noqa: E402
                  JapyRuntimeError, JapyExit)


def run(source, **kwargs):
    """Run Japy source and return everything it printed."""
    out = io.StringIO()
    interp = JapyInterpreter(stdout=out, **kwargs)
    interp.run_script(source)
    return out.getvalue()


def lines(source, **kwargs):
    return run(source, **kwargs).splitlines()


class LexerTests(unittest.TestCase):
    def test_comments_and_numbers(self):
        toks = JapyLexer().tokenize("var a = 0x10 # c\n// c2\n/* multi\nline */ 2.5")
        values = [t.value for t in toks if t.type in ("NUMBER",)]
        self.assertEqual(values, [16, 2.5])

    def test_line_numbers_after_block_comment(self):
        toks = JapyLexer().tokenize("/* a\nb */\nvar x = 1")
        self.assertEqual(toks[1].line, 3)  # NEWLINE token then VAR? first token is NEWLINE (line 2)

    def test_string_escapes(self):
        self.assertEqual(run('print("a\\tb\\n"+\'q\\\'\')'), "a\tb\nq'\n")

    def test_bad_input(self):
        for bad in ('"open', "/* open", "var a = @"):
            with self.assertRaises(JapySyntaxError):
                JapyLexer().tokenize(bad)


class LanguageTests(unittest.TestCase):
    def test_arithmetic_and_precedence(self):
        self.assertEqual(lines("print(2 + 3 * 4)\nprint((2 + 3) * 4)\nprint(2 ** 3 ** 2)\nprint(-2 ** 2)"),
                         ["14", "20", "512", "-4"])

    def test_division_rules(self):
        self.assertEqual(lines("print(10 / 2)\nprint(10 / 4)\nprint(7 % 3)"), ["5", "2.5", "1"])

    def test_strings_concat_and_compare(self):
        self.assertEqual(lines('print("n=" + 5 + true + null)\nprint("a" < "b")'), ["n=5truenull", "true"])

    def test_logic_and_word_operators(self):
        self.assertEqual(lines("print(true and not false)\nprint(false or 0 == 0)\nprint(!(1 == 2))"),
                         ["true", "true", "true"])

    def test_if_elif_else(self):
        src = "def f(n) {\n if n < 0 { return \"neg\" } elif n == 0 { return \"zero\" } else if n < 10 { return \"small\" } else { return \"big\" }\n}\nprint(f(-1), f(0), f(5), f(50))"
        self.assertEqual(run(src), "neg zero small big\n")

    def test_while_break_continue(self):
        src = "var i = 0\nvar t = 0\nwhile true {\n i += 1\n if i == 3 { continue }\n if i > 5 { break }\n t += i\n}\nprint(t)"
        self.assertEqual(run(src), "12\n")

    def test_for_loops(self):
        self.assertEqual(run("for i in range(3) { write(i) }"), "012")
        self.assertEqual(run("for (i in range(1, 4)) { write(i) }"), "123")
        self.assertEqual(run('for ch in "ab" { write(ch) }'), "ab")
        self.assertEqual(run("for k, v in {a: 1, b: 2} { write(k + v) }"), "a1b2")
        self.assertEqual(run("for i, v in enumerate([\"x\", \"y\"]) { write(i + v) }"), "0x1y")

    def test_functions_defaults_recursion_closures(self):
        src = ("def fib(n) { if n < 2 { return n } return fib(n - 1) + fib(n - 2) }\n"
               "def mk() { var c = 0\n return fn() { c += 1\n return c } }\n"
               "def hi(n, g = \"hi\") { return g + n }\n"
               "var k = mk()\nk()\nprint(fib(15), k(), hi(\"!\"), hi(\"!\", \"yo\"))")
        self.assertEqual(run(src), "610 2 hi! yo!\n")

    def test_function_hoisting(self):
        self.assertEqual(run("print(later())\ndef later() { return 7 }"), "7\n")

    def test_scoping_and_const(self):
        src = "var x = 1\nif true { var x = 2\n x += 1 }\nprint(x)"
        self.assertEqual(run(src), "1\n")
        with self.assertRaises(JapyRuntimeError):
            run("const A = 1\nA = 2")

    def test_assign_to_unknown_creates_global(self):
        self.assertEqual(run("def f() { made = 5 }\nf()\nprint(made)"), "5\n")

    def test_lists_dicts(self):
        src = ("var a = [1, 2, 3]\na[1] = 20\na[-1] += 1\nvar d = {x: 1, \"y z\": 2}\nd.x += 5\nd[\"w\"] = 9\n"
               "print(a, d, d.missing, len(a), a.length, 20 in a, \"w\" in d)")
        self.assertEqual(run(src), '[1, 20, 4] {"x": 6, "y z": 2, "w": 9} null 3 3 true true\n')

    def test_methods(self):
        src = ('var l = [3, 1, 2]\nl.push(0).sort()\nprint(l, "a-b".split("-"), "Hi".upper(), l.join("+"))\n'
               'var d = {a: 1}\nprint(d.keys(), d.has("a"), d.get("zz", 5))')
        self.assertEqual(run(src), '[0, 1, 2, 3] ["a", "b"] HI 0+1+2+3\n["a"] true 5\n')

    def test_multiline_expressions(self):
        src = "var total = 1 +\n  2 +\n  3\nprint(max(\n  total,\n  10\n))\nvar l = [\n 1,\n 2,\n]\nprint(l)"
        self.assertEqual(run(src), "10\n[1, 2]\n")

    def test_newline_ends_statement(self):
        # '-3' on its own line must NOT be glued to the previous line
        self.assertEqual(run("var a = 5\n-3\nprint(a)"), "5\n")

    def test_semicolons_optional(self):
        self.assertEqual(run("var a = 1; var b = 2; print(a + b);"), "3\n")

    def test_try_catch_finally_throw(self):
        src = ('try { throw "boom" } catch (e) { print("c:" + e) } finally { print("f") }\n'
               'try { print([1][5]) } catch e { print("engine") }\n'
               'def g() { try { return 1 } finally { print("cleanup") } }\nprint(g())')
        self.assertEqual(lines(src), ["c:boom", "f", "engine", "cleanup", "1"])

    def test_throw_non_string(self):
        self.assertEqual(run("try { throw [1, 2] } catch (e) { print(e[1]) }"), "2\n")

    def test_uncaught_throw(self):
        with self.assertRaises(JapyError) as ctx:
            run("throw \"bad\"")
        self.assertIn("bad", ctx.exception.message)

    def test_plugins_still_work(self):
        out = lines('var p = engineloadplugin("Anim")\np.setboneweight("Arm", 0.75)')
        self.assertEqual(out, ["[Japy Engine] Plugin successfully attached: Anim",
                               '[Japy Plugin Trigger] Object: Anim -> Executed Method: setboneweight with parameters: ["Arm", 0.75]'])

    def test_setup_and_loop(self):
        src = "var n = 0\ndef setup() { print(\"setup\") }\ndef loop() { n += 1\n print(\"frame \" + japyTime_frame()) }"
        self.assertEqual(lines(src, frames=3), ["setup", "frame 1", "frame 2", "frame 3"])
        self.assertEqual(lines(src), ["setup", "frame 1"])


class ErrorTests(unittest.TestCase):
    def err(self, source, kind=JapyError):
        with self.assertRaises(kind) as ctx:
            run(source)
        return ctx.exception

    def test_line_numbers(self):
        e = self.err("print(1)\nprint(2)\nvar x = nope + 1")
        self.assertEqual(e.line, 3)
        self.assertIn("Undefined", e.message)

    def test_line_number_inside_function(self):
        e = self.err("def f() {\n  var a = [1]\n  return a[3]\n}\nf()")
        self.assertEqual(e.line, 3)

    def test_did_you_mean(self):
        e = self.err("japy3D_createCub(1, 2, 3)")
        self.assertIn("japy3D_createCube", e.message)

    def test_syntax_errors(self):
        for bad in ("if true { print(1)", "var = 3", "print(1", "x = ", "else { }", "def f( { }",
                    "try { }", "for x range(3) { }", "5 = 3"):
            self.err(bad, JapySyntaxError)

    def test_syntax_error_position(self):
        e = self.err("var a = 1\nvar b = )", JapySyntaxError)
        self.assertEqual(e.line, 2)

    def test_runtime_type_errors(self):
        for bad in ('print(1 + [])', 'print("a" - 1)', "print(null < 1)", "print(-\"x\")",
                    "var a = 5\na.foo = 1", "5()", "print([1, 2].nope())", "print(1 / 0)", "print(5 % 0)"):
            self.err(bad, JapyRuntimeError)

    def test_bad_calls(self):
        self.err("def f(a) { }\nf()", JapyRuntimeError)
        self.err("def f(a) { }\nf(1, 2)", JapyRuntimeError)
        self.err("japy3D_createCube(1)", JapyRuntimeError)
        self.err("len(5)", JapyRuntimeError)

    def test_control_flow_misuse(self):
        self.err("break", JapyRuntimeError)
        self.err("continue", JapyRuntimeError)
        self.err("return 1", JapyRuntimeError)

    def test_infinite_loop_guard(self):
        self.err("while true { }", JapyRuntimeError)

    def test_recursion_guard(self):
        e = self.err("def f() { return f() }\nf()", JapyRuntimeError)
        self.assertIn("nested calls", e.message)

    def test_exit(self):
        with self.assertRaises(JapyExit) as ctx:
            run("exit(3)")
        self.assertEqual(ctx.exception.code, 3)


class ImportTests(unittest.TestCase):
    def test_import_relative_once(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "lib.japy"), "w") as f:
                f.write('print("loading")\ndef twice(n) { return n * 2 }\n')
            main = os.path.join(d, "main.japy")
            with open(main, "w") as f:
                f.write('import "lib"\nimport "lib.japy"\nprint(twice(4))\n')
            out = io.StringIO()
            interp = JapyInterpreter(stdout=out)
            with open(main) as f:
                interp.run_script(f.read(), main)
            self.assertEqual(out.getvalue(), "loading\n8\n")

    def test_missing_import(self):
        with self.assertRaises(JapyRuntimeError):
            run('import "does_not_exist"')

    def test_error_names_imported_file(self):
        with tempfile.TemporaryDirectory() as d:
            lib = os.path.join(d, "bad.japy")
            with open(lib, "w") as f:
                f.write("var ok = 1\nvar boom = [1][9]\n")
            main = os.path.join(d, "main.japy")
            interp = JapyInterpreter(stdout=io.StringIO())
            with self.assertRaises(JapyRuntimeError) as ctx:
                interp.run_script('import "bad.japy"', main)
            self.assertEqual(ctx.exception.filename, os.path.abspath(lib))
            self.assertEqual(ctx.exception.line, 2)


class LibraryTests(unittest.TestCase):
    def test_math(self):
        src = ("print(round(2.5), round(-2.5), round(3.14159, 2), floor(-1.5), ceil(1.2), sqrt(81), pow(2, 8))\n"
               "print(abs(-3), min(4, 2, 8), max([4, 2, 8]), sum([1, 2, 3]), avg([2, 4]), clamp(5, 0, 3), sign(-9))\n"
               "print(lerp(10, 20, 0.5), dist(0, 0, 3, 4), round(PI, 3), atan2(0, 1))")
        self.assertEqual(lines(src), ["3 -2 3.14 -2 2 9 256", "3 2 8 6 3 3 -1", "15 5 3.142 0"])

    def test_random_is_seedable(self):
        src = "seed(7)\nvar a = [random(), randint(1, 100)]\nseed(7)\nvar b = [random(), randint(1, 100)]\nprint(a == b)"
        self.assertEqual(run(src), "true\n")

    def test_conversions(self):
        self.assertEqual(lines('print(int("42"), int(3.9), float("2.5"), str(5) + "!", bool(0), type([]), type(null), type(1), type(print))'),
                         ["42 3 2.5 5! false list null number function"])

    def test_text(self):
        src = ('print(trim("  x "), upper("a"), lower("B"), split("a b  c"), join([1, 2], "-"), replace("aXa", "X", "-"))\n'
               'print(startswith("hello", "he"), endswith("hello", "lo"), substr("hello", 1, 3), substr("hello", 2), repeat("ab", 2))\n'
               'print(format("{}+{}", 1, "z"), chr(65), ord("A"), indexof("hello", "l"), contains("hello", "ell"), reverse("abc"))')
        self.assertEqual(lines(src), ["x A b [\"a\", \"b\", \"c\"] 1-2 a-a", "true true ell llo abab", "1+z A 65 2 true cba"])

    def test_lists(self):
        src = ("var l = [5, 3, 9]\nprint(sorted(l), sorted(l, fn(v) { return -v }), reversed(l), slice(l, 1), pop(l), l)\n"
               "print(range(3), range(2, 8, 3), enumerate([\"a\"]), zip([1, 2], [3, 4]), indexof(l, 3), contains(l, 9))\n"
               "print(map([1, 2], fn(v) { return v + 1 }), filter([1, 2, 3], fn(v) { return v > 1 }), "
               "reduce([1, 2, 3], fn(a, b) { return a + b }), find([1, 5], fn(v) { return v > 2 }), any([0, 1]), all([1, 0]))")
        self.assertEqual(lines(src), ["[3, 5, 9] [9, 5, 3] [9, 3, 5] [3, 9] 9 [5, 3]",
                                      "[0, 1, 2] [2, 5] [[0, \"a\"]] [[1, 3], [2, 4]] 1 false",
                                      "[2, 3] [2, 3] 6 5 true false"])

    def test_dicts_and_json(self):
        src = ('var d = {a: 1, b: [1, 2]}\nprint(keys(d), values(d), items(d), has(d, "a"), delete(d, "a"), d)\n'
               'var j = jsonencode({n: 1, s: "x", l: [true, null]})\nprint(j)\nprint(jsondecode(j).l)')
        self.assertEqual(lines(src), ['["a", "b"] [1, [1, 2]] [["a", 1], ["b", [1, 2]]] true 1 {"b": [1, 2]}',
                                      '{"n": 1, "s": "x", "l": [true, null]}', "[true, null]"])

    def test_copy_is_independent(self):
        self.assertEqual(run("var a = [[1]]\nvar b = copy(a)\nb[0].push(2)\nprint(a, b)"), "[[1]] [[1, 2]]\n")

    def test_game_apis(self):
        src = ('japy3D_createSphere(1, 2, 3)\njapyAudio_play("hit.wav")\nprint(japyInput_isKeyDown("A"), japyUI_getTouchCoordinates())\n'
               'japySave_set("lvl", 4)\nprint(japySave_get("lvl"), japySave_get("none", 0), japySave_has("lvl"))')
        self.assertEqual(lines(src), ["[Japy 3D] Sphere (radius 1) spawned at (1,2,3)",
                                      "[Japy Audio] Playing hit.wav at volume 1",
                                      "[Japy Mobile UI] Intercepting screen touch points vector coordinates",
                                      "false [0, 0]", "4 0 true"])

    def test_every_command_is_documented(self):
        interp = JapyInterpreter(stdout=io.StringIO())
        self.assertGreaterEqual(len(interp.builtins), 150)
        for name in interp.builtins:
            self.assertIn(name, interp.docs, name)

    def test_help_and_listapis(self):
        self.assertIn("clamp(x, low, high)", run('help("clamp")'))
        self.assertEqual(run('print(len(listapis("japyAudio_")))'), "4\n")


class ExampleTests(unittest.TestCase):
    def test_all_examples_run(self):
        paths = sorted(glob.glob(os.path.join(ROOT, "examples", "0*.japy")))
        self.assertGreaterEqual(len(paths), 8)
        for path in paths:
            out = io.StringIO()
            interp = JapyInterpreter(stdout=out, frames=2)
            with open(path, encoding="utf-8") as f:
                interp.run_script(f.read(), path)
            self.assertTrue(out.getvalue().strip(), path)


class CompatibilityTests(unittest.TestCase):
    """Guards for running on older Pythons (3.8+)."""

    def test_python_files_parse_as_python_38(self):
        files = glob.glob(os.path.join(ROOT, "src", "japy", "*.py")) + [os.path.join(ROOT, "main.py")]
        for path in files:
            with open(path, encoding="utf-8") as f:
                try:
                    ast.parse(f.read(), filename=path, feature_version=(3, 8))
                except TypeError:   # feature_version unsupported on this interpreter
                    self.skipTest("ast feature_version not available")

    def test_no_module_name_clashes_with_stdlib(self):
        # 'parser' was a stdlib module until Python 3.9: it must not be importable as a top-level name from src/
        top_level = {os.path.splitext(n)[0] for n in os.listdir(os.path.join(ROOT, "src"))}
        self.assertEqual(top_level - {"__pycache__"}, {"japy"})


if __name__ == "__main__":
    unittest.main()
