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

export async function aiMap(fileId: string, text: string, contentFiles?: File[], mode?: "direct" | "ai") {
  const fd = new FormData();
  fd.append("file_id", fileId);
  fd.append("text", text);
  if (mode) fd.append("mode", mode);
  if (contentFiles && contentFiles.length === 1) {
    fd.append("content_file", contentFiles[0]);
  } else if (contentFiles && contentFiles.length > 1) {
    contentFiles.forEach((f) => fd.append("content_files", f));
  }
  const token = await _getToken();
  const headers: Record<string, string> = { "X-Fingerprint": _fingerprint() };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 300000); // 5분 타임아웃
  try {
    const res = await fetch(`${API}/ai/map`, { method: "POST", body: fd, headers, signal: controller.signal });
    if (!res.ok) await handleError(res, "매핑 실패");
    return res.json();
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("AI 처리 시간이 초과되었습니다. 더 작은 양식으로 시도하거나, 잠시 후 다시 시도해주세요.");
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
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

// ═══ 프리셋 API ═══

export async function listPresets() {
  const token = await _getToken();
  if (!token) return [];
  const res = await fetch(`${API}/preset/list`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return [];
  const data = await res.json();
  return data.presets || [];
}

export async function createPreset(name: string, data: Record<string, string>) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/preset/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name, data }),
  });
  if (!res.ok) await handleError(res, "프리셋 저장 실패");
  return res.json();
}

export async function deletePreset(id: number) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/preset/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) await handleError(res, "프리셋 삭제 실패");
  return res.json();
}

// ═══ 매핑 저장 API ═══

export async function listMyMappings() {
  const token = await _getToken();
  if (!token) return [];
  const res = await fetch(`${API}/mapping/list`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return [];
  const data = await res.json();
  return data.mappings || [];
}

export async function saveMapping(formName: string, mappings: Record<string, string>, fieldCount: number) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/mapping/save`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ form_name: formName, mappings, form_field_count: fieldCount }),
  });
  if (!res.ok) await handleError(res, "매핑 저장 실패");
  return res.json();
}

export async function loadMapping(id: number) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/mapping/${id}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) await handleError(res, "매핑 불러오기 실패");
  return res.json();
}

export async function deleteMapping(id: number) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/mapping/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) await handleError(res, "매핑 삭제 실패");
  return res.json();
}

export async function listPublicMappings(page = 1) {
  const res = await fetch(`${API}/mapping/public/list?page=${page}&size=20`);
  if (!res.ok) return { mappings: [], page: 1, size: 20 };
  return res.json();
}

export async function toggleLike(mappingId: number) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/mapping/${mappingId}/like`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) await handleError(res, "좋아요 실패");
  return res.json();
}

export async function updateMappingPublic(id: number, isPublic: boolean) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/mapping/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ is_public: isPublic }),
  });
  if (!res.ok) await handleError(res, "공개 설정 실패");
  return res.json();
}

// ═══ 양식 갤러리 API ═══

export interface GalleryForm {
  id: number;
  title: string;
  category: string;
  field_count: number;
  doc_type: string | null;
  likes: number;
  downloads: number;
  created_at: string;
  user_id: string;
  liked?: boolean;
}

export async function listGalleryForms(opts?: { category?: string; sort?: string; q?: string; page?: number }) {
  const params = new URLSearchParams();
  if (opts?.category) params.set("category", opts.category);
  if (opts?.sort) params.set("sort", opts.sort);
  if (opts?.q) params.set("q", opts.q);
  if (opts?.page) params.set("page", String(opts.page));
  const res = await fetch(`${API}/gallery/list?${params}`);
  if (!res.ok) return { forms: [], page: 1, size: 20 };
  return res.json();
}

export async function getGalleryForm(id: number) {
  const res = await fetch(`${API}/gallery/${id}`);
  if (!res.ok) throw new Error("양식을 찾을 수 없습니다.");
  return res.json();
}

export async function downloadGalleryForm(id: number): Promise<Blob> {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/gallery/${id}/download`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("다운로드 실패");
  return res.blob();
}

export async function shareFormToGallery(file: File, title: string, category: string) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const fd = new FormData();
  fd.append("file", file);
  fd.append("title", title);
  fd.append("category", category);
  const res = await fetch(`${API}/gallery/share`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: fd,
  });
  if (!res.ok) await handleError(res, "양식 공유 실패");
  return res.json();
}

export async function toggleGalleryLike(formId: number) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/gallery/${formId}/like`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) await handleError(res, "좋아요 실패");
  return res.json();
}

export async function useGalleryForm(formId: number) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/gallery/${formId}/use`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) await handleError(res, "양식 불러오기 실패");
  return res.json();
}

export async function deleteGalleryForm(formId: number) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/gallery/${formId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) await handleError(res, "삭제 실패");
  return res.json();
}

// ═══ 마이페이지 API ═══

export async function listAchievements() {
  const token = await _getToken();
  if (!token) return { achievements: [], definitions: {} };
  const res = await fetch(`${API}/achievements/list`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return { achievements: [], definitions: {} };
  return res.json();
}

export async function getUsageHistory(days = 30) {
  const token = await _getToken();
  if (!token) return { history: [], summary: {} };
  const res = await fetch(`${API}/usage/history?days=${days}`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) return { history: [], summary: {} };
  return res.json();
}

// ═══ 쿠폰 API ═══

export async function checkCoupon(code: string) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/coupon/check`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "쿠폰 확인 실패" }));
    throw new Error(typeof data.detail === "string" ? data.detail : "쿠폰 확인 실패");
  }
  return res.json();
}

export async function redeemCoupon(code: string) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const res = await fetch(`${API}/coupon/redeem`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ code }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "쿠폰 적용 실패" }));
    throw new Error(typeof data.detail === "string" ? data.detail : "쿠폰 적용 실패");
  }
  return res.json();
}

export async function updatePreset(id: number, name?: string, data?: Record<string, string>) {
  const token = await _getToken();
  if (!token) throw new Error("로그인이 필요합니다.");
  const body: Record<string, unknown> = {};
  if (name !== undefined) body.name = name;
  if (data !== undefined) body.data = data;
  const res = await fetch(`${API}/preset/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!res.ok) await handleError(res, "프리셋 수정 실패");
  return res.json();
}
