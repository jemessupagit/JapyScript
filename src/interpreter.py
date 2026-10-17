from lexer import JapyLexer
from parser import (JapyParser, VarDeclNode, AssignNode, FuncDefNode, CallNode,
                    PropertyAccessNode, LiteralNode, BinaryOpNode, UnaryOpNode,
                    IfNode, WhileNode)
# Dynamic linking with the custom Japy API Database layer
from japy_api_db import JAPY_CUSTOM_APIS

# Safety net: stops accidental infinite loops from freezing a phone
MAX_LOOP_ITERATIONS = 100000

class JapyInterpreter:
    def __init__(self):
        self.globals = {}
        self.functions = {}
        # Seamlessly inject custom APIs database into core engine runtime
        self.custom_apis = JAPY_CUSTOM_APIS

    @staticmethod
    def _to_text(value):
        if value is True:
            return "true"
        if value is False:
            return "false"
        if value is None:
            return "null"
        return str(value)

    def execute_block(self, statements):
        result = None
        for statement in statements:
            result = self.execute(statement)
        return result

    def execute(self, node):
        if isinstance(node, VarDeclNode):
            val = self.execute(node.value_node)
            self.globals[node.name] = val
            return val

        elif isinstance(node, AssignNode):
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
                if node.value == 'true':
                    return True
                if node.value == 'false':
                    return False
                if node.value == 'null':
                    return None
                return node.value

        elif isinstance(node, UnaryOpNode):
            val = self.execute(node.operand)
            if node.op == '-':
                return -val
            if node.op == '!':
                return not val

        elif isinstance(node, BinaryOpNode):
            op = node.op
            # Short-circuit logic operators
            if op == '&&':
                return bool(self.execute(node.left)) and bool(self.execute(node.right))
            if op == '||':
                return bool(self.execute(node.left)) or bool(self.execute(node.right))

            left = self.execute(node.left)
            right = self.execute(node.right)

            if op == '+':
                if isinstance(left, str) or isinstance(right, str):
                    return self._to_text(left) + self._to_text(right)
                return left + right
            if op == '-':
                return left - right
            if op == '*':
                return left * right
            if op == '/':
                if right == 0:
                    raise ZeroDivisionError("Japy: division by zero")
                res = left / right
                if isinstance(left, int) and isinstance(right, int) and res == int(res):
                    return int(res)
                return res
            if op == '%':
                if right == 0:
                    raise ZeroDivisionError("Japy: modulo by zero")
                return left % right
            if op == '==':
                return left == right
            if op == '!=':
                return left != right
            if op == '<':
                return left < right
            if op == '>':
                return left > right
            if op == '<=':
                return left <= right
            if op == '>=':
                return left >= right
            raise SyntaxError(f"Unknown operator: {op}")

        elif isinstance(node, IfNode):
            if self.execute(node.condition):
                return self.execute_block(node.then_body)
            elif node.else_body is not None:
                return self.execute_block(node.else_body)
            return None

        elif isinstance(node, WhileNode):
            count = 0
            while self.execute(node.condition):
                self.execute_block(node.body)
                count += 1
                if count >= MAX_LOOP_ITERATIONS:
                    raise RuntimeError(
                        f"Japy: loop stopped after {MAX_LOOP_ITERATIONS} iterations (possible infinite loop)"
                    )
            return None

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
            return self.execute_block(self.functions[func_name])
        return None

    def run_script(self, source_code):
        lexer = JapyLexer()
        tokens = lexer.tokenize(source_code)

        parser = JapyParser(tokens)
        ast = parser.parse()

        for statement in ast.statements:
            self.execute(statement)

        if "setup" in self.functions:
            self.run_function("setup")
