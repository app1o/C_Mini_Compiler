from lexer import Tokentype, Token

class ParseError(Exception):
    pass

class AST:
    pass

class Program(AST):
    def __init__(self, statements):
        self.statements = statements

class Block(AST):
    def __init__(self, statements):
        self.statements = statements

class VarDecl(AST):
    def __init__(self, type_node, var_node, expr=None):
        self.type_node = type_node
        self.var_node = var_node
        self.expr = expr

class Assign(AST):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class If(AST):
    def __init__(self, condition, true_stmt, false_stmt=None):
        self.condition = condition
        self.true_stmt = true_stmt
        self.false_stmt = false_stmt

class While(AST):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class For(AST):
    def __init__(self, init, condition, increment, body):
        self.init = init
        self.condition = condition
        self.increment = increment
        self.body = body

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right

class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.errors = []
        self.current_token = None
        self.next_token = None
        
        # safely seed the token buffer
        self.advance_token()
        self.advance_token()

    def advance_token(self):
        self.current_token = self.next_token
        try:
            self.next_token = self.lexer.get_next_token()
        except Exception as e:
            self.errors.append(f"Lexer Error: {str(e)}")
            self.next_token = Token(Tokentype.EOF) # Stop early on lexer error

    def error(self, msg="Invalid syntax"):
        error_msg = f"Parser error: {msg} at token {self.current_token}"
        self.errors.append(error_msg)
        raise ParseError(error_msg)

    def eat(self, token_type):
        if self.current_token and self.current_token.type == token_type:
            self.advance_token()
        else:
            self.error(f"Expected {token_type.name}, got {self.current_token.type.name if self.current_token else 'None'}")

    def synchronize(self):
        # Panic mode error recovery - advance past the problematic token
        if getattr(self.current_token, 'type', None) != Tokentype.EOF:
            self.advance_token()
            
        while getattr(self.current_token, 'type', None) != Tokentype.EOF:
            # We naturally stop if we hit a statement terminator
            if getattr(self.current_token, 'type', None) == Tokentype.SEMCOL:
                self.advance_token()
                return
            
            # Or if we spot the beginning of a fresh statement
            if getattr(self.current_token, 'type', None) in (
                Tokentype.INT, Tokentype.FLOAT, Tokentype.CHAR, Tokentype.DOUBLE,
                Tokentype.IF, Tokentype.WHILE, Tokentype.FOR, Tokentype.RBRACE, Tokentype.LBRACE
            ):
                return
                
            self.advance_token()

    def parse(self):
        return self.program()

    # program : statement* EOF
    def program(self):
        statements = []
        while getattr(self.current_token, 'type', None) != Tokentype.EOF:
            try:
                statements.append(self.statement())
            except ParseError:
                self.synchronize()
        return Program(statements)

    # statement : block | declaration | assignment | if_statement | while_statement | for_statement | comparison SEMCOL
    def statement(self):
        if self.current_token.type == Tokentype.LBRACE:
            return self.block()
        elif self.current_token.type in (Tokentype.INT, Tokentype.FLOAT, Tokentype.CHAR, Tokentype.DOUBLE):
            return self.declaration()
        elif self.current_token.type == Tokentype.IF:
            return self.if_statement()
        elif self.current_token.type == Tokentype.WHILE:
            return self.while_statement()
        elif self.current_token.type == Tokentype.FOR:
            return self.for_statement()
        elif self.current_token.type == Tokentype.ID and self.next_token.type == Tokentype.EQUAL:
            return self.assignment()
        else:
            comp = self.comparison()
            self.eat(Tokentype.SEMCOL)
            return comp

    # block : LBRACE statement* RBRACE
    def block(self):
        self.eat(Tokentype.LBRACE)
        statements = []
        while self.current_token and self.current_token.type not in (Tokentype.RBRACE, Tokentype.EOF):
            try:
                statements.append(self.statement())
            except ParseError:
                self.synchronize()
        self.eat(Tokentype.RBRACE)
        return Block(statements)

    # declaration : var_decl SEMCOL
    def declaration(self):
        node = self.var_decl()
        self.eat(Tokentype.SEMCOL)
        return node

    # assignment : var_assign SEMCOL
    def assignment(self):
        node = self.var_assign()
        self.eat(Tokentype.SEMCOL)
        return node

    # var_decl : type_keyword ID (EQUAL comparison)?
    def var_decl(self):
        type_node = self.type_keyword()
        if self.current_token.type != Tokentype.ID:
            self.error("Expected ID after type keyword")
        var_node = Var(self.current_token)
        self.eat(Tokentype.ID)
        
        expr = None
        if self.current_token.type == Tokentype.EQUAL:
            self.eat(Tokentype.EQUAL)
            expr = self.comparison()
            
        return VarDecl(type_node, var_node, expr)

    # var_assign : ID EQUAL comparison
    def var_assign(self):
        if self.current_token.type != Tokentype.ID:
            self.error("Expected ID for assignment")
        var_node = Var(self.current_token)
        self.eat(Tokentype.ID)
        self.eat(Tokentype.EQUAL)
        expr = self.comparison()
        return Assign(var_node, expr)

    # if_statement : IF LPAREN comparison RPAREN statement (ELSE statement)?
    def if_statement(self):
        self.eat(Tokentype.IF)
        self.eat(Tokentype.LPAREN)
        cond = self.comparison()
        self.eat(Tokentype.RPAREN)
        true_stmt = self.statement()
        false_stmt = None
        if self.current_token.type == Tokentype.ELSE:
            self.eat(Tokentype.ELSE)
            false_stmt = self.statement()
        return If(cond, true_stmt, false_stmt)

    # while_statement: WHILE LPAREN comparison RPAREN statement
    def while_statement(self):
        self.eat(Tokentype.WHILE)
        self.eat(Tokentype.LPAREN)
        cond = self.comparison()
        self.eat(Tokentype.RPAREN)
        body = self.statement()
        return While(cond, body)

    # for_statement : FOR LPAREN (var_decl | var_assign)? SEMCOL comparison? SEMCOL var_assign? RPAREN statement
    def for_statement(self):
        self.eat(Tokentype.FOR)
        self.eat(Tokentype.LPAREN)
        
        init = None
        if getattr(self.current_token, 'type', None) in (Tokentype.INT, Tokentype.FLOAT, Tokentype.CHAR, Tokentype.DOUBLE):
            init = self.var_decl()
        elif getattr(self.current_token, 'type', None) == Tokentype.ID and getattr(self.next_token, 'type', None) == Tokentype.EQUAL:
            init = self.var_assign()
            
        self.eat(Tokentype.SEMCOL)
        
        cond = None
        if getattr(self.current_token, 'type', None) != Tokentype.SEMCOL:
            cond = self.comparison()
            
        self.eat(Tokentype.SEMCOL)
        
        inc = None
        if getattr(self.current_token, 'type', None) == Tokentype.ID and getattr(self.next_token, 'type', None) == Tokentype.EQUAL:
            inc = self.var_assign()
            
        self.eat(Tokentype.RPAREN)
        body = self.statement()
        return For(init, cond, inc, body)

    # type_keyword : INT | FLOAT | CHAR | DOUBLE
    def type_keyword(self):
        if getattr(self.current_token, 'type', None) in (Tokentype.INT, Tokentype.FLOAT, Tokentype.CHAR, Tokentype.DOUBLE):
            type_token = self.current_token
            self.eat(self.current_token.type)
            return type_token
        else:
            self.error("Expected type keyword (int, float, char, double)")

    # comparison : expr ((GREATER | LESS | EE) expr)*
    def comparison(self):
        node = self.expr()
        while getattr(self.current_token, 'type', None) in (Tokentype.GREATER, Tokentype.LESS, Tokentype.EE):
            token = self.current_token
            self.eat(token.type)
            node = BinOp(left=node, op=token, right=self.expr())
        return node
        
    # expr : term ((PLUS | MINUS) term)*
    def expr(self):
        node = self.term()
        while getattr(self.current_token, 'type', None) in (Tokentype.PLUS, Tokentype.MINUS):
            token = self.current_token
            self.eat(token.type)
            node = BinOp(left=node, op=token, right=self.term())
        return node

    # term : factor ((MULT | DIV) factor)*
    def term(self):
        node = self.factor()
        while getattr(self.current_token, 'type', None) in (Tokentype.MULT, Tokentype.DIV):
            token = self.current_token
            self.eat(token.type)
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    # factor : NUMBER | ID | LPAREN comparison RPAREN
    def factor(self):
        token = self.current_token
        if not token:
            self.error("Unexpected EOF")
        if token.type == Tokentype.NUMBER:
            self.eat(Tokentype.NUMBER)
            return Num(token)
        elif token.type == Tokentype.ID:
            self.eat(Tokentype.ID)
            return Var(token)
        elif token.type == Tokentype.LPAREN:
            self.eat(Tokentype.LPAREN)
            node = self.comparison()
            self.eat(Tokentype.RPAREN)
            return node
        elif token.type == Tokentype.MINUS:
            self.eat(Tokentype.MINUS)
            node = self.factor()
            return UnaryOp(op=token, expr=node)
        else:
            self.error(f"Expected NUMBER, ID, or '(' but got {token.type.name}")
