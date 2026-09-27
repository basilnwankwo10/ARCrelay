'use client';

import React from 'react';
import { Layers, CreditCard, ShieldCheck, ArrowRight, Wallet, CheckCircle, Database } from 'lucide-react';

export function Architecture() {
  const steps = [
    {
      num: '01',
      title: 'Corporate Gas Tank Top-Up',
      desc: 'Enterprises pre-fund gas in native USDC (or fiat credit card via Circle Onramp Kit) mapped to a unique bytes32 policyId.',
      badge: 'Circle Onramp Kit',
      icon: CreditCard,
      color: 'text-arc-cyan',
      border: 'border-arc-cyan/30',
    },
    {
      num: '02',
      title: '0-Balance User Action',
      desc: 'Consumer taps in-app action (swap, transfer, game move). No wallet popups, no gas calculations, zero native token needed.',
      badge: 'Invisible UX',
      icon: Wallet,
      color: 'text-arc-green',
      border: 'border-arc-green/30',
    },
    {
      num: '03',
      title: 'EIP-712 Fraud Protection',
      desc: 'The ArcRelay Policy Engine evaluates sliding-window spend quotas ($1.00/day default) and cryptographically signs authorization.',
      badge: 'Atomic Safety',
      icon: ShieldCheck,
      color: 'text-arc-purple',
      border: 'border-arc-purple/30',
    },
    {
      num: '04',
      title: 'On-Chain Paymaster Settlement',
      desc: 'ArcRelayPaymaster settles gas with Arc EntryPoint. Network fee is deducted from the corporate tank. User pays $0.00.',
      badge: 'Block 64122404',
      icon: Database,
      color: 'text-arc-blue',
      border: 'border-arc-blue/30',
    },
  ];

  return (
    <section id="architecture" className="py-20 bg-arc-surface/40 border-t border-arc-border/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-arc-blue/10 border border-arc-blue/20 text-xs font-semibold text-arc-cyan uppercase tracking-wider mb-4">
            <Layers className="w-3.5 h-3.5" />
            <span>Multi-Tenant Architecture</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            How Corporate Gas Tanks Work
          </h2>
          <p className="mt-4 text-slate-300 text-base sm:text-lg">
            A secure bridge between enterprise treasury balances and consumer smart accounts.
          </p>
        </div>

        {/* 4 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((s, i) => {
            const Icon = s.icon;
            return (
              <div
                key={i}
                className="relative rounded-2xl bg-arc-card border border-arc-border/80 p-6 flex flex-col justify-between hover:border-arc-cyan/40 transition-all group"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="font-mono text-2xl font-black text-slate-600 group-hover:text-arc-cyan transition-colors">
                      {s.num}
                    </span>
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 ${s.color}`}>
                      {s.badge}
                    </span>
                  </div>

                  <div className="w-10 h-10 rounded-xl bg-arc-dark flex items-center justify-center mb-4 border border-arc-border">
                    <Icon className={`w-5 h-5 ${s.color}`} />
                  </div>

                  <h3 className="text-lg font-bold text-white mb-2">{s.title}</h3>
                  <p className="text-xs text-slate-300 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
