import type { Metadata } from "next";
import "./globals.css";
import { AuthWrapper } from "./auth-wrapper";

export const metadata: Metadata = {
  title: "Eazy HWPX",
  description: "한글 양식에 내용을 채워 새 문서를 만듭니다",
  openGraph: {
    title: "Eazy HWPX",
    description: "한글 양식에 내용을 채워 새 문서를 만듭니다",
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
