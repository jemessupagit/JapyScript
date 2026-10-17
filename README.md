> ⚠️ **Under development** — Test Version v1.0.0 (beta)
> Features may change, and some parts are not finished yet.

# Japy Script Engine 🐍 + 🟨

**Japy Script** is a revolutionary, lightweight, and hybrid programming language designed specifically for developing 2D/3D games on **mobile smartphones**. By seamlessly uniting the clean readability of **Python** with the flexible dynamic architecture of **JavaScript**, Japy Script eliminates the physical pain points of writing code on tiny touchscreens.

---

## 📱 The Mobile-First Programming Philosophy
Coding on mobile screens is often frustrating due to limited keyboard real estate and complex text formatting. Japy Script solves this by implementing two core language rules:
- **No Semicolons (Python DNA):** Zero mandatory trailing semicolons (`;`). This drastically reduces the need to constantly flip between the alphabetical and symbol pages on virtual mobile keyboards.
- **Indentation Shield (JavaScript DNA):** The language completely ignores strict spacing or code alignment. Instead, it relies on strict curly braces `{ }` for block scoping. Your game logic will run perfectly 100% of the time, even if your code layout becomes messy or misaligned while typing on a touchscreen.

---

## ⚙️ Sprawling Architecture & High Scale APIs
Japy Script acts as the native scripting engine that binds to high-performance C++ rendering layers. It is built to comfortably manage:
- **100+ Core Keywords** for fluent syntax declarations.
- **200,000 to 300,000+ Custom Plugin APIs** split across dedicated families (`japy3D_`, `japy2D_`, `japyPhysics_`, `japyUI_`) to seamlessly trigger physics simulations, spatial sound, mobile screen touch inputs, and 3D character locomotion without namespace collisions.

---

## 📦 Project Ecosystem Setup
The engine files are organized inside the local storage repository as follows:
```text
JapyScript/
├── docs/            # Complete syntax specifications (syntax.md)
├── examples/        # Ready-to-run Japy script showcases (.japy)
├── src/             # The core Python runtime engine (lexer, parser, interpreter, api_db)
├── main.py          # The master runtime ignition trigger
├── LICENSE          # Open-source legal safety framework (MIT License)
└── README.md        # Project index landing page (This file)
```

---

## 💻 Quick Code Demonstration
A clean look at how Japy Script controls advanced 3D mechanics and mobile viewports smoothly:

```javascript
# Advanced Japy Script Showcase: 3D Model, Physics, and Mobile UI Integration
var base_gravity = 9.81
var spawn_x = 0

def setup() {
    engineloadplugin("Advanced3DAnim")
    engineloadplugin("JapyNativePhysics")
    
    japyPhysics_setGravity(base_gravity)
    japy3D_spawnMesh("assets/models/character_hero.fbx")
    japyUI_createVirtualJoystick("left")
    
    print("Mobile UI, Physics Matrix, and 3D Assets initialized!")
}
```

---

## 📄 Licensing & Open Source
This project is open for worldwide collaboration under the **MIT License**. Created and copyrighted by **James**.
