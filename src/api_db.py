"""Japy game API database.

These commands are SIMULATED: each one prints what a real engine back end
would do. A native engine can replace any of them by registering a function
with the same name (interp.register(...)).

Format of each entry: (name, [parameters], message)
  - a parameter written "name=default" is optional; the default is a JSON literal
  - {param} in the message is replaced with the argument value
"""
import json

from .errors import JapyRuntimeError
from .values import to_text

API_SPECS = [
    # --- 3D engine & camera
    ("japy3D_createCube", ["x", "y", "z"], "[Japy 3D] Cube spawned at ({x},{y},{z})"),
    ("japy3D_createSphere", ["x", "y", "z", "radius=1"], "[Japy 3D] Sphere (radius {radius}) spawned at ({x},{y},{z})"),
    ("japy3D_createPlane", ["width", "depth"], "[Japy 3D] Plane created ({width} x {depth})"),
    ("japy3D_setCamera", ["cam_type"], "[Japy Camera] Perspective set to: {cam_type}"),
    ("japy3D_setCameraPosition", ["x", "y", "z"], "[Japy Camera] Camera moved to ({x},{y},{z})"),
    ("japy3D_lookAt", ["x", "y", "z"], "[Japy Camera] Camera now looks at ({x},{y},{z})"),
    ("japy3D_spawnMesh", ["path"], "[Japy 3D] 3D Model Mesh loaded from {path}"),
    ("japy3D_move", ["obj", "x", "y", "z"], "[Japy 3D] {obj} moved to ({x},{y},{z})"),
    ("japy3D_rotate", ["obj", "x", "y", "z"], "[Japy 3D] {obj} rotated by ({x},{y},{z}) degrees"),
    ("japy3D_scale", ["obj", "x", "y", "z"], "[Japy 3D] {obj} scaled to ({x},{y},{z})"),
    ("japy3D_destroy", ["obj"], "[Japy 3D] {obj} destroyed"),
    ("japy3D_setMaterial", ["obj", "color"], "[Japy 3D] {obj} material color set to {color}"),
    ("japy3D_setLight", ["kind", "intensity=1"], "[Japy 3D] {kind} light set (intensity {intensity})"),
    ("japy3D_setSkybox", ["path"], "[Japy 3D] Skybox loaded from {path}"),
    ("japy3D_playAnimation", ["obj", "clip"], "[Japy 3D] {obj} plays animation '{clip}'"),
    # --- 2D graphics & tilemaps
    ("japy2D_loadSprite", ["path"], "[Japy 2D] Asset loaded: {path}"),
    ("japy2D_createSprite", ["path", "x", "y"], "[Japy 2D] Sprite {path} created at ({x},{y})"),
    ("japy2D_moveSprite", ["id", "x", "y"], "[Japy 2D] Sprite {id} moved to ({x},{y})"),
    ("japy2D_destroySprite", ["id"], "[Japy 2D] Sprite {id} destroyed"),
    ("japy2D_playAnimation", ["id", "name"], "[Japy 2D] Sprite {id} plays animation '{name}'"),
    ("japy2D_setTilemap", ["map_id"], "[Japy 2D] Active Tilemap changed to ID: {map_id}"),
    ("japy2D_drawText", ["text", "x", "y"], "[Japy 2D] Text '{text}' drawn at ({x},{y})"),
    ("japy2D_drawRect", ["x", "y", "w", "h", 'color="white"'], "[Japy 2D] Rectangle {w}x{h} drawn at ({x},{y}) color {color}"),
    ("japy2D_setBackground", ["color"], "[Japy 2D] Background color set to {color}"),
    ("japy2D_setCameraZoom", ["zoom"], "[Japy 2D] Camera zoom set to {zoom}"),
    ("japy2D_emitParticles", ["name", "x", "y"], "[Japy 2D] Particle emitter '{name}' fired at ({x},{y})"),
    # --- physics & collision
    ("japyPhysics_setGravity", ["g"], "[Japy Physics] Global gravity set to {g} m/s^2"),
    ("japyPhysics_checkCollision", ["obj1", "obj2"], "[Japy Physics] Collision matrix checking between: {obj1} and {obj2}"),
    ("japyPhysics_addImpulse", ["obj", "force"], "[Japy Physics] Applied physical impulse force of {force} to {obj}"),
    ("japyPhysics_addForce", ["obj", "x", "y", "z=0"], "[Japy Physics] Force ({x},{y},{z}) applied to {obj}"),
    ("japyPhysics_setVelocity", ["obj", "x", "y", "z=0"], "[Japy Physics] Velocity of {obj} set to ({x},{y},{z})"),
    ("japyPhysics_setMass", ["obj", "mass"], "[Japy Physics] Mass of {obj} set to {mass}"),
    ("japyPhysics_setFriction", ["obj", "friction"], "[Japy Physics] Friction of {obj} set to {friction}"),
    ("japyPhysics_enable", ["obj"], "[Japy Physics] Physics enabled for {obj}"),
    ("japyPhysics_raycast", ["ox", "oy", "oz", "dx", "dy", "dz"], "[Japy Physics] Ray cast from ({ox},{oy},{oz}) towards ({dx},{dy},{dz})"),
    # --- mobile UI & touch
    ("japyUI_createVirtualJoystick", ["side"], "[Japy Mobile UI] Virtual joystick attached on the {side} side"),
    ("japyUI_getTouchCoordinates", [], "[Japy Mobile UI] Intercepting screen touch points vector coordinates"),
    ("japyUI_addButton", ["label", "x", "y"], "[Japy Mobile UI] Virtual button '{label}' created at screen pos ({x},{y})"),
    ("japyUI_addLabel", ["text", "x", "y"], "[Japy Mobile UI] Label '{text}' created at screen pos ({x},{y})"),
    ("japyUI_addSlider", ["label", "low", "high", "value"], "[Japy Mobile UI] Slider '{label}' ({low}..{high}) set to {value}"),
    ("japyUI_showToast", ["message"], "[Japy Mobile UI] Toast: {message}"),
    ("japyUI_vibrate", ["ms=100"], "[Japy Mobile UI] Vibrate for {ms} ms"),
    ("japyUI_hide", ["id"], "[Japy Mobile UI] Element {id} hidden"),
    # --- audio
    ("japyAudio_play", ["path", "volume=1"], "[Japy Audio] Playing {path} at volume {volume}"),
    ("japyAudio_playMusic", ["path", "loop=true"], "[Japy Audio] Music {path} started (loop: {loop})"),
    ("japyAudio_stop", ["path"], "[Japy Audio] Stopped {path}"),
    ("japyAudio_setVolume", ["volume"], "[Japy Audio] Master volume set to {volume}"),
    # --- input
    ("japyInput_isKeyDown", ["key"], None),
    ("japyInput_isTouching", [], None),
    ("japyInput_getAccelerometer", [], None),
    # --- scenes
    ("japyScene_load", ["name"], "[Japy Scene] Scene '{name}' loaded"),
    ("japyScene_reload", [], "[Japy Scene] Current scene reloaded"),
    # --- networking (multiplayer pipeline stubs)
    ("japyNet_connect", ["host", "port=7777"], "[Japy Net] Connecting to {host}:{port}"),
    ("japyNet_send", ["channel", "data"], "[Japy Net] Sent on '{channel}': {data}"),
    ("japyNet_disconnect", [], "[Japy Net] Disconnected"),
]

