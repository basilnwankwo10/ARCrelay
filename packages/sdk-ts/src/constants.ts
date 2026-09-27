/**
 * ArcRelay SDK Constants
 */

/** Arc Testnet Chain ID */
export const ARC_TESTNET_CHAIN_ID = 5042002;

/** Public Arc Testnet RPC URL */
export const ARC_TESTNET_RPC = 'https://rpc.testnet.arc.network';

/** Canonical ArcRelayPaymaster deployed contract on Arc Testnet */
export const DEFAULT_PAYMASTER_ADDRESS = '0x600c83F91464440A1Fc2c4C723C78e2f51F43096';

/** Canonical ERC-4337 v0.7 EntryPoint contract on Arc Testnet */
export const DEFAULT_ENTRY_POINT_ADDRESS = '0x0000000071727De22E5E9d8BAf0edAc6f37da032';

/** Default General Policy ID */
export const DEFAULT_POLICY_ID = '0x0000000000000000000000000000000000000000000000000000000000000001';

/** Default HTTP request timeout (10 seconds) */
export const DEFAULT_TIMEOUT_MS = 10_000;

/** Default Paymaster verification gas limit */
export const DEFAULT_PAYMASTER_VERIFICATION_GAS = 100_000n;

/** Default Paymaster post-op gas limit */
export const DEFAULT_PAYMASTER_POST_OP_GAS = 50_000n;
