> ⚠️ **Under development** — Test Version v1.5.0 (beta)
> Features may change, and some parts are not finished yet. See [CHANGELOG.md](CHANGELOG.md).

# Japy Script Engine 🐍 + 🟨

**Japy Script** is a lightweight, hybrid scripting language for making 2D/3D games on **mobile phones**.
It mixes the readability of **Python** with the braces of **JavaScript**, so it is comfortable to type on a touchscreen.

## How to run
```
python main.py examples/01_hero_walk.japy      # run a script
python main.py                                 # interactive prompt (REPL)
python main.py -c 'print(1 + 2)'               # run one line
python main.py examples/06_game_loop.japy --frames 5
python main.py --check script.japy             # syntax check only
python main.py --list-apis                     # every built-in command
python -m unittest discover -s tests           # run the tests
```
Requires **Python 3.8 or newer** (the code is checked against 3.8 syntax). Tested on Python 3.12 and Termux (Android).

## Mobile-first rules
- **No semicolons needed** (a `;` is allowed but ignored).
- **Indentation Shield:** blocks use `{ }`, so messy spacing on a phone never changes what your code does.
- Long calls can be split over several lines inside `( )` and `[ ]`.

## A taste of v1.5.0
```javascript
const GRAVITY = 9.81
var player = { name: "Hero", hp: 100, items: ["sword"] }

def damage(target, amount = 10) {
    target.hp -= amount
    if target.hp <= 0 { throw target.name + " was defeated" }
}

def setup() {
    japyPhysics_setGravity(GRAVITY)
    player.items.push("shield")
    for i, item in enumerate(player.items) {
        print((i + 1) + ". " + item)
    }
}

def loop() {
    try { damage(player, 30) } catch (msg) { print(msg) }
    print("hp: " + player.hp)
}
```
`setup()` runs once, then `loop()` runs once per frame (`--frames N` to repeat).

## What is inside
```text
JapyScript/
├── main.py          # command line runner + interactive prompt
├── src/japy/        # the engine: lexer, parser, interpreter, stdlib, api_db
├── examples/        # ready-to-run .japy scripts (01 - 08, plus lib/)
├── docs/            # syntax.md (language guide) and api.md (all commands)
├── tests/           # unittest suite
├── tools/           # gen_api_doc.py regenerates docs/api.md
├── CHANGELOG.md
└── LICENSE          # MIT
```

## Commands and the game engine
**169 commands and constants** are available today (`python main.py --list-apis`, or see [docs/api.md](docs/api.md)):
core helpers for math, text, lists, dicts, JSON and time, plus game API families `japy3D_`, `japy2D_`,
`japyPhysics_`, `japyUI_`, `japyAudio_`, `japyInput_`, `japyScene_`, `japyNet_` and `japySave_`.

The game APIs are **simulated**: each prints what a real engine would do, so you can design and test game logic
before the native C++ rendering layer exists. The long-term goal is 100+ keywords and a very large plugin API
library; a native back end replaces a simulated command by registering a function with the same name.

## Licensing & Open Source
This project is open for worldwide collaboration under the **MIT License**. Created and copyrighted by **James**.
