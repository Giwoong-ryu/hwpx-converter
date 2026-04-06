import type { Metadata } from "next";
import "./globals.css";
import { AuthWrapper } from "./auth-wrapper";

export const metadata: Metadata = {
  title: "Eazy HWPX",
  description: "양식 파일 + 내 자료, AI가 합쳐서 완성합니다",
  openGraph: {
    title: "Eazy HWPX",
    description: "양식 파일 + 내 자료, AI가 합쳐서 완성합니다",
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
      <body className="antialiased">
        <AuthWrapper>{children}</AuthWrapper>
      </body>
    </html>
  );
}
