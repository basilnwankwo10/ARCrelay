import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ArcRelay | The Gasless Economic Layer for Arc',
  description:
    'Enterprise ERC-4337 v0.7 Paymaster-as-a-Service and Corporate Gas Tanks for Circle Arc. Deliver 100% invisible gas and $0 transaction fees to consumer apps, games, and fintechs.',
  keywords: [
    'Arc',
    'Circle',
    'USDC',
    'Paymaster',
    'ERC-4337',
    'Gasless',
    'Account Abstraction',
    'Corporate Gas Tank',
    'ArcRelay',
  ],
  authors: [{ name: 'ArcRelay Team', url: 'https://arcrelay.tech' }],
  creator: 'ArcRelay',
  openGraph: {
    title: 'ArcRelay | The Gasless Economic Layer for Arc',
    description:
      'Turn native USDC into invisible gas. Integrate 1-line sponsorship (await arcrelay.sponsor) for your dApp on Arc.',
    url: 'https://arcrelay.tech',
    siteName: 'ArcRelay',
    images: [
      {
        url: 'https://arcrelay.tech/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'ArcRelay Gasless Infrastructure',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ArcRelay | The Gasless Economic Layer for Arc',
    description:
      'ERC-4337 Paymaster-as-a-Service & native USDC corporate gas infrastructure for Arc.',
    creator: '@ArcRelayHQ',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="bg-arc-dark text-slate-100 antialiased selection:bg-cyan-500 selection:text-black">
        {children}
      </body>
    </html>
  );
}
