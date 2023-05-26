import pprint
import logging

from brownie import accounts
from brownie.convert.utils import get_type_strings

from .generate_inputs import generate_fuzz_params
from .funcs import decode_call_tree, is_reentrancy
from .utils import FunctionSignature
from .disamble_bytecode import *


def freezing_ether_detect(
    agent_contract, project_contract, logger,
    result_file_path='results/'
):

    log_msg = '当前被测合约: {}'.format(project_contract._name)
    log_msg += '(detecting freezing ether)'
    logger.warning(log_msg)

    # 判断能否向该合约转账ether
    if not send_ether_with_fallback(project_contract):
        # 如果不能直接向project_contract转账
        if not send_ether_with_payable_function(agent_contract, project_contract, logger):
            # 如果也不能通过payable函数向project_contract转账
            ## 那么该合约不会有freezing ether漏洞

            log_msg = '不能向被测合约转账，不含freezing ether漏洞'
            logger.warning(log_msg)
            
            return False

    is_freezing_ether = False
    abi = project_contract.abi
    flag1 = False
    flag2 = True
    flag3 = True
    for func_abi in abi:
        try:
            if func_abi['type'] != 'fallback':
                # 对该合约函数进行检测
                calldata = generate_calldata(project_contract, func_abi, logger)
                if not calldata:
                    continue
                # 用代理合约调用该函数
                tx_receipt = agent_contract.AgentCallWithoutValue(
                    project_contract.address, calldata,
                )

                flag1 = False
                flag2 = True
                flag3 = True

                # 判断是否调用了 DELEGATECALL 操作码
                for oper_code in tx_receipt.trace:
                    if oper_code["op"] == 'DELEGATECALL':
                        flag1 = True
                # 判断是否调用了call/suicide
                for oper_code in tx_receipt.trace:
                    if oper_code["op"] == 'CALL':
                        flag2 = False
                    if oper_code["op"] == 'SELFDESTRUCT':
                        flag3 = False
                if flag1 is False or flag2 is False or flag3 is False:
                    continue
                # 判断是否发生了交易，即判断是否发生了send or transfer
                if tx_receipt.value > 0 and tx_receipt.sender == project_contract.address :
                    continue
                log_msg = '当前合约含有冻结以太币漏洞'
                logger.warning(log_msg)
                is_freezing_ether = True
                break
        except KeyError:
            continue
    
    return is_freezing_ether


def fuzz_func(agent_contract, project_contract, func_abi, logger):
    
    calldata = generate_calldata(project_contract, func_abi, logger)
    if not calldata:
        return False, '', ''

    try:
        if is_payable(func_abi):
            msg_value = '1 ether'

            tx_receipt = agent_contract.AgentCallWithValue(
                project_contract.address, calldata,
                {"value":msg_value}
            )
        else:
            tx_receipt = agent_contract.AgentCallWithoutValue(
                project_contract.address, calldata
            )
    except:
        return False, '', ''

    try:
        tx_receipt.wait(1)
    except:
        return False, '', ''
    
    # call_trace经过修改，返回一个表示调用关系的嵌套列表
    tree_structure = tx_receipt.call_trace()

    pp = pprint.PrettyPrinter(indent=4)
    log_msg = '表示函数调用链的嵌套列表:\n'
    log_msg += pp.pformat(tree_structure)
    logger.warning(log_msg)

    # 解析嵌套列表，返回一个有向图
    graph, tree_str = decode_call_tree(tree_structure, logger)

    has_reentrancy, call_chain = is_reentrancy(graph, logger)

    return has_reentrancy, call_chain, tree_str

def is_payable(func_abi):

    if 'payable' in func_abi:
        return func_abi.get('payable')
    return False

def generate_calldata(project_contract, func_abi, logger):

    # 函数名
    func_name = func_abi['name']
    # 函数参数
    param_list = get_type_strings(func_abi['inputs'])
    # payable
    payable = False
    if 'payable' in func_abi:
        payable = func_abi['payable']

    function_signature = FunctionSignature(func_name, param_list, payable)
    logger.warning(str(function_signature))

    # brownie中表示该函数的对象
    try:
        func_object = eval('project_contract.{}'.format(func_name))
    except:
        return None

    # 生成参数
    param_list = generate_fuzz_params(param_list)
    param_list = tuple(param_list)

    log_msg = '执行函数: {}'.format(func_name)
    log_msg += '('
    if param_list:
        for param in param_list:
            log_msg += '{},'.format(param)
    log_msg += ')'
    logger.warning(log_msg)

    try:
        calldata = func_object.encode_input(*param_list)
    except:
        return None

    return calldata

def send_ether_with_payable_function(agent_contract, project_contract, logger):

    abi = project_contract.abi

    # 对每一个函数判断payable标识符
    for func_abi in abi:
        try:
            if func_abi['payable'] == True and func_abi['type'] != 'fallback':

                calldata = generate_calldata(project_contract, func_abi, logger)
                if not calldata:
                    continue

                msg_value = '20000 wei'
                tx_receipt = agent_contract.AgentCallWithValue(
                    project_contract.address, calldata,
                    {"value":msg_value}
                )

                # 判断是否发送成功
                if project_contract.balance() > 0:
                    break
        except KeyError:
            continue
    
    if project_contract.balance() > 0:
        return True
    return False


def send_ether_with_fallback(project_contract):
    """
    判断project_contract是否有fallback函数，
    如果有，则直接向其转账20ether，
    转账成功返回True，其他情况都返回False
    """

    abi = project_contract.abi

    # 判断是否有fallback函数
    has_fallback = False
    for func_abi in abi:
        if func_abi['type'] == 'fallback' and func_abi['payable']:
            has_fallback = True
    
    # 如果没有fallback函数则返回False
    if not has_fallback:
        return False
    
    # 如果有，尝试直接向该合约转账，如果成功则返回True，否则返回False
    try:
        accounts[-2].transfer(
            project_contract.address, '20000 wei')
    except:
        return False


    if project_contract.balance() > 0:
        return True
    else:
        return False


def main():
    from brownie import Agent, AnyContract

    agent_contract = Agent.deploy({'from':accounts[0]})

    accounts[-1].transfer(agent_contract, '900000000000000000 wei')

    project_contract = AnyContract.deploy({'from':agent_contract.address})

    freezing_ether_detect(agent_contract, project_contract, logging)

    pass
