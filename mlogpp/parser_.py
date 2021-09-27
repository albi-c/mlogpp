from .lexer import TokenType, Token, Position
from .error import parse_error
from . import functions

class Node:
    def generate(self, i = 0) -> str:
        return i * " " + "Node\n"

class AST(Node):
    def __init__(self, code: list):
        self.code = code
    
    def generate(self, i = 0) -> str:
        tmp = i * " " + "AST {\n"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict):
        return AST([n.rrename(vars_) for n in self.code])

class CodeNode(Node):
    def __init__(self, pos: Position, code: list):
        self.pos = pos
        self.code = code
    
    def generate(self, i) -> str:
        tmp = i * " " + "CodeNode {\n"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return CodeNode(self.pos, [n.rrename(vars_) for n in self.code])

class ValueNode(Node):
    def __init__(self, pos: Position, value: str):
        self.pos = pos
        self.value = value
    
    def generate(self, i) -> str:
        return i * " " +  "ValueNode: " + str(self.value) + "\n"
    
    def rrename(self, vars_: dict) -> str:
        if "." in self.value:
            spl = self.value.split(".")
            if len(spl) == 2:
                return ValueNode(self.pos, vars_.get(spl[0], spl[0]) + "." + spl[1])
        
        return ValueNode(self.pos, vars_.get(self.value, self.value))

class AtomNode(Node):
    def __init__(self, pos: Position, value):
        self.pos = pos
        self.value = value
    
    def generate(self, i) -> str:
        return i * " " + "AtomNode: \n" + self.value.generate(i + 1)
    
    def rrename(self, vars_: dict) -> Node:
        return self.value.rrename(vars_)

class AssignmentNode(Node):
    def __init__(self, pos: Position, left: str, atype: str, right: Node):
        self.pos = pos
        self.left = left
        self.atype = atype
        self.right = right
    
    def generate(self, i) -> str:
        return i * " " + "AssignmentNode: \n" + (i + 1) * " " + f"{self.left} {self.atype} {self.right.generate(0)}"
    
    def rrename(self, vars_: dict) -> Node:
        return AssignmentNode(self.pos, vars_.get(self.left, self.left), self.atype, self.right.rrename(vars_))

