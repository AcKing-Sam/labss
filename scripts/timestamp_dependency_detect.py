# 标准库
import logging

# 第三方库
from brownie.network.transaction import TransactionReceipt
from brownie.convert.utils import get_type_strings

# 本地库
from .generate_inputs import *
from .reentrancy_detect import generate_calldata
from .funcs import decode_call_tree, is_reentrancy
from .utils import FunctionSignature


def get_info_from_tx_receipt(tx_receipt):
    """ 从TransactionReceipt对象中获取信息 """

    # 判断传入参数类型是否合法
    if not isinstance(tx_receipt, TransactionReceipt):
        print("错误！ 传入参数不是TransactionReceipt类型！")
        
    # 该交易中被调用的合约
    contract_name = tx_receipt.contract_name
    # 该交易中被调用的函数
    fn_name = tx_receipt.fn_name
    # 该交易的gas limit
    gas_limit = tx_receipt.gas_limit
    # 函数的input
    input = tx_receipt.input
    # internal transfers
    internal_transfers = tx_receipt.internal_transfers
    # receiver
    receiver = tx_receipt.receiver
    # return value
    return_value = tx_receipt.return_value
    # subcalls
    subcalls = tx_receipt.subcalls
    # sender
    sender = tx_receipt.sender
    # status
    status = tx_receipt.status
    # value
    value = tx_receipt.value

    info_str = ''
    info_str += 'contract name: {}\n'.format(contract_name)
    info_str += 'func name: {}\n'.format(fn_name)
    info_str += 'gas limit: {}\n'.format(gas_limit)
    info_str += 'input: {}\n'.format(input)
    info_str += 'internal_transfers: {}\n'.format(internal_transfers)
    info_str += 'receiver: {}\n'.format(receiver)
    info_str += 'return_value: {}\n'.format(return_value)
    info_str += 'subcalls: {}\n'.format(subcalls)
    info_str += 'sender: {}\n'.format(sender)
    info_str += 'status: {}\n'.format(status)
    info_str += 'value: {}\n'.format(value)

    # return contract_name, fn_name, gas_limit, input, internal_transfers, \
    #     receiver, return_value, subcalls, sender, status, value

    return info_str

def generate_calldata_special(project_contract, func_abi, logger, agent_contract):

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
    param_list = generate_fuzz_params_special(param_list, agent_contract)
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

def generate_fuzz_params_special(param_list: list, agent_contract) ->list:
    """ 
    输入参数列表，生成模糊测试输入
    返回输入列表
    Arguments
    ---------
    param_list : list[str]
        参数类型列表
    Returns
    -------
    list
        生成的参数列表
    """

    return_list = []

    for param_type in param_list:
        return_list.append(generate_param_special(param_type, agent_contract))

    return return_list

def generate_param_special(param_type:str, agent_contract):
    """ 
    根据参数类型选择对应的函数，返回生成的值
    """

    if param_type.startswith('int') or param_type.startswith('uint'):
        if param_type.endswith('[]'):
            return generate_int_array(param_type.strip('[]'))
        return generate_int(param_type)
    elif param_type == 'bool':
        return generate_bool()
    elif param_type == 'address':
        return agent_contract.address   ### 对于address类型，永远返回该合约的地址
    elif param_type == 'str':
        return generate_str()
    elif param_type == 'bool[]':
        return generate_bool_array()
    elif param_type == 'address[]':
        return generate_address_array()
    elif param_type == 'str[]':
        return generate_str_array()


def send_ether_with_timestamp_operation(agent_contract, project_contract, logger):

    abi = project_contract.abi
    cnt = 1000000000000000000000
    flag = False
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
                flag = False
                # 判断是否成功发送以太币，小于 cnt，说明转账了
                if not project_contract.balance() < cnt :
                    flag = True
                # 接下来判断是否调用了 TIMESTAMP 操作码
                for oper_code in tx_receipt.trace:
                    if oper_code["op"] == 'TIMESTAMP' and flag is True:
                        break
                cnt = project_contract.balance()
        except KeyError:
            continue
    if flag is True :
        log_msg = '发现ts漏洞'
        logger.warning(log_msg)
    return flag

### 监测时间戳依赖漏洞
def timestamp_dependency_detect(
    agent_contract, project_contract, logger,
    result_file_path='results/'):

    # log记录当前正在被测试的合约  时间戳依赖漏洞
    log_msg = '当前被测合约: {}'.format(project_contract._name)
    log_msg += '(detecting timestamp dependency)'
    logger.warning(log_msg)

    # 结果文件路径
    result_file_path += project_contract._name

    result = send_ether_with_timestamp_operation(agent_contract, project_contract, logger)
    return result



def config_log(log_filename):

    LOG_FORMAT = "%(asctime)s - %(levelname)s\n%(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    logging.basicConfig(
        filename = 'logs/{}.log'.format(log_filename),
        level = logging.INFO,
        format = LOG_FORMAT,
        datefmt = DATE_FORMAT
    )


def main():
    from brownie import Agent, TUStoken


    agent_contract = Agent.deploy({'from':accounts[0]})

    accounts[-1].transfer(agent_contract, '3999999999998200000 wei')

    project_contract = TUStoken.deploy({'from':agent_contract.address})

    accounts[-1].transfer(project_contract, '90000000000000000 wei')

    timestamp_dependency_detect(agent_contract, project_contract, logging)

    pass