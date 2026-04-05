"""
AI 매핑 모듈 - Gemini 3 Flash로 양식 필드와 내용을 자동 매핑
"""
import json
import os
import re

import google.generativeai as genai

MODELS = {
    "mapping": "gemini-2.5-flash",       # 내용 매핑 (기존 내용 → 양식 채우기)
    "generation": "gemini-3-flash-preview",  # 내용 생성 (AI가 작성)
}
MODEL_NAME = os.environ.get("DOCFLOW_MODEL", MODELS["mapping"])

SYSTEM_PROMPT_MAP = """\
당신은 한글 문서 양식 작성 도우미입니다.
사용자가 양식(HWP/HWPX)과 내용을 제공하면, 양식의 텍스트 필드에 적절한 내용을 매핑합니다.

규칙:
1. 양식 필드의 원본 텍스트를 사용자 내용으로 교체할 매핑을 만드세요.
2. 아래 항목은 절대 교체하지 마세요 (양식의 구조를 유지해야 합니다):
   - 표의 헤더/라벨: "성명", "학교명", "회사명", "창업아이템명", "산출물", "자격명" 등 항목 이름
   - 행/열 제목: "학력사항", "경력사항", "자격사항" 등 섹션 제목
   - 구조 기호: □, ☑, ※, ①②③, /, ~
   - 안내 문구: "예시", "작성방법", "유의사항" 등 도움말
   - 선택지 텍스트: "졸업 / 중퇴 / 재학", "상/중/하" 등
3. 사용자 내용에 없는 정보는 추측하지 마세요.
4. 날짜, 이름, 회사명 같은 필드는 사용자 내용에서 찾아 매핑하세요.
5. 반드시 JSON만 반환하세요. 설명이나 마크다운 없이.
6. 핵심: "이 텍스트가 양식의 구조(라벨)인가, 채워야 할 내용인가?"를 판단하세요. 구조면 건너뛰세요."""

SYSTEM_PROMPT_GEN = """\
당신은 한글 문서 양식 작성 도우미입니다.
사용자가 양식(HWP/HWPX)과 간단한 지시를 제공하면, 양식의 내용을 직접 작성하여 채워줍니다.

규칙:
1. 양식의 내용 필드를 사용자 요청 주제에 맞게 새로 작성하세요.
2. 아래 항목은 절대 교체하지 마세요 (양식의 구조가 깨집니다):
   - 표의 헤더/라벨: "성명", "학교명", "회사명", "창업아이템명", "산출물" 등 항목 이름
   - 행/열 제목: "학력사항", "경력사항", "자격사항" 등 섹션 제목
   - 구조 기호: □, ☑, ※, ①②③, /, ~
   - 안내 문구: "예시", "작성방법", "유의사항" 등 도움말
   - 선택지 텍스트: "졸업 / 중퇴 / 재학", "상/중/하" 등
3. 기존에 채워진 회사명, 날짜, 금액, 설명 등 실제 내용은 모두 새 주제에 맞게 교체하세요.
4. 현실적이고 구체적인 내용을 작성하세요.
5. 반드시 JSON만 반환하세요. 설명이나 마크다운 없이.
6. 핵심: "이 텍스트가 양식의 구조(라벨)인가, 채워야 할 내용인가?"를 판단하세요. 구조면 건너뛰세요."""

USER_PROMPT_MAP = """\
[양식 필드 목록]
{fields}

[사용자 제공 내용]
{content}

위 양식 필드 중 사용자 내용으로 교체해야 할 항목을 JSON으로 반환하세요.
형식: {{"원본 텍스트": "새 텍스트", ...}}
변경 불필요한 필드는 제외하세요."""

