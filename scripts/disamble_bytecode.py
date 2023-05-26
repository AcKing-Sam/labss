""" 
从ContractContainer对象中获取字节码，反编译得到EVM操作码，
然后从操作码中解析出合约的各个函数对应的指令段，最后从这些指令段中找到
这些函数内部调用的其他函数的函数选择器
"""

# 标准库
import binascii

# 第三方库
from pyevmasm import disassemble_hex, disassemble_all, assemble_hex
from brownie.project import LabssProject

# 本地库


""" 获取brownie中的ContractContainer对象对应的指令序列 """
def get_instructions(contract_container):

    # contractcontainer的bytecode
    bytecode = contract_container.bytecode
    # 表示以太坊opcode的字符串
    instrs = disassemble_hex(assemble_hex(
        list(disassemble_all(binascii.unhexlify(bytecode)))))
    # 以太坊opcode列表
    instruction_sequence = instrs.split('\n')
    
    return instruction_sequence

""" 获取从入口代码处开始的指令序列 """
def get_instructions_start_from_entrancy(instructions):


    right_location = False
    idx = 0

    while not right_location:
        try:
            idx = instructions.index('PUSH4 0xffffffff', idx)
        except:
            raise Exception
        if not instructions[idx + 1].startswith('PUSH29'):
            idx += 1
            continue
        right_location = True
    
    if not right_location:
        raise Exception
    
    return instructions[idx - 8:]

""" 获取跳转表 """
def get_jump_table(instructions):
    
    jump_table = {}
    key = 0
    value = 0

    while value < len(instructions):
        jump_table[key] = value

        if instructions[value].startswith('PUSH'):
            push_suffix = int(instructions[value].split()[0].strip('PUSH'))
            key += push_suffix+1
            value += 1
        else:
            key += 1
            value += 1
    
    return jump_table

""" 获取智能合约入口代码中声明的函数选择器对应的index """
def get_func_signature_indexes(instructions):

    idx = 0
    func_signatures = []
    while idx < len(instructions):
        if instructions[idx] == 'STOP':
            break
        if instructions[idx].startswith('PUSH4') and \
            instructions[idx+1].startswith('DUP') and \
                instructions[idx+2] == 'EQ':
            func_signatures.append(
                (instructions[idx].split()[1],
                int(instructions[idx+3].split()[1], 16))
            )
        elif instructions[idx].startswith('PUSH4') and \
            instructions[idx+1] == 'EQ':
            func_signatures.append(
                (instructions[idx].split()[1],
                int(instructions[idx+2].split()[1], 16))
            )
        idx += 1
    
    return func_signatures


def get_func_start_line_number(func_signature_jump_line_number, jump_table, instructions):

    # 例：
    # 0x35: PUSH4 0x6289d385
    # 0x3a: DUP2
    # 0x3b: EQ
    # 0x3c: PUSH2 0x11c
    # func_signature_jump_line_number = 0x11c
    # value是0x11c对应的指令在instructions中的index
    value = jump_table[func_signature_jump_line_number]

    function_start_line_number = -1

    while value < len(instructions):
        if instructions[value].startswith('PUSH2') and \
            instructions[value+1].startswith('PUSH2') and \
                instructions[value+2] in ['JUMP', 'JUMPI']:
            function_start_line_number = int(instructions[value+1].split()[1], 16)
            break
        value += 1
    
    if function_start_line_number == -1:
        raise ValueError("Function start line")
    
    return function_start_line_number

""" 获取每一个函数的函数体 """
def get_func_body(start_line_number, jump_table, instructions):

    # 找到函数开始部分
    start_line_number = jump_table[start_line_number]
    JUMP_line_number = start_line_number + 1

    while True:
        if instructions[JUMP_line_number] == 'JUMP':
            break
        else:
            JUMP_line_number += 1
    
    return instructions[start_line_number: JUMP_line_number+1]

""" 从函数体中获取该函数内部调用的其它函数的function selector """
def get_inner_call_selectors_from_func_body(func_body):

    valid = False
    signatures = set()

    for instruction in func_body:
        if instruction == 'CALL':
            valid = True
        if instruction.startswith('PUSH4') and \
            instruction.split()[1]!="0xffffffff":
            signatures.add(instruction.split()[1])
    
    if valid:
        return signatures
    else:
        return set()

def get_function_selector_map(contract_container):

    function_selector_map = {}

    # 指令序列
    instructions = get_instructions(contract_container)
    # 去掉入口点前边的无关指令
    instructions = get_instructions_start_from_entrancy(instructions)

    # 跳转表
    jump_table = get_jump_table(instructions)
    # 获取其中的函数选择器，以及每个函数选择器对应的函数的index
    func_signature_indexes = get_func_signature_indexes(instructions)

    for signature, index in func_signature_indexes:
        ## 对每一个函数分析

        # print('signature:{}'.format(signature))
        # print('index:{}'.format(hex(index)))

        try:
            # 找到函数的开始下标
            start_line_number = get_func_start_line_number(index, jump_table, instructions)
        except:
            continue

        # print('start_line_number:{}'.format(hex(start_line_number)))
        
        # 获取函数体
        func_body = get_func_body(start_line_number, jump_table, instructions)
        
        # 获取函数签名
        signatures = get_inner_call_selectors_from_func_body(func_body)

        function_selector_map[signature] = signatures
    
    return function_selector_map

def merge_dict(d1, d2):

    for k, v in d2.items():
        if k in d1:
            d1[k].union(v)
        else:
            d1[k] = v

def get_all_function_selector_map():

    contract_container_list = LabssProject.dict().values()

    function_selector_map = {}

    for contract_container in contract_container_list:
        try:
            merge_dict(
                function_selector_map, 
                get_function_selector_map(contract_container))
        except:
            continue

    return function_selector_map


def main():

    # from brownie import Attack, EtherStore

    # with open('scripts/signature_analysis/instructions1.txt', 'w') as fw:
    #     instructions = get_instructions(Attack)
    #     for instruction in instructions:
    #         fw.write('{}\n'.format(instruction))

    # # function_selector_map = get_function_selector_map(Attack)
    # # print(function_selector_map)

    # print(Attack.signatures)
    # print(EtherStore.signatures)

    from .analysis_abi import get_selector2contractcontainer_map

    all_function_selector_map = get_all_function_selector_map()

    selector2contractcontainer_map = get_selector2contractcontainer_map()

    for key_selector, value_selectors in all_function_selector_map.items():
        if value_selectors:
            value_containers = set()
            for selector in value_selectors:
                value_containers.add(selector2contractcontainer_map[selector])
            all_function_selector_map[key_selector] = value_containers


    print(all_function_selector_map)
    # print()
    # print()
    # print(selector2contractcontainer_map)

    # for k , v in all_function_selector_map.items():
    #     print('{}\t\t{}'.format(k, v))

