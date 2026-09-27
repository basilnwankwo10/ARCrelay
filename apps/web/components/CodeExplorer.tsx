'use client';

import React, { useState } from 'react';
import { Code2, Copy, Check, Terminal, ExternalLink } from 'lucide-react';

export function CodeExplorer() {
  const [activeTab, setActiveTab] = useState<'ts' | 'py' | 'curl'>('ts');
  const [copied, setCopied] = useState<boolean>(false);

  const snippets = {
    ts: `import { ArcRelay } from '@arcrelay/sdk';

// 1. Initialize client with your Corporate Policy ID
const arcrelay = new ArcRelay({
  rpcUrl: 'https://relay.arcrelay.tech',
  policyId: '0x0000000000000000000000000000000000000000000000000000000000000001',
});

// 2. Sponsor any ERC-4337 v0.7 UserOperation in 1 call
const sponsoredOp = await arcrelay.sponsor(userOp);

// 3. User pays $0.00 gas. Network fees deducted from corporate tank.
await bundlerClient.sendUserOperation({ userOperation: sponsoredOp });`,

    py: `from arcrelay import ArcRelay, PackedUserOperation

# 1. Initialize async client
async with ArcRelay(
    rpc_url="https://relay.arcrelay.tech",
    policy_id="0x0000000000000000000000000000000000000000000000000000000000000001",
) as arcrelay:
    # 2. Sponsor UserOperation in 1 call
    sponsored_op = await arcrelay.sponsor(user_op)
    
    print(f"Sponsored paymasterAndData: {sponsored_op.paymasterAndData[:42]}...")`,

    curl: `curl -X POST https://relay.arcrelay.tech/rpc \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "pm_sponsorUserOperation",
    "params": [
      {
        "sender": "0x8b397aA41DA9383eAb34f9A268FCecd86813F7DD",
        "nonce": 0,
        "initCode": "0x",
        "callData": "0x12345678"
      },
      "0x0000000000000000000000000000000000000000000000000000000000000001"
    ]
  }'`,
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(snippets[activeTab]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section id="sdk" className="py-20 bg-arc-dark">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-arc-purple/10 border border-arc-purple/20 text-xs font-semibold text-arc-purple uppercase tracking-wider mb-4">
            <Terminal className="w-3.5 h-3.5" />
            <span>Developer SDK</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            Integrate Invisible Gas in 3 Lines of Code
          </h2>
          <p className="mt-4 text-slate-300 text-base sm:text-lg">
            No complex cryptographic ABI encoding or manual gas fee math. Drop into Viem, Permissionless.js, Biconomy, or Python bots in minutes.
          </p>
        </div>

        {/* Code Box */}
        <div className="max-w-3xl mx-auto rounded-2xl bg-arc-card border border-arc-border shadow-2xl overflow-hidden">
          {/* Header Bar */}
          <div className="px-5 py-3.5 bg-arc-dark/80 border-b border-arc-border flex items-center justify-between">
            {/* Tabs */}
            <div className="flex items-center gap-1.5 sm:gap-2">
              <button
                onClick={() => setActiveTab('ts')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'ts'
                    ? 'bg-arc-cyan/20 text-arc-cyan border border-arc-cyan/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                TypeScript (@arcrelay/sdk)
              </button>

              <button
                onClick={() => setActiveTab('py')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'py'
                    ? 'bg-arc-blue/20 text-arc-cyan border border-arc-blue/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Python (arcrelay-sdk)
              </button>

              <button
                onClick={() => setActiveTab('curl')}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  activeTab === 'curl'
                    ? 'bg-arc-purple/20 text-purple-300 border border-arc-purple/40'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                JSON-RPC 2.0
              </button>
            </div>

            {/* Copy Button */}
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-all"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-arc-green" />
                  <span className="text-arc-green">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>

          {/* Code Viewer */}
          <pre className="p-6 text-xs sm:text-sm font-mono text-slate-200 overflow-x-auto bg-[#080d1a] leading-relaxed">
            <code>{snippets[activeTab]}</code>
          </pre>

          {/* Footer Bar */}
          <div className="px-6 py-3 bg-arc-dark/60 border-t border-arc-border/60 flex items-center justify-between text-xs text-slate-400">
            <span>Standard: ERC-4337 v0.7 PackedUserOperation</span>
            <a
              href="https://github.com/ArcRelayHQ"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-arc-cyan hover:underline"
            >
              <span>GitHub Documentation</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
