import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Leibniz's Monadologia — Where Math Meets Chaos",
  description: "An autonomous agent simulation where gossip chains ARE monadic bind, parties ARE Kleisli composition, and the Landlord IS the runtime.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
