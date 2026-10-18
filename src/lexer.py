"""Japy lexer: turns source text into tokens with line/column information."""
import re

from .errors import JapySyntaxError

KEYWORDS = {
    'var': 'VAR', 'let': 'VAR', 'const': 'CONST',
    'def': 'DEF', 'fn': 'FN',
    'if': 'IF', 'elif': 'ELIF', 'else': 'ELSE',
    'while': 'WHILE', 'for': 'FOR', 'in': 'IN',
    'break': 'BREAK', 'continue': 'CONTINUE', 'return': 'RETURN',
    'try': 'TRY', 'catch': 'CATCH', 'finally': 'FINALLY', 'throw': 'THROW',
    'import': 'IMPORT',
    'true': 'TRUE', 'false': 'FALSE', 'null': 'NULL',
}
KEYWORD_TYPES = frozenset(KEYWORDS.values())

# Word operators are converted to their symbol form.
WORD_OPS = {'and': '&&', 'or': '||', 'not': '!'}

_ESCAPES = {'n': '\n', 't': '\t', 'r': '\r', '0': '\0',
            '\\': '\\', '"': '"', "'": "'"}


class JapyToken(object):
    __slots__ = ('type', 'value', 'line', 'col')

    def __init__(self, type_, value, line=0, col=0):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return "Token(%s, %r, line %d)" % (self.type, self.value, self.line)


def _unescape(body):
    if '\\' not in body:
        return body
    out = []
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == '\\' and i + 1 < len(body):
            nxt = body[i + 1]
            out.append(_ESCAPES.get(nxt, '\\' + nxt))
            i += 2
        else:
            out.append(ch)
            i += 1
    return ''.join(out)


class JapyLexer(object):
    def __init__(self):
        specs = [
            ('BLOCKCOMMENT', r'/\*.*?\*/'),
            ('BADCOMMENT',   r'/\*'),
            ('COMMENT',      r'(?:#|//)[^\n]*'),
            ('NUMBER',       r'0[xX][0-9a-fA-F]+|\d+\.\d+|\d+'),
            ('STRING',       r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\''),
            ('BADSTRING',    r'["\']'),
            ('ID',           r'[A-Za-z_][A-Za-z0-9_]*'),
            ('OP',           r'==|!=|<=|>=|&&|\|\||\*\*|\+=|-=|\*=|/=|%=|[+\-*/%<>!]'),
            ('ASSIGN',       r'='),
            ('LBRACE',       r'\{'),
            ('RBRACE',       r'\}'),
            ('LPAREN',       r'\('),
            ('RPAREN',       r'\)'),
            ('LBRACKET',     r'\['),
            ('RBRACKET',     r'\]'),
            ('COLON',        r':'),
            ('COMMA',        r','),
            ('DOT',          r'\.'),
            ('NEWLINE',      r'\n'),
            ('SKIP',         r'[ \t\r;\ufeff\u00a0]+'),
            ('MISMATCH',     r'.'),
        ]
        self.regex = re.compile(
            '|'.join('(?P<%s>%s)' % (name, pat) for name, pat in specs), re.DOTALL)

    def tokenize(self, source):
        tokens = []
        line = 1
        line_start = 0
        for m in self.regex.finditer(source):
            kind = m.lastgroup
            text = m.group(kind)
            col = m.start() - line_start + 1

            if kind == 'SKIP' or kind == 'COMMENT':
                continue
            if kind == 'BLOCKCOMMENT':
                newlines = text.count('\n')
                if newlines:
                    line += newlines
                    line_start = m.start() + text.rfind('\n') + 1
                continue
            if kind == 'NEWLINE':
                tokens.append(JapyToken('NEWLINE', '\n', line, col))
                line += 1
                line_start = m.end()
                continue
            if kind == 'BADCOMMENT':
                raise JapySyntaxError("Comment starting with /* is never closed", line, col)
            if kind == 'BADSTRING':
                raise JapySyntaxError("Text in quotes is not closed on the same line", line, col)
            if kind == 'MISMATCH':
                raise JapySyntaxError("Unexpected character %r" % text, line, col)

            value = text
            if kind == 'NUMBER':
                if text[:2] in ('0x', '0X'):
                    value = int(text, 16)
                elif '.' in text:
                    value = float(text)
                else:
                    value = int(text)
            elif kind == 'STRING':
                value = _unescape(text[1:-1])
            elif kind == 'ID':
                if text in KEYWORDS:
                    kind = KEYWORDS[text]
                elif text in WORD_OPS:
                    kind = 'OP'
                    value = WORD_OPS[text]
            tokens.append(JapyToken(kind, value, line, col))

        tokens.append(JapyToken('EOF', '', line, 1))
        return tokens
