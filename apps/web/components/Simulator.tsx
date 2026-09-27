'use client';

import React, { useState } from 'react';
import {
  Zap,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  ExternalLink,
  Shield,
  Layers,
  Sparkles,
} from 'lucide-react';

export function Simulator() {
  const [isGasless, setIsGasless] = useState<boolean>(true);
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [step, setStep] = useState<number>(0);
  const [completed, setCompleted] = useState<boolean>(false);

  const runSimulation = () => {
    setIsExecuting(true);
    setCompleted(false);
    setStep(1);

    setTimeout(() => {
      setStep(2);
      setTimeout(() => {
        setStep(3);
        setTimeout(() => {
          setIsExecuting(false);
          setCompleted(true);
        }, 800);
      }, 900);
    }, 800);
  };

  const resetSimulation = () => {
    setIsExecuting(false);
    setCompleted(false);
    setStep(0);
  };

  return (
    <section id="simulator" className="py-20 bg-arc-surface/60 border-t border-arc-border/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-arc-cyan/10 border border-arc-cyan/20 text-xs font-semibold text-arc-cyan uppercase tracking-wider mb-4">
            <Zap className="w-3.5 h-3.5" />
            <span>Interactive Simulator</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-white">
            See the User Experience Difference
          </h2>
          <p className="mt-4 text-slate-300 text-base sm:text-lg">
            Toggle between traditional Web3 gas friction and ArcRelay&apos;s invisible gas sponsorship.
          </p>

          {/* Toggle Button */}
          <div className="mt-8 inline-flex p-1.5 rounded-2xl bg-arc-dark border border-arc-border shadow-inner">
            <button
              onClick={() => {
                setIsGasless(true);
                resetSimulation();
              }}
              className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 ${
                isGasless
                  ? 'bg-gradient-to-r from-arc-cyan to-arc-blue text-arc-dark shadow-glow-cyan'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Zap className="w-4 h-4 fill-current" />
              <span>With ArcRelay (Gasless)</span>
            </button>
            <button
              onClick={() => {
                setIsGasless(false);
                resetSimulation();
              }}
              className={`px-5 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2 ${
                !isGasless
                  ? 'bg-red-500/20 text-red-300 border border-red-500/40'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span>Without ArcRelay (Legacy)</span>
            </button>
          </div>
        </div>

        {/* Interactive App Window */}
        <div className="max-w-xl mx-auto rounded-3xl bg-arc-card border border-arc-border shadow-2xl overflow-hidden">
          {/* Mock Window Top Bar */}
          <div className="px-6 py-4 bg-arc-dark/60 border-b border-arc-border/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500/80" />
              <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <span className="w-3 h-3 rounded-full bg-green-500/80" />
              <span className="ml-2 text-xs font-mono text-slate-400">arc-checkout-demo.app</span>
            </div>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              User Balance: 0.00 USDC Gas
            </span>
          </div>

          {/* App Body */}
          <div className="p-6 sm:p-8">
            <div className="rounded-2xl bg-arc-dark/70 border border-arc-border/60 p-5 mb-6">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-medium text-slate-400">Action</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-arc-blue/20 text-arc-cyan">
                  USDC Instant Transfer
                </span>
              </div>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold text-white">10.00 USDC</span>
                <span className="text-xs text-slate-400">Recipient: 0x8b39...F7DD</span>
              </div>

              {/* Gas Fee Line */}
              <div className="mt-4 pt-4 border-t border-arc-border/40 flex items-center justify-between text-sm">
                <span className="text-slate-400">Network Gas Fee</span>
                {isGasless ? (
                  <div className="flex items-center gap-1.5 text-emerald-400 font-semibold">
                    <span className="line-through text-slate-500 font-normal">$0.0033</span>
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-xs">
                      $0.00 (Sponsored)
                    </span>
                  </div>
                ) : (
                  <span className="text-red-400 font-semibold">$0.0033 USDC (Required)</span>
                )}
              </div>
            </div>

            {/* Gasless State Banner vs Friction Banner */}
            {isGasless ? (
              <div className="rounded-xl bg-arc-cyan/10 border border-arc-cyan/30 p-4 mb-6 flex items-start gap-3">
                <Sparkles className="w-5 h-5 text-arc-cyan shrink-0 mt-0.5" />
                <div className="text-xs text-slate-300 leading-relaxed">
                  <strong className="text-white block font-semibold mb-0.5">Invisible Gas Active</strong>
                  Your corporate gas tank covers network fees automatically. User signs 1 tap with zero gas balance.
                </div>
              </div>
            ) : (
              <div className="rounded-xl bg-red-500/10 border border-red-500/30 p-4 mb-6 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
                <div className="text-xs text-red-200 leading-relaxed">
                  <strong className="text-red-100 block font-semibold mb-0.5">Transaction Blocked: No Gas</strong>
                  User has no USDC gas balance. 74% of consumer drop-offs occur at this step.
                </div>
              </div>
            )}

            {/* Execution Steps */}
            {isExecuting && (
              <div className="space-y-2.5 mb-6 text-xs font-mono">
                <div className={`flex items-center gap-2 ${step >= 1 ? 'text-arc-cyan' : 'text-slate-500'}`}>
                  <RefreshCw className={`w-3.5 h-3.5 ${step === 1 ? 'animate-spin' : ''}`} />
                  <span>1. Packaging ERC-4337 v0.7 UserOperation</span>
                </div>
                <div className={`flex items-center gap-2 ${step >= 2 ? 'text-arc-cyan' : 'text-slate-500'}`}>
                  <RefreshCw className={`w-3.5 h-3.5 ${step === 2 ? 'animate-spin' : ''}`} />
                  <span>2. ArcRelay Policy Engine signs EIP-712 paymasterData</span>
                </div>
                <div className={`flex items-center gap-2 ${step >= 3 ? 'text-arc-cyan' : 'text-slate-500'}`}>
                  <RefreshCw className={`w-3.5 h-3.5 ${step === 3 ? 'animate-spin' : ''}`} />
                  <span>3. Deducting gas from Corporate Tank &amp; Mining on Arc</span>
                </div>
              </div>
            )}

            {/* Success Card */}
            {completed && isGasless && (
              <div className="rounded-2xl bg-emerald-500/10 border border-emerald-500/30 p-4 mb-6 text-left">
                <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm mb-1">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Transaction Confirmed (0.00 Gas Paid)</span>
                </div>
                <p className="text-xs text-slate-300 font-mono mt-1">
                  Mined in Block 64,122,404 • Arc Testnet
                </p>
                <div className="mt-2 text-[11px] text-slate-400 flex items-center justify-between">
                  <span>Paymaster: 0x600c...43096</span>
                  <span className="text-emerald-400">Gas Paid: $0.00</span>
                </div>
              </div>
            )}

            {/* Interactive Button */}
            {isGasless ? (
              <button
                disabled={isExecuting}
                onClick={runSimulation}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-arc-cyan to-arc-blue text-arc-dark font-bold text-base hover:brightness-110 shadow-glow-cyan transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isExecuting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Sponsoring Transaction on Arc...</span>
                  </>
                ) : completed ? (
                  <>
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Test Another Sponsorship</span>
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 fill-current" />
                    <span>Confirm 1-Tap Gasless Payment</span>
                  </>
                )}
              </button>
            ) : (
              <button
                disabled
                className="w-full py-4 rounded-xl bg-slate-800 border border-red-500/30 text-red-300/80 font-bold text-sm cursor-not-allowed flex items-center justify-center gap-2"
              >
                <AlertTriangle className="w-4 h-4 text-red-400" />
                <span>Cannot Confirm (Insufficient USDC Gas)</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