# Values returned by APIs that would answer a question in a real engine.
_RETURNS = {
    "japyPhysics_checkCollision": lambda interp, args: False,
    "japyPhysics_raycast": lambda interp, args: None,
    "japyUI_getTouchCoordinates": lambda interp, args: [0, 0],
}

CATEGORIES = {
    "japy3D_": "3D", "japy2D_": "2D", "japyPhysics_": "Physics", "japyUI_": "Mobile UI",
    "japyAudio_": "Audio", "japyInput_": "Input", "japyScene_": "Scenes", "japyNet_": "Network",
    "japySave_": "Save data", "japyTime_": "Time",
}


def _category(name):
    for prefix, label in CATEGORIES.items():
        if name.startswith(prefix):
            return label
    return "Game"


def _make(interp, name, spec, message):
    names, defaults = [], {}
    for part in spec:
        if "=" in part:
            pname, default = part.split("=", 1)
            defaults[pname] = json.loads(default)
            names.append(pname)
        else:
            names.append(part)
    required = len(names) - len(defaults)
    shown = ", ".join(spec) if spec else ""

    def api(*args):
        if len(args) < required or len(args) > len(names):
            raise JapyRuntimeError("%s(%s) was called with %d argument(s)" % (name, shown, len(args)))
        values = dict(defaults)
        values.update(zip(names, args))
        if message is not None:
            interp.write(message.format(**dict((k, to_text(v)) for k, v in values.items())))
        ret = _RETURNS.get(name)
        if ret is not None:
            return ret(interp, args)
        return _input_default(name)

    api.__name__ = name
    return api


def _input_default(name):
    if name == "japyInput_getAccelerometer":
        return [0, 0, 0]
    if name in ("japyInput_isKeyDown", "japyInput_isTouching"):
        return False
    return None


def install(interp):
    for name, spec, message in API_SPECS:
        description = ("(simulated) prints: " + message) if message else "(simulated) returns a default value"
        signature = "%s(%s)" % (name, ", ".join(spec))
        interp.register(name, _category(name), signature, description, _make(interp, name, spec, message))

    # --- save data (kept in memory while the script runs)
    def reg(name, signature, description):
        def deco(fn):
            interp.register(name, "Save data", signature, description, fn)
            return fn
        return deco

    @reg("japySave_set", "japySave_set(key, value)", "Store a value under a key (in memory).")
    def _save_set(key, value):
        interp.save_data[to_text(key)] = value

    @reg("japySave_get", "japySave_get(key, default = null)", "Read a stored value.")
    def _save_get(key, default=None):
        return interp.save_data.get(to_text(key), default)

    @reg("japySave_has", "japySave_has(key)", "true when the key is stored.")
    def _save_has(key):
        return to_text(key) in interp.save_data

    @reg("japySave_delete", "japySave_delete(key)", "Forget a stored key.")
    def _save_delete(key):
        interp.save_data.pop(to_text(key), None)

    @reg("japySave_clear", "japySave_clear()", "Forget everything stored.")
    def _save_clear():
        interp.save_data.clear()

    # --- time
    def treg(name, signature, description):
        def deco(fn):
            interp.register(name, "Time", signature, description, fn)
            return fn
        return deco

    @treg("japyTime_deltaTime", "japyTime_deltaTime()", "Seconds per frame (fixed 1/60 in the simulator).")
    def _delta():
        return 1.0 / 60.0

    @treg("japyTime_frame", "japyTime_frame()", "Number of the current loop() frame (1, 2, 3 ...).")
    def _frame():
        return interp.frame