class ExpressionNode(Node):
    def __init__(self, pos: Position, left, right = None):
        self.pos = pos
        self.left = left
        self.right = right
    
    def generate(self, i) -> str:
        tmp = ""
        if self.right is not None:
            for r in self.right:
                tmp += f" {r[0]} {r[1].generate(i + 1)}"
        return i * " " + f"ExpressionNode: \n{self.left.generate(i + 1)}{tmp}"
    
    def rrename(self, vars_: dict) -> Node:
        return ExpressionNode(self.pos, self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class CompExpressionNode(Node):
    def __init__(self, pos: Position, left, right = None):
        self.pos = pos
        self.left = left
        self.right = right
    
    def generate(self, i) -> str:
        tmp = ""
        if self.right is not None:
            for r in self.right:
                tmp += f" {r[0]} {r[1].generate(i + 1)}"
        return i * " " + f"CompExpressionNode: \n{self.left.generate(i + 1)}{tmp}"
    
    def rrename(self, vars_: dict) -> Node:
        return CompExpressionNode(self.pos, self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class ArithExpNode(Node):
    def __init__(self, pos: Position, left, right = None):
        self.pos = pos
        self.left = left
        self.right = right
    
    def generate(self, i) -> str:
        tmp = ""
        if self.right is not None:
            for r in self.right:
                tmp += f" {r[0]} {r[1].generate(i + 1)}"
        return i * " " + f"ArithExpNode: \n{self.left.generate(i + 1)}{tmp}"
    
    def rrename(self, vars_: dict) -> Node:
        return ArithExpNode(self.pos, self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class TermNode(Node):
    def __init__(self, pos: Position, left, right = None):
        self.pos = pos
        self.left = left
        self.right = right
    
    def generate(self, i) -> str:
        tmp = ""
        if self.right is not None:
            for r in self.right:
                tmp += f" {r[0]} {r[1].generate(i + 1)}"
        return i * " " + f"TermNode: \n{self.left.generate(i + 1)}{tmp}"
    
    def rrename(self, vars_: dict) -> Node:
        return TermNode(self.pos, self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class FactorNode(Node):
    def __init__(self, pos: Position, left, sign: bool, not_: bool):
        self.pos = pos
        self.left = left
        self.sign = sign
        self.not_ = not_
    
    def generate(self, i) -> str:
        return i * " " + f"FactorNode: \n{'!' if self.not_ else ''}{'+' if self.sign else '-'}{self.left.generate(i + 1)}"
    
    def rrename(self, vars_: dict) -> Node:
        return FactorNode(self.pos, self.left.rrename(vars_), self.sign, self.not_)

class CallNode(Node):
    def __init__(self, pos: Position, function, is_call: bool, params: list = []):
        self.pos = pos
        self.function = function
        self.is_call = is_call
        self.params = params
    
    def generate(self, i) -> str:
        if self.is_call:
            return i * " " + f"CallNode [1]: {self.function}({','.join(self.params)})\n"
        else:
            return i * " " + f"CallNode [0]: {self.function.generate(i + 1)}\n"
    
    def rrename(self, vars_: dict) -> Node:
        return CallNode(self.pos, self.function if type(self.function) == str else self.function.rrename(vars_), self.is_call, [n.rrename(vars_) for n in self.params])

class KeywordNode(Node):
    def __init__(self):
        pass

class IfNode(KeywordNode):
    def __init__(self, pos: Position, condition: ExpressionNode, code: list, elsecode: list = None):
        self.pos = pos
        self.condition = condition
        self.code = code
        self.elsecode = elsecode if elsecode is not None else []
    
    def generate(self, i) -> str:
        tmp = i * " " + f"IfNode ({self.condition.generate(i + 1)}) {{"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "} {\n"
        for c in self.elsecode:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return IfNode(self.pos, self.condition.rrename(vars_), [n.rrename(vars_) for n in self.code], [n.rrename(vars_) for n in self.elsecode])

class WhileNode(KeywordNode):
    def __init__(self, pos: Position, condition: ExpressionNode, code: list):
        self.pos = pos
        self.condition = condition
        self.code = code
    
    def generate(self, i) -> str:
        tmp = i * " " + f"WhileNode ({self.condition.generate(i + 1)}) {{"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return WhileNode(self.pos, self.condition.rrename(vars_), [n.rrename(vars_) for n in self.code])

class ForNode(KeywordNode):
    def __init__(self, pos: Position, init: Node, condition: ExpressionNode, action: Node, code: list):
        self.pos = pos
        self.init = init
        self.condition = condition
        self.action = action
        self.code = code
    
    def generate(self, i) -> str:
        tmp = i * " " + f"ForNode ({self.init.generate(i + 1)}; {self.condition.generate(i + 1)}; {self.action.generate(i + 1)}) {{"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return ForNode(self.pos, self.init.rrename(vars_), self.condition.rrename(vars_), self.action.rrename(vars_), [n.rrename(vars_) for n in self.code])

class FunctionNode(KeywordNode):
    def __init__(self, pos: Position, name: str, args: list, code: list):
        self.pos = pos
        self.name = name
        self.args = args
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return FunctionNode(self.pos, self.name, self.args, [n.rrename(vars_) for n in self.code])

class RepeatNode(KeywordNode):
    def __init__(self, pos: Position, amount: int, code: list):
        self.pos = pos
        self.amount = amount
        self.code = code
    
    def generate(self, i) -> str:
        tmp = i * " " + f"RepeatNode ({self.amount}) {{"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return RepeatNode(self.pos, self.amount, [n.rrename(vars_) for n in self.code])

class NativeNode(KeywordNode):
    def __init__(self, pos: Position, code: str):
        self.pos = pos
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return NativeNode(self.pos, self.code)

class ReturnNode(KeywordNode):
    def __init__(self, pos: Position, value):
        self.pos = pos
        self.value = value
    
    def rrename(self, vars_: dict) -> Node:
        return ReturnNode(self.pos, self.value.rrename(vars_))

class LoopActionNode(KeywordNode):
    def __init__(self, pos: Position, action: str):
        self.pos = pos
        self.action = action
    
    def rrename(self, vars_: dict) -> Node:
        return LoopActionNode(self.pos, self.action)

class ExternNode(Node):
    def __init__(self, pos: Position, name: str):
        self.pos = pos
        self.name = name
    
    def rrename(self, vars_: dict) -> Node:
        return ExternNode(self.pos, self.name)

class Parser:
    def parse(self, tokens: list) -> CodeNode:
        self.tokens = tokens
        self.pos = -1

        nodes = []
        while self.has_token():
            nodes.append(self.parse_AnyNode())

        return AST(nodes)
    
    def has_token(self) -> bool:
        return self.pos < len(self.tokens) - 1
    
    def curr_token(self) -> Token:
        return self.tokens[self.pos]
    
    def next_token(self, ttype=None) -> Token:
        if self.has_token():
            self.pos += 1

            if self.tokens[self.pos].type != ttype and ttype is not None:
                parse_error(self.tokens[self.pos], "Unexpected token")

            return self.tokens[self.pos]
        
        parse_error(self.tokens[-1], "Unexpected EOF")
    
    # node parsers

    def parse_AnyNode(self, can_be_special=True) -> Node:
        id_ = self.next_token()
        if id_.type == TokenType.ID:
            n = self.next_token()

            if id_.value == "return":
                self.pos -= 1
                return ReturnNode(id_.pos(), self.parse_ExpressionNode())
            elif id_.value in ["break", "continue"]:
                self.pos -= 1
                return LoopActionNode(id_.pos(), id_.value)
            elif id_.value == "extern":
                if n.type != TokenType.ID:
                    parse_error(n, "Unexpected token")
                
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
                if id_.value in functions.special:
                    parse_error(n, "Cannot override a keyword")
                
                return AssignmentNode(id_.pos(), id_.value, n.value, self.parse_ExpressionNode())
            elif n.type == TokenType.DOT:
                if id_.value in functions.special:
                    parse_error(n, "Cannot use property of a keyword")

                node = self.parse_AnyNode()
                if type(node) != AssignmentNode:
                    parse_error(n, "Unexpected token")
                
                node.left = id_.value + "." + node.left

                return node
            elif n.type == TokenType.LPAREN:
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
                if id_.value == "function":
                    self.pos -= 2
                    return self.parse_KeywordNode()
                else:
                    parse_error(n, "Unexpected token")
            elif n.type == TokenType.LBRACE:
                if id_.value == "else":
                    self.pos -= 2
                    return self.parse_KeywordNode()
                else:
                     parse_error(n, "Unexpected token")
            else:
                parse_error(n, "Unexpected token")
        elif id_.type == TokenType.DOT:
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
