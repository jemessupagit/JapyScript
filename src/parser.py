"""Japy parser: tokens -> AST.

Blocks use braces, so indentation never matters. Statements need no
semicolons; a newline (or just the next statement) ends them. Inside
( ) and [ ] line breaks are ignored, so long calls can be split freely.
"""
from .errors import JapySyntaxError
from .lexer import KEYWORD_TYPES


# ---------------------------------------------------------------- AST nodes
class Node(object):
    fields = ()

    def __init__(self, *args, **kwargs):
        self.line = kwargs.get('line')
        for name, value in zip(self.fields, args):
            setattr(self, name, value)


class Program(Node):      fields = ('statements',)
class VarDecl(Node):      fields = ('name', 'value', 'const')
class Assign(Node):       fields = ('target', 'op', 'value')      # op: '' or '+', '-', ...
class FuncDef(Node):      fields = ('name', 'params', 'body')
class FuncExpr(Node):     fields = ('params', 'body')
class Call(Node):         fields = ('callee', 'args')
class Index(Node):        fields = ('obj', 'index')
class Member(Node):       fields = ('obj', 'name')
class Ident(Node):        fields = ('name',)
class Literal(Node):      fields = ('value',)
class ListLit(Node):      fields = ('items',)
class DictLit(Node):      fields = ('pairs',)
class Binary(Node):       fields = ('op', 'left', 'right')
class Unary(Node):        fields = ('op', 'operand')
class If(Node):           fields = ('condition', 'then_body', 'else_body')
class While(Node):        fields = ('condition', 'body')
class For(Node):          fields = ('names', 'iterable', 'body')
class Break(Node):        fields = ()
class Continue(Node):     fields = ()
class Return(Node):       fields = ('value',)
class Try(Node):          fields = ('body', 'catch_name', 'catch_body', 'finally_body')
class Throw(Node):        fields = ('value',)
class Import(Node):       fields = ('path',)

# Kept for scripts/tools written against v1.0.x names.
ProgramNode = Program

AUG_OPS = ('+=', '-=', '*=', '/=', '%=')

_TYPE_NAMES = {
    'LBRACE': "'{'", 'RBRACE': "'}'", 'LPAREN': "'('", 'RPAREN': "')'",
    'LBRACKET': "'['", 'RBRACKET': "']'", 'COLON': "':'", 'COMMA': "','",
    'ASSIGN': "'='", 'ID': 'a name', 'STRING': 'text in quotes', 'IN': "'in'",
}


def _describe(tok):
    if tok.type == 'EOF':
        return 'the end of the script'
    if tok.type == 'NEWLINE':
        return 'the end of the line'
    if tok.type == 'STRING':
        return 'text "%s"' % tok.value
    return "'%s'" % (tok.value,)


