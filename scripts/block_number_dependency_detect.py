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


def send_ether_with_timestamp_operation(agent_contract, project_contract, logger):

    abi = project_contract.abi
    cnt = 10000
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

                # 判断是否成功发送以太币，小于cnt，说明转账了
                if not project_contract.balance() < cnt :
                    break
                # 接下来判断是否调用了BLOCKNUMBER操作码
                for oper_code in tx_receipt.trace:
                    if oper_code["op"] == 'BLOCKNUMBER':
                        flag = True
                if flag:
                    break
                cnt = project_contract.balance()
        except KeyError:
            continue
    
    return flag

### 监测时间戳依赖漏洞
def timestamp_dependency_detect(
    agent_contract, project_contract, logger,
    result_file_path='results/'):

    # log记录当前正在被测试的合约  区块号依赖漏洞
    log_msg = '当前被测合约: {}'.format(project_contract._name)
    log_msg += '(detecting block number dependency)'
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


    pass