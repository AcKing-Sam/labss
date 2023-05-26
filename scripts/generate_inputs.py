# 标准库
import random
import string

# 第三方库
from brownie import accounts
from brownie.convert.utils import get_int_bounds

# 本地库
from .analysis_abi import get_selector2containers_map

def generate_fuzz_params(param_list: list, func_selector = None) ->list:
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
        return_list.append(generate_param(param_type, func_selector))

    return return_list

def generate_param(param_type:str, func_selector = None):
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
        return generate_address(func_selector)
    elif param_type == 'str':
        return generate_str()
    elif param_type == 'bool[]':
        return generate_bool_array()
    elif param_type == 'address[]':
        return generate_address_array()
    elif param_type == 'str[]':
        return generate_str_array()
    

def generate_int(type_str:str) -> int:
    """ 
    随机生成不同的int值

    生成策略：
    1. 接近下界的值
    2. 接近上界的值
    3. 中间值
    4. 容易导致异常的值(如int8类型的0b10000000，容易导致上溢)
    """

    lower_bound, upper_bound = get_int_bounds(type_str)

    interval1 = (lower_bound, lower_bound + 10)
    interval2 = (lower_bound + 10, lower_bound + 20)
    interval3 = (upper_bound // 2 - 20, upper_bound // 2 + 20)
    interval4 = (upper_bound - 20, upper_bound)

    r = random.randint(1, 6)
    if r == 1:
        start, stop = interval1
        result = random.randrange(start, stop)
    elif r == 2:
        start, stop = interval2
        result = random.randrange(start, stop)
    elif r == 3:
        start, stop = interval3
        result = random.randrange(start, stop)
    elif r == 4:
        start, stop = interval4
        result = random.randrange(start, stop)
    elif r == 5:
        result = upper_bound
    elif r == 6:
        result = (upper_bound+1)//2

    # return result
    # 暂时改为1
    return 1e18


def generate_bool()->bool:
    """ 
    随机生成布尔值
    """
    
    r = random.randint(0,1)
    
    if r:
        return True
    else:
        return False
    
def generate_address(func_selector = None):
    """ 
    生成address类型的参数
    """

    if func_selector:
        selector2containers_map = get_selector2containers_map()

        # 获取该函数内部调用的其他函数所在合约的ContractContainer对象
        containers = set()
        if func_selector in selector2containers_map:
            containers = selector2containers_map[func_selector]
        if len(containers) != 0:
            return list(containers)[0][0]

    return accounts[3]


def generate_str()->str:

    character_set = list(string.ascii_letters + string.digits)

    # 随机正数作为字符串长度
    random_length = random.randint(1,30)

    return ''.join(random.sample(character_set, random_length))


def generate_int_array(param_type:str):
    
    # 随机正数作为数组长度
    random_length = random.randint(1,30)

    int_array = []
    for i in range(random_length):
        int_array.append(generate_int(param_type))

    return int_array

def generate_bool_array():

    # 随机正数作为数组长度
    random_length = random.randint(1,30)

    bool_array = []
    for i in range(random_length):
        bool_array.append(generate_bool())

    return bool_array

def generate_address_array():

    # 随机正数作为数组长度
    random_length = random.randint(1,30)

    address_array = []
    for i in range(random_length):
        address_array.append(generate_address())

    return address_array

def generate_str_array():

    # 随机正数作为数组长度
    random_length = random.randint(1,30)

    str_array = []
    for i in range(random_length):
        str_array.append(generate_str())

    return str_array
    

def main():
    for i in range(100):
        # print(bin(generate_int('uint256')))
        # print(generate_fuzz_params(['int256', 'bool']))
        print(generate_str_array())


if __name__ == '__main__':
    main()