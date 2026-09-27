'use client';

import React, { useState } from 'react';
import { Navbar } from '@/components/Navbar';
import { LiveProofBanner } from '@/components/LiveProofBanner';
import { Hero } from '@/components/Hero';
import { Simulator } from '@/components/Simulator';
import { CodeExplorer } from '@/components/CodeExplorer';
import { Architecture } from '@/components/Architecture';
import { PilotModal } from '@/components/PilotModal';
import { Footer } from '@/components/Footer';

export default function Home() {
  const [isPilotOpen, setIsPilotOpen] = useState<boolean>(false);

  return (
    <div className="min-h-screen flex flex-col bg-arc-dark">
      <Navbar onOpenPilot={() => setIsPilotOpen(true)} />
      <LiveProofBanner />

      <main className="flex-1">
        <Hero onOpenPilot={() => setIsPilotOpen(true)} />
        <Simulator />
        <CodeExplorer />
        <Architecture />
      </main>

      <Footer />

      <PilotModal
        isOpen={isPilotOpen}
        onClose={() => setIsPilotOpen(false)}
      />
    </div>
  );
}
