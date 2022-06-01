from .lexer import TokenType, Token, Position
from .error import parse_error
from . import functions

class Node:
    """
    base node class
    """

class AST(Node):
    """
    root node for the AST
    """

    def __init__(self, code: list):
        self.code = code
    
    def rrename(self, vars_: dict):
        return AST([n.rrename(vars_) for n in self.code])

class CodeNode(Node):
    """
    node with a list of nodes
    """

    def __init__(self, pos: Position, code: list):
        self.pos = pos
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return CodeNode(self.pos, [n.rrename(vars_) for n in self.code])

class ValueNode(Node):
    """
    node with a value
    """

    def __init__(self, pos: Position, value: str):
        self.pos = pos
        self.value = value
    
    def rrename(self, vars_: dict) -> Node:
        if "." in self.value:
            spl = self.value.split(".")
            if len(spl) == 2:
                return ValueNode(self.pos, vars_.get(spl[0], spl[0]) + "." + spl[1])
        
        return ValueNode(self.pos, vars_.get(self.value, self.value))

class IndexNode(Node):
    """
    indexed reading node
    """

    def __init__(self, pos: Position, var: str, index: Node):
        self.pos = pos
        self.var = var
        self.index = index
    
    def rrename(self, vars_: dict) -> Node:
        return IndexNode(self.pos, vars_.get(self.var, self.var), self.index.rrename(vars_))

class IndexAssignNode(Node):
    """
    indexed writing node
    """

    def __init__(self, pos: Position, var: str, index: Node, atype: str, val: Node):
        self.pos = pos
        self.var = var
        self.index = index
        self.atype = atype
        self.val = val
    
    def rrename(self, vars_: dict) -> Node:
        return IndexNode(self.pos, vars_.get(self.var, self.var), self.index.rrename(vars_), self.atype, self.val.rrename(vars_))

class AtomNode(Node):
    """
    atomic value node
    """

    def __init__(self, pos: Position, value):
        self.pos = pos
        self.value = value
    
    def rrename(self, vars_: dict) -> Node:
        return self.value.rrename(vars_)

class AssignmentNode(Node):
    """
    node with an assignment
    """

    def __init__(self, pos: Position, left: str, atype: str, right: Node):
        self.pos = pos
        self.left = left
        self.atype = atype
        self.right = right
    
    def rrename(self, vars_: dict) -> Node:
        return AssignmentNode(self.pos, vars_.get(self.left, self.left), self.atype, self.right.rrename(vars_))

