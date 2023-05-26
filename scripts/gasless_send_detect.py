# 标准库
import logging

# 第三方库
from brownie.network.transaction import TransactionReceipt
from brownie import accounts

# 本地库


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


def gasless_send_detect(
    agent_contract, project_contract, logger,
    result_file_path='results/'):

    # log记录当前正在测试被测合约的gasless send漏洞
    log_msg = '当前被测合约: {}'.format(project_contract._name)
    log_msg += '(detecting gasless send)'
    logger.warning(log_msg)

    # 结果文件路径
    result_file_path += project_contract._name

    # 判断project_contract是否有fallback函数
    has_fallback = False
    for func in project_contract.abi:
        if 'fallback' in func.values():
            has_fallback = True
    # 如果没有fallback函数，则不用检测gasless send漏洞
    if not has_fallback:

        # 结果信息
        result_msg = '该合约没有fallback函数，所以不会有gasless send漏洞\n'
        # TODO 将result_msg写入结果文件

        # log记录没有fallback函数
        logger.warning(result_msg)
        
        return False

    # 将send()的信息计入log文件
    log_msg = 'send from {} to {}\n'.format(
        agent_contract.address, project_contract.address)

    # log记录send信息
    logger.warning(log_msg)

    # 使用AgentSend向该合约地址转账
    sent = agent_contract.AgentSend(
        project_contract.address, {'value':1})
    sent.wait(1)

    if len(sent.events) > 0:
        try:
            log_msg += 'msg.value: {}WEI'.format(sent.events[0]['msg_value'])
        except:
            pass
    
    # 如果返回值为false，则说明send失败，有gasless send漏洞
    if not sent.return_value:
        # 结果信息
        result_msg = '存在gasless send漏洞\n'
        result_msg += 'send方法的msg.value: {}Wei\n\n'.format(sent.events[0]['msg_value'])
        # TODO 将result_msg写入结果文件

        logger.warning(result_msg)

    result = not sent.return_value

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
    from brownie import Agent, BetBuyer, BigRisk, BuyerFund, CreditDepositBank
    contract_list = [BetBuyer, BigRisk, BuyerFund, CreditDepositBank]

    agent_contract = Agent.deploy({'from':accounts[0]})

    accounts[-1].transfer(agent_contract, '900000000000000000 wei')

    project_contract = BetBuyer.deploy({'from':agent_contract.address})
    gasless_send_detect(agent_contract, project_contract, logging, 'results/{}'.format(project_contract._name))
    '''
    for contract_container in contract_list:
        agent_contract, project_contract = deploy_contract(contract_container)
        gasless_send_detect(agent_contract, project_contract, 'results/{}'.format(project_contract._name))
    '''
    pass
