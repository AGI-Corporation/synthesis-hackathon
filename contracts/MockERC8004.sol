// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MockERC8004
 * @notice Minimal mock ERC-8004 registry for use in tests only.
 * @dev    NOT for production. Deploy the real ERC-8004 registry on Base.
 */
contract MockERC8004 {
    mapping(address => bool)    private _isAgent;
    mapping(address => bytes32) private _agentIds;

    event AgentRegistered(address indexed agent, bytes32 agentId);

    function registerAgent(address agent) external {
        bytes32 id = keccak256(abi.encodePacked(agent, block.timestamp));
        _isAgent[agent]   = true;
        _agentIds[agent]  = id;
        emit AgentRegistered(agent, id);
    }

    function isAgent(address account) external view returns (bool) {
        return _isAgent[account];
    }

    function agentOf(address account) external view returns (bytes32) {
        return _agentIds[account];
    }
}
