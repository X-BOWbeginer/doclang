import clang.cindex as cx
from cfg import Cfg, G
from automa import Automa

au = Automa()


def traverse(node: cx.Cursor, prefix="", is_last=True):
    branch = "└──" if is_last else "├──"
    text = f"{str(node.kind).removeprefix('CursorKind.')}: {node.spelling}"
    if node.kind == cx.CursorKind.INTEGER_LITERAL:
        value = list(node.get_tokens())[0].spelling
        text = f"{text}{value}"

    print(f"{prefix}{branch} {text}")
    new_prefix = prefix + ("    " if is_last else "│   ")
    children = list(node.get_children())

    # 分析函数体
    if node.kind is cx.CursorKind.FUNCTION_DECL:
        if node.is_definition():
            fuc_body_children = list(node.get_children())
            body = Cfg(fuc_body_children[-1])
            G.fucTable[str(node.spelling)] = body.startNode, body.endNode
            # body.buildChildCfg()

    # 遍历子节点
    for child in children:
        traverse(child, new_prefix, child is children[-1])


def get_diag_info(diag):
    return {
        "severity": diag.severity,
        "location": diag.location,
        "spelling": diag.spelling,
        "ranges": diag.ranges,
        "fixits": diag.fixits,
    }


def main():
    from pprint import pprint
    index = cx.Index.create(excludeDecls=True)
    tu = index.parse('main.cpp', args=['-std=c++20'])
    pprint(("diags", [get_diag_info(d) for d in tu.diagnostics]))
    traverse(tu.cursor)
    #G.draw()
    #G.toGexf()
    # G.drawSub()
    # for test
    au.g2nfa(G)
    au.nfa2dfa()
    au.drawnfa()
    au.drawdfa()
    pass


if __name__ == "__main__":
    main()
