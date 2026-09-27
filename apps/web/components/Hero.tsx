'use client';

import React from 'react';
import { Sparkles, ArrowRight, Play, CheckCircle2, Shield, Zap, Code2 } from 'lucide-react';

interface HeroProps {
  onOpenPilot: () => void;
}

export function Hero({ onOpenPilot }: HeroProps) {
  return (
    <section className="relative pt-16 pb-20 md:pt-24 md:pb-28 overflow-hidden">
      {/* Background Glow Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-arc-cyan/20 to-arc-blue/20 blur-[130px] rounded-full pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Subhead Pill */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-arc-card/90 border border-arc-border shadow-glow-cyan text-xs sm:text-sm font-medium text-slate-200 mb-8">
          <Sparkles className="w-4 h-4 text-arc-cyan" />
          <span>Circle Arc Ecosystem • Native USDC Gas Layer</span>
        </div>

        {/* Primary Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-white max-w-4xl mx-auto leading-[1.1]">
          The <span className="bg-gradient-to-r from-arc-cyan via-cyan-300 to-arc-blue bg-clip-text text-transparent">Gasless Economic Layer</span> for Arc.
        </h1>

        {/* Subtitle */}
        <p className="mt-6 text-lg sm:text-xl text-slate-300 max-w-2xl mx-auto font-normal leading-relaxed">
          Eliminate user onboarding drop-off. Turn Arc&apos;s native USDC into 100% invisible gas with enterprise corporate gas tanks and a 3-line developer SDK.
        </p>

        {/* CTAs */}
        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onOpenPilot}
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-gradient-to-r from-arc-cyan to-arc-blue text-arc-dark font-bold text-base hover:brightness-110 shadow-glow-cyan transition-all flex items-center justify-center gap-2 group"
          >
            <span>Apply for Pilot ($500 Gas Credit)</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>

          <a
            href="#simulator"
            className="w-full sm:w-auto px-8 py-3.5 rounded-xl bg-arc-card/80 border border-arc-border hover:border-arc-cyan/40 text-slate-200 font-semibold text-base transition-all flex items-center justify-center gap-2 hover:bg-arc-card"
          >
            <Play className="w-4 h-4 text-arc-cyan fill-arc-cyan/20" />
            <span>Interactive Simulator</span>
          </a>

          <a
            href="#sdk"
            className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-transparent hover:bg-white/5 text-slate-400 hover:text-white font-medium text-base transition-colors flex items-center justify-center gap-2"
          >
            <Code2 className="w-4 h-4" />
            <span>View SDK</span>
          </a>
        </div>

        {/* 4 Feature Badges */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
          <div className="p-4 rounded-2xl bg-arc-card/50 border border-arc-border/70 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-arc-cyan mb-1.5 font-bold text-xl sm:text-2xl">
              <span>$0.00</span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Gas Paid by End Users</p>
          </div>

          <div className="p-4 rounded-2xl bg-arc-card/50 border border-arc-border/70 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-arc-purple mb-1.5 font-bold text-xl sm:text-2xl">
              <span>ERC-4337</span>
            </div>
            <p className="text-xs text-slate-400 font-medium">v0.7 EntryPoint Standard</p>
          </div>

          <div className="p-4 rounded-2xl bg-arc-card/50 border border-arc-border/70 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-arc-green mb-1.5 font-bold text-xl sm:text-2xl">
              <span>&lt; 3.0s</span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Sub-Second Sponsorship</p>
          </div>

          <div className="p-4 rounded-2xl bg-arc-card/50 border border-arc-border/70 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-slate-100 mb-1.5 font-bold text-xl sm:text-2xl">
              <span>3 Lines</span>
            </div>
            <p className="text-xs text-slate-400 font-medium">Plug-and-Play Integration</p>
          </div>
        </div>
      </div>
    </section>
  );
}
