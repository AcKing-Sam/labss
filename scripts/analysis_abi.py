# 标准库
import sha3

# 第三方库
from brownie.convert.utils import get_type_strings
from brownie.project import LabssProject

# 本地库
from .utils import FunctionSignature
from .disamble_bytecode import get_all_function_selector_map


class FunctionSignature:
    """ 
    表示Solidity函数签名的Python Class

    属性：
    self.func_name : str
        函数名
    self.param_list : list[str]
        函数参数类型列表
    self.payable : bool
        函数是否有payable标识符
    self.function_signature_str : str
        函数签名，例如：withdrawFunds(uint256)
    
    方法：
    self.get_function_selector()
        返回该函数的函数选择器

    """

    def __init__(self, func_name: str, param_list: list, payable: bool, func_selector: str = None):
        self.func_name = func_name
        self.param_list = param_list
        self.payable = payable
        self.function_signature_str = self.get_function_signature_str()
        if func_selector:
            self.func_selector = func_selector
        else:
            self.func_selector = self.get_function_selector()

    def get_function_signature_str(self):
        """ 
        返回函数签名字符串
        例如： func_name(param1,param2,param3)
        """

        function_signature_str = ''
        function_signature_str += self.func_name
        function_signature_str += '('
        if self.param_list:
            for param in self.param_list[:-1]:
                function_signature_str += '{},'.format(param)
            function_signature_str += self.param_list[-1]
        function_signature_str += ')'

        return function_signature_str
    
    def get_function_selector(self):
        """ 
        返回函数选择器
        """

        s = sha3.keccak_256()
        s.update(self.function_signature_str.encode('utf-8'))
        hex = s.hexdigest()
        bytes4 = "0x"+hex[:8]
        return bytes4


def get_func_signatures(project_contract):
    """ 
    输入部署合约返回的ProjectContract对象，解析该合约中各个函数的函数签名

    Arguments
    ---------
    project_contract :  brownie.network.contract.ProjectContract
        brownie中一个已经部署好的合约对象
        
    Returns
    -------
    list[FunctionSignature]
        该合约中函数签名的列表
    """

    function_signature_list = []

    for func in project_contract.abi:
        if 'constant' in func and func['constant'] == False:
            # 函数的constant是False

            # 函数名
            func_name = func['name']

            # 函数参数
            param_list = get_type_strings(func['inputs'])

            # payable标识符
            payable = False
            if 'payable' in func and func['payable']:
                payable = True

            function_signature = FunctionSignature(func_name, param_list, payable)

            function_signature_list.append(function_signature)

    return function_signature_list


def get_selector2contractcontainer_map():
    """ 
    分析brownie项目下的所有ABI，创建一个map
    这个map的key是一个function selector
    value是含有这个function selector的ContractContainer对象
    """

    selector2contractcontainer_map = {}

    contract_container_list = LabssProject.dict().values()

    for contract_container in contract_container_list:
        function_selectors = contract_container.signatures.values()
        for function_selector in function_selectors:
            selector2contractcontainer_map[function_selector] = contract_container

    return selector2contractcontainer_map

def get_selector2containers_map():
    """ 
    分析brownie项目下的所有abi，创建一个map
    这个map的key是一个function selector
    value是这个function selector所表示的函数中调用的
    其他函数所在合约的ContractContainer的集合
    """

    all_function_selector_map = get_all_function_selector_map()

    selector2contractcontainer_map = get_selector2contractcontainer_map()

    for key_selector, value_selectors in all_function_selector_map.items():
        if value_selectors:
            value_containers = set()
            for selector in value_selectors:
                try:
                    value_containers.add(selector2contractcontainer_map[selector])
                except:
                    continue
            all_function_selector_map[key_selector] = value_containers

    return all_function_selector_map


def main():

    # contract = EtherStore.deploy({'from':accounts[0]})

    # for func_signature in get_func_signatures(contract):
    #     print(func_signature.func_name)
    #     print(func_signature.param_list)

    get_selector2contractcontainer_map()