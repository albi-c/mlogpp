from .lexer import TokenType, Token, Position
from .error import parse_error
from .node import *
from . import functions

class Parser:
    """
    parses token list
    """

    def parse(self, tokens: list):
        """
        parse token list
        """

        self.tokens = tokens
        # current token position
        self.pos = -1

        # create list of generated nodes
        nodes = []
        while self.has_token():
            nodes.append(self.parse_Node())
        
        return 
    
    def has_token(self) -> bool:
        """
        check if token is available
        """

        return self.pos < len(self.tokens) - 1
    
    def current_token(self) -> Token:
        """
        get the current token
        """

        return self.tokens[self.pos]
    
    def next_token(self) -> Token:
        """
        get the next token
        """


    
    def parse_Node(self) -> Node:
        return Node(Position(0, 0, 0, ""))
