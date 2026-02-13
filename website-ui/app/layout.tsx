import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Assyntrax | Eigen Engine",
  description: "Assyntrax - Eigen Engine for regime and risk diagnostics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning className="antialiased">
        {children}
      </body>
    </html>
  );
}

