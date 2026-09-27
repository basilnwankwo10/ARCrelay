'use client';

import React from 'react';
import { Zap, ExternalLink, ShieldCheck, ArrowRight } from 'lucide-react';

interface NavbarProps {
  onOpenPilot: () => void;
}

export function Navbar({ onOpenPilot }: NavbarProps) {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-arc-dark/80 border-b border-arc-border/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-arc-cyan to-arc-blue p-[1px] shadow-glow-cyan">
            <div className="w-full h-full bg-arc-dark rounded-[11px] flex items-center justify-center">
              <Zap className="w-5 h-5 text-arc-cyan fill-arc-cyan/20" />
            </div>
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
              ArcRelay
            </span>
            <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-arc-cyan bg-arc-cyan/10 rounded-full border border-arc-cyan/30 uppercase">
              Gasless Layer
            </span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
          <a href="#simulator" className="hover:text-arc-cyan transition-colors">
            Simulator
          </a>
          <a href="#sdk" className="hover:text-arc-cyan transition-colors">
            SDK (3 Lines)
          </a>
          <a href="#architecture" className="hover:text-arc-cyan transition-colors">
            Corporate Tanks
          </a>
          <a
            href="https://testnet.arcscan.app/address/0x600c83F91464440A1Fc2c4C723C78e2f51F43096"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-slate-400 hover:text-white transition-colors"
          >
            <span>Verified Contract</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
          <a
            href="https://t.me/ArcRelayDemo_bot"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-slate-400 hover:text-arc-cyan transition-colors"
          >
            <span>Telegram Bot</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        </nav>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          {/* Arc Testnet Badge */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-arc-card border border-arc-border text-xs text-slate-300">
            <span className="w-2 h-2 rounded-full bg-arc-green animate-pulse" />
            <span className="font-mono text-slate-400">Chain 5042002</span>
          </div>

          <button
            onClick={onOpenPilot}
            className="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl bg-gradient-to-r from-arc-cyan to-arc-blue text-arc-dark font-semibold text-sm hover:opacity-95 shadow-glow-cyan transition-all flex items-center gap-2 group"
          >
            <span>Apply for Pilot</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </header>
  );
}
