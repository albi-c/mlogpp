from re import T
from lexer import TokenType, Token

keywords = ["if", "while", "for", "function", "repeat"]

class Node:
    def generate(self, i = 0) -> str:
        return i * " " + "Node\n"

class CodeNode(Node):
    def __init__(self, code: list):
        self.code = code
    
    def generate(self, i = 0) -> str:
        tmp = i * " " + "CodeNode {\n"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return CodeNode([n.rrename(vars_) for n in self.code])

class ValueNode(Node):
    def __init__(self, value: str):
        self.value = value
    
    def generate(self, i) -> str:
        return i * " " +  "ValueNode: " + str(self.value) + "\n"
    
    def rrename(self, vars_: dict) -> str:
        return ValueNode(vars_.get(self.value, self.value))

class AtomNode(Node):
    def __init__(self, value):
        self.value = value
    
    def generate(self, i) -> str:
        return i * " " + "AtomNode: \n" + self.value.generate(i + 1)
    
    def rrename(self, vars_: dict) -> Node:
        return self.value.rrename(vars_)

class AssignmentNode(Node):
    def __init__(self, left: str, atype: str, right: Node):
        self.left = left
        self.atype = atype
        self.right = right
    
    def generate(self, i) -> str:
        return i * " " + "AssignmentNode: \n" + (i + 1) * " " + f"{self.left} {self.atype} {self.right.generate(0)}"
    
    def rrename(self, vars_: dict) -> Node:
        return AssignmentNode(vars_.get(self.left, self.left), self.atype, self.right.rrename(vars_))

