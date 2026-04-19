from enum import Enum, auto
from typing import Any
class Tokentype(Enum):
    NUMBER = auto()
    PLUS = auto()       #+
    MINUS = auto()      #-
    MULL = auto()       #*
    DIV = auto()        #/
    SEMCOL = auto()     #;
    EQUAL = auto()      #=
    GREATER = auto()    #>
    LESS = auto()       #<
    EE = auto()         #==
    LPAREN = auto()     #(
    RPAREN = auto()     #)
    LBRACE = auto()     #{
    RBRACE = auto()     #}
    EOF = auto()
    ID     = auto()
    IF     = auto()
    ELSE   = auto()
    WHILE  = auto()
    INT    = auto()
    FLOAT  = auto()
    CHAR   = auto()
    DOUBLE = auto()
    FOR    = auto()
    

RESERVED_KEYWORDS = {
    'if':     Tokentype.IF,
    'while':  Tokentype.WHILE,
    'int':    Tokentype.INT,
    'float':  Tokentype.FLOAT,
    'char':   Tokentype.CHAR,
    'double': Tokentype.DOUBLE,
    'else': Tokentype.ELSE,
    'for': Tokentype.FOR
}

class Token:
    def __init__(self,type:Tokentype,value:Any=None):
        self.type=type
        self.value=value

    def __repr__(self):
        if self.value is not None:
            return f"Token({self.type.name},{self.value})"
        return f"Token({self.type.name})"
    
class Lexer:
    def __init__(self,text:str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        if len(self.text)>0:
            self.current_char = self.text[self.pos]
        else:
            self.current_char= None
        

        
    def advance(self):
        if self.current_char == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1
        if self.pos>=len(self.text):
            self.current_char = None
        else:
            self.current_char= self.text[self.pos]
        
    def id(self):
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result = result+self.current_char
            self.advance()
        token_type = RESERVED_KEYWORDS.get(result,Tokentype.ID)
        return Token(token_type,result)
    
    def number(self):
        result=''
        has_dot = False
        while self.current_char is not None and (self.current_char.isdigit() or (self.current_char == "." and not has_dot)):
            if self.current_char == ".":
                has_dot = True
            result = result + self.current_char
            self.advance()
        if has_dot:
            return Token(Tokentype.NUMBER,float(result))
        return Token(Tokentype.NUMBER,int(result))

    def skip_space(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()
    
    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_space()
                continue

            if self.current_char.isalpha() or self.current_char =="_":
                return self.id()
            
            if self.current_char.isdigit():
                return self.number()

            if self.current_char == '+':
                self.advance()
                return Token(Tokentype.PLUS)
            
            if self.current_char == '-':
                self.advance()
                return Token(Tokentype.MINUS)
            
            if self.current_char == '*':
                self.advance()
                return Token(Tokentype.MULL)
            
            if self.current_char == '/':
                self.advance()
                return Token(Tokentype.DIV)
            
            if self.current_char == '(':
                self.advance()
                return Token(Tokentype.LPAREN)
            
            if self.current_char == ')':
                self.advance()
                return Token(Tokentype.RPAREN)
            
            if self.current_char == ';':
                self.advance()
                return Token(Tokentype.SEMCOL)
            
            if self.current_char == '=':
                if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == "=":
                    self.advance()
                    self.advance()
                    return Token(Tokentype.EE)
                self.advance()
                return Token(Tokentype.EQUAL)
            
            if self.current_char == '{':
                self.advance()
                return Token(Tokentype.LBRACE)
            
            if self.current_char == '}':
                self.advance()
                return Token(Tokentype.RBRACE)

            if self.current_char == '>':
                self.advance()
                return Token(Tokentype.GREATER)
            
            if self.current_char == '<':
                self.advance()
                return Token(Tokentype.LESS)
            
            
            raise Exception(f"Lexer error at line {self.line}, col {self.col}: invalid character '{self.current_char}'")
        return Token(Tokentype.EOF)



if __name__ == "__main__":
    code = "int count = 4.3 + 98; " \
    "for(int i =0;i<n;i++)&{}"
    lexer = Lexer(code)
    token = lexer.get_next_token()
    while token.type != Tokentype.EOF:
        print(token)
        token = lexer.get_next_token()

