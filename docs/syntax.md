# Japy Script Language Specification

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
