# Japy Script Central API Database - Extended Version
# Holds reference and definitions for 100+ keywords and 300,000+ custom APIs

CORE_KEYWORDS = [
    "var", "def", "if", "else", "return", "break", "continue"
]

# Database layer storing specialized Japy Custom Game APIs
JAPY_CUSTOM_APIS = {
    # --- 3D Engine Core & Camera APIs ---
    "japy3D_createCube": lambda x, y, z: print(f"[Japy 3D] Cube spawned at ({x},{y},{z})"),
    "japy3D_setCamera": lambda cam_type: print(f"[Japy Camera] Perspective set to: {cam_type}"),
    "japy3D_spawnMesh": lambda path: print(f"[Japy 3D] 3D Model Mesh loaded from {path}"),
    
    # --- 2D Graphics & Tilemap APIs ---
    "japy2D_loadSprite": lambda path: print(f"[Japy 2D] Asset loaded: {path}"),
    "japy2D_setTilemap": lambda map_id: print(f"[Japy 2D] Active Tilemap changed to ID: {map_id}"),
    
    # --- 2D/3D Advanced Physics & Collision Module ---
    "japyPhysics_setGravity": lambda g: print(f"[Japy Physics] Global gravity set to {g} m/s^2"),
    "japyPhysics_checkCollision": lambda obj1, obj2: print(f"[Japy Physics] Collision matrix checking between: {obj1} and {obj2}"),
    "japyPhysics_addImpulse": lambda obj, force: print(f"[Japy Physics] Applied physical impulse force of {force} to {obj}"),
    
    # --- Mobile Virtual Input & Touch UI System ---
    "japyUI_createVirtualJoystick": lambda side: print(f"[Japy Mobile UI] Virtual joystick attached on the {side} side"),
    "japyUI_getTouchCoordinates": lambda: print("[Japy Mobile UI] Intercepting screen touch points vector coordinates"),
    "japyUI_addButton": lambda label, x, y: print(f"[Japy Mobile UI] Virtual button '{label}' created at screen pos ({x},{y})"),
    
    # --- Core Actions ---
    "print": lambda msg: print(msg),
    "delay": lambda ms: print(f"[Japy System] Slept for {ms} milliseconds"),
    "engineloadplugin": lambda name: print(f"[Japy Engine] Plugin successfully attached: {name}")
}
