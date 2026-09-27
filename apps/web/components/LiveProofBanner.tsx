'use client';

import React from 'react';
import { ShieldCheck, ExternalLink, CheckCircle2 } from 'lucide-react';

export function LiveProofBanner() {
  const txHash = '0x29a632268fa2fd8749c1bef57700ce15aaf120ae4991d79a991fe2e76ebb4aef';
  const paymasterAddr = '0x600c83F91464440A1Fc2c4C723C78e2f51F43096';

  return (
    <div className="bg-gradient-to-r from-arc-blue/10 via-arc-cyan/10 to-arc-purple/10 border-y border-arc-cyan/20 py-3">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-wrap items-center justify-between gap-4 text-xs sm:text-sm">
        <div className="flex items-center gap-2.5">
          <span className="flex h-2.5 w-2.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-arc-green opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-arc-green" />
          </span>
          <span className="font-medium text-slate-300">
            Verified On-Chain Proof on <strong className="text-white font-semibold">Arc Testnet</strong>
          </span>
          <span className="hidden md:inline text-slate-500">•</span>
          <span className="hidden md:inline font-mono text-slate-400">Block 64,122,404</span>
        </div>

        <div className="flex items-center gap-4">
          <a
            href={`https://testnet.arcscan.app/address/${paymasterAddr}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-arc-cyan hover:underline font-mono"
          >
            <span>Paymaster: {paymasterAddr.slice(0, 6)}...{paymasterAddr.slice(-4)}</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>

          <a
            href={`https://testnet.arcscan.app/tx/${txHash}`}
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:flex items-center gap-1.5 text-emerald-400 hover:underline font-mono"
          >
            <span>Live Tx ($0.00 Gas Paid)</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>
    </div>
  );
}
