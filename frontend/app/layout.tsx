import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "CivicLens AI", description: "Report civic issues. Track action. Build better neighbourhoods with transparent civic intelligence." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }
