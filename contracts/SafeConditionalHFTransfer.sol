pragma solidity ^0.4.18;

/**
 *Submitted for verification at Etherscan.io on 2016-07-25
*/

contract ClassicCheck {
       function isClassic() constant returns (bool isClassic);
}

contract SafeConditionalHFTransfer {

    bool classic;
    uint safe_counter;
    
    function SafeConditionalHFTransfer() {
        // classic = ClassicCheck(0x882fb4240f9a11e197923d0507de9a983ed69239).isClassic();
    }
    
    function classicTransfer(address to) {
        if (!classic) 
            msg.sender.send(msg.value);
        else
            to.send(msg.value);
    }

    function () {
        safe_counter += 1;
    }
    
    function transfer(address to) {
        if (classic)
            msg.sender.send(msg.value);
        else
            to.send(msg.value);
    }
    
}
