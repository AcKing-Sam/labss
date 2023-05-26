# 标准库
from calendar import c
import logging
import json

# 第三方库
from brownie import accounts, Agent
from web3 import Web3
from brownie.convert.utils import get_type_strings
from brownie.project import LabssProject

# 本地库
# from .generate_inputs import generate_fuzz_params
from .utils import FunctionSignature



# 配置 部署合约 的日志信息
def config_log(log_filename):
    LOG_FORMAT = "%(asctime)s - %(levelname)s\n%(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
    logging.basicConfig(
        filename = 'logs/{}.log'.format(log_filename),
        level = logging.INFO,
        format = LOG_FORMAT,
        datefmt = DATE_FORMAT
    )


def deploy_contract_with_web3(json_file_path:str, owner_address:str):

    # 连接到本地geth节点
    web3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
    # 判断是否连接成功
    if not web3.isConnected():
        print('web3未成功连接！')
        return

    # 获取ABI和字节码
    with open(json_file_path, 'r') as fr:
        content = fr.read()
        abi = json.loads(content)['abi']
        bytecode = json.loads(content)['bytecode']

    # 创建contract对象
    new_contract = web3.eth.contract(bytecode=bytecode, abi=abi)
    # 选项
    option = {'from': owner_address, 'gas': 1000000}
    # 发起交易部署合约
    tx_hash = new_contract.constructor().transact(option)
    # 等待挖矿使得交易成功
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_hash)

    return tx_receipt.contractAddress
    

def deploy_all_contracts(logger):

    # 默认账户
    accounts.default = accounts[0]
    # 部署代理合约
    agent_contract = Agent.deploy()
    # 向Agent合约转账
    accounts[-1].transfer(agent_contract.address, '9 ether')

    # 日志记录智能合约名字、地址和余额
    log_msg = 'contract name: {}\ncontract address: {}\n'.format(
        agent_contract._name, agent_contract.address)
    log_msg += 'contract balance: {}\n'.format(
        agent_contract.balance().to('ether'))
    logger.info(log_msg)

    ## 部署其他合约
    # 获取brownie项目中所有的ContractContainer对象
    contract_container_list = LabssProject.dict().values()

    for contract_container in contract_container_list:
        # 对于brownie项目中的每一个ContractContainer对象

        # 不再重复部署代理合约
        if contract_container._name == 'Agent':
            continue
    
        # 如果该合约对象还没有被部署过，进行部署
        if len(contract_container) == 0:
            # 获取ABI
            abi = contract_container.abi
            constructor_has_inputs = False
            # 判断构造函数是否有参数
            for function_abi in abi:
                if function_abi['type'] == 'constructor' and \
                    function_abi['inputs']:
                    constructor_has_inputs = True
                    constructor_abi = function_abi
            # 如果有输入参数，进行分析
            if constructor_has_inputs:
                try:
                    function_abi = constructor_abi
                    func_name = function_abi['name']
                    param_list = get_type_strings(function_abi['inputs'])
                    function_signature = FunctionSignature(func_name, param_list, False)

                    param_list = tuple(generate_fuzz_params(param_list, function_signature.func_selector))

                    project_contract = contract_container.deploy(*param_list, {'from':agent_contract})

                    # 记录被部署的合约名字、地址和余额
                    log_msg = 'contract name: {}\ncontract address: {}\n'.format(
                        project_contract._name, project_contract.address)
                    log_msg += 'contract balance: {}\n'.format(
                        project_contract.balance().to('ether'))
                    logger.info(log_msg)
                    continue
                except:
                    continue

        project_contract = contract_container.deploy({'from':agent_contract})
        ## 给被部署的待测合约转账 10000 以太币，用于测试时间戳依赖漏洞和区块号依赖漏洞，观察函数运行时，是否运行了op和向外转账
        # accounts[-1].transfer(project_contract.address, '10000 ether')
        # 记录智能合约名字、地址和余额
        log_msg = 'contract name: {}\ncontract address: {}\n'.format(
            project_contract._name, project_contract.address)
        log_msg += 'contract balance: {}\n'.format(
            project_contract.balance().to('ether'))
        logger.info(log_msg)

    return agent_contract




def main():

    # from .reentrancy_detect import reentrancy_detect

    # contract_address = deploy_contract_with_web3('build/contracts/Agent.json', str(accounts[0].address))

    # from brownie.network.contract import ContractContainer

    # contract_container = ContractContainer()
    # contract = ContractContainer.at(address=contract_address)
    # print(type(contract))

    # from brownie.project import TokenProject

    # build = TokenProject._build

    # for name, data in build.items():
    #     print(build.get(name)['abi'])

    # print(TokenProject.dict())

    # 事先配置日志
    # config_log('../logs/deploy')
    deploy_all_contracts(logging)

    contract_container_list = LabssProject.dict().values()

    for contract_container in contract_container_list:
       print(len(contract_container))

    # agent_contract = Agent[0]

    # for contract_container in contract_container_list:
    #     if len(contract_container) > 0:
    #         project_contract = contract_container[0]

    #         reentrancy_detect(agent_contract, project_contract)
    

