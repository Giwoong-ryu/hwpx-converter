"""
AI 매핑 모듈 - Gemini 3 Flash로 양식 필드와 내용을 자동 매핑
"""
import json
import os
import re

from google import genai
from google.genai import types

MODELS = {
    "mapping": "gemini-2.5-flash",       # 내용 매핑 (기존 내용 → 양식 채우기)
    "generation": "gemini-3-flash-preview",  # 내용 생성 (AI가 작성)
}
MODEL_NAME = os.environ.get("DOCFLOW_MODEL", MODELS["mapping"])

SYSTEM_PROMPT_MAP = """\
당신은 한글 문서 양식 작성 도우미입니다.
사용자가 양식(HWP/HWPX)의 테이블 구조와 내용을 제공하면, 값 필드에 적절한 내용을 매핑합니다.

양식은 테이블 구조로 제공됩니다. 각 행에서:
- [H] 표시가 있는 셀 = 라벨/헤더 (절대 교체 금지)
- __N 접미사가 붙은 셀 = 같은 유형의 N번째 항목 (예: 회사명__1, 회사명__2)
- 일반 글씨 셀 = 값 (교체 대상)

규칙:
1. 라벨/헤더 셀은 절대 교체하지 마세요.
2. 값 셀만 사용자 내용에서 찾아 매핑하세요.
3. 사용자 내용에 없는 정보는 추측하지 마세요.
4. __N 접미사 셀은 N번째 해당 항목을 채우세요. 빠짐없이 모두 포함하세요.
5. 경력, 학력처럼 시기/날짜가 있는 항목은 과거(오래된 순)에서 현재 순으로 위(__1)부터 채우세요.
6. 반드시 JSON만 반환하세요. 설명이나 마크다운 없이.
7. __N 접미사가 있는 셀은 JSON 키에도 반드시 __N을 포함하세요. 예: {"회사명__1": "A사", "회사명__2": "B사"}"""

SYSTEM_PROMPT_GEN = """\
당신은 한글 문서 양식 작성 도우미입니다.
사용자가 양식(HWP/HWPX)의 테이블 구조와 간단한 지시를 제공하면, 값 필드를 새로 작성합니다.

양식은 테이블 구조로 제공됩니다. 각 행에서:
- [H] 표시가 있는 셀 = 라벨/헤더 (절대 교체 금지)
- __N 접미사가 붙은 셀 = 같은 유형의 N번째 항목 (예: 회사명__1, 회사명__2)
- 일반 글씨 셀 = 값 (교체 대상)

규칙:
1. 라벨/헤더 셀은 절대 교체하지 마세요. 테이블 구조를 보고 판단하세요.
2. 값 셀만 사용자 요청 주제에 맞게 새로 작성하세요.
3. 현실적이고 구체적인 내용을 작성하세요.
4. __N 접미사 셀은 N번째 해당 항목을 작성하세요. 빠짐없이 모두 포함하세요.
5. 경력, 학력처럼 시기/날짜가 있는 항목은 과거(오래된 순)에서 현재 순으로 위(__1)부터 채우세요.
6. 반드시 JSON만 반환하세요. 설명이나 마크다운 없이.
7. __N 접미사가 있는 셀은 JSON 키에도 반드시 __N을 포함하세요. 예: {"회사명__1": "A사", "회사명__2": "B사"}
8. 가능한 한 많은 값 필드를 채우세요. 빠뜨리지 마세요."""

USER_PROMPT_MAP = """\
[양식 구조]
{fields}

[사용자 제공 내용]
{content}

위 양식에서 [H] 태그가 없는 값 셀 중, 사용자 내용으로 교체해야 할 항목을 JSON으로 반환하세요.
형식: {{"원본 텍스트": "새 텍스트", ...}}
라벨/헤더는 절대 포함하지 마세요."""

