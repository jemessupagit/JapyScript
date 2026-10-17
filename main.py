import os
import sys

# Ensure the interpreter modules inside src/ can be found correctly
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from interpreter import JapyInterpreter

def run_japy_engine():
    # Usage: python main.py <script.japy>
    if len(sys.argv) < 2:
        print("Usage: python main.py <script.japy>")
        print("Example: python main.py examples/01_hero_walk.japy")
        return

    script_path = sys.argv[1]

    if not os.path.exists(script_path):
        print(f"[Error] Japy script not found: {script_path}")
        return

    print("--- [Japy Engine Runtime Initialized] ---")

    # Read the content of the mobile-written Japy script
    with open(script_path, 'r', encoding='utf-8') as file:
        source_code = file.read()

    # Create the core interpreter instance and execute the code blocks
    interpreter = JapyInterpreter()
    interpreter.run_script(source_code)

    print("--- [Japy Engine Execution Finished] ---")

if __name__ == "__main__":
    run_japy_engine()
