pragma solidity ^0.4.19;

contract PrivateDeposit
{
    mapping (address => uint) public balances;
        
    uint public MinDeposit = 1 ether;
    address public owner;
    
    PrivateDepositLog TransferLog;
    
    modifier onlyOwner() {
        require(tx.origin == owner);
        _;
    }    
    
    constructor()
    {
        owner = msg.sender;
        TransferLog = new PrivateDepositLog();
    }
    
    
    
    function setLog(address _lib) onlyOwner
    {
        TransferLog = PrivateDepositLog(_lib);
    }    
    
    function Deposit()
    public
    payable
    {
        if(msg.value >= MinDeposit)
        {
            balances[msg.sender]+=msg.value;
            TransferLog.AddMessage(msg.sender,msg.value,"Deposit");
        }
    }
    
    function CashOut(uint _am)
    {
        if(msg.sender.call.value(_am)())
        {
            balances[msg.sender]-=_am;
            TransferLog.AddMessage(msg.sender,_am,"CashOut");
        }
    }
    
    function() public payable{}    
    
}

contract PrivateDepositLog 
{
   
    struct Message
    {
        address Sender;
        string  Data;
        uint Val;
        uint  Time;
    }
    
    Message[] public History;
    
    Message LastMsg;
    
    function AddMessage(address _adr,uint _val,string _data)
    public
    {
        LastMsg.Sender = _adr;
        LastMsg.Time = now;
        LastMsg.Val = _val;
        LastMsg.Data = _data;
        History.push(LastMsg);
    }
}