USER_PROMPT_GEN = """\
[양식 구조]
{fields}

[사용자 요청]
{content}

위 양식에서 [H] 태그가 없는 값 셀을 사용자 요청 주제로 새로 작성하세요.
라벨/헤더 셀은 절대 교체하지 마세요. 값 셀만 교체하세요.
__N 접미사 셀은 각각 별도로 작성하세요 (예: {{"회사명__1": "A사", "회사명__2": "B사"}}).
가능한 한 빠짐없이 교체하세요.

형식: {{"원본 텍스트": "새로 작성한 텍스트", ...}}"""

# 생성 요청 감지 키워드
_GEN_KEYWORDS = [
    "써줘", "작성해줘", "만들어줘", "채워줘", "생성해줘", "작성해",
    "만들어", "채워", "생성해", "써", "작성", "통합으로", "간략히",
    "쓰게끔", "으로 써", "으로 작성", "내용을 넣어", "정리해줘",
]


def _format_structured_fields(structured):
    """구조화된 필드 데이터를 AI 프롬프트용 텍스트로 변환한다.

    테이블은 마크다운 테이블 형태, bold/bg 셀은 [H] 태그로 표시.
    중복 값 셀에는 __N 인덱스를 붙여 AI가 순서대로 개별 매핑하도록 한다.
    """
    _SKIP = {"□", "☑", "※", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "☐", "○", "●"}

    # 1패스: 값 셀 텍스트 빈도 계산 (중복 여부 파악)
    text_freq: dict[str, int] = {}
    for table in structured["tables"]:
        for row in table["rows"]:
            for cell in row:
                t = cell["text"].strip()
                if t and t not in _SKIP and not cell["bold"] and not cell["bg"]:
                    text_freq[t] = text_freq.get(t, 0) + 1

    # 2패스: 마크다운 테이블 생성 (중복 셀만 __N 추가)
    lines = []
    text_seen: dict[str, int] = {}

    for ti, table in enumerate(structured["tables"]):
        lines.append(f"[표{ti+1}]")
        for row in table["rows"]:
            cells = []
            for cell in row:
                text = cell["text"].strip()
                if not text or text in _SKIP:
                    cells.append("")
                    continue
                if cell["bold"] or cell["bg"]:
                    cells.append(f"[H]{text}")
                else:
                    if text_freq.get(text, 1) > 1:
                        # 중복 셀: __N 인덱스 추가 (AI가 각각 구분하도록)
                        text_seen[text] = text_seen.get(text, 0) + 1
                        cells.append(f"{text}__{text_seen[text]}")
                    else:
                        cells.append(text)
            if any(c for c in cells):
                lines.append("| " + " | ".join(cells) + " |")

    if structured.get("paragraphs"):
        lines.append("\n[본문]")
        for p in structured["paragraphs"]:
            p = p.strip()
            if p and p not in _SKIP:
                lines.append(f"- {p}")

    return "\n".join(lines)


def _call_with_retry(client, model_name, prompt, system_prompt, temperature, max_retries=2):
    """Gemini API 호출 + 429 재시도"""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=32768,
                )
            )
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                import time
                print(f"[ai/map] 429 rate limit, 3초 대기 후 재시도")
                time.sleep(3)
            else:
                raise


def _call_cached_with_retry(client, model_name, cache_name, prompt, temperature, max_retries=2):
    """캐시 사용 Gemini API 호출 + 429 재시도"""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    cached_content=cache_name,
                    temperature=temperature,
                    max_output_tokens=32768,
                )
            )
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                import time
                print(f"[ai/map] 429 rate limit, 3초 대기 후 재시도")
                time.sleep(3)
            else:
                raise


def _collect_results(parsed):
    """파싱된 JSON에서 유효한 key-value 쌍만 수집"""
    results = {}
    for k, v in parsed.items():
        if not isinstance(k, str) or not k.strip():
            continue
        k = k.strip()
        if isinstance(v, (int, float)):
            v = str(v)
        if not isinstance(v, str) or not v.strip():
            continue
        results[k] = v.strip()
    return results


