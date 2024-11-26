from dataclasses import dataclass
from typing import Optional, Union, Dict, Any
from flask import Flask, render_template, request, jsonify
from lark import Lark, Transformer, v_args
from ply import lex
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

MATH_GRAMMAR = """
    ?start: expr
    ?expr: term
        | expr "+" term   -> addition
        | expr "-" term   -> subtraction
    ?term: factor
        | term "*" factor -> multiplication
        | term "/" factor -> division
    ?factor: NUMBER       -> number
        | "(" expr ")"
    %import common.NUMBER
    %import common.WS
    %ignore WS
"""

@dataclass
class Node:
    value: Union[float, str]
    left: Optional['Node'] = None
    right: Optional['Node'] = None

class MathExpressionParser(Transformer):
    @v_args(inline=True)
    def number(self, n: str) -> Node:
        return Node(float(n))
    
    def _create_operation_node(self, args: list, operator: str) -> Node:
        return Node(operator, args[0], args[1])
    
    def addition(self, args: list) -> Node:
        return self._create_operation_node(args, '+')
    
    def subtraction(self, args: list) -> Node:
        return self._create_operation_node(args, '-')
    
    def multiplication(self, args: list) -> Node:
        return self._create_operation_node(args, '*')
    
    def division(self, args: list) -> Node:
        return self._create_operation_node(args, '/')

# Definición de tokens
tokens = (
    'NUMBER',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
    'DECIMAL'
)

# Reglas para tokens
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'

def t_NUMBER(t):
    r'\d+'
    t.value = float(t.value)
    return t

def t_DECIMAL(t):
    r'\.'
    return t

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

t_ignore = ' \t'

class ExpressionEvaluator:
    def __init__(self):
        self.parser = Lark(MATH_GRAMMAR, parser='lalr', transformer=MathExpressionParser())
        self.lexer = lex.lex()
        self.stored_value = None
    
    def get_tokens(self, expression):
        self.lexer.input(expression)
        tokens_list = []
        token_counts = {
            'números': 0,
            'operadores': 0,
            'decimales': 0
        }
        
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            tokens_list.append({
                'tipo': tok.type,
                'valor': tok.value
            })
            
            if tok.type == 'NUMBER':
                token_counts['números'] += 1
            elif tok.type in ['PLUS', 'MINUS', 'TIMES', 'DIVIDE']:
                token_counts['operadores'] += 1
            elif tok.type == 'DECIMAL':
                token_counts['decimales'] += 1
                
        return tokens_list, token_counts
    
    def parse_expression(self, expression: str) -> Dict[str, Any]:
        try:
            tokens_list, token_counts = self.get_tokens(expression)
            tree = self.parser.parse(expression)
            result = eval(expression)
            return {
                "result": result,
                "tree": tree,
                "tokens": tokens_list,
                "token_counts": token_counts
            }
        except Exception as e:
            return {"error": str(e)}
    
    def store_result(self, value):
        self.stored_value = value
    
    def get_stored_value(self):
        return self.stored_value

class MathAPI:
    def __init__(self):
        self.evaluator = ExpressionEvaluator()
    
    def process_request(self, expression: str) -> Dict[str, Any]:
        return self.evaluator.parse_expression(expression)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        expression = request.form.get("expression")
        math_api = MathAPI()
        return jsonify(math_api.process_request(expression))
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)