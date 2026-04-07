import type { Metadata } from "next";
import "./globals.css";
import { AuthWrapper } from "./auth-wrapper";
import Footer from "@/components/ui/Footer";

export const metadata: Metadata = {
  icons: { icon: "/favicon.svg" },
  title: "Eazy HWPX",
  description: "양식 파일 + 내 자료, AI가 합쳐서 완성합니다",
  openGraph: {
    title: "Eazy HWPX",
    description: "양식 파일 + 내 자료, AI가 합쳐서 완성합니다",
    images: [{ url: "https://eazyhwpx.kr/og-image.png", width: 1200, height: 630 }],
    siteName: "Eazy HWPX",
  },
  twitter: {
    card: "summary_large_image",
    title: "Eazy HWPX",
    description: "양식 파일 + 내 자료, AI가 합쳐서 완성합니다",
    images: ["https://eazyhwpx.kr/og-image.png"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
        />
      </head>
      <body className="antialiased flex flex-col min-h-screen">
        <AuthWrapper>{children}</AuthWrapper>
        <Footer />
      </body>
    </html>
  );
}
