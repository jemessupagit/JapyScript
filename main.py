"""JapyScript command line runner.

Usage:
    python main.py script.japy            run a script
    python main.py                        interactive prompt (REPL)
    python main.py -c 'print(1 + 2)'      run one line of code
    python main.py --check script.japy    check syntax only
    python main.py --list-apis [prefix]   list built-in commands
"""
import sys

if sys.version_info < (3, 8):
    sys.stderr.write("JapyScript needs Python 3.8 or newer (this is Python %s).\n"
                     % sys.version.split()[0])
    sys.exit(1)

import argparse
import os

# src/ goes FIRST so our package is always found (and never a same-named stdlib module).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from japy import (VERSION_LABEL, JapyInterpreter, JapyLexer, JapyParser, JapyError,
                  JapyExit, JapySyntaxError, format_error)


def _utf8_output():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _report(err, interp):
    sys.stdout.flush()
    sys.stderr.write(format_error(err, interp.sources) + "\n")
    sys.stderr.flush()


def _read_file(path):
    with open(path, "r", encoding="utf-8-sig") as handle:
        return handle.read()


def list_apis(prefix):
    interp = JapyInterpreter()
    groups = {}
    for name in sorted(interp.builtins):
        if name.startswith(prefix):
            category, signature, _ = interp.docs[name]
            groups.setdefault(category, []).append(signature)
    for category in sorted(groups):
        print("== %s (%d)" % (category, len(groups[category])))
        for signature in groups[category]:
            print("   " + signature)
    print("\n%d commands" % sum(len(v) for v in groups.values()))
    return 0


def check_file(path):
    interp = JapyInterpreter()
    try:
        source = _read_file(path)
        interp.sources[path] = source
        JapyParser(JapyLexer().tokenize(source)).parse()
    except JapyError as err:
        err.filename = path
        _report(err, interp)
        return 1
    print("%s: syntax OK" % path)
    return 0


def run_source(source, name, args):
    interp = JapyInterpreter(base_dir=os.path.dirname(os.path.abspath(name)) if os.path.exists(name) else None,
                             max_loops=args.max_loops, realtime=args.realtime, frames=args.frames)
    if not args.quiet:
        print("--- [Japy Engine Runtime Initialized] ---")
    try:
        interp.run_script(source, name)
    except JapyExit as stop:
        return stop.code
    except JapyError as err:
        _report(err, interp)
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\n[Japy] Stopped by the user.\n")
        return 130
    if not args.quiet:
        print("--- [Japy Engine Execution Finished] ---")
    return 0


def _open_depth(source):
    """How many ( [ { are still open? Used by the REPL to read multi-line input."""
    depth = 0
    for tok in JapyLexer().tokenize(source):
        if tok.type in ("LBRACE", "LPAREN", "LBRACKET"):
            depth += 1
        elif tok.type in ("RBRACE", "RPAREN", "RBRACKET"):
            depth -= 1
    return depth


def repl(args):
    try:
        import readline  # noqa: F401  (gives arrow keys / history where available)
    except ImportError:
        pass
    interp = JapyInterpreter(max_loops=args.max_loops, realtime=args.realtime, frames=args.frames)
    print("JapyScript %s - type :help for help, :quit to leave" % VERSION_LABEL)
    buffer = ""
    while True:
        try:
            line = input("... " if buffer else "japy> ")
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            buffer = ""
            continue
        if not buffer and line.strip() in (":quit", ":q", ":exit"):
            return 0
        if not buffer and line.strip() == ":help":
            print("Type Japy code. Blocks may span several lines.  help(\"print\") explains a command,\n"
                  "listapis() lists them all, :quit leaves.")
            continue
        buffer += line + "\n"
        try:
            if _open_depth(buffer) > 0:
                continue
        except JapySyntaxError:
            pass                                    # let the real run report the error
        source, buffer = buffer, ""
        if not source.strip():
            continue
        try:
            value = interp.execute_source(source, "<repl>", want_value=True)
            if value is not None:
                print(interp.to_text(value, True))
        except JapyExit as stop:
            return stop.code
        except JapyError as err:
            _report(err, interp)
        except KeyboardInterrupt:
            print("\n[Japy] Stopped.")


def main(argv=None):
    _utf8_output()
    parser = argparse.ArgumentParser(prog="main.py", description="JapyScript %s" % VERSION_LABEL)
    parser.add_argument("script", nargs="?", help="a .japy script to run (omit for the interactive prompt)")
    parser.add_argument("-c", "--code", metavar="CODE", help="run this code instead of a file")
    parser.add_argument("--check", action="store_true", help="only check the syntax of the script")
    parser.add_argument("--frames", type=int, default=1, metavar="N",
                        help="how many times to call loop() after setup() (default 1)")
    parser.add_argument("--realtime", action="store_true", help="make delay()/sleep() really wait")
    parser.add_argument("--max-loops", type=int, default=1000000, metavar="N",
                        help="stop a while-loop after N rounds (default 1000000)")
    parser.add_argument("--list-apis", nargs="?", const="", metavar="PREFIX",
                        help="list the built-in commands (optionally only those starting with PREFIX)")
    parser.add_argument("-q", "--quiet", action="store_true", help="hide the start/finish banner lines")
    parser.add_argument("--version", action="store_true", help="show the version and exit")
    args = parser.parse_args(argv)

    if args.version:
        print("JapyScript %s (Python %s)" % (VERSION_LABEL, sys.version.split()[0]))
        return 0
    if args.list_apis is not None:
        return list_apis(args.list_apis)
    if args.code is not None:
        return run_source(args.code, "<code>", args)
    if args.script is None:
        return repl(args)
    if not os.path.exists(args.script):
        sys.stderr.write("[Error] Japy script not found: %s\n" % args.script)
        return 2
    if args.check:
        return check_file(args.script)
    try:
        source = _read_file(args.script)
    except (OSError, UnicodeDecodeError) as exc:
        sys.stderr.write("[Error] Cannot read %s: %s\n" % (args.script, exc))
        return 2
    return run_source(source, args.script, args)


if __name__ == "__main__":
    sys.exit(main())
