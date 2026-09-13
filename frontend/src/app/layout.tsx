import type { Metadata } from "next";
import { Inter, Roboto_Mono, Pacifico } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const robotoMono = Roboto_Mono({
  variable: "--font-roboto-mono",
  subsets: ["latin"],
});

const pacifico = Pacifico({
  variable: "--font-pacifico",
  subsets: ["latin"],
  weight: "400",
});

export const metadata: Metadata = {
  title: {
    default: "TripMate AI — AI-Powered Travel Planner",
    template: "%s | TripMate AI",
  },
  description:
    "Plan your perfect trip with our LangGraph multi-agent AI. Get personalized flights, hotels, and day-by-day itineraries in seconds.",
  keywords: [
    "AI travel planner",
    "trip planning",
    "flights",
    "hotels",
    "itinerary",
    "LangGraph",
  ],
  authors: [{ name: "TripMate AI" }],
  openGraph: {
    type: "website",
    siteName: "TripMate AI",
    title: "TripMate AI — AI-Powered Travel Planner",
    description:
      "Plan your perfect trip with our LangGraph multi-agent AI. Get personalized flights, hotels, and day-by-day itineraries in seconds.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} ${robotoMono.variable} ${pacifico.variable} antialiased min-h-screen bg-background`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
