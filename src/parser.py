class ASTNode:
    pass

class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements

class VarDeclNode(ASTNode):
    def __init__(self, name, value_node):
        self.name = name
        self.value_node = value_node

class AssignNode(ASTNode):
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

class BinaryOpNode(ASTNode):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class UnaryOpNode(ASTNode):
    def __init__(self, op, operand):
        self.op = op
        self.operand = operand

class IfNode(ASTNode):
    def __init__(self, condition, then_body, else_body=None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body

class WhileNode(ASTNode):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

# Token types that carry no meaning for the parser
SKIP_TYPES = ('NEWLINE', 'COMMENT')

class JapyParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- token helpers ----------
    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def peek_at(self, offset):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
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

    # ---------- statements ----------
    def parse(self):
        statements = []
        while True:
            self.skip_newlines()
            if self.peek() is None or self.peek().type == 'EOF':
                break
            statements.append(self.parse_statement())
        return ProgramNode(statements)

    def parse_block(self):
        """Parse { ... } and return a list of statements. Layout is ignored."""
        self.skip_newlines()
        self.consume('LBRACE')
        body = []
        while True:
            self.skip_newlines()
            nxt = self.peek()
            if nxt is None:
                raise SyntaxError("Missing closing brace '}'")
            if nxt.type == 'RBRACE':
                break
            body.append(self.parse_statement())
        self.consume('RBRACE')
        return body

    def parse_statement(self):
        self.skip_newlines()
        token = self.peek()
        if token is None:
            raise SyntaxError("Unexpected end of script")

        # var name = value
        if token.type == 'VAR':
            self.consume('VAR')
            name_token = self.consume('ID')
            self.consume('ASSIGN')
            value_node = self.parse_expression()
            return VarDeclNode(name_token.value, value_node)

        # def name() { ... }
        elif token.type == 'DEF':
            self.consume('DEF')
            name_token = self.consume('ID')
            self.consume('LPAREN')
            self.consume('RPAREN')
            body = self.parse_block()
            return FuncDefNode(name_token.value, body)

        # if (cond) { ... } else if (cond) { ... } else { ... }
        elif token.type == 'IF':
            return self.parse_if()

        # while (cond) { ... }
        elif token.type == 'WHILE':
            self.consume('WHILE')
            condition = self.parse_expression()
            body = self.parse_block()
            return WhileNode(condition, body)

        # name = value  (re-assign without var)
        elif token.type == 'ID' and self.peek_at(1) is not None and self.peek_at(1).type == 'ASSIGN':
            name_token = self.consume('ID')
            self.consume('ASSIGN')
            value_node = self.parse_expression()
            return AssignNode(name_token.value, value_node)

        # Default: expression statement (API call, plugin call)
        return self.parse_expression()

    def parse_if(self):
        self.consume('IF')
        condition = self.parse_expression()
        then_body = self.parse_block()
        else_body = None

        saved = self.pos
        self.skip_newlines()
        if self.peek() is not None and self.peek().type == 'ELSE':
            self.consume('ELSE')
            self.skip_newlines()
            if self.peek() is not None and self.peek().type == 'IF':
                else_body = [self.parse_if()]   # else if
            else:
                else_body = self.parse_block()
        else:
            self.pos = saved  # no else: do not swallow newlines
        return IfNode(condition, then_body, else_body)

    # ---------- expressions (lowest -> highest precedence) ----------
    def parse_expression(self):
        self.skip_newlines()
        return self.parse_or()

    def _binary(self, ops, next_fn):
        left = next_fn()
        while self.peek() is not None and self.peek().type == 'OP' and self.peek().value in ops:
            op = self.consume().value
            self.skip_newlines()
            right = next_fn()
            left = BinaryOpNode(op, left, right)
        return left

    def parse_or(self):
        return self._binary(('||',), self.parse_and)

    def parse_and(self):
        return self._binary(('&&',), self.parse_equality)

    def parse_equality(self):
        return self._binary(('==', '!='), self.parse_comparison)

    def parse_comparison(self):
        return self._binary(('<', '>', '<=', '>='), self.parse_term)

    def parse_term(self):
        return self._binary(('+', '-'), self.parse_factor)

    def parse_factor(self):
        return self._binary(('*', '/', '%'), self.parse_unary)

    def parse_unary(self):
        tok = self.peek()
        if tok is not None and tok.type == 'OP' and tok.value in ('-', '!'):
            self.consume()
            return UnaryOpNode(tok.value, self.parse_unary())
        return self.parse_primary()

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

    def parse_primary(self):
        self.skip_newlines()
        token = self.consume()

        if token.type in ('NUMBER', 'STRING'):
            return LiteralNode(token.value)

        elif token.type == 'LPAREN':
            expr = self.parse_expression()
            self.skip_newlines()
            self.consume('RPAREN')
            return expr

        elif token.type == 'ID':
            next_token = self.peek()

            # API call: print("hello")
            if next_token and next_token.type == 'LPAREN':
                self.consume('LPAREN')
                args = self.parse_args()
                return CallNode(token.value, args)

            # Plugin access: plugin.setboneweight(x, y)
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
