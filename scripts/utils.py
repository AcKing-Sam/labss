import _pysha3


class FunctionSignature:

    def __init__(self, func_name: str, param_list: list, payable: bool, func_selector: str = None):
        self.func_name = func_name
        self.param_list = param_list
        self.payable = payable
        self.function_signature_str = self.get_function_signature_str()
        self.func_selector = ''
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

        s = _pysha3.keccak_256()
        s.update(self.function_signature_str.encode('utf-8'))
        hex = s.hexdigest()
        bytes4 = "0x"+hex[:8]
        return bytes4

    def __repr__(self):

        self_str = 'function name: {}\n'.format(self.func_name)

        self_str += 'param_list: {}\n'.format(self.param_list)

        self_str += 'payable: {}\n'.format(self.payable)

        self_str += 'function signature: {}\n'.format(self.function_signature_str)

        self_str += 'function selector: {}\n'.format(self.func_selector)

        return self_str
        
class CallInformation:

    def __init__(
        self, caller, callee, fn_name, input, msg_value):
        self.caller = caller
        self.callee = callee
        self.fn_name = fn_name
        self.input = input
        self.msg_value = msg_value

    def __str__(self):

        attrs_str = ''

        attrs_str += 'caller:{}\ncallee:{}\nfn_name:{}\n'.format(
            self.caller, self.callee, self.fn_name)
        
        attrs_str += 'input:{}\nmsg_value:{}\n'.format(
            self.input, self.msg_value)

        return attrs_str