USER_PROMPT_GEN = """\
[양식 필드 목록]
{fields}

[사용자 요청]
{content}

위 양식의 내용을 사용자 요청 주제로 교체하세요.
- 표의 항목 이름(라벨/헤더)은 절대 교체하지 마세요. 예: "창업아이템명", "산출물", "학교명" 등
- OOO, XXXX 같은 플레이스홀더는 반드시 교체하세요.
- 예시 문구("OO기술이 적용된..." 등)는 실제 내용으로 교체하세요.
- 사용자 내용에 없는 항목은 빈 문자열로 두지 말고, 주제에 맞게 작성하세요.

형식: {{"원본 텍스트": "새로 작성한 텍스트", ...}}"""

# 생성 요청 감지 키워드
_GEN_KEYWORDS = [
    "써줘", "작성해줘", "만들어줘", "채워줘", "생성해줘", "작성해",
    "만들어", "채워", "생성해", "써", "작성", "통합으로", "간략히",
    "쓰게끔", "으로 써", "으로 작성", "내용을 넣어", "정리해줘",
]


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


def map_content(form_texts, user_content, content_file=None, label_set=None):
    """양식 필드와 사용자 내용을 AI로 매핑한다.

    Args:
        form_texts: 양식에서 추출된 텍스트 목록
        user_content: 사용자가 입력한 텍스트
        content_file: 내용이 담긴 파일 경로 (선택)
        label_set: 라벨로 탐지된 텍스트 집합 (치환 제외 대상)

    Returns:
        dict: {원본텍스트: 새텍스트} 또는 에러 시 None
        str: 에러 메시지 (성공 시 None)
    """
    label_set = label_set or set()
    api_key = _get_api_key()
    if not api_key:
        return None, "GEMINI_API_KEY가 설정되지 않았습니다. 환경변수 또는 .env 파일에 설정해주세요."

    # 내용 조합
    content_parts = []
    if user_content and user_content.strip():
        content_parts.append(user_content.strip())
    if content_file:
        file_text = _read_content_file(content_file)
        content_parts.append(file_text)

    if not content_parts:
        return None, "내용을 입력하거나 파일을 업로드해주세요."

    combined_content = "\n\n".join(content_parts)

    # 생성 요청 vs 매핑 요청 판단
    is_gen = _is_generation_request(combined_content)

    # 양식 필드 필터링 (원래 기호만 제외)
    _SKIP = {"□", "☑", "※", "①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "☐", "○", "●"}
    if is_gen:
        filtered_fields = [t for t in form_texts if len(t) > 4 and t.strip() not in _SKIP]
        filtered_fields = [t[:200] if len(t) > 200 else t for t in filtered_fields]
    else:
        filtered_fields = [t for t in form_texts if 1 < len(t) <= 120 and t.strip() not in _SKIP]

    # 필드 상한: 1000개 (Railway 타임아웃 vs 매핑 품질 균형)
    MAX_FIELDS = 1000
    if len(filtered_fields) > MAX_FIELDS:
        print(f"[ai/map] 필드 {len(filtered_fields)}개 → {MAX_FIELDS}개로 제한")
        filtered_fields = filtered_fields[:MAX_FIELDS]

    # 배치 분할 호출 (150개씩)
    BATCH_SIZE = 150
    if is_gen:
        system_prompt = SYSTEM_PROMPT_GEN
        model_name = MODELS["generation"]
    else:
        system_prompt = SYSTEM_PROMPT_MAP
        model_name = MODELS["mapping"]

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name, system_instruction=system_prompt)
        gen_config = genai.GenerationConfig(
            temperature=0.3 if is_gen else 0.1,
            max_output_tokens=32768,
        )

        all_results = {}
        total_batches = (len(filtered_fields) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_idx in range(total_batches):
            start = batch_idx * BATCH_SIZE
            batch = filtered_fields[start:start + BATCH_SIZE]
            # 라벨 표시: AI가 라벨과 값을 구분할 수 있도록
            lines = []
            for t in batch:
                if t in label_set:
                    lines.append(f"- [라벨] {t}")
                else:
                    lines.append(f"- {t}")
            fields_text = "\n".join(lines)

            if is_gen:
                prompt = USER_PROMPT_GEN.format(fields=fields_text, content=combined_content)
            else:
                prompt = USER_PROMPT_MAP.format(fields=fields_text, content=combined_content)

            print(f"[ai/map] batch {batch_idx+1}/{total_batches}: {len(batch)} fields")

            # 배치 간 간격 + 429 재시도
            if batch_idx > 0:
                import time
                time.sleep(0.5)

            for attempt in range(2):
                try:
                    response = model.generate_content(prompt, generation_config=gen_config)
                    break
                except Exception as retry_err:
                    if "429" in str(retry_err) and attempt == 0:
                        import time
                        print(f"[ai/map] 429 rate limit, 3초 대기 후 재시도")
                        time.sleep(3)
                    else:
                        raise

            parsed = _parse_json_response(response.text)

            if parsed:
                # 빈 값 제거 + 비-문자열 안전 처리
                for k, v in parsed.items():
                    if not isinstance(k, str):
                        continue
                    k = k.strip()
                    if not k:
                        continue
                    if isinstance(v, (int, float)):
                        v = str(v)
                    if not isinstance(v, str):
                        continue
                    v = v.strip()
                    # 짧은 키 제거 (2자 이하 → 다중 section에서 중복 치환 위험)
                    if v and len(k) > 2 and k not in _SKIP and k not in label_set:
                        all_results[k] = v

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
            # 최장 매칭 우선 + 유사도 90% 이상만
            if not matched:
                best_t = None
                best_len = 0
                for t in form_texts:
                    if t.endswith(k) or k.endswith(t):
                        ratio = min(len(k), len(t)) / max(len(k), len(t))
                        if ratio > 0.9 and len(t) > best_len:
                            best_t = t
                            best_len = len(t)
                matched = best_t

            normalized[matched or k] = v

        # [Fix 3] 미매핑 필드 재시도: 1차에서 누락된 필드만 모아서 2차 호출
        mapped_keys = set(normalized.keys())
        unmapped = [f for f in filtered_fields if f not in mapped_keys]
        if unmapped and len(unmapped) > 5:
            retry_batches = (len(unmapped) + BATCH_SIZE - 1) // BATCH_SIZE
            print(f"[ai/map] 미매핑 {len(unmapped)}개 재시도 ({retry_batches} batches)")
            for rb in range(min(retry_batches, 3)):  # 최대 3배치만 재시도
                start = rb * BATCH_SIZE
                batch = unmapped[start:start + BATCH_SIZE]
                retry_lines = []
                for t in batch:
                    if t in label_set:
                        retry_lines.append(f"- [라벨] {t}")
                    else:
                        retry_lines.append(f"- {t}")
                fields_text = "\n".join(retry_lines)
                if is_gen:
                    prompt = USER_PROMPT_GEN.format(fields=fields_text, content=combined_content)
                else:
                    prompt = USER_PROMPT_MAP.format(fields=fields_text, content=combined_content)

                import time
                time.sleep(1)
                try:
                    response = model.generate_content(prompt, generation_config=gen_config)
                    retry_parsed = _parse_json_response(response.text)
                    if retry_parsed:
                        for k2, v2 in retry_parsed.items():
                            if not isinstance(k2, str) or not k2.strip():
                                continue
                            k2 = k2.strip()
                            if isinstance(v2, (int, float)):
                                v2 = str(v2)
                            if not isinstance(v2, str) or not v2.strip():
                                continue
                            # 라벨 필터 + 환각 키 정규화
                            if k2 in label_set:
                                continue
                            if k2 in field_set:
                                normalized[k2] = v2.strip()
                            else:
                                k2_esc = k2.replace("<", "&lt;").replace(">", "&gt;")
                                if k2_esc in field_set:
                                    normalized[k2_esc] = v2.strip()
                                else:
                                    normalized[k2] = v2.strip()
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
