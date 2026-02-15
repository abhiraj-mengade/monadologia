import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Leibniz's Monadologia — Where Math Meets Chaos",
  description: "An autonomous agent simulation where gossip chains ARE monadic bind, parties ARE Kleisli composition, and the Landlord IS the runtime.",
  icons: {
    icon: [
      { url: '/icon.svg', type: 'image/svg+xml' },
      { url: '/favicon.ico', sizes: 'any' },
    ],
    apple: '/icon.svg',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="alternate icon" href="/favicon.ico" />
      </head>
      <body>{children}</body>
    </html>
  );
}
