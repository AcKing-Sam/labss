pragma solidity ^0.4.22;

contract Agent{
    uint public count = 0;
    // 要调用的合约的地址
    address  public call_contract_addr;
    // calldata
    bytes  public  call_msg_data;
    bool public turnoff = true;

    uint public reentrancy_flag = 1;
    
    bool public hasValue = false;
    uint public sendCount = 0;
    uint public sendFailedCount =0;

    // 打印gasless send所需变量
    event gaslessSend(
        uint msg_value
    );
    
    function() payable {
        call_contract_addr.call(call_msg_data);
    }
    
    function Agent(){

    }
    function getContractAddr() returns(address addr){
        return call_contract_addr;
    }
    function getCallMsgData() returns(bytes msg_data){
        return call_msg_data;
    }
    function AgentCallWithoutValue(address contract_addr,bytes msg_data){
        hasValue = false;
        call_contract_addr  = contract_addr;
        call_msg_data = msg_data;
        contract_addr.call(msg_data);
    }
    function AgentCallWithValue(address contract_addr,bytes msg_data) payable{
      hasValue = true;
      uint msg_value = msg.value;
      call_contract_addr = contract_addr;
      call_msg_data = msg_data;
      contract_addr.call.value(msg_value)(msg_data);
    }
    function AgentSend(address contract_addr) payable returns(bool){

        sendCount ++;
        bool sent = contract_addr.send(msg.value);
        if(!sent){
            sendFailedCount ++;
            emit gaslessSend(
                msg.value
            );
            return false;
        }
        return true;
    }

    function uint2str(uint _i) internal pure returns (string memory _uintAsString) {
        if (_i == 0) {
            return "0";
        }
        uint j = _i;
        uint len;
        while (j != 0) {
            len++;
            j /= 10;
        }
        bytes memory bstr = new bytes(len);
        uint k = len;
        while (_i != 0) {
            k = k-1;
            uint8 temp = (48 + uint8(_i - _i / 10 * 10));
            bytes1 b1 = bytes1(temp);
            bstr[k] = b1;
            _i /= 10;
        }
        return string(bstr);
    }
    
}