class ExpressionNode(Node):
    """
    node with an expression
    """

    def __init__(self, pos: Position, left, right = None):
        self.pos = pos
        self.left = left
        self.right = right
    
    def rrename(self, vars_: dict) -> Node:
        return ExpressionNode(self.pos, self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class CompExpressionNode(Node):
    """
    node with a comp expression
    """

    def __init__(self, pos: Position, left, right = None):
        self.pos = pos
        self.left = left
        self.right = right
    
    def rrename(self, vars_: dict) -> Node:
        return CompExpressionNode(self.pos, self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class ArithExpNode(Node):
    """
    node with an arithmetic expression
    """

    def __init__(self, pos: Position, left, right = None):
        self.pos = pos
        self.left = left
        self.right = right
    
    def rrename(self, vars_: dict) -> Node:
        return ArithExpNode(self.pos, self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class TermNode(Node):
    """
    node with a term
    """

    def __init__(self, pos: Position, left, right = None):
        self.pos = pos
        self.left = left
        self.right = right
    
    def rrename(self, vars_: dict) -> Node:
        return TermNode(self.pos, self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class FactorNode(Node):
    """
    node with a factor
    """

    def __init__(self, pos: Position, left, sign: bool, not_: bool):
        self.pos = pos
        self.left = left
        self.sign = sign
        self.not_ = not_
    
    def rrename(self, vars_: dict) -> Node:
        return FactorNode(self.pos, self.left.rrename(vars_), self.sign, self.not_)

class CallNode(Node):
    """
    call node
    """

    def __init__(self, pos: Position, function, is_call: bool, params: list = []):
        self.pos = pos
        self.function = function
        self.is_call = is_call
        self.params = params
    
    def rrename(self, vars_: dict) -> Node:
        return CallNode(self.pos, self.function if type(self.function) == str else self.function.rrename(vars_), self.is_call, [n.rrename(vars_) for n in self.params])

class SubCallNode(Node):
    """
    subcommand call node
    """

    def __init__(self, pos: Position, function: str, params: list = []):
        self.pos = pos
        self.function = function
        self.params = params
    
    def rrename(self, vars_: dict) -> Node:
        return SubCallNode(self.pos, self.function, [n.rrename(vars_) for n in self.params])


class KeywordNode(Node):
    """
    base keyword node
    """

    def __init__(self):
        pass

class IfNode(KeywordNode):
    """
    if expression node
    """

    def __init__(self, pos: Position, condition: ExpressionNode, code: list, elsecode: list = None):
        self.pos = pos
        self.condition = condition
        self.code = code
        self.elsecode = elsecode if elsecode is not None else []
    
    def rrename(self, vars_: dict) -> Node:
        return IfNode(self.pos, self.condition.rrename(vars_), [n.rrename(vars_) for n in self.code], [n.rrename(vars_) for n in self.elsecode])

class WhileNode(KeywordNode):
    """
    while expression node
    """
    
    def __init__(self, pos: Position, condition: ExpressionNode, code: list):
        self.pos = pos
        self.condition = condition
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return WhileNode(self.pos, self.condition.rrename(vars_), [n.rrename(vars_) for n in self.code])

class ForNode(KeywordNode):
    """
    for expression node
    """
    
    def __init__(self, pos: Position, init: Node, condition: ExpressionNode, action: Node, code: list):
        self.pos = pos
        self.init = init
        self.condition = condition
        self.action = action
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return ForNode(self.pos, self.init.rrename(vars_), self.condition.rrename(vars_), self.action.rrename(vars_), [n.rrename(vars_) for n in self.code])

class FunctionNode(KeywordNode):
    """
    function expression node
    """
    
    def __init__(self, pos: Position, name: str, args: list, code: list):
        self.pos = pos
        self.name = name
        self.args = args
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return FunctionNode(self.pos, self.name, self.args, [n.rrename(vars_) for n in self.code])

class RepeatNode(KeywordNode):
    """
    repeat expression node
    """
    
    def __init__(self, pos: Position, amount: int, code: list):
        self.pos = pos
        self.amount = amount
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return RepeatNode(self.pos, self.amount, [n.rrename(vars_) for n in self.code])

class NativeNode(KeywordNode):
    """
    native expression node
    """
    
    def __init__(self, pos: Position, code: str):
        self.pos = pos
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return NativeNode(self.pos, self.code)

class ReturnNode(KeywordNode):
    """
    return statement node
    """
    
    def __init__(self, pos: Position, value):
        self.pos = pos
        self.value = value
    
    def rrename(self, vars_: dict) -> Node:
        return ReturnNode(self.pos, self.value.rrename(vars_))

class LoopActionNode(KeywordNode):
    """
    break/continue statement node
    """
    
    def __init__(self, pos: Position, action: str):
        self.pos = pos
        self.action = action
    
    def rrename(self, vars_: dict) -> Node:
        return LoopActionNode(self.pos, self.action)

class ExternNode(KeywordNode):
    """
    extern function expression node
    """

    def __init__(self, pos: Position, name: str):
        self.pos = pos
        self.name = name
    
    def rrename(self, vars_: dict) -> Node:
        return ExternNode(self.pos, self.name)

class Parser:
    """
    parses tokenized code
    """

    def parse(self, tokens: list) -> CodeNode:
        """
        parse tokenized code
        """

        # list of tokens
        self.tokens = tokens
        # current token pointer
        self.pos = -1

        # list of generated nodes
        nodes = []
        while self.has_token():
            nodes.append(self.parse_AnyNode())

        return AST(nodes)
    
    def has_token(self) -> bool:
        """
        check if token is available
        """

        return self.pos < len(self.tokens) - 1
    
    def curr_token(self) -> Token:
        """
        return the current token
        """

        return self.tokens[self.pos]
    
    def next_token(self, ttype=None) -> Token:
        """
        get the next token
        """

        # check if available
        if self.has_token():
            self.pos += 1
            
            # type checking
            if self.tokens[self.pos].type != ttype and ttype is not None:
                parse_error(self.tokens[self.pos], "Unexpected token")

            return self.tokens[self.pos]
        
        parse_error(self.tokens[-1], "Unexpected EOF")
    
    def parse_AnyNode(self, can_be_special=True) -> Node:
        """
        parses any node
        """

        id_ = self.next_token()
        if id_.type == TokenType.ID:
            # next token is an id

            n = self.next_token()

            if id_.value == "return":
                # return statement

                self.pos -= 1
                return ReturnNode(id_.pos(), self.parse_ExpressionNode())

            elif id_.value in ["break", "continue"]:
                # break/continue statement

                self.pos -= 1
                return LoopActionNode(id_.pos(), id_.value)

            elif id_.value == "extern":
                # extern function expression

                if n.type != TokenType.ID:
                    parse_error(n, "Unexpected token")
                
                # read list of parameters
                n_ = self.next_token()
                if n_.type == TokenType.LPAREN:
                    args = []
                    last = TokenType.LPAREN
                    n__ = n
                    while True:
                        n = self.next_token()
                        if n.type == TokenType.RPAREN:
                            if last == TokenType.COMMA:
                                parse_error(n, "Unexpected token")
                            break

                        elif n.type == TokenType.COMMA:
                            if last == TokenType.COMMA:
                                parse_error(n, "Unexpected token")
                            pass

                        elif n.type == TokenType.ID:
                            if last == TokenType.ID:
                                parse_error(n, "Unexpected token")
                            args.append(n.value)

                    return ExternNode(id_.pos(), functions.gen_signature(n__.value, args))
                
                self.pos -= 1
                return ExternNode(id_.pos(), n.value)
            
            if n.type == TokenType.SET:
                # variable assignment

                # check if id is a special keyword
                if id_.value in functions.special:
                    parse_error(n, "Cannot override a keyword")
                
                return AssignmentNode(id_.pos(), id_.value, n.value, self.parse_ExpressionNode())

            elif n.type == TokenType.DOT:
                # native subcommand or property assignment

                if id_.value in functions.native_sub:
                    # native subcommand

                    n_ = self.next_token(TokenType.ID)
                    
                    # check if subcommand is valid
                    if not n_.value in functions.native_sub[id_.value]:
                        parse_error(n_, "Invalid subcommand")

                    self.next_token(TokenType.LPAREN)

                    # read parameter list
                    e = False
                    p = []
                    while True:
                        t = self.next_token()
                        if t.type == TokenType.RPAREN:
                            break

                        elif t.type == TokenType.COMMA:
                            if e:
                                p.append(self.parse_ExpressionNode())
                            else:
                                parse_error(t, "Unexpected token")

                        else:
                            if not e:
                                self.pos -= 1
                                p.append(self.parse_ExpressionNode())
                                e = True

                            else:
                                parse_error(t, "Unexpected token")
                    
                    return SubCallNode(id_.pos(), f"{id_.value}.{n_.value}", p)

                # check if id is a special keyword
                if id_.value in functions.special:
                    parse_error(n, "Cannot use property of a keyword")

                # parse rest of assignment
                node = self.parse_AnyNode()
                if type(node) != AssignmentNode:
                    parse_error(n, "Unexpected token")
                
                # add variable and dot to left of the assignment node
                node.left = id_.value + "." + node.left

                return node

            elif n.type == TokenType.LBRACK:
                # indexed assignment

                # check if id is a special keyword
                if id_.value in functions.special:
                    parse_error(n, "Cannot use keyword as a memory cell")
                
                # parse index
                node = self.parse_ExpressionNode()

                self.next_token(TokenType.RBRACK)
                a = self.next_token(TokenType.SET)

                # parse value
                val = self.parse_ExpressionNode()

                return IndexAssignNode(id_.pos(), id_.value, node, a.value, val)

            elif n.type == TokenType.LPAREN:
                # function call
                
                # check if id is a special keyword
                if id_.value in functions.keywords:
                    if not can_be_special:
                        parse_error(id_, "Unexpected token")
                    
                    self.pos -= 2
                    return self.parse_KeywordNode()

                else:
                    e = False
                    p = []
                    while True:
                        t = self.next_token()
                        if t.type == TokenType.RPAREN:
                            break

                        elif t.type == TokenType.COMMA:
                            if e:
                                p.append(self.parse_ExpressionNode())
                            else:
                                parse_error(t, "Unexpected token")

                        else:
                            if not e:
                                self.pos -= 1
                                p.append(self.parse_ExpressionNode())
                                e = True

                            else:
                                parse_error(t, "Unexpected token")
                    
                    return CallNode(id_.pos(), id_.value, True, p)

            elif n.type == TokenType.ID:
                # function definition

                if id_.value == "function":
                    self.pos -= 2
                    return self.parse_KeywordNode()

                else:
                    parse_error(n, "Unexpected token")

            elif n.type == TokenType.LBRACE:
                # else statement

                if id_.value == "else":
                    self.pos -= 2
                    return self.parse_KeywordNode()

                else:
                     parse_error(n, "Unexpected token")

            else:
                parse_error(n, "Unexpected token")

        elif id_.type == TokenType.DOT:
            # native code

            n = self.next_token(TokenType.STRING)

            return NativeNode(id_.pos(), n.value[1:-1])
        
        parse_error(id_, "Unexpected token")
    
    def parse_ExpressionNode(self) -> ExpressionNode:
        c = self.parse_CompExpressionNode()
        l = []
        while self.has_token():
            n = self.next_token()
            if n.type == TokenType.LOGIC and n.value in ["&&", "||"]:
                l.append((n.value, self.parse_CompExpressionNode()))
            else:
                self.pos -= 1
                break
        
        return ExpressionNode(c.pos, c, l if len(l) > 0 else None)

    def parse_CompExpressionNode(self) -> CompExpressionNode:
        e = self.parse_ArithExpNode()
        c = []
        while self.has_token():
            n = self.next_token()
            if n.type == TokenType.OPERATOR and n.value in ["==", "!=", "<", ">", "<=", ">=", "==="]:
                c.append((n.value, self.parse_ArithExpNode()))
            else:
                self.pos -= 1
                break
        
        return CompExpressionNode(e.pos, e, c if len(c) > 0 else None)
    
    def parse_ArithExpNode(self) -> ArithExpNode:
        t = self.parse_TermNode()
        a = []
        while self.has_token():
            n = self.next_token()
            if n.type == TokenType.OPERATOR and n.value in ["+", "-"]:
                a.append((n.value, self.parse_TermNode()))
            else:
                self.pos -= 1
                break
        
        return ArithExpNode(t.pos, t, a if len(a) > 0 else None)
    
    def parse_TermNode(self) -> TermNode:
        f = self.parse_FactorNode()
        m = []
        while self.has_token():
            n = self.next_token()
            if n.type == TokenType.OPERATOR and n.value in ["*", "/", "**"]:
                m.append((n.value, self.parse_FactorNode()))
            else:
                self.pos -= 1
                break
        
        return TermNode(f.pos, f, m if len(m) > 0 else None)
    
    def parse_FactorNode(self) -> FactorNode:
        sign = True
        not_ = False
        while self.has_token():
            n = self.next_token()
            if n.type == TokenType.OPERATOR and n.value in ["+", "-", "!"]:
                if n.value == "-":
                    sign = not sign
                elif n.value == "!":
                    not_ = not not_
            elif n.type in [TokenType.ID, TokenType.STRING, TokenType.NUMBER, TokenType.LPAREN]:
                self.pos -= 1
                return FactorNode(n.pos(), self.parse_CallNode(), sign, not_)
            else:
                parse_error(n, "Unexpected token")
    
    def parse_CallNode(self) -> CallNode:
        a = self.parse_AtomNode()
        p = []
        is_call = False

        if self.has_token():
            n = self.next_token()
            if n.type == TokenType.LPAREN:
                is_call = True

                if not self.has_token():
                    parse_error(n, "Unexpected EOF")
                
                n = self.next_token()
                if n.type == TokenType.RPAREN:
                    pass
                else:
                    self.pos -= 1
                    while self.has_token():
                        p.append(self.parse_ExpressionNode())
                        n = self.next_token()
                        if n.type == TokenType.RPAREN:
                            break
                        elif n.type == TokenType.COMMA:
                            pass
                        else:
                            parse_error(n, "Unexpected token")
            else:
                self.pos -= 1
        
        return CallNode(a.pos, a, is_call, p)
    
    def parse_AtomNode(self) -> AtomNode:
        n = self.next_token()
        
        if n.type in [TokenType.ID, TokenType.STRING, TokenType.NUMBER]:
            if self.has_token() and n.type == TokenType.ID:
                n_ = self.next_token()
                if n_.type == TokenType.DOT:
                    n_ = self.next_token(TokenType.ID)
                    return AtomNode(n.pos(), ValueNode(n.pos(), f"{n.value}.{n_.value}"))
                elif n_.type == TokenType.LBRACK:
                    n_ = self.parse_ExpressionNode()
                    self.next_token(TokenType.RBRACK)
                    return AtomNode(n.pos(), IndexNode(n.pos(), n.value, n_))
                else:
                    self.pos -= 1
            
            return AtomNode(n.pos(), ValueNode(n.pos(), n.value))

        elif n.type == TokenType.LPAREN:
            e = self.parse_ExpressionNode()
            self.next_token()
            return AtomNode(n.pos(), e)
            
        else:
            parse_error(n, "Unexpected token")
    
    def parse_KeywordNode(self) -> KeywordNode:
        id_ = self.next_token()

        if id_.value in ["if", "while"]:
            self.next_token(TokenType.LPAREN)
            e = self.parse_ExpressionNode()
            self.next_token(TokenType.RPAREN)

            c = []
            self.next_token()
            while True:
                n = self.next_token()
                if n.type == TokenType.RBRACE:
                    break
                else:
                    self.pos -= 1
                    c.append(self.parse_AnyNode())
            
            if id_.value == "if":
                if self.has_token():
                    n = self.next_token()
                    if n.type == TokenType.ID and n.value == "else":
                        self.next_token(TokenType.LBRACE)

                        ec = []
                        while True:
                            n = self.next_token()
                            if n.type == TokenType.RBRACE:
                                break
                            else:
                                self.pos -= 1
                                ec.append(self.parse_AnyNode())
                        
                        return IfNode(id_.pos(), e, c, ec)
                    else:
                        self.pos -= 1

                return IfNode(id_.pos(), e, c)
            elif id_.value == "while":
                return WhileNode(id_.pos(), e, c)
        elif id_.value == "for":
            self.next_token(TokenType.LPAREN)

            init = self.parse_AnyNode(False)

            self.next_token(TokenType.SEMICOLON)
            cond = self.parse_ExpressionNode()

            self.next_token(TokenType.SEMICOLON)
            action = self.parse_AnyNode(False)

            self.next_token(TokenType.RPAREN)

            c = []
            self.next_token(TokenType.LBRACE)
            while True:
                n = self.next_token()
                if n.type == TokenType.RBRACE:
                    break
                else:
                    self.pos -= 1
                    c.append(self.parse_AnyNode())

            return ForNode(id_.pos(), init, cond, action, c)
        elif id_.value == "function":
            id_ = self.next_token(TokenType.ID)

            self.next_token(TokenType.LPAREN)

            args = []
            last = TokenType.LPAREN
            while True:
                n = self.next_token()
                if n.type == TokenType.RPAREN:
                    if last == TokenType.COMMA:
                        parse_error(n, "Unexpected token")
                    break
                elif n.type == TokenType.COMMA:
                    if last == TokenType.COMMA:
                        parse_error(n, "Unexpected token")
                    pass
                elif n.type == TokenType.ID:
                    if last == TokenType.ID:
                        parse_error(n, "Unexpected token")
                    args.append(n.value)

            c = []
            self.next_token(TokenType.LBRACE)
            while True:
                n = self.next_token()
                if n.type == TokenType.RBRACE:
                    break
                else:
                    self.pos -= 1
                    c.append(self.parse_AnyNode())
            
            return FunctionNode(id_.pos(), id_.value, args, c)
        elif id_.value == "repeat":
            self.next_token(TokenType.LPAREN)
            amount = self.next_token(TokenType.NUMBER)
            self.next_token(TokenType.RPAREN)

            c = []
            self.next_token(TokenType.LBRACE)
            while True:
                n = self.next_token()
                if n.type == TokenType.RBRACE:
                    break
                else:
                    self.pos -= 1
                    c.append(self.parse_AnyNode())
            
            return RepeatNode(id_.pos(), int(amount.value), c)
        
        parse_error(id_, "Unexpected token")
