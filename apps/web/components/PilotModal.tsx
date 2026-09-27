'use client';

import React, { useState } from 'react';
import { X, Sparkles, CheckCircle2, ArrowRight, ShieldCheck } from 'lucide-react';

interface PilotModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PilotModal({ isOpen, onClose }: PilotModalProps) {
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [projectName, setProjectName] = useState('');
  const [category, setCategory] = useState('Fintech / Payments');
  const [volume, setVolume] = useState('1,000 - 10,000');
  const [contact, setContact] = useState('');
  const [email, setEmail] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Save to local storage for pilot whitelist records
    const pilotRecord = {
      projectName,
      category,
      volume,
      contact,
      email,
      timestamp: new Date().toISOString(),
      creditsGrantedUsd: 500,
    };
    try {
      const existing = JSON.parse(localStorage.getItem('arcrelay_pilots') || '[]');
      existing.push(pilotRecord);
      localStorage.setItem('arcrelay_pilots', JSON.stringify(existing));
    } catch {
      // Fallback
    }
    setSubmitted(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative w-full max-w-lg rounded-3xl bg-arc-card border border-arc-cyan/30 shadow-glow-cyan p-6 sm:p-8 overflow-hidden">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-full text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {!submitted ? (
          <div>
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-arc-cyan/10 border border-arc-cyan/30 text-xs font-semibold text-arc-cyan w-fit mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Closed Beta Whitelist • 5 Pilot Slots</span>
            </div>

            <h3 className="text-2xl font-bold text-white tracking-tight">
              Apply for Free Gas Sponsorship
            </h3>
            <p className="mt-2 text-xs sm:text-sm text-slate-300">
              Selected teams receive <strong className="text-white">$500 in native USDC gas credits</strong> and dedicated technical support for ERC-4337 v0.7 integration.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Project or Company Name *
                </label>
                <input
                  type="text"
                  required
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="e.g. ArcPay, CyberRealm, PulseSwap"
                  className="w-full px-4 py-2.5 rounded-xl bg-arc-dark border border-arc-border text-white text-sm focus:outline-none focus:border-arc-cyan transition-colors"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    dApp Category
                  </label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-arc-dark border border-arc-border text-white text-sm focus:outline-none focus:border-arc-cyan"
                  >
                    <option>Fintech / Payments</option>
                    <option>Gaming / Metaverse</option>
                    <option>DeFi / Trading</option>
                    <option>AI Agents / Autonomous</option>
                    <option>Social / Creator Economy</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Monthly Tx Volume
                  </label>
                  <select
                    value={volume}
                    onChange={(e) => setVolume(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-arc-dark border border-arc-border text-white text-sm focus:outline-none focus:border-arc-cyan"
                  >
                    <option>&lt; 1,000 tx/mo</option>
                    <option>1,000 - 10,000 tx/mo</option>
                    <option>10,000 - 100,000 tx/mo</option>
                    <option>100,000+ tx/mo</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Telegram or X/Twitter Handle *
                </label>
                <input
                  type="text"
                  required
                  value={contact}
                  onChange={(e) => setContact(e.target.value)}
                  placeholder="@yourhandle or t.me/username"
                  className="w-full px-4 py-2.5 rounded-xl bg-arc-dark border border-arc-border text-white text-sm focus:outline-none focus:border-arc-cyan"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Work Email (Optional)
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="builder@yourproject.com"
                  className="w-full px-4 py-2.5 rounded-xl bg-arc-dark border border-arc-border text-white text-sm focus:outline-none focus:border-arc-cyan"
                />
              </div>

              <button
                type="submit"
                className="w-full mt-2 py-3.5 rounded-xl bg-gradient-to-r from-arc-cyan to-arc-blue text-arc-dark font-bold text-sm hover:brightness-110 shadow-glow-cyan transition-all flex items-center justify-center gap-2"
              >
                <span>Submit Application &amp; Claim $500 Gas</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>
          </div>
        ) : (
          <div className="py-6 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-400 mx-auto flex items-center justify-center mb-4 border border-emerald-500/30">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <h3 className="text-2xl font-bold text-white tracking-tight">
              Application Submitted!
            </h3>
            <p className="mt-2 text-sm text-slate-300 max-w-sm mx-auto leading-relaxed">
              Thank you, <strong className="text-white">{projectName}</strong>. Your pilot application has been registered for the ArcRelay Closed Beta with <span className="text-emerald-400 font-semibold">$500 in gas credits</span>.
            </p>

            <div className="mt-6 p-4 rounded-2xl bg-arc-dark border border-arc-border text-xs text-slate-300 font-mono">
              Status: Whitelist Pre-Approved • @ArcRelayHQ
            </div>

            <button
              onClick={() => {
                setSubmitted(false);
                onClose();
              }}
              className="mt-6 w-full py-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-sm transition-colors"
            >
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