def _is_generation_request(text):
    """사용자 입력이 생성 요청인지 판단한다."""
    if not text:
        return False
    return any(kw in text for kw in _GEN_KEYWORDS)


def _get_api_key():
    """환경변수에서 Gemini API 키를 가져온다."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        # .env 파일 체크
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip("\"'")
                        break
    return key


def _parse_json_response(text):
    """Gemini 응답에서 JSON을 추출한다. 잘린 JSON도 최대한 복구한다."""
    # 마크다운 코드블록 제거
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 첫 { 부터 마지막 } 까지 추출
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        try:
            return json.loads(text[first:last + 1])
        except json.JSONDecodeError:
            pass

    # 잘린 JSON 복구 시도: 마지막 완전한 key-value 쌍까지 자르고 } 추가
    if first >= 0:
        fragment = text[first:]
        # 마지막 완전한 "value" 다음의 쉼표나 줄바꿈까지 찾기
        last_quote = fragment.rfind('"')
        if last_quote > 0:
            # 마지막 따옴표 이후 잘라내고 } 추가
            candidate = fragment[:last_quote + 1]
            # 마지막 항목 뒤 쉼표 제거
            candidate = candidate.rstrip().rstrip(",")
            candidate += "\n}"
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass

    # 배열 시도
    first = text.find("[")
    last = text.rfind("]")
    if first >= 0 and last > first:
        try:
            return json.loads(text[first:last + 1])
        except json.JSONDecodeError:
            pass

    return None


def _read_content_file(file_path):
    """내용 파일을 읽어 텍스트로 반환한다."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".txt", ".md", ".csv"):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    if ext in (".xlsx", ".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True)
            lines = []
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    cells = [str(c) if c is not None else "" for c in row]
                    lines.append(" | ".join(cells))
            wb.close()
            return "\n".join(lines)
        except Exception as e:
            return f"[엑셀 읽기 실패: {e}]"

    if ext == ".docx":
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception as e:
            return f"[워드 읽기 실패: {e}]"

    if ext in (".html", ".htm"):
        try:
            from bs4 import BeautifulSoup
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
            # script/style 제거 후 텍스트 추출
            for tag in soup(["script", "style"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except Exception as e:
            return f"[HTML 읽기 실패: {e}]"

    if ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data, ensure_ascii=False, indent=2)

    # 기본: 텍스트로 읽기
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return f"[파일 읽기 실패: {file_path}]"


def _parse_kv_from_text(text: str) -> dict[str, str]:
    """텍스트에서 key:value 쌍을 파싱한다.

    지원 형식:
    - "이름: 홍길동"
    - "이름 홍길동" (공백 구분, 짧은 키)
    - 탭 구분 "이름\t홍길동"
    - 엑셀 행 "이름 | 홍길동 | ..."
    """
    kv = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # 콜론 구분 (가장 일반적)
        if ":" in line:
            key, _, val = line.partition(":")
            key, val = key.strip(), val.strip()
            if key and val and len(key) <= 30:
                kv[key] = val
            continue

        # 탭 구분
        if "\t" in line:
            parts = [p.strip() for p in line.split("\t") if p.strip()]
            if len(parts) >= 2 and len(parts[0]) <= 30:
                kv[parts[0]] = parts[1]
            continue

        # 파이프 구분 (엑셀 변환 형식)
        if " | " in line:
            parts = [p.strip() for p in line.split(" | ") if p.strip()]
            if len(parts) >= 2 and len(parts[0]) <= 30:
                kv[parts[0]] = parts[1]
            continue

    return kv


def _parse_kv_from_excel(file_path: str) -> dict[str, str]:
    """엑셀 파일에서 key:value 구조를 직접 추출한다.

    지원 구조:
    - A열=키, B열=값 (2열 구조)
    - 헤더 행 자동 감지
    """
    try:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        kv = {}
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                cells = [str(c).strip() if c is not None else "" for c in row]
                non_empty = [c for c in cells if c]
                if len(non_empty) >= 2:
                    key = non_empty[0]
                    val = non_empty[1]
                    if key and val and len(key) <= 30 and key not in ("None", ""):
                        kv[key] = val
        wb.close()
        return kv
    except Exception as e:
        print(f"[direct_map] 엑셀 직접 추출 실패: {e}")
        return {}


def direct_map(form_texts: list[str], content_paths: list[str], text: str = "") -> tuple[dict, str | None]:
    """AI 없이 문서에서 텍스트 추출 → 양식 필드명과 직접 매칭한다.

    Args:
        form_texts: 양식에서 추출된 텍스트 목록
        content_paths: 내용 파일 경로 목록
        text: 사용자가 입력한 텍스트 (선택)

    Returns:
        dict: {원본필드텍스트: 매핑된값} — 못 찾은 필드는 포함하지 않음
        str: 에러 메시지 (성공 시 None)
    """
    # 1. 모든 소스에서 key:value 수집
    all_kv: dict[str, str] = {}

    # 텍스트 입력
    if text and text.strip():
        all_kv.update(_parse_kv_from_text(text.strip()))

    # 파일별 처리
    for fp in content_paths:
        ext = os.path.splitext(fp)[1].lower()
        if ext in (".xlsx", ".xls"):
            # 엑셀: key:value 직접 추출 우선
            kv = _parse_kv_from_excel(fp)
            if kv:
                all_kv.update(kv)
            else:
                # 폴백: 텍스트로 변환 후 파싱
                raw = _read_content_file(fp)
                all_kv.update(_parse_kv_from_text(raw))
        else:
            raw = _read_content_file(fp)
            all_kv.update(_parse_kv_from_text(raw))

    if not all_kv and not text.strip():
        return None, "내용을 입력하거나 파일을 업로드해주세요."

    if not all_kv:
        return None, "파일에서 키:값 형식의 내용을 찾지 못했습니다. '항목명: 값' 형식으로 입력해주세요."

    print(f"[direct_map] key:value 파싱 완료: {len(all_kv)}개")

    # 2. 양식 필드와 매칭
    _SKIP = {"□", "☑", "※", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "☐", "○", "●"}
    result: dict[str, str] = {}

    # 키 정규화 인덱스 (공백 제거 버전으로 매칭)
    kv_norm: dict[str, str] = {}
    for k, v in all_kv.items():
        kv_norm[k] = v
        kv_norm[re.sub(r"\s+", "", k)] = v

    # __N 접미사별 카운터 (같은 기본 필드 여러 개 순서대로 채우기)
    base_counter: dict[str, int] = {}

    for field in form_texts:
        if not field.strip() or field.strip() in _SKIP:
            continue

        # __N 접미사 처리
        base = re.sub(r"__\d+$", "", field)
        has_suffix = base != field

        if has_suffix:
            base_counter[base] = base_counter.get(base, 0) + 1
            # 소스에서 해당 순번 값 찾기
            # 먼저 "기본키__N" 직접 매칭 시도
            direct_key = field
            if direct_key in kv_norm:
                result[field] = kv_norm[direct_key]
                continue
            # 기본키로 첫 번째 값 사용 (순번=1일 때만)
            base_norm = re.sub(r"\s+", "", base)
            val = kv_norm.get(base) or kv_norm.get(base_norm)
            if val and base_counter[base] == 1:
                result[field] = val
            continue

        # 일반 필드: 정확 매칭
        field_norm = re.sub(r"\s+", "", field)
        val = kv_norm.get(field) or kv_norm.get(field_norm)
        if val:
            result[field] = val

    print(f"[direct_map] 매핑 결과: {len(result)}개 / {len(form_texts)}개 필드")

    if not result:
        return None, "양식 필드와 일치하는 항목을 찾지 못했습니다. 파일의 항목명이 양식과 일치하는지 확인해주세요."

    return result, None


def map_content(form_texts, user_content, content_file=None, structured=None, extra_content_files=None):
    """양식 필드와 사용자 내용을 AI로 매핑한다.

    Args:
        form_texts: 양식에서 추출된 텍스트 목록 (평면 리스트)
        user_content: 사용자가 입력한 텍스트
        content_file: 내용이 담긴 파일 경로 (선택)
        structured: extract_structured_fields()의 결과 (테이블 구조, 선택)
        extra_content_files: 추가 내용 파일 경로 리스트 (선택, 복수 파일)

    Returns:
        dict: {원본텍스트: 새텍스트} 또는 에러 시 None
        str: 에러 메시지 (성공 시 None)
    """
    api_key = _get_api_key()
    if not api_key:
        return None, "GEMINI_API_KEY가 설정되지 않았습니다. 환경변수 또는 .env 파일에 설정해주세요."

    # 내용 조합 (텍스트 + 파일 1개 + 추가 파일들)
    content_parts = []
    if user_content and user_content.strip():
        content_parts.append(user_content.strip())
    if content_file:
        file_text = _read_content_file(content_file)
        content_parts.append(file_text)
    if extra_content_files:
        for fp in extra_content_files:
            try:
                extra_text = _read_content_file(fp)
                content_parts.append(extra_text)
            except Exception as e:
                print(f"[ai/map] 추가 파일 읽기 실패: {e}")

    if not content_parts:
        return None, "내용을 입력하거나 파일을 업로드해주세요."

    combined_content = "\n\n".join(content_parts)
    print(f"[ai/map] 콘텐츠 합산: {len(content_parts)}개 소스, {len(combined_content):,}자")

    # 생성 요청 vs 매핑 요청 판단
    is_gen = _is_generation_request(combined_content)

    # 구조화된 필드가 있으면 테이블 형식 프롬프트 사용
    use_structured = structured is not None and len(structured.get("tables", [])) > 0
    if use_structured:
        structured_text = _format_structured_fields(structured)
        print(f"[ai/map] 구조화 모드: 표 {len(structured['tables'])}개, 본문 {len(structured.get('paragraphs', []))}개")

    # 양식 필드 필터링 (평면 리스트 - 구조화 미사용 시 폴백)
    _SKIP = {"□", "☑", "※", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "☐", "○", "●"}
    if is_gen:
        filtered_fields = [t for t in form_texts if len(t) > 4 and t.strip() not in _SKIP]
        filtered_fields = [t[:200] if len(t) > 200 else t for t in filtered_fields]
    else:
        filtered_fields = [t for t in form_texts if 1 < len(t) <= 120 and t.strip() not in _SKIP]

    # 필드 상한: 3000개 (약 100장 분량)
    MAX_FIELDS = 3000
    if len(filtered_fields) > MAX_FIELDS:
        print(f"[ai/map] 필드 {len(filtered_fields)}개 → {MAX_FIELDS}개로 제한")
        filtered_fields = filtered_fields[:MAX_FIELDS]

    # 배치 분할 호출 (150개씩 나눠서 전체 커버)
    BATCH_SIZE = 150
    if is_gen:
        system_prompt = SYSTEM_PROMPT_GEN
        model_name = MODELS["generation"]
    else:
        system_prompt = SYSTEM_PROMPT_MAP
        model_name = MODELS["mapping"]

    try:
        client = genai.Client(api_key=api_key)
        temperature = 0.3 if is_gen else 0.1

        all_results = {}

        # 양식 필드를 배치로 분할
        if use_structured:
            struct_lines = structured_text.split("\n")
            field_batches = []
            current_batch = []
            current_lines = 0
            STRUCT_BATCH_LINES = 200
            for line in struct_lines:
                is_section_start = line.startswith("[표") or line.startswith("[본문")
                is_oversized = current_lines >= STRUCT_BATCH_LINES * 2
                if (is_section_start and current_lines >= STRUCT_BATCH_LINES) or is_oversized:
                    field_batches.append("\n".join(current_batch))
                    current_batch = []
                    current_lines = 0
                current_batch.append(line)
                current_lines += 1
            if current_batch:
                field_batches.append("\n".join(current_batch))
        else:
            field_batches = []
            for i in range(0, len(filtered_fields), BATCH_SIZE):
                batch = filtered_fields[i:i + BATCH_SIZE]
                field_batches.append("\n".join(f"- {t}" for t in batch))

        total_batches = len(field_batches)
        need_cache = total_batches > 1

        # 소형 문서 (1배치): 캐시 없이 1회 호출
        if not need_cache:
            prompt_template = USER_PROMPT_GEN if is_gen else USER_PROMPT_MAP
            prompt = prompt_template.format(fields=field_batches[0], content=combined_content)
            print(f"[ai/map] 1회 호출 (캐시 불필요, 필드 {len(filtered_fields)}개)")

            response = _call_with_retry(client, model_name, prompt, system_prompt, temperature)
            parsed = _parse_json_response(response.text)
            if parsed:
                all_results = _collect_results(parsed)

        # 대형 문서 (다배치): Explicit Caching 사용
        else:
            cache = None
            try:
                # 캐시 생성: 시스템 프롬프트 + 콘텐츠 (TTL 10분)
                cache = client.caches.create(
                    model=model_name,
                    config=types.CreateCachedContentConfig(
                        system_instruction=system_prompt,
                        contents=[types.Content(role="user", parts=[types.Part(text=combined_content)])],
                        ttl="600s",
                    )
                )
                print(f"[ai/map] 캐시 생성 완료: {total_batches}배치, TTL=10분")

                for batch_idx, batch_text in enumerate(field_batches):
                    prompt_template = USER_PROMPT_GEN if is_gen else USER_PROMPT_MAP
                    # 캐시에 콘텐츠가 있으므로 프롬프트에서는 양식만
                    prompt = prompt_template.format(fields=batch_text, content="(위에 제공된 내용 참조)")

                    print(f"[ai/map] cached batch {batch_idx+1}/{total_batches}")

                    if batch_idx > 0:
                        import time
                        time.sleep(0.5)

                    # 캐시 유효성 체크 + 재생성
                    try:
                        client.caches.get(name=cache.name)
                    except Exception:
                        print("[ai/map] 캐시 만료, 재생성")
                        cache = client.caches.create(
                            model=model_name,
                            config=types.CreateCachedContentConfig(
                                system_instruction=system_prompt,
                                contents=[types.Content(role="user", parts=[types.Part(text=combined_content)])],
                                ttl="600s",
                            )
                        )

                    response = _call_cached_with_retry(client, model_name, cache.name, prompt, temperature)
                    parsed = _parse_json_response(response.text)
                    if parsed:
                        for k, v in _collect_results(parsed).items():
                            all_results[k] = v

            except Exception as cache_err:
                if "cache" in str(cache_err).lower() or "CachedContent" in str(cache_err):
                    # 캐시 기능 실패 → 폴백: 캐시 없이 반복 전송
                    print(f"[ai/map] 캐시 실패, 폴백 모드: {cache_err}")
                    for batch_idx, batch_text in enumerate(field_batches):
                        prompt_template = USER_PROMPT_GEN if is_gen else USER_PROMPT_MAP
                        prompt = prompt_template.format(fields=batch_text, content=combined_content)
                        print(f"[ai/map] fallback batch {batch_idx+1}/{total_batches}")
                        if batch_idx > 0:
                            import time
                            time.sleep(0.5)
                        response = _call_with_retry(client, model_name, prompt, system_prompt, temperature)
                        parsed = _parse_json_response(response.text)
                        if parsed:
                            for k, v in _collect_results(parsed).items():
                                all_results[k] = v
                else:
                    raise
            finally:
                # 3중 방어 (1): 즉시 삭제
                if cache:
                    try:
                        client.caches.delete(name=cache.name)
                        print("[ai/map] 캐시 삭제 완료")
                    except Exception:
                        pass  # (2): TTL 10분 자동 만료가 백업

        if not all_results:
            return None, "매핑할 항목을 찾지 못했습니다. 내용을 더 구체적으로 입력해주세요."

        # [Fix 1+5] AI 환각 키 정규화
        field_set = set(form_texts)
        # 공백/이스케이프 정규화된 역방향 인덱스
        _norm_index = {}
        for t in form_texts:
            _norm_index[t] = t
            _norm_index[t.replace("&lt;", "<").replace("&gt;", ">")] = t
            _norm_index[t.replace("<", "&lt;").replace(">", "&gt;")] = t
            _norm_index[re.sub(r"\s+", "", t)] = t  # 공백 제거 버전

        normalized = {}
        for k, v in all_results.items():
            if k in field_set:
                normalized[k] = v
                continue

            # 1단계: 이스케이프 변환
            matched = _norm_index.get(k) or _norm_index.get(
                k.replace("<", "&lt;").replace(">", "&gt;")
            ) or _norm_index.get(
                k.replace("&lt;", "<").replace("&gt;", ">")
            )

            # 2단계: 공백 제거 매칭
            if not matched:
                k_no_space = re.sub(r"\s+", "", k)
                matched = _norm_index.get(k_no_space)

            # 3단계: 접두사 매칭 (AI가 "- " 같은 접두사를 빼먹은 경우)
            if not matched:
                for t in form_texts:
                    if t.endswith(k) or k.endswith(t):
                        if min(len(k), len(t)) / max(len(k), len(t)) > 0.8:
                            matched = t
                            break

            normalized[matched or k] = v

        # [Fix 3] 미매핑 필드 재시도: 1차에서 누락된 필드만 모아서 2차 호출
        # 구조화 모드에서는 재시도 스킵 (평면 형식으로 보내면 라벨 보호 무효화됨)
        mapped_keys = set(normalized.keys())
        unmapped = [f for f in filtered_fields if f not in mapped_keys]
        if not use_structured and unmapped and len(unmapped) > 5:
            retry_batches = (len(unmapped) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"[ai/map] 미매핑 {len(unmapped)}개 재시도 ({retry_batches} batches)")
            for rb in range(min(retry_batches, 3)):  # 최대 3배치만 재시도
                start = rb * BATCH_SIZE
                batch = unmapped[start:start + BATCH_SIZE]
                fields_text = "\n".join(f"- {t}" for t in batch)
                prompt_template = USER_PROMPT_GEN if is_gen else USER_PROMPT_MAP
                retry_prompt = prompt_template.format(fields=fields_text, content=combined_content)

                import time
                time.sleep(1)
                try:
                    retry_resp = _call_with_retry(
                        client, model_name, retry_prompt, system_prompt, temperature
                    )
                    retry_parsed = _parse_json_response(retry_resp.text)
                    if retry_parsed:
                        for k2, v2 in _collect_results(retry_parsed).items():
                            matched2 = _norm_index.get(k2) or _norm_index.get(
                                k2.replace("<", "&lt;").replace(">", "&gt;")
                            ) or _norm_index.get(
                                k2.replace("&lt;", "<").replace("&gt;", ">")
                            )
                            normalized[matched2 or k2] = v2
                    print(f"[ai/map] 재시도 batch {rb+1}: +{len(retry_parsed or {})}개")
                except Exception as retry_e:
                    print(f"[ai/map] 재시도 실패: {retry_e}")

        return normalized, None

    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg or "401" in error_msg:
            return None, "AI 서비스 연결에 문제가 있습니다. 관리자에게 문의해주세요."
        if "429" in error_msg:
            return None, "요청이 많아 잠시 처리가 지연됩니다. 1분 후 다시 시도해주세요."
        if "timeout" in error_msg.lower() or "deadline" in error_msg.lower():
            return None, "AI 처리 시간이 초과되었습니다. 다시 시도해주세요."
        return None, "AI 처리 중 문제가 발생했습니다. 다시 시도해주세요."
