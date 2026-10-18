# Changelog

## v1.5.0 Beta
A big update: the language is much bigger, runs on more Python versions, and reports errors clearly.

### Runs on more Python versions
- Works on Python 3.8 and newer (checked against 3.8 syntax; main.py shows a clear message on older Pythons).
- **Fixed:** the old `src/parser.py` had the same name as Python's built-in `parser` module (present up to
  Python 3.9), which could break `python main.py` there. All engine code now lives in the `src/japy/` package.
- `main.py` reads files with UTF-8 (including a BOM from phone editors) and prints Thai/emoji safely.

### New language features
- `return`, `break`, `continue`; functions with parameters, default values, recursion and closures; `fn(x) { ... }` values
- `for` loops: `for i in range(5)`, `for item in list`, `for k, v in dict`, `for i, v in enumerate(list)`
- `elif` (and `else if`), `const`, `let` (same as `var`), `try / catch / finally`, `throw`, `import "file.japy"`
- Lists `[1, 2]`, dicts `{ name: "Hero" }`, indexing `a[0]`, properties `d.hp`, methods `list.push(3)`, `"text".upper()`
- Operators `**`, `+= -= *= /= %=`, `in`, and the words `and`, `or`, `not`
- Comments with `#`, `//` and `/* ... */`; optional `;`; hex numbers `0xFF`; string escapes `\n \t \"`
- Line breaks inside `( )` and `[ ]` are ignored, so long calls can be split freely
- Functions can be used before the line that defines them
- `loop()` is now called after `setup()` (once by default, `--frames N` for more)

### New commands (169 in total, see docs/api.md)
- Math, text, list, dict, JSON and type helpers (`clamp`, `lerp`, `format`, `map`, `filter`, `jsonencode` ...)
- More simulated game APIs: audio, input, scenes, networking, save data, extra 3D / 2D / physics / UI calls
- `help("name")`, `listapis("prefix")`, `apicount()`, `japyversion()`

### Better tools
- Errors show file, line, the code line and a hint (`Did you mean 'japy3D_createCube'?`)
- `python main.py` with no file opens an interactive prompt (REPL); `-c "code"`, `--check`, `--list-apis`, `--version`
- Safety limits: `--max-loops N` for while loops, call-depth limit for runaway recursion
- Test suite: `python -m unittest discover -s tests` (52 tests)

### Behaviour changes from v1.0.x (please read)
- Using a name that was never defined is now an error (before, it silently became the text of its own name).
- Variables created with `var` inside `{ }` blocks (if / while / for / functions) only exist inside that block.
  Assigning to a never-declared name still creates a global, as before.
- `print` accepts several values: `print("hp", 10)`.
- `delay(ms)` still prints its message and does not wait, unless you run with `--realtime`.
- `japyPhysics_checkCollision` now returns `false` and `japyUI_getTouchCoordinates` returns `[0, 0]` (they returned nothing).
- Calling a method on a plugin handle prints the plugin's name instead of the variable's name.

## v1.0.x Beta
First release: lexer, parser, interpreter, simulated 3D / 2D / physics / mobile UI commands.
