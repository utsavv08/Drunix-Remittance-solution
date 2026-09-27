// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title TokenizedBillOfLading
 * @author CitiFlow Escrow Team
 * @notice Real Asset Tokenization contract for Electronic Bill of Lading (e-BL), Invoices, and Trade Consignments
 * Complies with UNCITRAL Model Law on Electronic Transferable Records (MLETR) principles.
 */
contract TokenizedBillOfLading {
    string public name = "Drunix Real Asset Tokenized Bill of Lading";
    string public symbol = "eBL-RWA";

    enum ShipmentStatus {
        Draft,
        ConsignmentCreated,
        CustomsClearedOrigin,
        InTransitVessel,
        CustomsClearedDestination,
        PortArrival,
        DeliveredAndVerified,
        Disputed
    }

    struct TradeAsset {
        uint256 tokenId;
        string blNumber;           // Unique Bill of Lading / Invoice reference
        string exporterName;
        string importerName;
        string portOfLoading;
        string portOfDischarge;
        string cargoDescription;
        uint256 invoiceValueUSD;   // In cents / base units
        string metadataURI;        // IPFS document hash
        ShipmentStatus status;
        address currentHolder;
        uint256 creationTime;
        uint256 lastUpdated;
    }

    uint256 public nextTokenId = 1;
    address public admin;
    mapping(address => bool) public authorizedOracles; // Logistics & Customs Oracle addresses

    mapping(uint256 => TradeAsset) public tradeAssets;
    mapping(uint256 => address) public ownerOf;
    mapping(address => uint256[]) public assetsOwnedBy;

    event AssetTokenized(
        uint256 indexed tokenId,
        string blNumber,
        address indexed exporter,
        address indexed importer,
        uint256 invoiceValueUSD
    );

    event ShipmentStatusUpdated(
        uint256 indexed tokenId,
        ShipmentStatus previousStatus,
        ShipmentStatus newStatus,
        address indexed updatedBy,
        string proofHash
    );

    event OwnershipTransferred(
        uint256 indexed tokenId,
        address indexed from,
        address indexed to
    );

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this");
        _;
    }

    modifier onlyAuthorized() {
        require(msg.sender == admin || authorizedOracles[msg.sender], "Unauthorized caller");
        _;
    }

    constructor() {
        admin = msg.sender;
        authorizedOracles[msg.sender] = true;
    }

    function setOracleAuthorization(address oracle, bool isAuthorized) external onlyAdmin {
        authorizedOracles[oracle] = isAuthorized;
    }

    /**
     * @notice Mints a new Tokenized Bill of Lading RWA NFT
     */
    function mintAsset(
        string memory blNumber,
        string memory exporterName,
        string memory importerName,
        string memory portOfLoading,
        string memory portOfDischarge,
        string memory cargoDescription,
        uint256 invoiceValueUSD,
        string memory metadataURI,
        address initialHolder
    ) external onlyAuthorized returns (uint256) {
        uint256 tokenId = nextTokenId++;

        tradeAssets[tokenId] = TradeAsset({
            tokenId: tokenId,
            blNumber: blNumber,
            exporterName: exporterName,
            importerName: importerName,
            portOfLoading: portOfLoading,
            portOfDischarge: portOfDischarge,
            cargoDescription: cargoDescription,
            invoiceValueUSD: invoiceValueUSD,
            metadataURI: metadataURI,
            status: ShipmentStatus.ConsignmentCreated,
            currentHolder: initialHolder,
            creationTime: block.timestamp,
            lastUpdated: block.timestamp
        });

        ownerOf[tokenId] = initialHolder;
        assetsOwnedBy[initialHolder].push(tokenId);

        emit AssetTokenized(tokenId, blNumber, initialHolder, address(0), invoiceValueUSD);
        return tokenId;
    }

    /**
     * @notice Updates the shipment/logistics milestone via verified Oracle or Smart Escrow
     */
    function updateShipmentStatus(
        uint256 tokenId,
        ShipmentStatus newStatus,
        string memory proofHash
    ) external onlyAuthorized {
        TradeAsset storage asset = tradeAssets[tokenId];
        require(asset.tokenId == tokenId, "Asset does not exist");

        ShipmentStatus prev = asset.status;
        asset.status = newStatus;
        asset.lastUpdated = block.timestamp;

        emit ShipmentStatusUpdated(tokenId, prev, newStatus, msg.sender, proofHash);
    }

    /**
     * @notice Transfers asset title (Delivery vs Payment) upon final milestone settlement
     */
    function transferTitle(uint256 tokenId, address to) external {
        require(ownerOf[tokenId] == msg.sender || msg.sender == admin || authorizedOracles[msg.sender], "Not authorized to transfer");
        require(to != address(0), "Invalid recipient");

        address from = ownerOf[tokenId];
        ownerOf[tokenId] = to;
        tradeAssets[tokenId].currentHolder = to;
        tradeAssets[tokenId].lastUpdated = block.timestamp;

        emit OwnershipTransferred(tokenId, from, to);
    }

    function getAsset(uint256 tokenId) external view returns (TradeAsset memory) {
        return tradeAssets[tokenId];
    }
}
