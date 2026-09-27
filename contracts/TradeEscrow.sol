// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./MockERC20.sol";
import "./TokenizedBillOfLading.sol";

/**
 * @title TradeEscrow (CitiFlow Escrow Engine)
 * @author CitiFlow Escrow Team for Drunix Hackathon with Citi
 * @notice Programmable Smart Escrow handling multi-milestone payments, automated delivery-vs-payment (DvP),
 * and dual-rail settlement bridging (NPCI UPI / e-RUPI and Citi Treasury ISO 20022).
 */
contract TradeEscrow {
    enum EscrowStatus {
        Created,
        Funded,
        InExecution,
        Completed,
        Disputed,
        Refunded,
        Cancelled
    }

    enum SettlementRail {
        OnChainDigitalRupee, // e-INR ERC20
        OnChainCitiUSD,      // cUSD ERC20
        OffChainUPIRealtime, // NPCI UPI 2.0 / AutoPay Mandate
        OffChaineRUPILinked, // NPCI e-RUPI Purpose-Bound Voucher
        CitiTreasuryISO20022 // Citi Cross-Border Swift / ISO 20022
    }

    struct Milestone {
        string description;
        uint256 payoutBps;           // Basis points (e.g. 2000 = 20%, 3000 = 30%)
        uint256 payoutAmount;        // Calculated token/fiat amount
        bool isCompleted;
        bool isReleased;
        uint256 completedAt;
        string verificationProof;    // IPFS or Oracle hash (e.g., Customs clearance doc hash)
        TokenizedBillOfLading.ShipmentStatus requiredShipmentStatus;
    }

    struct TradeDeal {
        uint256 dealId;
        string dealReference;        // Commercial contract ref / Purchase Order
        address buyer;               // Indian Importer / Buyer
        address seller;              // Global/Domestic Supplier
        address citiEscrowAgent;     // Citi Escrow Officer / Oracle
        address settlementToken;     // Address of ERC20 token (if on-chain)
        uint256 totalAmount;         // Total deal value
        SettlementRail rail;
        EscrowStatus status;
        uint256 tokenizedAssetId;    // Linked RWA e-BL Token ID
        uint256 milestonesCount;
        uint256 totalReleased;
        uint256 createdAt;
        uint256 fundedAt;
        uint256 completedAt;
        bool isTitleTransferredOnCompletion;
    }

    uint256 public nextDealId = 1001;
    address public contractOwner;
    TokenizedBillOfLading public rwaContract;

    mapping(uint256 => TradeDeal) public deals;
    mapping(uint256 => Milestone[]) public dealMilestones;
    mapping(address => uint256[]) public userDeals;

    // Events for auditable tracking
    event DealCreated(
        uint256 indexed dealId,
        string dealReference,
        address indexed buyer,
        address indexed seller,
        uint256 totalAmount,
        SettlementRail rail
    );

    event DealFunded(
        uint256 indexed dealId,
        uint256 amount,
        string fundingTxReference,
        SettlementRail rail
    );

    event MilestoneCompleted(
        uint256 indexed dealId,
        uint256 indexed milestoneIndex,
        string description,
        string verificationProof
    );

    event MilestoneReleased(
        uint256 indexed dealId,
        uint256 indexed milestoneIndex,
        uint256 amountReleased,
        address indexed recipient,
        string settlementReference
    );

    event DisputeRaised(uint256 indexed dealId, address indexed raisedBy, string reason);
    event DisputeResolved(uint256 indexed dealId, bool refundToBuyer, uint256 buyerAmount, uint256 sellerAmount);
    event DealCompleted(uint256 indexed dealId, uint256 totalPayout);

    modifier onlyContractOwner() {
        require(msg.sender == contractOwner, "Only contract owner");
        _;
    }

    modifier onlyDealPartyOrAgent(uint256 dealId) {
        TradeDeal storage deal = deals[dealId];
        require(
            msg.sender == deal.buyer ||
            msg.sender == deal.seller ||
            msg.sender == deal.citiEscrowAgent ||
            msg.sender == contractOwner,
            "Unauthorized deal access"
        );
        _;
    }

    constructor(address _rwaContractAddress) {
        contractOwner = msg.sender;
        if (_rwaContractAddress != address(0)) {
            rwaContract = TokenizedBillOfLading(_rwaContractAddress);
        }
    }

    function setRwaContract(address _rwaContractAddress) external onlyContractOwner {
        rwaContract = TokenizedBillOfLading(_rwaContractAddress);
    }

    /**
     * @notice Initializes a programmable trade deal with milestone terms
     */
    function createTradeDeal(
        string memory dealReference,
        address seller,
        address citiEscrowAgent,
        address settlementToken,
        uint256 totalAmount,
        SettlementRail rail,
        uint256 tokenizedAssetId,
        bool isTitleTransferredOnCompletion,
        string[] memory milestoneDescriptions,
        uint256[] memory milestoneBps,
        TokenizedBillOfLading.ShipmentStatus[] memory requiredStatuses
    ) external returns (uint256) {
        require(seller != address(0), "Invalid seller address");
        require(milestoneDescriptions.length == milestoneBps.length, "Milestone arrays mismatch");
        require(milestoneDescriptions.length > 0, "At least 1 milestone required");

        uint256 totalBps = 0;
        for (uint256 i = 0; i < milestoneBps.length; i++) {
            totalBps += milestoneBps[i];
        }
        require(totalBps == 10000, "Milestone percentages must sum to 100% (10000 bps)");

        uint256 dealId = nextDealId++;
        TradeDeal storage newDeal = deals[dealId];
        newDeal.dealId = dealId;
        newDeal.dealReference = dealReference;
        newDeal.buyer = msg.sender;
        newDeal.seller = seller;
        newDeal.citiEscrowAgent = citiEscrowAgent != address(0) ? citiEscrowAgent : contractOwner;
        newDeal.settlementToken = settlementToken;
        newDeal.totalAmount = totalAmount;
        newDeal.rail = rail;
        newDeal.status = EscrowStatus.Created;
        newDeal.tokenizedAssetId = tokenizedAssetId;
        newDeal.milestonesCount = milestoneDescriptions.length;
        newDeal.totalReleased = 0;
        newDeal.createdAt = block.timestamp;
        newDeal.isTitleTransferredOnCompletion = isTitleTransferredOnCompletion;

        for (uint256 i = 0; i < milestoneDescriptions.length; i++) {
            uint256 payout = (totalAmount * milestoneBps[i]) / 10000;
            dealMilestones[dealId].push(Milestone({
                description: milestoneDescriptions[i],
                payoutBps: milestoneBps[i],
                payoutAmount: payout,
                isCompleted: false,
                isReleased: false,
                completedAt: 0,
                verificationProof: "",
                requiredShipmentStatus: requiredStatuses[i]
            }));
        }

        userDeals[msg.sender].push(dealId);
        userDeals[seller].push(dealId);

        emit DealCreated(dealId, dealReference, msg.sender, seller, totalAmount, rail);
        return dealId;
    }

    /**
     * @notice Funds the escrow on-chain (using ERC20) or registers off-chain lock (via NPCI UPI mandate / Citi ISO 20022)
     */
    function fundEscrow(uint256 dealId, string memory fundingTxReference) external {
        TradeDeal storage deal = deals[dealId];
        require(deal.status == EscrowStatus.Created, "Deal not in Created state");
        require(msg.sender == deal.buyer || msg.sender == deal.citiEscrowAgent || msg.sender == contractOwner, "Unauthorized funder");

        if (deal.rail == SettlementRail.OnChainDigitalRupee || deal.rail == SettlementRail.OnChainCitiUSD) {
            require(deal.settlementToken != address(0), "No token set for on-chain rail");
            MockERC20 token = MockERC20(deal.settlementToken);
            require(token.transferFrom(msg.sender, address(this), deal.totalAmount), "Token transfer failed");
        }

        deal.status = EscrowStatus.Funded;
        deal.fundedAt = block.timestamp;

        emit DealFunded(dealId, deal.totalAmount, fundingTxReference, deal.rail);
    }

    /**
     * @notice Verifies milestone conditions (can be called by Buyer, Citi Escrow Officer, or verified Oracle)
     */
    function verifyMilestone(
        uint256 dealId,
        uint256 milestoneIndex,
        string memory verificationProof
    ) external onlyDealPartyOrAgent(dealId) {
        TradeDeal storage deal = deals[dealId];
        require(deal.status == EscrowStatus.Funded || deal.status == EscrowStatus.InExecution, "Deal not funded");
        require(milestoneIndex < deal.milestonesCount, "Invalid milestone index");

        Milestone storage m = dealMilestones[dealId][milestoneIndex];
        require(!m.isCompleted, "Milestone already completed");

        // If prior milestones exist, check if preceding milestone was completed
        if (milestoneIndex > 0) {
            require(dealMilestones[dealId][milestoneIndex - 1].isCompleted, "Previous milestone not completed");
        }

        m.isCompleted = true;
        m.completedAt = block.timestamp;
        m.verificationProof = verificationProof;
        deal.status = EscrowStatus.InExecution;

        // Optionally update RWA status
        if (deal.tokenizedAssetId > 0 && address(rwaContract) != address(0)) {
            try rwaContract.updateShipmentStatus(deal.tokenizedAssetId, m.requiredShipmentStatus, verificationProof) {} catch {}
        }

        emit MilestoneCompleted(dealId, milestoneIndex, m.description, verificationProof);
    }

    /**
     * @notice Releases payment for a verified milestone
     */
    function releaseMilestone(
        uint256 dealId,
        uint256 milestoneIndex,
        string memory settlementReference
    ) external onlyDealPartyOrAgent(dealId) {
        TradeDeal storage deal = deals[dealId];
        require(deal.status == EscrowStatus.InExecution || deal.status == EscrowStatus.Funded, "Invalid deal status");
        require(milestoneIndex < deal.milestonesCount, "Invalid milestone index");

        Milestone storage m = dealMilestones[dealId][milestoneIndex];
        require(m.isCompleted, "Milestone not yet verified");
        require(!m.isReleased, "Milestone already released");

        m.isReleased = true;
        deal.totalReleased += m.payoutAmount;

        // For on-chain settlement tokens, transfer directly to seller
        if (deal.rail == SettlementRail.OnChainDigitalRupee || deal.rail == SettlementRail.OnChainCitiUSD) {
            MockERC20 token = MockERC20(deal.settlementToken);
            require(token.transfer(deal.seller, m.payoutAmount), "Token release transfer failed");
        }

        emit MilestoneReleased(dealId, milestoneIndex, m.payoutAmount, deal.seller, settlementReference);

        // Check if all milestones completed
        bool allDone = true;
        for (uint256 i = 0; i < deal.milestonesCount; i++) {
            if (!dealMilestones[dealId][i].isReleased) {
                allDone = false;
                break;
            }
        }

        if (allDone) {
            deal.status = EscrowStatus.Completed;
            deal.completedAt = block.timestamp;

            // Atomic DvP: Transfer ownership of RWA Bill of Lading to buyer upon final settlement!
            if (deal.isTitleTransferredOnCompletion && deal.tokenizedAssetId > 0 && address(rwaContract) != address(0)) {
                try rwaContract.transferTitle(deal.tokenizedAssetId, deal.buyer) {} catch {}
            }

            emit DealCompleted(dealId, deal.totalReleased);
        }
    }

    /**
     * @notice Raise a dispute
     */
    function raiseDispute(uint256 dealId, string memory reason) external onlyDealPartyOrAgent(dealId) {
        TradeDeal storage deal = deals[dealId];
        require(deal.status == EscrowStatus.Funded || deal.status == EscrowStatus.InExecution, "Cannot dispute");
        deal.status = EscrowStatus.Disputed;

        emit DisputeRaised(dealId, msg.sender, reason);
    }

    /**
     * @notice Resolve dispute via Citi Escrow Agent or Contract Owner
     */
    function resolveDispute(
        uint256 dealId,
        bool refundToBuyer,
        uint256 buyerAmount,
        uint256 sellerAmount
    ) external {
        TradeDeal storage deal = deals[dealId];
        require(deal.status == EscrowStatus.Disputed, "Deal not disputed");
        require(msg.sender == deal.citiEscrowAgent || msg.sender == contractOwner, "Only escrow agent can arbitrate");

        uint256 remainingFunds = deal.totalAmount - deal.totalReleased;
        require(buyerAmount + sellerAmount <= remainingFunds, "Amounts exceed remaining funds");

        if (deal.rail == SettlementRail.OnChainDigitalRupee || deal.rail == SettlementRail.OnChainCitiUSD) {
            MockERC20 token = MockERC20(deal.settlementToken);
            if (buyerAmount > 0) token.transfer(deal.buyer, buyerAmount);
            if (sellerAmount > 0) token.transfer(deal.seller, sellerAmount);
        }

        deal.status = refundToBuyer ? EscrowStatus.Refunded : EscrowStatus.Completed;
        emit DisputeResolved(dealId, refundToBuyer, buyerAmount, sellerAmount);
    }

    function getDeal(uint256 dealId) external view returns (TradeDeal memory) {
        return deals[dealId];
    }

    function getDealMilestones(uint256 dealId) external view returns (Milestone[] memory) {
        return dealMilestones[dealId];
    }
}
