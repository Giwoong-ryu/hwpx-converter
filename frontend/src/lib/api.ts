const API = process.env.NEXT_PUBLIC_API_URL || "/api";

// 인증 토큰 주입용 (AuthContext에서 설정 + Supabase 폴백)
let _accessToken: string | null = null;
export function setApiToken(token: string | null) { _accessToken = token; }

async function _getToken(): Promise<string | null> {
  if (_accessToken) return _accessToken;
  // 폴백: Supabase에서 직접 세션 조회
  try {
    const { createClient } = await import("@supabase/supabase-js");
    const sb = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL || "",
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""
    );
    const { data } = await sb.auth.getSession();
    return data.session?.access_token || null;
  } catch { return null; }
}

function _authHeaders(): Record<string, string> {
  if (_accessToken) return { Authorization: `Bearer ${_accessToken}` };
  return {};
}

// 브라우저 핑거프린트 (비로그인 맛보기용)
function _fingerprint(): string {
  if (typeof window === "undefined") return "ssr";
  const nav = window.navigator;
  return btoa(`${nav.language}|${nav.hardwareConcurrency}|${screen.width}`).slice(0, 16);
}

export class GaugeEmptyError extends Error {
  error_code: string;
  plan: string;
  gauge_pct: number;
  constructor(data: { detail?: string; error_code?: string; plan?: string; gauge_pct?: number }) {
    super(data.detail || "사용량 초과");
    this.error_code = data.error_code || "GAUGE_EMPTY";
    this.plan = data.plan || "";
    this.gauge_pct = data.gauge_pct || 0;
  }
}

async function handleError(res: Response, fallback: string): Promise<never> {
  let detail = "";
  try {
    const data = await res.json();
    // 게이지 소진 에러 → 별도 에러 클래스
    if (data.detail?.error_code === "GAUGE_EMPTY" || data.detail?.error_code === "LOGIN_REQUIRED" || data.error_code) {
      const errData = typeof data.detail === "object" ? data.detail : data;
      throw new GaugeEmptyError(errData);
    }
    detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail) || "";
  } catch (e) {
    if (e instanceof GaugeEmptyError) throw e;
    // 비-JSON 응답 (프록시 에러 등)
  }
  throw new Error(detail || `${fallback} (${res.status})`);
}

export async function analyzeForm(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API}/form/analyze`, { method: "POST", body: fd });
  if (!res.ok) await handleError(res, "분석 실패");
  return res.json();
}

export async function aiMap(fileId: string, text: string, contentFile?: File) {
  const fd = new FormData();
  fd.append("file_id", fileId);
  fd.append("text", text);
  if (contentFile) fd.append("content_file", contentFile);
  const token = await _getToken();
  const headers: Record<string, string> = { "X-Fingerprint": _fingerprint() };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API}/ai/map`, { method: "POST", body: fd, headers });
  if (!res.ok) await handleError(res, "매핑 실패");
  return res.json();
}

export async function generateDoc(fileId: string, replacements: Record<string, string>, stripImages = false, outputFormat = "hwpx") {
  const res = await fetch(`${API}/form/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, replacements, strip_images: stripImages, output_format: outputFormat }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "생성 실패");
  return res.blob();
}

export async function batchGenerate(fileId: string, excel: File) {
  const fd = new FormData();
  fd.append("file_id", fileId);
  fd.append("excel", excel);
  const res = await fetch(`${API}/batch/generate`, { method: "POST", body: fd });
  if (!res.ok) throw new Error((await res.json()).detail || "대량 생성 실패");
  return res.blob();
}

export async function batchMapHeaders(fileId: string, excel: File) {
  const fd = new FormData();
  fd.append("file_id", fileId);
  fd.append("excel", excel);
  const res = await fetch(`${API}/batch/map-headers`, { method: "POST", body: fd });
  if (!res.ok) throw new Error((await res.json()).detail || "헤더 매핑 실패");
  return res.json();
}

export async function batchGenerateMapped(
  fileId: string, excelId: string,
  columnMappings: { header: string; form_text: string }[]
) {
  const res = await fetch(`${API}/batch/generate-mapped`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, excel_id: excelId, column_mappings: columnMappings }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "대량 생성 실패");
  return res.blob();
}

export async function extractData(files: File[]) {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  const res = await fetch(`${API}/extract/`, { method: "POST", body: fd });
  if (!res.ok) throw new Error((await res.json()).detail || "추출 실패");
  return res.blob();
}

export async function periodicGenerate(
  fileId: string, dateText: string, start: string, end: string,
  interval: string, dateFormat: string
) {
  const res = await fetch(`${API}/periodic/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      file_id: fileId, date_text: dateText,
      start, end, interval, date_format: dateFormat,
    }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "정기 문서 생성 실패");
  return res.blob();
}

export async function stampInsert(fileId: string, image: File, targetText: string) {
  const fd = new FormData();
  fd.append("file_id", fileId);
  fd.append("image", image);
  fd.append("target_text", targetText);
  const res = await fetch(`${API}/stamp/insert`, { method: "POST", body: fd });
  if (!res.ok) throw new Error((await res.json()).detail || "도장 삽입 실패");
  return res.blob();
}

export async function mergeDocs(files: File[]) {
  const fd = new FormData();
  files.forEach((f) => fd.append("files", f));
  const res = await fetch(`${API}/merge/`, { method: "POST", body: fd });
  if (!res.ok) throw new Error((await res.json()).detail || "병합 실패");
  return res.blob();
}

// 엑셀 채우기
export async function analyzeExcel(file: File) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${API}/excel/analyze`, { method: "POST", body: fd });
  if (!res.ok) throw new Error((await res.json()).detail || "엑셀 분석 실패");
  return res.json();
}

export async function fillExcel(fileId: string, replacements: Record<string, string>) {
  const res = await fetch(`${API}/excel/fill`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, replacements }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "엑셀 채우기 실패");
  return res.blob();
}

export async function excelBatch(fileId: string, dataExcel: File) {
  const fd = new FormData();
  fd.append("file_id", fileId);
  fd.append("data_excel", dataExcel);
  const res = await fetch(`${API}/excel/batch`, { method: "POST", body: fd });
  if (!res.ok) throw new Error((await res.json()).detail || "엑셀 대량 생성 실패");
  return res.blob();
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
