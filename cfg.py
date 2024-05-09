from clang.cindex import *
import networkx as nx
import matplotlib.pyplot as plt


class Graph:
    def __init__(self):
        self.Cnode_num = -1
        self.cfgs = []
        self.dig = nx.DiGraph()
        self.dig.graph['alphabet'] = []
        self.mainNodeList = []
        self.fucTable = {}  # 存储函数名+ 入口+出口

    def addNode(self, node):
        self.dig.add_node(node.id)

    def addEdge(self, From, To, label=None):
        if label == None:
            self.dig.add_edge(From.id, To.id)
        else:
            self.dig.add_edge(From.id, To.id, label=label)

    def removeEdge(self, From, To):
        self.dig.remove_edge(From.id, To.id)

    def removeEdgeFromNode(self, Node):
        out_edge = list(self.dig.out_edges(Node.id))
        self.dig.remove_edges_from(out_edge)

    def removeEdgeToNode(self, Node):
        in_edge = list(self.dig.in_edges(Node.id))
        self.dig.remove_edges_from(in_edge)

    def changeLabel(self, cfg, label):
        self.removeEdge(cfg.startNode, cfg.endNode)
        self.addEdge(cfg.startNode, cfg.endNode, label=label)
        cfg.label = label

    def draw(self):
        pos = nx.spring_layout(self.dig)
        edge_labels = nx.get_edge_attributes(self.dig, 'label')
        nx.draw_networkx(self.dig, pos, with_labels=True, arrows=True, node_size=300, font_size=8, arrowsize=20)
        nx.draw_networkx_edge_labels(self.dig, pos, edge_labels=edge_labels, font_color='red')
        plt.show()

    def drawSub(self):
        for c in self.cfgs:
            if c.showInSubGraph:
                self.mainNodeList.append(c.startNode.id)
                self.mainNodeList.append(c.endNode.id)
        sub_nodes = G.dig.subgraph(self.mainNodeList)
        pos = nx.spring_layout(sub_nodes)
        edge_labels = nx.get_edge_attributes(sub_nodes, 'label')

        nx.draw_networkx(sub_nodes, pos, with_labels=True, arrows=True, node_size=300, font_size=8, arrowsize=20)
        nx.draw_networkx_edge_labels(self.dig, pos, edge_labels=edge_labels, font_color='red')
        plt.show()

    def toGexf(self):
        nx.write_gexf(self.dig, "test.gexf")

    def travel(self):
        pass


G = Graph()


class AstNode:
    def __init__(self, id, cfg=None, isStart=False, isEnd=False, showInSubGraph=False):
        self.id = id
        self.cfg = cfg
        # 是CFG的起始or终止node
        self.isStart = isStart
        self.isEnd = isEnd
        G.addNode(self)


class Cfg:
    def __init__(self, cursor: Cursor, childs=None, breakTarget=None, continueTarget=None, returnTarget=None,
                 parent=None, isCondition=False, showInSubGraph=False, isEmpty=False, label=None):

        self.cursor = cursor

        # for while switch
        self.breakTarget = breakTarget
        self.continueTarget = continueTarget
        self.isCondition = isCondition
        # 用于for语句出现空的情况
        self.isEmpty = isEmpty
        if not isEmpty:
            self.tokens = cursor.get_tokens()
            self.kind = str(cursor.kind)
        else:
            self.tokens = None
            self.kind = "EMPTY"
        self.returnTarget = returnTarget
        # CFG list
        self.childs = childs if childs is not None else []
        # 父节点 CFG
        self.parent = parent

        G.Cnode_num += 1
        self.gid = G.Cnode_num
        self.showInSubGraph = showInSubGraph
        self.startNode = AstNode(id=str(self.gid) + "Start", cfg=self, isStart=True)
        self.endNode = AstNode(id=str(self.gid) + "End", cfg=self, isEnd=True)
        self.label = label
        if self.label:
            G.addEdge(self.startNode, self.endNode, self.label)
        else:
            G.addEdge(self.startNode, self.endNode, self.kind)
        G.cfgs.append(self)
        self.buildChildCfg()

    def buildChildCfg(self):
        cursorChilds = list(self.cursor.get_children())
        if len(cursorChilds) == 0:
            # BREAK,CONTINUE
            if self.cursor.kind == CursorKind.BREAK_STMT:
                # G.removeEdgeFromNode(self.endNode) uesless because order
                G.changeLabel(self, "break")
                G.addEdge(self.endNode, self.breakTarget, "to")
            elif self.cursor.kind == CursorKind.CONTINUE_STMT:
                G.changeLabel(self, "continue")
                G.addEdge(self.endNode, self.continueTarget, "to")
        elif self.cursor.kind == CursorKind.RETURN_STMT:
            tokens = list(self.cursor.get_tokens())
            s = list(n.spelling for n in tokens)
            label = " ".join(s)
            G.changeLabel(self, label)
        elif self.cursor.kind == CursorKind.DECL_STMT:
            tokens = list(self.cursor.get_tokens())
            s = list(n.spelling for n in tokens[0:-1])
            label = " ".join(s)
            G.changeLabel(self, label)
        elif self.cursor.kind == CursorKind.BINARY_OPERATOR:
            tokens = list(self.cursor.get_tokens())
            s = list(n.spelling for n in tokens)
            label = " ".join(s)
            G.changeLabel(self, label)

        elif self.cursor.kind == CursorKind.UNARY_OPERATOR:
            tokens = list(self.cursor.get_tokens())
            s = list(n.spelling for n in tokens)
            label = " ".join(s)
            G.changeLabel(self, label)

        elif self.cursor.kind == CursorKind.CALL_EXPR:
            if self.cursor.spelling == "log":
                params = list(self.cursor.get_children())
                val = list(params[-1].get_children())
                input = str(val[-1].spelling)[1:-2]
                G.dig.graph['alphabet'].append(input)
                G.changeLabel(self, "#" + input)
            else:
                G.removeEdge(self.startNode, self.endNode)
                body = G.fucTable[str(self.cursor.spelling)]
                G.addEdge(self.startNode, body[0], "in")
                G.addEdge(body[1], self.endNode, "out")


        elif self.cursor.kind == CursorKind.COMPOUND_STMT:
            G.removeEdge(self.startNode, self.endNode)
            self.showInSubGraph = True
            bottom = self.endNode
            for c in reversed(cursorChilds):  # 反向
                newCfg = Cfg(c, breakTarget=self.breakTarget, continueTarget=self.continueTarget, parent=self)
                if c.kind != CursorKind.BREAK_STMT and c.kind != CursorKind.CONTINUE_STMT:  # attention
                    G.addEdge(newCfg.endNode, bottom)
                if c == cursorChilds[0]:
                    G.addEdge(self.startNode, newCfg.startNode)

                bottom = newCfg.startNode
                # 递归
                # newCfg.buildChildCfg()
                self.childs.append(newCfg)

        elif self.cursor.kind == CursorKind.FOR_STMT:
            G.removeEdge(self.startNode, self.endNode)
            l = [False, False, False]
            index = 0
            # 双指针,解析for
            tokens = self.cursor.get_tokens()
            next_token = self.cursor.get_tokens()
            next(next_token)
            for i in tokens:
                try:
                    nextToken = next(next_token)
                except StopIteration:
                    pass
                if index == 0:
                    if str(i.spelling) == '(':
                        if str(nextToken.spelling) != ';':
                            l[index] = True
                            index += 1
                        else:
                            index += 1
                if index == 1 or index == 2:
                    if str(i.spelling) == ';':
                        if str(nextToken.spelling) != ';' and str(nextToken.spelling) != ')':
                            l[index] = True
                            index += 1
                        else:
                            index += 1

                if str(i.spelling) == '{':
                    break
            index = 0
            if l[0]:
                init = cursorChilds[index]
                initCfg = Cfg(init, parent=self)
                index += 1
            else:
                initCfg = Cfg(None, parent=self, isEmpty=True)

            if l[1]:
                con = cursorChilds[index]
                conCfg = Cfg(con, parent=self, isCondition=True, label="FOR_COND")
                index += 1
            else:
                conCfg = Cfg(None, parent=self, isCondition=True, isEmpty=True)

            if l[2]:
                inc = cursorChilds[index]
                incCfg = Cfg(inc, parent=self)
                index += 1
            else:
                incCfg = Cfg(None, parent=self, isEmpty=True)

            body = cursorChilds[-1]
            bodyCfg = Cfg(body, breakTarget=self.endNode, continueTarget=incCfg.startNode)
            # bodyCfg.buildChildCfg()
            # initCfg.buildChildCfg()
            G.addEdge(self.startNode, initCfg.startNode)
            G.addEdge(initCfg.endNode, conCfg.startNode)
            # TRUE
            G.addEdge(conCfg.endNode, bodyCfg.startNode, "True")
            # FALSE
            G.addEdge(conCfg.endNode, self.endNode, "False")

            G.addEdge(bodyCfg.endNode, incCfg.startNode)
            G.addEdge(incCfg.endNode, conCfg.startNode)

        elif self.cursor.kind == CursorKind.WHILE_STMT:
            G.removeEdge(self.startNode, self.endNode)
            self.showInSubGraph = True
            con = cursorChilds[0]
            stmts = cursorChilds[-1]
            conCfg = Cfg(con, parent=self, isCondition=True, showInSubGraph=True, label="WHILE_COND")
            # conCfg.buildChildCfg()
            # 提供breaktarget
            stmtsCfg = Cfg(stmts, breakTarget=self.endNode, continueTarget=self.startNode, parent=self,
                           showInSubGraph=True)
            # stmtsCfg.buildChildCfg()
            G.addEdge(self.startNode, conCfg.startNode)
            # TRUE
            G.addEdge(conCfg.endNode, stmtsCfg.startNode, "True")
            # FALSE
            G.addEdge(conCfg.endNode, self.endNode, "False")
            G.addEdge(stmtsCfg.endNode, conCfg.startNode)


        elif self.cursor.kind == CursorKind.IF_STMT:
            G.removeEdge(self.startNode, self.endNode)
            self.showInSubGraph = True
            con = cursorChilds[0]
            then = cursorChilds[1]
            conCfg = Cfg(con, parent=self, isCondition=True, showInSubGraph=True, label="IF_COND")
            thenCfg = Cfg(then, parent=self, continueTarget=self.continueTarget, breakTarget=self.breakTarget)
            # thenCfg.buildChildCfg()
            G.addEdge(self.startNode, conCfg.startNode)
            # Then
            G.addEdge(conCfg.endNode, thenCfg.startNode, "Then")
            G.addEdge(thenCfg.endNode, self.endNode)
            # if it has else part
            if len(cursorChilds) > 2:
                elsePart = cursorChilds[2]
                elsePartCfg = Cfg(elsePart, parent=self, showInSubGraph=True)
                # elsePartCfg.buildChildCfg()
                G.addEdge(conCfg.endNode, elsePartCfg.startNode, "Else")
                G.addEdge(elsePartCfg.endNode, self.endNode)
            else:
                G.addEdge(conCfg.endNode, self.endNode, "Else(no else part)")

        elif self.cursor.kind == CursorKind.SWITCH_STMT:
            G.removeEdge(self.startNode, self.endNode)
            self.showInSubGraph = True
            cases = cursorChilds[-1]
            if cases.kind == CursorKind.COMPOUND_STMT:
                casesCfg = Cfg(cases, parent=self, breakTarget=self.endNode)
                # casesCfg.buildChildCfg()
                G.addEdge(self.startNode, casesCfg.startNode, "enter cases")
                G.addEdge(casesCfg.endNode, self.endNode)

        elif self.cursor.kind == CursorKind.CASE_STMT:
            G.removeEdge(self.startNode, self.endNode)
            con = cursorChilds[0]
            then = cursorChilds[1]
            conCfg = Cfg(con, parent=self, isCondition=True, showInSubGraph=True, label="CASE_COND")
            thenCfg = Cfg(then, parent=self, continueTarget=self.continueTarget, breakTarget=self.breakTarget)
            # thenCfg.buildChildCfg()
            G.addEdge(self.startNode, conCfg.startNode)
            # Then
            G.addEdge(conCfg.endNode, thenCfg.startNode, "case match")
            G.addEdge(conCfg.endNode, self.endNode, "case miss")
            G.addEdge(thenCfg.endNode, self.endNode)

        elif self.cursor.kind == CursorKind.DEFAULT_STMT:
            G.removeEdge(self.startNode, self.endNode)
            default = cursorChilds[-1]
            defaultCfg = Cfg(default, parent=self, continueTarget=self.continueTarget, breakTarget=self.breakTarget)
            # defaultCfg.buildChildCfg()
            G.addEdge(self.startNode, defaultCfg.startNode, "case default")
            G.addEdge(defaultCfg.endNode, self.endNode)