class JapyParser(object):
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.nl_skip = 0     # >0 while inside ( ) or [ ]: newlines are ignored

    # ---------------------------------------------------------- token helpers
    def peek(self):
        if self.nl_skip:
            while self.tokens[self.pos].type == 'NEWLINE':
                self.pos += 1
        return self.tokens[self.pos]

    def advance(self):
        tok = self.peek()
        if tok.type != 'EOF':
            self.pos += 1
        return tok

    def skip_newlines(self):
        while self.tokens[self.pos].type == 'NEWLINE':
            self.pos += 1

    def error(self, message, tok=None):
        tok = tok or self.peek()
        if tok.type == 'EOF':                    # point at the last real token instead of an empty last line
            i = len(self.tokens) - 2
            while i >= 0 and self.tokens[i].type == 'NEWLINE':
                i -= 1
            if i >= 0:
                tok = self.tokens[i]
        return JapySyntaxError(message, tok.line, tok.col)

    def expect(self, type_, message=None):
        tok = self.peek()
        if tok.type != type_:
            if message is None:
                message = "Expected %s but found %s" % (_TYPE_NAMES.get(type_, type_), _describe(tok))
            raise self.error(message, tok)
        return self.advance()

    # ------------------------------------------------------------- statements
    def parse(self):
        statements = []
        while True:
            self.skip_newlines()
            if self.peek().type == 'EOF':
                break
            statements.append(self.parse_statement())
        return Program(statements, line=1)

    def parse_block(self):
        self.skip_newlines()
        open_tok = self.expect('LBRACE', "Expected '{' to start a block")
        saved = self.nl_skip
        self.nl_skip = 0
        body = []
        while True:
            self.skip_newlines()
            tok = self.peek()
            if tok.type == 'EOF':
                raise self.error("Missing closing brace '}' for the block opened here", open_tok)
            if tok.type == 'RBRACE':
                break
            body.append(self.parse_statement())
        self.advance()
        self.nl_skip = saved
        return body

    def parse_statement(self):
        self.skip_newlines()
        tok = self.peek()
        t = tok.type

        if t == 'VAR' or t == 'CONST':
            self.advance()
            name = self.expect('ID', "Expected a variable name after '%s'" % tok.value).value
            value = Literal(None, line=tok.line)
            if self.peek().type == 'ASSIGN':
                self.advance()
                value = self.parse_expression()
            elif t == 'CONST':
                raise self.error("A const needs a value, e.g.  const %s = 10" % name, tok)
            return VarDecl(name, value, t == 'CONST', line=tok.line)

        if t == 'DEF' or (t == 'FN' and self.tokens[self.pos + 1].type == 'ID'):
            self.advance()
            name = self.expect('ID', "Expected a function name").value
            self.expect('LPAREN', "Expected '(' after the function name")
            params = self.parse_params()
            body = self.parse_block()
            return FuncDef(name, params, body, line=tok.line)

        if t == 'IF':
            return self.parse_if()

        if t == 'WHILE':
            self.advance()
            cond = self.parse_expression()
            return While(cond, self.parse_block(), line=tok.line)

        if t == 'FOR':
            return self.parse_for()

        if t == 'RETURN':
            self.advance()
            nxt = self.peek()
            value = None
            if nxt.type not in ('NEWLINE', 'RBRACE', 'EOF'):
                value = self.parse_expression()
            return Return(value, line=tok.line)

        if t == 'BREAK':
            self.advance()
            return Break(line=tok.line)

        if t == 'CONTINUE':
            self.advance()
            return Continue(line=tok.line)

        if t == 'TRY':
            return self.parse_try()

        if t == 'THROW':
            self.advance()
            return Throw(self.parse_expression(), line=tok.line)

        if t == 'IMPORT':
            self.advance()
            path = self.expect('STRING', 'import needs a file name in quotes, e.g.  import "lib/util.japy"')
            return Import(path.value, line=tok.line)

        if t in ('ELSE', 'ELIF'):
            raise self.error("'%s' without a matching 'if'" % tok.value, tok)
        if t in ('CATCH', 'FINALLY'):
            raise self.error("'%s' without a matching 'try'" % tok.value, tok)

        # expression statement or assignment
        expr = self.parse_expression()
        nxt = self.peek()
        if nxt.type == 'ASSIGN' or (nxt.type == 'OP' and nxt.value in AUG_OPS):
            if not isinstance(expr, (Ident, Index, Member)):
                raise self.error("You can only assign to a variable, list item or property", nxt)
            self.advance()
            self.skip_newlines()
            value = self.parse_expression()
            op = '' if nxt.type == 'ASSIGN' else nxt.value[:-1]
            return Assign(expr, op, value, line=tok.line)
        return expr

    def parse_params(self):
        """Parse parameters after '(' up to and including ')'."""
        self.nl_skip += 1
        params = []
        if self.peek().type != 'RPAREN':
            while True:
                name = self.expect('ID', "Expected a parameter name").value
                default = None
                if self.peek().type == 'ASSIGN':
                    self.advance()
                    default = self.parse_expression()
                params.append((name, default))
                if self.peek().type == 'COMMA':
                    self.advance()
                    continue
                break
        self.expect('RPAREN', "Expected ')' to close the parameter list")
        self.nl_skip -= 1
        return params

    def parse_if(self):
        tok = self.advance()                       # IF or ELIF
        cond = self.parse_expression()
        then_body = self.parse_block()
        else_body = None
        saved = self.pos
        self.skip_newlines()
        nxt = self.peek()
        if nxt.type == 'ELIF':
            else_body = [self.parse_if()]
        elif nxt.type == 'ELSE':
            self.advance()
            self.skip_newlines()
            if self.peek().type == 'IF':
                else_body = [self.parse_if()]
            else:
                else_body = self.parse_block()
        else:
            self.pos = saved                       # do not swallow newlines
        return If(cond, then_body, else_body, line=tok.line)

    def parse_for(self):
        tok = self.advance()
        paren = False
        if (self.peek().type == 'LPAREN' and self.tokens[self.pos + 1].type == 'ID'
                and self.tokens[self.pos + 2].type in ('IN', 'COMMA')):
            paren = True
            self.advance()
        names = [self.expect('ID', "Expected a loop variable name after 'for'").value]
        if self.peek().type == 'COMMA':
            self.advance()
            names.append(self.expect('ID', "Expected a second loop variable name").value)
        self.expect('IN', "Expected 'in' in the for loop, e.g.  for i in range(5) { ... }")
        iterable = self.parse_expression()
        if paren:
            self.expect('RPAREN')
        return For(names, iterable, self.parse_block(), line=tok.line)

    def parse_try(self):
        tok = self.advance()
        body = self.parse_block()
        catch_name = catch_body = finally_body = None
        saved = self.pos
        self.skip_newlines()
        if self.peek().type == 'CATCH':
            self.advance()
            if self.peek().type == 'LPAREN':
                self.advance()
                catch_name = self.expect('ID', "Expected a name for the error value").value
                self.expect('RPAREN')
            elif self.peek().type == 'ID':
                catch_name = self.advance().value
            catch_body = self.parse_block()
            saved = self.pos
            self.skip_newlines()
        if self.peek().type == 'FINALLY':
            self.advance()
            finally_body = self.parse_block()
        else:
            self.pos = saved
        if catch_body is None and finally_body is None:
            raise self.error("'try' needs a 'catch' or a 'finally' block", tok)
        return Try(body, catch_name, catch_body, finally_body, line=tok.line)

    # ------------------------------------------------- expressions (low -> high)
    def parse_expression(self):
        self.skip_newlines()
        return self.parse_binary(0)

    # precedence levels, lowest first
    _LEVELS = (('||',), ('&&',), ('==', '!='), ('<', '>', '<=', '>=', 'in'), ('+', '-'), ('*', '/', '%'))

    def parse_binary(self, level):
        if level == len(self._LEVELS):
            return self.parse_unary()
        ops = self._LEVELS[level]
        left = self.parse_binary(level + 1)
        while True:
            tok = self.peek()
            if tok.type in ('OP', 'IN') and tok.value in ops:
                self.advance()
                self.skip_newlines()
                right = self.parse_binary(level + 1)
                left = Binary(tok.value, left, right, line=tok.line)
            else:
                return left

    def parse_unary(self):
        tok = self.peek()
        if tok.type == 'OP' and tok.value in ('-', '!'):
            self.advance()
            return Unary(tok.value, self.parse_unary(), line=tok.line)
        return self.parse_power()

    def parse_power(self):
        base = self.parse_postfix()
        tok = self.peek()
        if tok.type == 'OP' and tok.value == '**':
            self.advance()
            self.skip_newlines()
            return Binary('**', base, self.parse_unary(), line=tok.line)
        return base

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            tok = self.peek()
            if tok.type == 'LPAREN':
                self.advance()
                expr = Call(expr, self.parse_args(), line=tok.line)
            elif tok.type == 'LBRACKET':
                self.advance()
                self.nl_skip += 1
                index = self.parse_expression()
                self.expect('RBRACKET', "Expected ']' to close the index")
                self.nl_skip -= 1
                expr = Index(expr, index, line=tok.line)
            elif tok.type == 'DOT':
                self.advance()
                name = self.peek()
                if name.type != 'ID' and name.type not in KEYWORD_TYPES:
                    raise self.error("Expected a property or method name after '.'", name)
                self.advance()
                expr = Member(expr, name.value, line=tok.line)
            else:
                return expr

    def parse_args(self):
        """Parse call arguments after '(' up to and including ')'."""
        self.nl_skip += 1
        args = []
        if self.peek().type != 'RPAREN':
            args.append(self.parse_expression())
            while self.peek().type == 'COMMA':
                self.advance()
                if self.peek().type == 'RPAREN':     # trailing comma
                    break
                args.append(self.parse_expression())
        self.expect('RPAREN', "Expected ')' to close the call")
        self.nl_skip -= 1
        return args

    def parse_primary(self):
        tok = self.peek()
        t = tok.type

        if t in ('NUMBER', 'STRING'):
            self.advance()
            return Literal(tok.value, line=tok.line)
        if t == 'TRUE':
            self.advance()
            return Literal(True, line=tok.line)
        if t == 'FALSE':
            self.advance()
            return Literal(False, line=tok.line)
        if t == 'NULL':
            self.advance()
            return Literal(None, line=tok.line)
        if t == 'ID':
            self.advance()
            return Ident(tok.value, line=tok.line)

        if t == 'LPAREN':
            self.advance()
            self.nl_skip += 1
            expr = self.parse_expression()
            self.expect('RPAREN', "Expected ')' to close the parenthesis")
            self.nl_skip -= 1
            return expr

        if t == 'LBRACKET':
            self.advance()
            self.nl_skip += 1
            items = []
            if self.peek().type != 'RBRACKET':
                items.append(self.parse_expression())
                while self.peek().type == 'COMMA':
                    self.advance()
                    if self.peek().type == 'RBRACKET':
                        break
                    items.append(self.parse_expression())
            self.expect('RBRACKET', "Expected ']' to close the list")
            self.nl_skip -= 1
            return ListLit(items, line=tok.line)

        if t == 'LBRACE':
            return self.parse_dict()

        if t == 'FN':
            self.advance()
            self.expect('LPAREN', "Expected '(' after 'fn'")
            params = self.parse_params()
            return FuncExpr(params, self.parse_block(), line=tok.line)

        raise self.error("Unexpected %s" % _describe(tok), tok)

    def parse_dict(self):
        open_tok = self.advance()
        self.nl_skip += 1
        pairs = []
        while self.peek().type != 'RBRACE':
            key_tok = self.peek()
            if key_tok.type in ('NUMBER', 'STRING') or key_tok.type == 'ID' or key_tok.type in KEYWORD_TYPES:
                self.advance()
            else:
                raise self.error("Expected a key (a name, text or number) in the dict", key_tok)
            self.expect('COLON', "Expected ':' after the dict key")
            pairs.append((key_tok.value, self.parse_expression()))
            if self.peek().type == 'COMMA':
                self.advance()
            elif self.peek().type != 'RBRACE':
                raise self.error("Expected ',' or '}' in the dict", self.peek())
        self.advance()
        self.nl_skip -= 1
        return DictLit(pairs, line=open_tok.line)
