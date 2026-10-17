class ASTNode:
    pass

class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class VarDeclNode(ASTNode):
    def __init__(self, name, value_node):
        self.name = name
        self.value_node = value_node

class FuncDefNode(ASTNode):
    def __init__(self, name, body_statements):
        self.name = name
        self.body_statements = body_statements

class CallNode(ASTNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class PropertyAccessNode(ASTNode):
    def __init__(self, obj_name, prop_name, args=None):
        self.obj_name = obj_name
        self.prop_name = prop_name
        self.args = args  # For plugin method calls like plugin.method()

class LiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value

class JapyParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def consume(self, expected_type=None):
        token = self.peek()
        if not token:
            raise SyntaxError("Unexpected end of script")
        if expected_type and token.type != expected_type:
            raise SyntaxError(f"Expected token type {expected_type}, but got {token.type}")
        self.pos += 1
        return token

    def parse(self):
        statements = []
        while self.peek() is not None:
            statements.append(self.parse_statement())
        return ProgramNode(statements)

    def parse_statement(self):
        token = self.peek()
        
        # 1. Parse variable declaration: var name = value
        if token.type == 'VAR':
            self.consume('VAR')
            name_token = self.consume('ID')
            self.consume('ASSIGN')
            value_node = self.parse_expression()
            return VarDeclNode(name_token.value, value_node)
            
        # 2. Parse function definition: def name() { ... }
        elif token.type == 'DEF':
            self.consume('DEF')
            name_token = self.consume('ID')
            self.consume('LPAREN')
            self.consume('RPAREN')
            self.consume('LBRACE')
            
            # Safe block parsing: collects inside curly braces ignoring layout
            body = []
            while self.peek() and self.peek().type != 'RBRACE':
                body.append(self.parse_statement())
            self.consume('RBRACE')
            return FuncDefNode(name_token.value, body)
            
        # 3. Default to parsing expression statements (e.g., API calls or assignments)
        return self.parse_expression()

    def parse_expression(self):
        token = self.consume()
        
        if token.type in ['NUMBER', 'STRING']:
            return LiteralNode(token.value)
            
        elif token.type == 'ID':
            next_token = self.peek()
            
            # Parse standalone API Call: print("hello")
            if next_token and next_token.type == 'LPAREN':
                self.consume('LPAREN')
                args = []
                if self.peek().type != 'RPAREN':
                    args.append(self.parse_expression())
                    while self.peek().type == 'COMMA':
                        self.consume('COMMA')
                        args.append(self.parse_expression())
                self.consume('RPAREN')
                return CallNode(token.value, args)
                
            # Parse Plugin Property/Method Access: plugin.setboneweight(x, y)
            elif next_token and next_token.type == 'DOT':
                self.consume('DOT')
                prop_token = self.consume('ID')
                
                # Check if it's a method call with arguments
                if self.peek() and self.peek().type == 'LPAREN':
                    self.consume('LPAREN')
                    args = []
                    if self.peek().type != 'RPAREN':
                        args.append(self.parse_expression())
                        while self.peek().type == 'COMMA':
                            self.consume('COMMA')
                            args.append(self.parse_expression())
                    self.consume('RPAREN')
                    return PropertyAccessNode(token.value, prop_token.value, args)
                
                return PropertyAccessNode(token.value, prop_token.value)
                
            return LiteralNode(token.value)
            
        raise SyntaxError(f"Invalid expression syntax near: {token.value}")
