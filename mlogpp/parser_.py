from .lexer import TokenType, Token, Position
from .error import MlogError, parse_error
from .node import *
from . import functions

from inspect import getframeinfo, stack

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

        # function definition stack for `return`
        self.func_stack = []
        # loop stack for `break/continue`
        self.loop_stack = []
        # loop count for loop names
        self.loop_count = 0

        # create list of generated nodes
        nodes = []
        while self.has_token():
            nodes.append(self.parse_Node())
        
        return CodeListNode(Position(0, 0, 0, ""), nodes)
    
    def loop_name(self) -> str:
        """
        generate an unique loop name
        """

        self.loop_count += 1
        return f"loop{self.loop_count-1}"
    
    def has_token(self, n: int = 1) -> bool:
        """
        check if token is available
        """

        return self.pos < len(self.tokens) - n
    
    def current_token(self) -> Token:
        """
        get the current token
        """

        return self.tokens[self.pos]
    
    def next_token(self, type_: TokenType = None) -> Token:
        """
        get the next token
        """

        if self.has_token():
            self.pos += 1

            tok = self.tokens[self.pos]

            # check type
            if tok.type != type_ and type_ is not None:
                parse_error(tok.pos, "Unexpected token")
            
            return tok
        
        parse_error(self.tokens[-1].pos, "Unexpected EOF")
    
    def lookahead_token(self, type_: TokenType, n: int = 1) -> bool:
        if self.has_token(n):
            return self.tokens[self.pos + n].type == type_
        
        return False

    def parse_funcArgVars(self) -> list:
        """
        parse function argument variables
        """
        
        self.next_token(TokenType.LPAREN)

        args = []
        last = TokenType.LPAREN
        while True:
            tok = self.next_token()

            if tok.type == TokenType.RPAREN:
                if last == TokenType.COMMA:
                    parse_error(tok.pos, "Unexpected token")
                break

            elif tok.type == TokenType.COMMA:
                if last == TokenType.COMMA:
                    parse_error(tok.pos, "Unexpected token")
                last = TokenType.COMMA
                continue
            
            elif tok.type == TokenType.ID:
                if last == TokenType.ID:
                    parse_error(tok.pos, "Unexpected token")
                args.append(tok.value)
            
            else:
                parse_error(tok.pos, "Unexpected token")
            
            last = tok.type
        
        return args
    
    def parse_funcArgVals(self) -> list:
        """
        parse function argument values
        """

        self.next_token(TokenType.LPAREN)

        args = []
        last = TokenType.LPAREN
        while True:
            tok = self.next_token()

            if tok.type == TokenType.RPAREN:
                if last == TokenType.COMMA:
                    parse_error(tok.pos, "Unexpected token")
                break

            elif tok.type == TokenType.COMMA:
                if last == TokenType.COMMA:
                    parse_error(tok.pos, "Unexpected token")
                last = TokenType.COMMA
                continue
            
            else:
                if last == TokenType.ID:
                    parse_error(tok.pos, "Unexpected token")
                last = TokenType.ID
                self.pos -= 1
                args.append(self.parse_Value())
        
        return args
    
    def parse_codeBlock(self) -> list:
        """
        parse a block of code
        """

        self.next_token(TokenType.LBRACE)

        code = []
        while self.has_token():
            if self.lookahead_token(TokenType.RBRACE):
                break

            code.append(self.parse_Node())
        
        self.next_token(TokenType.RBRACE)
        
        return code
    
    def parse_Node(self) -> Node:
        """
        parse any node
        """

        tok = self.next_token()
        if tok.type == TokenType.ID:
            if tok.value == "return":
                # return statement

                # check if in a function
                if len(self.func_stack) == 0:
                    parse_error(tok.pos, "\"return\" has to be used in a function")

                value = self.parse_Value()
                return ReturnNode(tok.pos + value.pos(), self.func_stack[-1], value)
            
            elif tok.value in LoopActionNode.ACTIONS:
                # break/continue statement

                # check if in a loop
                if len(self.loop_stack) == 0:
                    parse_error(tok.pos, f"\"{tok.value}\" has to be used in a function")

                return LoopActionNode(tok.pos, self.loop_stack[-1], tok.value)
            
            elif tok.value == "end":
                # end statement

                return EndNode(tok.pos, False)
            
            elif tok.value == "endr":
                # end reset statement

                return EndNode(tok.pos, True)
            
            elif tok.value == "extern":
                # extern function/variable

                name = self.next_token(TokenType.ID)

                # is a function
                if self.lookahead_token(TokenType.LPAREN):
                    return ExternNode(tok.pos + name.pos, functions.gen_signature(name.value, self.parse_funcArgVars()))
                
                # not a function
                return ExternNode(tok.pos + name.pos, name.value)
            
            # next token
            n = self.next_token()

            if n.type == TokenType.SET:
                # variable assignment

                return AssignmentNode(tok.pos, ValueNode(tok.pos, tok.value), n.value, self.parse_Value())
            
            elif n.type == TokenType.LBRACK:
                # indexed variable assignment
                # TODO: combine with normal assignment

                idx = self.parse_Value()
                self.next_token(TokenType.RBRACK)

                op = self.next_token(TokenType.SET)

                return AssignmentNode(tok.pos, IndexedValueNode(tok.pos, tok.value, idx), op.value, self.parse_Value())
            
            elif n.type == TokenType.LPAREN:
                # keyword or function

                if tok.value in functions.keywords_paren:
                    # is a keyword

                    self.pos -= 2
                    return self.parse_KeywordNode()
                
                # is a function

                self.pos -= 1
                return CallNode(tok.pos, tok.value, self.parse_funcArgVals())
            
            elif n.type == TokenType.ID:
                # function definition

                if tok.value == "function":
                    self.pos -= 2
                    return self.parse_KeywordNode()
                
                parse_error(tok.pos, "Unexpected token")

        parse_error(tok.pos, "Unexpected token")
    
    def parse_Value(self) -> Node:
        """
        parse a value node
        """

        # base node
        left = self.parse_CompExpression()
        # logic operations
        right = []
        while self.has_token():
            tok = self.next_token()

            if tok.type == TokenType.LOGIC and tok.value in ["&&", "||"]:
                right.append((tok.value, self.parse_CompExpression()))

            else:
                self.pos -= 1
                break
        
        return ExpressionNode(left.pos, left, right)
    
    def parse_CompExpression(self) -> Node:
        """
        parse a comparation expression
        """

        # base node
        left = self.parse_ArithExpression()
        # comparation operations
        right = []
        while self.has_token():
            tok = self.next_token()

            if tok.type == TokenType.OPERATOR and tok.value in ["==", "!=", "<", ">", "<=", ">=", "==="]:
                right.append((tok.value, self.parse_ArithExpression()))

            else:
                self.pos -= 1
                break
        
        return CompExpressionNode(left.pos, left, right)
    
    def parse_ArithExpression(self) -> Node:
        """
        parse an arithmetic expression
        """

        # base node
        left = self.parse_Term()
        # arithmetic operations
        right = []
        while self.has_token():
            tok = self.next_token()

            if tok.type == TokenType.OPERATOR and tok.value in ["+", "-"]:
                right.append((tok.value, self.parse_Term()))

            else:
                self.pos -= 1
                break
        
        return ArithExpressionNode(left.pos, left, right)
    
    def parse_Term(self) -> Node:
        """
        parse a term
        """

        # base node
        left = self.parse_Factor()
        # arithmetic operations
        right = []
        while self.has_token():
            tok = self.next_token()

            if tok.type == TokenType.OPERATOR and tok.value in ["*", "/", "**"]:
                right.append((tok.value, self.parse_Factor()))

            else:
                self.pos -= 1
                break
        
        return TermNode(left.pos, left, right)
    
    def parse_Factor(self) -> Node:
        """
        parse a factor
        """

        sign = True
        not_ = False
        flip = False

        while self.has_token():
            tok = self.next_token()

            if tok.type == TokenType.OPERATOR and tok.value in ["+", "-", "!", "~"]:
                if tok.value == "-":
                    # negate

                    sign = not sign
                
                elif tok.value == "!":
                    # not

                    not_ = not not_
                
                elif tok.value == "~":
                    # flip

                    flip = not flip
            
            elif tok.type in [TokenType.ID, TokenType.STRING, TokenType.NUMBER, TokenType.LPAREN, TokenType.SEMICOLON]:
                self.pos -= 1
                return FactorNode(tok.pos, self.parse_Call(), {"sign": sign, "not": not_, "flip": flip})
            
            else:
                parse_error(tok.pos, "Unexpected token")
    
    def parse_Call(self) -> Node:
        """
        parse a call or value
        """

        if self.lookahead_token(TokenType.ID):
            if self.lookahead_token(TokenType.LPAREN, 2):
                # is a function call

                if self.lookahead_token(TokenType.LBRACE, 3):
                    parse_error(self.next_token().pos, "Unexpected token")

                name = self.next_token(TokenType.ID)
                args = self.parse_funcArgVals()

                return CallNode(name.pos, name.value, args)
        
        return self.parse_Atom()
    
    def parse_Atom(self) -> Node:
        """
        parse an atom
        """

        tok = self.next_token()
        
        if tok.type in [TokenType.ID, TokenType.STRING, TokenType.NUMBER]:
            if self.has_token() and tok.type == TokenType.ID:
                if self.lookahead_token(TokenType.LBRACK):
                    # indexed access

                    self.next_token(TokenType.LBRACK)
                    idx = self.parse_Value()
                    self.next_token(TokenType.RBRACK)

                    return IndexedValueNode(tok.pos, tok.value, idx)
            
            return ValueNode(tok.pos, tok.value)
        
        elif tok.type == TokenType.LPAREN:
            val = self.parse_Value()
            self.next_token(TokenType.RPAREN)

            return val
        
        parse_error(tok.pos, "Unexpected token")
    
    def parse_KeywordNode(self) -> Node:
        """
        parse a keyword
        """

        tok = self.next_token(TokenType.ID)

        if tok.value == "if":
            self.next_token(TokenType.LPAREN)
            cond = self.parse_Value()
            self.next_token(TokenType.RPAREN)

            code = self.parse_codeBlock()
            
            # else block code
            elseCode = []
            if self.lookahead_token(TokenType.ID):
                n = self.next_token(TokenType.ID)
                if n.value == "else":
                    elseCode = self.parse_codeBlock()
                else:
                    self.pos -= 1

            return IfNode(tok.pos, cond, CodeListNode(cond, code), CodeListNode(cond, elseCode))
        
        elif tok.value == "while":
            self.next_token(TokenType.LPAREN)
            cond = self.parse_Value()
            self.next_token(TokenType.RPAREN)
            
            name = self.loop_name()
            self.loop_stack.append(name)
            code = self.parse_codeBlock()
            self.loop_stack.pop()

            return WhileNode(tok.pos, name, cond, CodeListNode(cond, code))
        
        elif tok.value == "for":
            self.next_token(TokenType.LPAREN)
            init = self.parse_Node()
            self.next_token(TokenType.SEMICOLON)
            cond = self.parse_Value()
            self.next_token(TokenType.SEMICOLON)
            action = self.parse_Node()
            self.next_token(TokenType.RPAREN)

            name = self.loop_name()
            self.loop_stack.append(name)
            code = self.parse_codeBlock()
            self.loop_stack.pop()

            return ForNode(tok.pos, name, init, cond, action, CodeListNode(action.get_pos(), code))

        elif tok.value == "function":
            name = self.next_token(TokenType.ID)
            args = self.parse_funcArgVars()

            self.func_stack.append(name.value)
            code = self.parse_codeBlock()
            self.func_stack.pop()

            return FunctionNode(tok.pos, name.value, args, CodeListNode(name.pos, code))
        
        parse_error(tok.pos, "Unexpected token")
