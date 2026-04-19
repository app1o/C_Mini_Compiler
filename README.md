# GRAMMAR

program        : statement* EOF

statement      : block 
               | declaration 
               | assignment 
               | if_statement 
               | while_statement 
               | for_statement    
               | comparison SEMCOL

block          : LBRACE statement* RBRACE

## --- THE SPLIT DECLARATION & ASSIGNMENT RULES ---
var_decl : type_keyword ID (EQUAL comparison)?
var_assign     : ID EQUAL comparison

declaration    : var_decl SEMCOL
assignment     : var_assign SEMCOL

## --- THE CONTROL FLOW RULES ---
if_statement   : IF LPAREN comparison RPAREN statement (ELSE statement)?
while_statement: WHILE LPAREN comparison RPAREN statement
for_statement  : FOR LPAREN (var_decl | var_assign)? SEMCOL comparison? SEMCOL var_assign? RPAREN statement

type_keyword   : INT | FLOAT | CHAR | DOUBLE

## --- THE MATH & LOGIC RULES ---
comparison     : expr ((GREATER | LESS | EE) expr)*

expr           : term ((PLUS | MINUS) term)*
term           : factor ((MULL | DIV) factor)*
factor         : NUMBER | ID | LPAREN comparison RPAREN