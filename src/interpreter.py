from lexer import JapyLexer
from parser import JapyParser, VarDeclNode, FuncDefNode, CallNode, PropertyAccessNode, LiteralNode
# Dynamic linking with the custom Japy API Database layer
from japy_api_db import JAPY_CUSTOM_APIS

class JapyInterpreter:
    def __init__(self):
        self.globals = {}
        self.functions = {}
        # Seamlessly inject custom APIs database into core engine runtime
        self.custom_apis = JAPY_CUSTOM_APIS

    def execute(self, node):
        if isinstance(node, VarDeclNode):
            val = self.execute(node.value_node)
            self.globals[node.name] = val
            return val
            
        elif isinstance(node, LiteralNode):
            if isinstance(node.value, str) and (node.value.startswith('"') or node.value.startswith("'")):
                return node.value[1:-1]
            try:
                return float(node.value) if '.' in node.value else int(node.value)
            except ValueError:
                if node.value in self.globals:
                    return self.globals[node.value]
                return node.value
                
        elif isinstance(node, FuncDefNode):
            self.functions[node.name] = node.body_statements
            return None
            
        elif isinstance(node, CallNode):
            args = [self.execute(arg) for arg in node.args]
            if node.name in self.custom_apis:
                return self.custom_apis[node.name](*args)
            elif node.name in self.functions:
                return self.run_function(node.name)
            else:
                raise NameError(f"Japy API or Function '{node.name}' is undefined.")
                
        elif isinstance(node, PropertyAccessNode):
            # Dynamic interceptor tracking nested plugin configurations
            args = [self.execute(arg) for arg in node.args] if node.args else []
            print(f"[Japy Plugin Trigger] Object: {node.obj_name} -> Executed Method: {node.prop_name} with parameters: {args}")
            return None

    def run_function(self, func_name):
        if func_name in self.functions:
            result = None
            for statement in self.functions[func_name]:
                result = self.execute(statement)
            return result
        return None

    def run_script(self, source_code):
        lexer = JapyLexer()
        tokens = lexer.tokenize(source_code)
        
        parser = JapyParser(tokens)
        ast = parser.parse()
        
        for statement in ast.statements:
            if not isinstance(statement, FuncDefNode):
                self.execute(statement)
            else:
                self.execute(statement)
                
        if "setup" in self.functions:
            self.run_function("setup")
