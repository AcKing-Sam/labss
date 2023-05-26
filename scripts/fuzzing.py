# 标准库
import random
import os
import logging
import re

# 第三方库
from brownie import EtherStore, Agent, FunFairSale
from brownie import accounts
from brownie.project import LabssProject

# 本地库
from .config import k
from .deploy import deploy_all_contracts
from .analysis_abi import get_func_signatures
from .generate_inputs import generate_fuzz_params
from .funcs import decode_call_tree, is_reentrancy
from .utils import CallInformation
from .gasless_send_detect import gasless_send_detect, get_info_from_tx_receipt
from .reentrancy_detect import reentrancy_detect


def get_all_contracts(file_paths: list):
    """ 
    输入一个文件路径列表，读取这些路径下的智能合约的名字，返回一个包含这些名字并且名字
    之间以逗号分隔的字符串

    Arguments
    ---------
    file_paths : list[str]
        文件路径列表

    Returns
    -------
    str
        以逗号分隔的智能合约的名字
    """

    contracts = []

    for file_path in file_paths:
        for file_name in os.listdir(file_path):
            contracts.append(file_name.split('.')[0])
        
    contracts_str = '{}'.format(contracts[0])
    for contract in contracts[1:]:
        contracts_str += ', {}'.format(contract)

    return contracts_str


def fuzzing():

    logger = config_log()
    
    # 获取所有ContractContainer对象
    contract_containers = get_contract_containers()

    # 部署所有合约
    agent_contract = deploy_all_contracts(logger)

    gasless_send_list_fw = open('results/gasless_send_list.txt', 'w')
    reentrancy_list_fw = open('results/reentrancy_list.txt', 'w')

    for contract_container in contract_containers:

        if len(contract_container) == 0:
            continue

        project_contract = contract_container[0]

        ## 检测无gas发送漏洞
        result = gasless_send_detect(agent_contract, project_contract, logger)
        if result:
            gasless_send_list_fw.write(project_contract._name)
            gasless_send_list_fw.write('\n')
        
        ## 检测可重入漏洞
        result, tree_str, reentrancy_func_name, call_chain = reentrancy_detect(
            agent_contract, project_contract, logger)
        if result:
            reentrancy_list_fw.write(contract_container._name)
            reentrancy_list_fw.write('\n')
            if tree_str:
                # reentrancy_list_fw.write(strip_ansi_escape_code(tree_str))
                reentrancy_list_fw.write(
                    '{}.{}'.format(project_contract._name, reentrancy_func_name)
                )
                reentrancy_list_fw.write('\n')
                reentrancy_list_fw.write(call_chain)
                reentrancy_list_fw.write('\n')
            reentrancy_list_fw.write('\n')
        

def strip_ansi_escape_code(tree_str_line):
    """ 去掉用于显示颜色的ANSI escape code """

    tree_str_line = re.sub('\x1b.*?m', '', tree_str_line)

    return tree_str_line

def get_contract_containers():
    """ 获取当前brownie项目的所有ContractContainer对象，以列表形式返回 """

    # 获取当前brownie项目的所有ContractContainer对象
    contract_container_list = list(LabssProject.dict().values())

    return contract_container_list

### 配置日志
def config_log():

    # 获取logger
    logger = logging.getLogger('fuzzing')

    LOG_FORMAT = "%(asctime)s \n%(message)s"
    DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"

    # 部署时log
    deploy_handler = logging.FileHandler('logs/deploy.log', 'w')

    # 执行时log
    execute_handler = logging.FileHandler('logs/execute.log', 'w')

    deploy_handler.setFormatter(logging.Formatter(
        fmt = LOG_FORMAT,
        datefmt = DATE_FORMAT
    ))

    execute_handler.setFormatter(logging.Formatter(
        fmt = LOG_FORMAT,
        datefmt = DATE_FORMAT
    ))

    info_filter = logging.Filter()
    info_filter.filter = lambda record: record.levelno == logging.INFO
    warning_filter = logging.Filter()
    warning_filter.filter = lambda record: record.levelno == logging.WARNING

    deploy_handler.addFilter(info_filter)
    execute_handler.addFilter(warning_filter)

    logger.addHandler(deploy_handler)
    logger.addHandler(execute_handler)

    logger.setLevel('INFO')

    return logger


def main():
    fuzzing()
