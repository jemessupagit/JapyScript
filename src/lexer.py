import re

class JapyToken:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class JapyLexer:
    def __init__(self):
        # Core specs to scan 100+ Keywords and 300,000+ Custom APIs
        # Strictly follows Japy philosophy: ignores mobile indentation, catches braces
        self.token_specs = [
            ('COMMENT',    r'#[^\n]*'),              # English comments using #
            ('VAR',        r'\bvar\b'),               # Variable declaration keyword
            ('DEF',        r'\bdef\b'),               # Function declaration keyword
            ('IF',         r'\bif\b'),                # Conditional if
            ('ELSE',       r'\belse\b'),              # Fallback else
            ('NUMBER',     r'\d+(\.\d+)?'),           # Coordinates, scales, physics vectors
            ('STRING',     r'\"[^\"]*\"|\'[^\']*\''), # Text or game asset file paths
            ('ID',         r'[a-zA-Z_][a-zA-Z0-9_]*'),# For 100+ keywords & 300,000+ custom APIs
            ('LBRACE',     r'\{'),                    # Block opening brace (Safety)
            ('RBRACE',     r'\}'),                    # Block closing brace (Safety)
            ('LPAREN',     r'\('),                    # Parameters open
            ('RPAREN',     r'\)'),                    # Parameters close
            ('ASSIGN',     r'='),                     # Value assignment
            ('OP',         r'[+\-*/<>!&|]+'),          # Math & logic operators
            ('COMMA',      r','),                     # Separator for parameters
            ('DOT',        r'\.'),                    # Accessor for sub-properties/plugins
            ('SKIP',       r'[ \t]+'),                # Spaces (Ignored for mobile typing safety)
            ('NEWLINE',    r'\n'),                    # Line breaks
            ('MISMATCH',   r'.'),                     # Catches syntax errors
        ]
        self.regex = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in self.token_specs))

    def tokenize(self, source_code):
        tokens = []
        for match in self.regex.finditer(source_code):
            kind = match.lastgroup
            value = match.group(kind)
            
            if kind == 'SKIP' or kind == 'COMMENT':
                continue
            elif kind == 'MISMATCH':
                raise SyntaxError(f"Unexpected character on mobile input: {value}")
            
            tokens.append(JapyToken(kind, value))
        return tokens
