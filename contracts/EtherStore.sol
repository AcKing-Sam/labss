pragma solidity ^0.4.22;

contract EtherStore{
    
    // 每次最多取1 ether
    uint256 public withdrawalLimit = 1 ether;
    // 上次取款时间
    mapping(address => uint256) public lastWithdrawTime;
    // 账户余额
    mapping(address => uint256) public balances;

    /// @notice 其他合约向本合约存款
    /// @dev 不太清楚为什么要以etherStore.depositFunds.value(5 ether)()的形式调用该函数
    function depositFunds() public payable{
        balances[msg.sender] += msg.value;
    }

    /// @notice 其他合约从本合约取款
    /// @param _weiToWithdraw 取款的数额
    function withdrawFunds(uint256 _weiToWithdraw) public{
        require(balances[msg.sender] >= _weiToWithdraw);
        
        // 限制取回金额不能超过1Ether
        require(_weiToWithdraw<=withdrawalLimit);
        //限制每周只能取一次款
        require(now >= lastWithdrawTime[msg.sender] + 1 weeks);
        require(msg.sender.call.value(_weiToWithdraw)());
        balances[msg.sender] -= _weiToWithdraw;
        lastWithdrawTime[msg.sender] = now;
    }

}
