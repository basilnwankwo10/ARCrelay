'use client';

import React from 'react';
import { Zap, ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-arc-dark border-t border-arc-border/80 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Logo & Tagline */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-arc-cyan to-arc-blue p-[1px]">
              <div className="w-full h-full bg-arc-dark rounded-[7px] flex items-center justify-center">
                <Zap className="w-4 h-4 text-arc-cyan fill-arc-cyan/20" />
              </div>
            </div>
            <div>
              <span className="text-base font-bold text-white tracking-tight">ArcRelay</span>
              <p className="text-xs text-slate-400">The Gasless Economic Layer for Arc</p>
            </div>
          </div>

          {/* Links */}
          <div className="flex flex-wrap items-center gap-6 text-xs text-slate-400">
            <a
              href="https://twitter.com/ArcRelayHQ"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-arc-cyan transition-colors"
            >
              X / Twitter (@ArcRelayHQ)
            </a>
            <a
              href="https://testnet.arcscan.app/address/0x600c83F91464440A1Fc2c4C723C78e2f51F43096"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-arc-cyan transition-colors"
            >
              Arcscan Contract
            </a>
            <a
              href="https://arc.network"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-arc-cyan transition-colors"
            >
              Arc Network
            </a>
            <a
              href="https://circle.com"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-arc-cyan transition-colors"
            >
              Circle Ecosystem
            </a>
          </div>

          {/* Copyright */}
          <div className="text-xs text-slate-500 font-mono">
            Chain ID 5042002 • MIT Open Source
          </div>
        </div>
      </div>
    </footer>
  );
}
