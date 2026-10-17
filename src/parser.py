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

# Token types that carry no meaning for the parser
SKIP_TYPES = ('NEWLINE', 'COMMENT')

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

    def skip_newlines(self):
        while self.peek() is not None and self.peek().type in SKIP_TYPES:
            self.pos += 1

    def parse(self):
        statements = []
        while True:
            self.skip_newlines()
            if self.peek() is None or self.peek().type == 'EOF':
                break
            statements.append(self.parse_statement())
        return ProgramNode(statements)

    def parse_statement(self):
        self.skip_newlines()
        token = self.peek()
        if token is None:
            raise SyntaxError("Unexpected end of script")

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
            self.skip_newlines()
            self.consume('LBRACE')

            # Block parsing: collect statements inside curly braces, ignoring layout
            body = []
            while True:
                self.skip_newlines()
                nxt = self.peek()
                if nxt is None:
                    raise SyntaxError("Missing closing brace '}' for function " + name_token.value)
                if nxt.type == 'RBRACE':
                    break
                body.append(self.parse_statement())
            self.consume('RBRACE')
            return FuncDefNode(name_token.value, body)

        # 3. Default to parsing expression statements (e.g., API calls)
        return self.parse_expression()

    def parse_args(self):
        """Parse call arguments after '(' up to and including ')'."""
        args = []
        self.skip_newlines()
        if self.peek() is not None and self.peek().type != 'RPAREN':
            args.append(self.parse_expression())
            self.skip_newlines()
            while self.peek() is not None and self.peek().type == 'COMMA':
                self.consume('COMMA')
                self.skip_newlines()
                args.append(self.parse_expression())
                self.skip_newlines()
        self.consume('RPAREN')
        return args

    def parse_expression(self):
        self.skip_newlines()
        token = self.consume()

        # Negative number literal: -5, -0.25
        if token.type == 'OP' and token.value == '-':
            num = self.consume('NUMBER')
            v = num.value
            return LiteralNode('-' + v if isinstance(v, str) else -v)

        if token.type in ['NUMBER', 'STRING']:
            return LiteralNode(token.value)

        elif token.type == 'ID':
            next_token = self.peek()

            # Standalone API call: print("hello")
            if next_token and next_token.type == 'LPAREN':
                self.consume('LPAREN')
                args = self.parse_args()
                return CallNode(token.value, args)

            # Plugin property/method access: plugin.setboneweight(x, y)
            elif next_token and next_token.type == 'DOT':
                self.consume('DOT')
                prop_token = self.consume('ID')

                if self.peek() and self.peek().type == 'LPAREN':
                    self.consume('LPAREN')
                    args = self.parse_args()
                    return PropertyAccessNode(token.value, prop_token.value, args)

                return PropertyAccessNode(token.value, prop_token.value)

            return LiteralNode(token.value)

        raise SyntaxError(
            f"Invalid expression near: type={token.type} value={token.value!r}"
        )
