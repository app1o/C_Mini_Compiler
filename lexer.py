from enum import Enum, auto

class Tokentype(Enum):
    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    MULL = auto()
    DIV = auto()
    SEMCOL = auto()
    EQUAL = auto()
    LPAREN = auto()
    RPAREN = auto()
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
    def __init__(self,type:Tokentype,value:any=None):
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
        if len(self.text)>0:
            self.current_char = self.text[self.pos]
        else:
            self.current_char= None
        
    def advance(self):
        self.pos += 1
        if self.pos>=len(self.text):
            self.current_char = None
        else:
            self.current_char= self.text[self.pos]
        
    def id(self):
        result = ''
        while self.current_char is not None and self.current_char.isalnum():
            result = result+self.current_char
            self.advance()
        token_type = RESERVED_KEYWORDS.get(result,Tokentype.ID)
        return Token(token_type,result)
    
    def number(self):
        result=''
        while self.current_char is not None and self.current_char.isdigit():
            result = result + self.current_char
            self.advance()
        return Token(Tokentype.NUMBER,int(result))

    def skip_space(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()
    
    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_space()
                continue

            if self.current_char.isalpha():
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
                self.advance()
                return Token(Tokentype.EQUAL)
            
            raise Exception(f"Lexer error : invalid character {self.current_char}")
        return Token(Tokentype.EOF)



if __name__ == "__main__":
    code = "int count = 43 + 98;"
    lexer = Lexer(code)
    token = lexer.get_next_token()
    while token.type != Tokentype.EOF:
        print(token)
        token = lexer.get_next_token()

