const API = "/api";

async function handleError(res: Response, fallback: string): Promise<never> {
  let detail = "";
  try {
    const data = await res.json();
    detail = data.detail || "";
  } catch {
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
  const res = await fetch(`${API}/ai/map`, { method: "POST", body: fd });
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
