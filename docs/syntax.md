# Japy Script Language Specification

> ⚠️ **Under development** — Test Version v1.0.3-beta. Features may change, and some parts are not finished yet (see [Current Status & Roadmap](#-9-current-status--roadmap)).

This document details the core syntax rules, design philosophies, and architectural layers for **Japy Script**—a mobile-first, lightweight scripting language engineered as the primary logic driving system for a modern 2D/3D Universal Game Engine.

---

## 📐 1. Language Architecture & Philosophy

Coding natively on handheld screens with touch virtual keyboards poses major physical constraints: limited typing space, cumbersome special character switching, and fragile indentation layouts. Japy Script addresses these issues by fusing structural attributes from Python and JavaScript into an optimised hybrid dialect:

- **Ultra-Short Syntax (Python Character):** Completely removes mandatory semicolons (`;`) from statement endings to reduce touch keyboard page-switching.
- **Accidental Space Shield (JavaScript Character):** Discards strict whitespace indentation dependencies. Code structures rely solely on rigid curly braces `{ }` to define block scoping. Code logic runs flawlessly even if physical spacing gets misaligned on mobile layouts.
- **Scale Capability:** Built from the ground up to support a database of **100+ Core Keywords** and **200,000 - 300,000+ Extended Sub-System/Plugin API Commands**.

---

## 🔑 2. Core Keywords (100+ Total Capabilities)

The fundamental syntax layout utilizes concise declaration phrases to initiate code execution pipelines.

### Variable Scoping
Variables use a universal dynamic definition approach:
```javascript
var speed = 12
var playerName = "Warrior_01"
```

### Function Definition & Structural Boundaries
Functions discard long typing triggers and wrap blocks inside explicit safe boundaries:
```javascript
def setup() {
    # System logic loads here instantly
    print("Core Bootstrapping Completed")
}

def loop() {
    # Real-time frame actions run perpetually
}
```

> **Note:** `setup()` runs automatically once, after the whole script has loaded. Then `loop()` runs once per frame (see [Running a Script](#️-8-running-a-script)). Inside `loop()`, the built-in variable `frame` holds the current frame number, starting at 1.

### Functions with Parameters and Return Values
Functions can take parameters and give a value back with `return`:
```javascript
def add(a, b) {
    return a + b
}

def factorial(n) {
    if (n <= 1) {
        return 1
    }
    return n * factorial(n - 1)
}

var total = add(3, 4)        # 7
print(factorial(5))          # 120
```
- Parameters and variables declared with `var` inside a function are **local** to that call.
- Assigning to an existing global variable inside a function (`score = score + 1`) updates the global.
- Calling a function with the wrong number of arguments is an error.
- A function without `return` gives back `null`.
- Recursion is limited to 100 nested calls to protect against infinite recursion.

---

## 🔌 3. Monster Sub-System Plugins (200,000 - 300,000+ APIs)

To comfortably support up to 300,000 unique actions without cluttering global namespaces or causing keyword collisions on small viewports, Japy Script deploys a modular **Dynamic Dot Property Access System** (`Object.Property/Method`) to communicate with native C++ engine plug-ins.

### Naming Conventions
- Standalone commands and system wrappers are kept strictly lowercase with no separating punctuation characters.
- Complex nested modules are accessed smoothly through variables referencing attached hardware/rendering layers.

### Plugin Integration Code Layout
```javascript
def setup() {
    # Instantiating an advanced skeletal 3D rendering plugin
    var locomotionPlugin = engineloadplugin("Advanced3DAnim")
    
    # Executing precise structural modifications via Japy Custom APIs
    locomotionPlugin.setboneweight("RightArm", 0.75)
    locomotionPlugin.blendtothreshold("run_to_jump", 0.4)
}
```

---

## 🎨 4. Game Engine Target Capabilities

With its sprawling micro-command library, scripts written in Japy Script are designed to effectively govern:
1. **3D Matrix & Meshes:** Bone transformations, perspective rendering pipelines, shader injection vectors.
2. **2D Graphics Layers:** Real-time tilemap collision tracking, automated particle emitter adjustments.
3. **Multiplayer Pipelines:** Low-latency socket state synchronization across server clusters.

---

## ➕ 5. Values, Operators & Expressions

### Values
| Type | Examples | Notes |
|------|----------|-------|
| Number | `12`, `9.81`, `-5` | Whole numbers and decimals; negatives use `-` |
| String | `"Warrior_01"`, `'hero.fbx'` | Double or single quotes |
| Boolean | `true`, `false` | Result of comparisons and logic |
| Null | `null` | Empty value |

### Operators
From highest to lowest precedence:

| Level | Operators | Meaning |
|-------|-----------|---------|
| 1 | `-x` `!x` | Negative, logical NOT |
| 2 | `*` `/` `%` | Multiply, divide, remainder |
| 3 | `+` `-` | Add (or join text), subtract |
| 4 | `<` `>` `<=` `>=` | Comparison |
| 5 | `==` `!=` | Equal, not equal |
| 6 | `&&` | Logical AND |
| 7 | `\|\|` | Logical OR |

Use parentheses `( )` to group and override the order:
```javascript
var damage = (base + bonus) * 2
var speed = -3
var half = 10 / 4        # 2.5
var left = 10 % 3        # 1
```

### Joining Text
When either side of `+` is text, the other side is converted and joined:
```javascript
print("Score: " + 120)      # Score: 120
print("Alive: " + true)     # Alive: true
```

---

## 🔀 6. Control Flow

### if / else if / else
Conditions go in parentheses and each branch uses braces:
```javascript
if (health <= 0) {
    print("Game Over")
} else if (health < 30) {
    print("Low health!")
} else {
    print("Healthy")
}
```

### while
Repeats the block as long as the condition is true:
```javascript
var i = 0
while (i < 5) {
    i = i + 1
    print("Step " + i)
}
```

> **Safety:** a `while` loop stops with an error after 100,000 iterations, so a mistaken infinite loop cannot freeze a phone.

---

## 📝 7. Assignment, Comments & Statements

- **Declare** a new variable with `var`; **change** it later without `var`:
  ```javascript
  var score = 0
  score = score + 10
  ```
- **Comments** start with `#` and run to the end of the line.
- **One statement per line.** No semicolons needed. A line may continue after an operator or inside `( )`.
- **Blocks** are always wrapped in `{ }`. Indentation never matters.
- **Calling your own function:** `reset()` runs `def reset() { ... }`, and `add(3, 4)` passes arguments (see section 2).

---

## ▶️ 8. Running a Script

Japy Script runs on a Python-based interpreter. Run any `.japy` file with:

```
python main.py examples/01_hero_walk.japy
python main.py examples/02_logic.japy
python main.py examples/03_functions.japy --frames 4
```

Execution order:
1. Top-level statements run from top to bottom.
2. `setup()` runs once, if it is defined.
3. `loop()` runs once per frame (about 60 frames per second), if it is defined.

By default `loop()` runs **60 frames** (about one second). Use `--frames N` to choose how many, or `--frames 0` to run until you press Ctrl+C.

---

## 🚧 9. Current Status & Roadmap

**Working now (v1.0.3-beta)**
- `var`, re-assignment, `def` with parameters, `return`, local variables, recursion
- `if` / `else if` / `else`, `while`
- Arithmetic, comparison and logic operators, text joining
- Custom API calls such as `print(...)` and plugin calls such as `plugin.method(a, b)`
- `#` comments, automatic `setup()`, per-frame `loop()` with the `frame` variable

**Planned**
- `for` loops, lists/arrays, `break` / `continue`
- Real-time frame timing tied to a real renderer
- Real native bindings for the 3D / physics / mobile UI plugins (they currently print what they would do)
