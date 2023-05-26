pragma solidity ^0.4.19;

contract PIGGYBANK
{
    mapping (address => uint) public Accounts;
    
    uint public MinSum = 1 ether;
    
    PIGGYBANK_Log LogFile;
    
    uint putBlock;
    
    constructor(address _log)
    public 
    {
        LogFile = PIGGYBANK_Log(_log);
    }
    
    function Put(address to)
    public
    payable
    {
        Accounts[to]+=msg.value;
        LogFile.AddMessage(msg.sender,msg.value,"Put");
        putBlock = block.number;
    }
    
    function Collect(uint _am)
    public
    payable
    {
        if(msg.sender.call.value(_am)())
        {
            Accounts[msg.sender]-=_am;
            LogFile.AddMessage(msg.sender,_am,"Collect");
        }
    }
    
    function() 
    public 
    payable
    {
    }    
    
}

contract PIGGYBANK_Log 
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
