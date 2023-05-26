import re
from typing import List, Optional, Sequence

import networkx as nx
import matplotlib.pyplot as plt


def is_reentrancy(graph, logger):
    """ 输入表示函数调用的有向图，如果有重入则返回true """

    is_reentrancy = False
    log_msg = ''

    for node in list(graph.nodes)[1:]:
        path = nx.shortest_path(graph, 1, node)

        names = []
        for node_id in path:
            node_name = graph.nodes[node_id]['name']
            names.append(node_name)
        
        if len(set(names)) < len(names):
            is_reentrancy = True

            log_msg = names[0]
            for name in names[1:]:
                log_msg += '-{}'.format(name)

            logger.warning(log_msg)

            return is_reentrancy, log_msg
    
    return is_reentrancy, log_msg

def decode_call_tree(tree_structure: str, logger):
    """ 解析str类型的call tree，返回一个有向图 """

    # 将嵌套列表转化为字符串类型的树
    tree_str = build_tree(tree_structure)

    log_msg = '表示函数调用链的字符串:\n'
    log_msg += tree_str
    logger.warning(log_msg)

    # 将字符串类型的树转化为有向图
    graph = parse_tree_str(tree_str)

    return graph, tree_str


def parse_tree_str(tree_str):

    # ******************************init******************************
    
    # 创建有向图
    di_graph = nx.DiGraph()
    # 初始化indent_dict
    # key: 缩进值 value: 对应的节点的id
    # 如果有一个新的节点与之前节点缩进值相同，则用新节点id替换之前节点id
    indent_dict = {}
    # 节点id，初始为1
    id = 1
    
    # ******************************init******************************

    # tree_node的每一个元素是一个树节点
    # 但是包含缩进和\x1b等无关字符
    tree_nodes = tree_str.split('\n')

    # ******************************将根节点加入di_graph******************************
    
    # 第一个函数调用的名字
    name = tree_nodes[0].split()[0]
    # 去掉ANSI escape code 语法颜色
    name = re.sub('\x1b.*?m', '', name)
    # 将根节点加入di_graph
    di_graph.add_node(id, name=name)
    # 更新indent_dict
    indent_dict[0] = id
    # 更新id
    id += 1
    
    # ******************************将根节点加入di_graph******************************

    # ******************************将根节点之外的其他节点加入di_graph******************************
    
    for node in tree_nodes[1:]:
        try:
            # 获取该节点的缩进值
            # try是为了跳过空行
            indent = re.search(r'\x1b', node).start()
            
            # 名字
            tab_count = 1
            name = node.split()[tab_count]
            name = re.sub('\x1b.*?m', '', name)
            invalid = name.startswith('\u2514') or name.startswith('\u251c') or \
                name.startswith('\u2502') or name.startswith('\u2500')
            while invalid:
                tab_count += 1
                name = node.split()[tab_count]
                name = re.sub('\x1b.*?m', '', name)
                invalid = name.startswith('\u2514') or name.startswith('\u251c') or \
                    name.startswith('\u2502') or name.startswith('\u2500')

            # 去掉ANSI escape code 语法颜色
            name = re.sub('\x1b.*?m', '', name)
            # 将该节点加入di_graph
            di_graph.add_node(id, name=name)
            # 更新indent_dict
            indent_dict[indent/4] = id
            # 更新id
            id += 1

            # 添加指向该节点的边
            father = indent_dict[indent/4-1]
            di_graph.add_edge(father, id - 1)
        except:
            pass
    
    # ******************************将根节点之外的其他节点加入di_graph******************************

    return di_graph

def build_tree(
    tree_structure: Sequence,
    multiline_pad: int = 1,
    pad_depth: Optional[List[int]] = None,
    _indent_data: Optional[list] = None,
) -> str:
    """
    Build a tree graph from a nested list.
    将嵌套列表转化为树

    Each item in the list if a top-level value to be added to the tree. The item may be:


    * A sequence, where the first value is the key and each subsequent value is
      a node beneath it.
    * A string, where the value is a key with no subnodes

    By nesting sequences it is possible to produce multi-level trees.

    For keys that contain a new line, all lines beyond the first are indented. It
    is possible to create complex trees that contain subtrees, by using the tree_str
    of `build_tree` as a key value in another tree.

    Arguments
    ---------
    tree_structure : Sequence
        List or tuple to be turned into a tree.
    multiline_pad : int, optional
        如果一个树节点的内容一行写不下，第二行的缩进
        Number of padding lines to leave before and after a tree value that spans
        multiple lines.
    pad_depth : List[int], optional
        每一级树节点的缩进
        Number of padding lines to leave between each node. Each entry in the list
        represents padding at a specific depth of the tree. If no value is given,
        zero is assumed.
    _indent_data
        递归调用缩进
        Internal list to handle indentation during recursive calls. The initial
        call to this function should always leave this value as `None`.

    Returns
    -------
    str
        Tree graph.
    """

    tree_str = ""

    if _indent_data is None:
        _indent_data = []

    was_padded = False
    
    for i, row in enumerate(tree_structure):

        # row是tree_structure中的最后一个元素
        is_last_item = bool(i < len(tree_structure) - 1)

        # create indentation string
        indent = ""
        for value in _indent_data[1:]:
            indent = f"{indent}\u2502   " if value else f"{indent}    "
        if _indent_data:

            symbol = "\u251c" if is_last_item else "\u2514"
            indent = f"{indent}{symbol}\u2500\u2500 "

        # 如果row是list或是tuple类型就取其第一个元素为key
        key = row[0] if isinstance(row, (list, tuple)) else row
        lines = [x for x in key.split("\n") if x]
        if pad_depth and i > 0:
            for x in range(pad_depth[0]):
                tree_str = f"{tree_str}{indent[:-4]}\u2502   \n"
        elif len(lines) > 1 and not was_padded:
            for x in range(multiline_pad):
                tree_str = f"{tree_str}{indent[:-4]}\u2502   \n"

        tree_str = f"{tree_str}{indent}{lines[0]}\n"
        was_padded = False

        if len(lines) > 1:
            # handle multiline keys
            symbol = "\u2502" if is_last_item else " "
            symbol2 = "\u2502" if isinstance(row, (list, tuple)) and len(row) > 1 else " "
            indent = f"{indent[:-4]}{symbol}   {symbol2}   "
            for line in lines[1:] + ([""] * multiline_pad):
                tree_str = f"{tree_str}{indent}{line}\n"
            was_padded = True

        if isinstance(row, (list, tuple)) and len(row) > 1:
            # create nested tree
            new_pad_depth = pad_depth[1:] if pad_depth else None
            nested_tree = build_tree(
                row[1:], multiline_pad, new_pad_depth, _indent_data + [is_last_item]
            )
            tree_str = f"{tree_str}{nested_tree}"

    return tree_str


def main():

    from brownie.network.transaction import TransactionReceipt

    TransactionReceipt.call_trace


if __name__ == '__main__':
    main()