class ExpressionNode(Node):
    def __init__(self, left, right = None):
        self.left = left
        self.right = right
    
    def generate(self, i) -> str:
        tmp = ""
        if self.right is not None:
            for r in self.right:
                tmp += f" {r[0]} {r[1].generate(i + 1)}"
        return i * " " + f"ExpressionNode: \n{self.left.generate(i + 1)}{tmp}"
    
    def rrename(self, vars_: dict) -> Node:
        return ExpressionNode(self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class CompExpressionNode(Node):
    def __init__(self, left, right = None):
        self.left = left
        self.right = right
    
    def generate(self, i) -> str:
        tmp = ""
        if self.right is not None:
            for r in self.right:
                tmp += f" {r[0]} {r[1].generate(i + 1)}"
        return i * " " + f"CompExpressionNode: \n{self.left.generate(i + 1)}{tmp}"
    
    def rrename(self, vars_: dict) -> Node:
        return CompExpressionNode(self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class ArithExpNode(Node):
    def __init__(self, left, right = None):
        self.left = left
        self.right = right
    
    def generate(self, i) -> str:
        tmp = ""
        if self.right is not None:
            for r in self.right:
                tmp += f" {r[0]} {r[1].generate(i + 1)}"
        return i * " " + f"ArithExpNode: \n{self.left.generate(i + 1)}{tmp}"
    
    def rrename(self, vars_: dict) -> Node:
        return ArithExpNode(self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class TermNode(Node):
    def __init__(self, left, right = None):
        self.left = left
        self.right = right
    
    def generate(self, i) -> str:
        tmp = ""
        if self.right is not None:
            for r in self.right:
                tmp += f" {r[0]} {r[1].generate(i + 1)}"
        return i * " " + f"TermNode: \n{self.left.generate(i + 1)}{tmp}"
    
    def rrename(self, vars_: dict) -> Node:
        return TermNode(self.left.rrename(vars_), [[n[0], n[1].rrename(vars_)] for n in self.right] if self.right is not None else None)

class FactorNode(Node):
    def __init__(self, left, sign: bool):
        self.left = left
        self.sign = sign
    
    def generate(self, i) -> str:
        return i * " " + f"FactorNode: \n{'+' if self.sign else '-'}{self.left.generate(i + 1)}"
    
    def rrename(self, vars_: dict) -> Node:
        return FactorNode(self.left.rrename(vars_), self.sign)

class CallNode(Node):
    def __init__(self, function, is_call: bool, params: list = []):
        self.function = function
        self.is_call = is_call
        self.params = params
    
    def generate(self, i) -> str:
        if self.is_call:
            return i * " " + f"CallNode [1]: {self.function}({','.join(self.params)})\n"
        else:
            return i * " " + f"CallNode [0]: {self.function.generate(i + 1)}\n"
    
    def rrename(self, vars_: dict) -> Node:
        return CallNode(self.function if type(self.function) == str else self.function.rrename(vars_), self.is_call, [n.rrename(vars_) for n in self.params])

class KeywordNode(Node):
    def __init__(self):
        pass

class IfNode(KeywordNode):
    def __init__(self, condition: ExpressionNode, code: list):
        self.condition = condition
        self.code = code
    
    def generate(self, i) -> str:
        tmp = i * " " + f"IfNode ({self.condition.generate(i + 1)}) {{"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return IfNode(self.condition.rrename(vars_), [n.rrename(vars_) for n in self.code])

class WhileNode(KeywordNode):
    def __init__(self, condition: ExpressionNode, code: list):
        self.condition = condition
        self.code = code
    
    def generate(self, i) -> str:
        tmp = i * " " + f"WhileNode ({self.condition.generate(i + 1)}) {{"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return WhileNode(self.condition.rrename(vars_), [n.rrename(vars_) for n in self.code])

class ForNode(KeywordNode):
    def __init__(self, init: Node, condition: ExpressionNode, action: Node, code: list):
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
        return ForNode(self.init.rrename(vars_), self.condition.rrename(vars_), self.action.rrename(vars_), [n.rrename(vars_) for n in self.code])

class FunctionNode(KeywordNode):
    def __init__(self, name: str, args: list, code: list):
        self.name = name
        self.args = args
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return FunctionNode(self.name, self.args, [n.rrename(vars_) for n in self.code])

class RepeatNode(KeywordNode):
    def __init__(self, amount: int, code: list):
        self.amount = amount
        self.code = code
    
    def generate(self, i) -> str:
        tmp = i * " " + f"RepeatNode ({self.amount}) {{"
        for c in self.code:
            tmp += c.generate(i + 1)
        tmp += i * " " + "}\n"
        return tmp
    
    def rrename(self, vars_: dict) -> Node:
        return RepeatNode(self.amount, [n.rrename(vars_) for n in self.code])

class NativeNode(KeywordNode):
    def __init__(self, code: str):
        self.code = code
    
    def rrename(self, vars_: dict) -> Node:
        return NativeNode(self.code)

class ReturnNode(KeywordNode):
    def __init__(self, value):
        self.value = value
    
    def rrename(self, vars_: dict) -> Node:
        return ReturnNode(self.value.rrename(vars_))

class LoopActionNode(KeywordNode):
    def __init__(self, action: str):
        self.action = action
    
    def rrename(self, vars_: dict) -> Node:
        return LoopActionNode(self.action)

class Parser:
    def parse(self, tokens: list) -> CodeNode:
        self.tokens = tokens
        self.pos = -1

        nodes = []
        while self.has_token():
            nodes.append(self.parse_AnyNode())

        return CodeNode(nodes)
    
    def has_token(self) -> bool:
        return self.pos < len(self.tokens) - 1
    
    def curr_token(self) -> Token:
        return self.tokens[self.pos]
    
    def next_token(self, ttype=None) -> Token:
        if self.has_token():
            self.pos += 1

            while self.tokens[self.pos].type == TokenType.SEPARATOR:
                if self.has_token():
                    self.pos += 1
                else:
                    break

            if ttype is not None:
                if self.tokens[self.pos].type != ttype:
                    raise RuntimeError(f"Unexpected \"{self.tokens[self.pos].value}\"")

            return self.tokens[self.pos]
        
        raise RuntimeError("Unexpected EOF")
    
    # node parsers

    def parse_AnyNode(self, can_be_special=True) -> Node:
        id_ = self.next_token()
        if id_.type == TokenType.ID:
            n = self.next_token()

            if id_.value == "return":
                self.pos -= 1
                return ReturnNode(self.parse_ExpressionNode())
            elif id_.value in ["break", "continue"]:
                self.pos -= 1
                return LoopActionNode(id_.value)
            
            if n.type == TokenType.SET:
                return AssignmentNode(id_.value, n.value, self.parse_ExpressionNode())
            elif n.type == TokenType.LPAREN:
                if id_.value in keywords:
                    if not can_be_special:
                        raise RuntimeError(f"Unexpected \"{id_.value}\"")
                    
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
                                raise RuntimeError(f"Unexpected \"{n.value}\"")
                        else:
                            if not e:
                                self.pos -= 1
                                p.append(self.parse_ExpressionNode())
                                e = True
                            else:
                                raise RuntimeError(f"Unexpected \"{n.value}\"")
                    
                    return CallNode(id_.value, True, p)
            elif n.type == TokenType.ID:
                if id_.value == "function":
                    self.pos -= 2
                    return self.parse_KeywordNode()
                else:
                    raise RuntimeError(f"Unexpected \"{n.value}\"")
            else:
                raise RuntimeError(f"Unexpected \"{n.value}\"")
        elif id_.type == TokenType.DOT:
            n = self.next_token(TokenType.STRING)

            return NativeNode(n.value[1:-1])
        
        raise RuntimeError(f"Unexpected \"{id_.value}\"")
    
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
        
        return ExpressionNode(c, l if len(l) > 0 else None)

    def parse_CompExpressionNode(self) -> CompExpressionNode:
        e = self.parse_ArithExpNode()
        c = []
        while self.has_token():
            n = self.next_token()
            if n.type == TokenType.OPERATOR and n.value in ["==", "!=", "<", ">", "<=", ">="]:
                c.append((n.value, self.parse_ArithExpNode()))
            else:
                self.pos -= 1
                break
        
        return CompExpressionNode(e, c if len(c) > 0 else None)
    
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
        
        return ArithExpNode(t, a if len(a) > 0 else None)
    
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
        
        return TermNode(f, m if len(m) > 0 else None)
    
    def parse_FactorNode(self) -> FactorNode:
        sign = True
        while self.has_token():
            n = self.next_token()
            if n.type == TokenType.OPERATOR and n.value in ["+", "-"]:
                if n.value == "-":
                    sign = not sign
            elif n.type in [TokenType.ID, TokenType.STRING, TokenType.NUMBER, TokenType.LPAREN]:
                self.pos -= 1
                return FactorNode(self.parse_CallNode(), sign)
            else:
                raise RuntimeError(f"Unexpected \"{n.value}\"")
    
    def parse_CallNode(self) -> CallNode:
        a = self.parse_AtomNode()
        p = []
        is_call = False

        if self.has_token():
            n = self.next_token()
            if n.type == TokenType.LPAREN:
                is_call = True

                if not self.has_token():
                    raise RuntimeError(f"Unexpected EOF")
                
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
                            raise RuntimeError(f"Unexpected \"{n.value}\"")
            else:
                self.pos -= 1
        
        return CallNode(a, is_call, p)
    
    def parse_AtomNode(self) -> AtomNode:
        n = self.next_token()
        
        if n.type in [TokenType.ID, TokenType.STRING, TokenType.NUMBER]:
            return AtomNode(ValueNode(n.value))
        elif n.type == TokenType.LPAREN:
            e = self.parse_ExpressionNode()
            self.next_token()
            return AtomNode(e)
        else:
            raise RuntimeError(f"Unexpected \"{n.value}\"")
    
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
                return IfNode(e, c)
            elif id_.value == "while":
                return WhileNode(e, c)
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

            return ForNode(init, cond, action, c)
        elif id_.value == "function":
            id_ = self.next_token(TokenType.ID)

            self.next_token(TokenType.LPAREN)

            args = []
            last = TokenType.LPAREN
            while True:
                n = self.next_token()
                if n.type == TokenType.RPAREN:
                    if last == TokenType.COMMA:
                        raise RuntimeError(f"Unexpected \"{n.value}\"")
                    break
                elif n.type == TokenType.COMMA:
                    if last == TokenType.COMMA:
                        raise RuntimeError(f"Unexpected \"{n.value}\"")
                    pass
                elif n.type == TokenType.ID:
                    if last == TokenType.ID:
                        raise RuntimeError(f"Unexpected \"{n.value}\"")
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
            
            return FunctionNode(id_.value, args, c)
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
            
            return RepeatNode(int(amount.value), c)
        
        raise RuntimeError(f"Unexpected \"{id_.value}\"")
