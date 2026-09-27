import { expect } from "chai";
import hre from "hardhat";
const { ethers } = hre;

describe("ArcRelayPaymaster (ERC-4337 v0.7 + Native USDC Gas)", function () {
  let owner, verifyingSigner, clientUser, attacker, recipient;
  let mockEntryPoint, paymaster;
  let paymasterAddress, entryPointAddress;
  const policyId = ethers.id("fintech-client-policy-001");
  const feeMarkupBps = 500; // 5.00% markup

  beforeEach(async function () {
    [owner, verifyingSigner, clientUser, attacker, recipient] = await ethers.getSigners();

    // Deploy Mock EntryPoint
    const MockEntryPoint = await ethers.getContractFactory("MockEntryPoint");
    mockEntryPoint = await MockEntryPoint.deploy();
    await mockEntryPoint.waitForDeployment();
    entryPointAddress = await mockEntryPoint.getAddress();

    // Deploy ArcRelayPaymaster
    const ArcRelayPaymaster = await ethers.getContractFactory("ArcRelayPaymaster");
    paymaster = await ArcRelayPaymaster.deploy(
      entryPointAddress,
      verifyingSigner.address,
      owner.address,
      feeMarkupBps
    );
    await paymaster.waitForDeployment();
    paymasterAddress = await paymaster.getAddress();
  });

  describe("Deployment & Configuration", function () {
    it("should set entryPoint, verifyingSigner, and fee markup correctly", async function () {
      expect(await paymaster.entryPoint()).to.equal(entryPointAddress);
      expect(await paymaster.verifyingSigner()).to.equal(verifyingSigner.address);
      expect(await paymaster.feeMarkupBps()).to.equal(feeMarkupBps);
      expect(await paymaster.owner()).to.equal(owner.address);
    });

    it("should reject deployment with zero address for EntryPoint or Signer", async function () {
      const ArcRelayPaymaster = await ethers.getContractFactory("ArcRelayPaymaster");
      await expect(
        ArcRelayPaymaster.deploy(ethers.ZeroAddress, verifyingSigner.address, owner.address, 500)
      ).to.be.revertedWithCustomError(paymaster, "ZeroAddress");

      await expect(
        ArcRelayPaymaster.deploy(entryPointAddress, ethers.ZeroAddress, owner.address, 500)
      ).to.be.revertedWithCustomError(paymaster, "ZeroAddress");
    });

    it("should reject fee markup above maximum (20%)", async function () {
      const ArcRelayPaymaster = await ethers.getContractFactory("ArcRelayPaymaster");
      await expect(
        ArcRelayPaymaster.deploy(entryPointAddress, verifyingSigner.address, owner.address, 2500)
      ).to.be.revertedWithCustomError(paymaster, "FeeMarkupTooHigh");
    });
  });

  describe("Corporate Gas Tank Deposits & Withdrawals", function () {
    it("should allow a client to pre-fund a gas tank and forward to EntryPoint", async function () {
      const depositAmount = ethers.parseEther("5.0");

      const tx = await paymaster.connect(clientUser).depositFor(policyId, { value: depositAmount });
      await expect(tx)
        .to.emit(paymaster, "ClientDeposited")
        .withArgs(policyId, clientUser.address, depositAmount);

      expect(await paymaster.clientBalances(policyId)).to.equal(depositAmount);
      expect(await paymaster.policyOwners(policyId)).to.equal(clientUser.address);
      expect(await mockEntryPoint.balanceOf(paymasterAddress)).to.equal(depositAmount);
    });

    it("should allow policy owner to withdraw unspent balance", async function () {
      const depositAmount = ethers.parseEther("5.0");
      await paymaster.connect(clientUser).depositFor(policyId, { value: depositAmount });

      const withdrawAmount = ethers.parseEther("2.0");
      const tx = await paymaster
        .connect(clientUser)
        .withdrawClientBalance(policyId, recipient.address, withdrawAmount);

      await expect(tx)
        .to.emit(paymaster, "ClientWithdrawn")
        .withArgs(policyId, recipient.address, withdrawAmount);

      expect(await paymaster.clientBalances(policyId)).to.equal(depositAmount - withdrawAmount);
      expect(await mockEntryPoint.balanceOf(paymasterAddress)).to.equal(depositAmount - withdrawAmount);
    });

    it("should prevent unauthorized users from withdrawing client balances", async function () {
      const depositAmount = ethers.parseEther("5.0");
      await paymaster.connect(clientUser).depositFor(policyId, { value: depositAmount });

      await expect(
        paymaster
          .connect(attacker)
          .withdrawClientBalance(policyId, attacker.address, ethers.parseEther("1.0"))
      ).to.be.revertedWithCustomError(paymaster, "UnauthorizedPolicyAccess");
    });
  });

  describe("EIP-712 Sponsorship Validation", function () {
    async function signSponsorship(sender, nonce, validUntil, validAfter, maxCost, pId, signer) {
      const domain = {
        name: "ArcRelayPaymaster",
        version: "1",
        chainId: (await ethers.provider.getNetwork()).chainId,
        verifyingContract: paymasterAddress,
      };

      const types = {
        Sponsorship: [
          { name: "sender", type: "address" },
          { name: "nonce", type: "uint256" },
          { name: "validUntil", type: "uint48" },
          { name: "validAfter", type: "uint48" },
          { name: "maxCost", type: "uint256" },
          { name: "policyId", type: "bytes32" },
        ],
      };

      const value = {
        sender,
        nonce,
        validUntil,
        validAfter,
        maxCost,
        policyId: pId,
      };

      return await signer.signTypedData(domain, types, value);
    }

    function encodePaymasterAndData(pmAddress, validUntil, validAfter, pId, sig) {
      // 20 bytes paymaster + 16 bytes verificationGasLimit + 16 bytes postOpGasLimit
      const prefix = ethers.solidityPacked(
        ["address", "uint128", "uint128"],
        [pmAddress, 100000n, 50000n]
      );

      // payload: 6 bytes validUntil + 6 bytes validAfter + 32 bytes policyId + 65 bytes signature
      const payload = ethers.solidityPacked(
        ["uint48", "uint48", "bytes32", "bytes"],
        [validUntil, validAfter, pId, sig]
      );

      return ethers.concat([prefix, payload]);
    }

    it("should accept valid EIP-712 signature from verifyingSigner", async function () {
      const depositAmount = ethers.parseEther("10.0");
      await paymaster.connect(clientUser).depositFor(policyId, { value: depositAmount });

      const sender = clientUser.address;
      const nonce = 0n;
      const validUntil = 2000000000;
      const validAfter = 1000000000;
      const maxCost = ethers.parseEther("0.1");

      const sig = await signSponsorship(
        sender,
        nonce,
        validUntil,
        validAfter,
        maxCost,
        policyId,
        verifyingSigner
      );

      const paymasterAndData = encodePaymasterAndData(
        paymasterAddress,
        validUntil,
        validAfter,
        policyId,
        sig
      );

      const userOp = {
        sender,
        nonce,
        initCode: "0x",
        callData: "0x",
        accountGasLimits: ethers.ZeroHash,
        preVerificationGas: 21000n,
        gasFees: ethers.ZeroHash,
        paymasterAndData,
        signature: "0x",
      };

      const [context, validationData] = await mockEntryPoint.simulateValidation.staticCall(
        paymasterAddress,
        userOp,
        ethers.ZeroHash,
        maxCost
      );

      // Validation authorizer should be 0 (success)
      const authorizer = validationData & 0xffffffffffffffffffffffffffffffffffffffffn;
      expect(authorizer).to.equal(0n);
      expect(context).to.not.equal("0x");
    });

    it("should fail validation (sigFailed = 1) if signed by unauthorized key", async function () {
      const depositAmount = ethers.parseEther("10.0");
      await paymaster.connect(clientUser).depositFor(policyId, { value: depositAmount });

      const sender = clientUser.address;
      const nonce = 0n;
      const validUntil = 2000000000;
      const validAfter = 1000000000;
      const maxCost = ethers.parseEther("0.1");

      // Attacker signs instead of verifyingSigner
      const sig = await signSponsorship(
        sender,
        nonce,
        validUntil,
        validAfter,
        maxCost,
        policyId,
        attacker
      );

      const paymasterAndData = encodePaymasterAndData(
        paymasterAddress,
        validUntil,
        validAfter,
        policyId,
        sig
      );

      const userOp = {
        sender,
        nonce,
        initCode: "0x",
        callData: "0x",
        accountGasLimits: ethers.ZeroHash,
        preVerificationGas: 21000n,
        gasFees: ethers.ZeroHash,
        paymasterAndData,
        signature: "0x",
      };

      const [, validationData] = await mockEntryPoint.simulateValidation.staticCall(
        paymasterAddress,
        userOp,
        ethers.ZeroHash,
        maxCost
      );

      // Authorizer should be 1 (sigFailed)
      const authorizer = validationData & 0xffffffffffffffffffffffffffffffffffffffffn;
      expect(authorizer).to.equal(1n);
    });

    it("should revert if client corporate tank balance is insufficient", async function () {
      // Tank has 0.05 ETH, maxCost is 0.1 ETH
      await paymaster.connect(clientUser).depositFor(policyId, { value: ethers.parseEther("0.05") });

      const sender = clientUser.address;
      const nonce = 0n;
      const validUntil = 2000000000;
      const validAfter = 1000000000;
      const maxCost = ethers.parseEther("0.1");

      const sig = await signSponsorship(
        sender,
        nonce,
        validUntil,
        validAfter,
        maxCost,
        policyId,
        verifyingSigner
      );

      const paymasterAndData = encodePaymasterAndData(
        paymasterAddress,
        validUntil,
        validAfter,
        policyId,
        sig
      );

      const userOp = {
        sender,
        nonce,
        initCode: "0x",
        callData: "0x",
        accountGasLimits: ethers.ZeroHash,
        preVerificationGas: 21000n,
        gasFees: ethers.ZeroHash,
        paymasterAndData,
        signature: "0x",
      };

      await expect(
        mockEntryPoint.simulateValidation(paymasterAddress, userOp, ethers.ZeroHash, maxCost)
      ).to.be.revertedWithCustomError(paymaster, "InsufficientClientBalance");
    });
  });

  describe("PostOp Settlement & Accounting", function () {
    it("should deduct actual gas cost plus convenience fee markup from client balance", async function () {
      const initialDeposit = ethers.parseEther("2.0");
      await paymaster.connect(clientUser).depositFor(policyId, { value: initialDeposit });

      const context = ethers.AbiCoder.defaultAbiCoder().encode(
        ["bytes32", "address", "uint256"],
        [policyId, clientUser.address, ethers.parseEther("0.1")]
      );

      const actualGasCost = ethers.parseEther("0.01");
      // 5% markup on 0.01 = 0.0005. Total fee = 0.0105
      const expectedFee = actualGasCost + (actualGasCost * BigInt(feeMarkupBps)) / 10000n;

      const tx = await mockEntryPoint.simulatePostOp(
        paymasterAddress,
        0, // opSucceeded
        context,
        actualGasCost,
        ethers.parseUnits("1", "gwei")
      );

      await expect(tx)
        .to.emit(paymaster, "UserOpSponsored")
        .withArgs(policyId, clientUser.address, actualGasCost, expectedFee);

      const remainingBalance = await paymaster.clientBalances(policyId);
      expect(remainingBalance).to.equal(initialDeposit - expectedFee);
    });
  });

  describe("Admin, Governance & Emergency Controls", function () {
    it("should allow owner to update verifyingSigner and feeMarkup", async function () {
      await expect(paymaster.connect(owner).setVerifyingSigner(clientUser.address))
        .to.emit(paymaster, "VerifyingSignerUpdated")
        .withArgs(verifyingSigner.address, clientUser.address);

      expect(await paymaster.verifyingSigner()).to.equal(clientUser.address);

      await expect(paymaster.connect(owner).setFeeMarkup(800))
        .to.emit(paymaster, "FeeMarkupUpdated")
        .withArgs(500, 800);

      expect(await paymaster.feeMarkupBps()).to.equal(800);
    });

    it("should prevent non-owner from updating admin parameters", async function () {
      await expect(
        paymaster.connect(attacker).setVerifyingSigner(attacker.address)
      ).to.be.revertedWithCustomError(paymaster, "OwnableUnauthorizedAccount");

      await expect(
        paymaster.connect(attacker).setFeeMarkup(800)
      ).to.be.revertedWithCustomError(paymaster, "OwnableUnauthorizedAccount");
    });

    it("should pause and unpause properly", async function () {
      await paymaster.connect(owner).pause();
      expect(await paymaster.paused()).to.be.true;

      await paymaster.connect(owner).unpause();
      expect(await paymaster.paused()).to.be.false;
    });
  });
});
