import os
import sys

# Ensure the interpreter modules inside src/ can be found correctly
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from interpreter import JapyInterpreter

def run_japy_engine():
    # Define the exact path to our first example script
    script_path = os.path.join(os.path.dirname(__file__), 'examples', '01_hero_walk.japy')
    
    if not os.path.exists(script_path):
        print(f"[Error] Target Japy script not found at: {script_path}")
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
