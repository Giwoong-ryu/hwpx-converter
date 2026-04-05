"""양식 필드 키워드 기반 문서 종류 추론 + 스마트 입력 필드 생성

개선 v2: 문서명 직접 매칭 + 가중치 시스템 + 필드 단위 매칭
"""

# 키워드 가중치: (키워드, 점수)
# 3 = 해당 문서에서만 나타나는 고유 키워드
# 2 = 해당 문서에서 주로 나타나는 특화 키워드
# 1 = 여러 문서에서 나타날 수 있는 일반 키워드
DOC_TYPES = {
    "사업계획서": {
        "doc_names": ["사업계획서", "사업계획", "창업계획서", "창업사업계획"],
        "keywords": [
            ("창업아이템", 3), ("총사업비", 3), ("사업화자금", 3), ("사업화", 3),
            ("창업기업", 3), ("주관기관", 3), ("초기창업", 3), ("창업프로그램", 3),
            ("사업개요", 2), ("시장분석", 2), ("매출계획", 2), ("자금계획", 2),
            ("사업목적", 2), ("수익모델", 2), ("성장전략", 2), ("경쟁분석", 2),
            ("개업연월일", 2), ("사업자등록", 2), ("산출물", 2), ("사업비", 2),
            ("사업명", 1), ("사업내용", 1), ("사업배경", 1), ("투자계획", 1),
            ("사업규모", 1), ("목표시장", 1), ("마케팅전략", 1), ("지원대상", 1),
        ],
        "smart_fields": [
            {"key": "company", "label": "회사명", "placeholder": "주식회사 OO"},
            {"key": "industry", "label": "업종/사업분야", "placeholder": "AI 문서 자동화 SaaS"},
            {"key": "ceo", "label": "대표자", "placeholder": "홍길동"},
            {"key": "established", "label": "설립일", "placeholder": "2026.01.15"},
            {"key": "summary", "label": "사업 한줄 요약", "placeholder": "한글 문서를 AI로 자동 작성하는 서비스"},
        ],
    },
    "이력서": {
        "doc_names": ["이력서", "자기소개서", "입사지원서"],
        "keywords": [
            ("생년월일", 3), ("경력사항", 3), ("자격증", 3), ("병역", 3),
            ("희망연봉", 3), ("자기소개", 3), ("어학능력", 3), ("특기사항", 3),
            ("지원분야", 2), ("경력기술", 2), ("교육사항", 2),
            ("성명", 1), ("학력", 1), ("연락처", 1),
        ],
        "smart_fields": [
            {"key": "name", "label": "이름", "placeholder": "홍길동"},
            {"key": "birth", "label": "생년월일", "placeholder": "1995.03.20"},
            {"key": "education", "label": "최종 학력", "placeholder": "서울대 컴퓨터공학과 졸업"},
            {"key": "career", "label": "주요 경력", "placeholder": "네이버 3년 (백엔드), 카카오 2년 (플랫폼)"},
            {"key": "position", "label": "지원 직종", "placeholder": "백엔드 개발자"},
        ],
    },
    "견적서": {
        "doc_names": ["견적서", "견적내역서", "가격견적서"],
        "keywords": [
            ("견적일", 3), ("납품일", 3), ("유효기간", 3), ("견적번호", 3),
            ("공급가액", 3), ("부가세", 2),
            ("품명", 2), ("규격", 2), ("단가", 2), ("수량", 2),
            ("거래처", 1), ("공급자", 1), ("금액", 1), ("합계", 1),
        ],
        "smart_fields": [
            {"key": "vendor", "label": "발행 업체", "placeholder": "주식회사 웹스타"},
            {"key": "client", "label": "고객사", "placeholder": "ABC 무역"},
            {"key": "items", "label": "주요 항목/금액", "placeholder": "디자인 300만원, 개발 500만원"},
            {"key": "due_date", "label": "납품 예정일", "placeholder": "2026.05.30"},
        ],
    },
    "보고서": {
        "doc_names": ["보고서", "실적보고서", "업무보고서", "월간보고", "분기보고"],
        "keywords": [
            ("달성률", 3), ("보고일", 3), ("전월대비", 3), ("월간보고", 3),
            ("개선방안", 3), ("향후계획", 3), ("전기대비", 3),
            ("보고기간", 2), ("보고대상", 2),
        ],
        "smart_fields": [
            {"key": "department", "label": "부서", "placeholder": "영업팀"},
            {"key": "author", "label": "작성자", "placeholder": "이팀장"},
            {"key": "period", "label": "보고 기간", "placeholder": "2026년 1분기"},
            {"key": "topic", "label": "보고 주제", "placeholder": "매출 실적 보고 (목표 5억, 달성 4.2억)"},
        ],
    },
    "계약서": {
        "doc_names": ["계약서", "용역계약서", "근로계약서", "매매계약서", "임대차계약서"],
        "keywords": [
            ("계약금액", 3), ("계약기간", 3), ("계약일", 3), ("위약금", 3),
            ("손해배상", 3), ("해지", 3), ("계약조건", 3), ("계약당사자", 3),
            ("계약내용", 2), ("분쟁", 2), ("갑과을", 2),
        ],
        "smart_fields": [
            {"key": "party_a", "label": "갑 (발주사)", "placeholder": "주식회사 ABC"},
            {"key": "party_b", "label": "을 (수주사)", "placeholder": "주식회사 개발나라"},
            {"key": "amount", "label": "계약 금액", "placeholder": "3,000만원"},
            {"key": "period", "label": "계약 기간", "placeholder": "2026.04 ~ 2026.09 (6개월)"},
            {"key": "scope", "label": "계약 내용", "placeholder": "웹 애플리케이션 개발 용역"},
        ],
    },
    "공문": {
        "doc_names": ["공문", "공문서", "협조문"],
        "keywords": [
            ("수신", 3), ("발신", 3), ("시행일", 3), ("경유", 3),
            ("관인", 3), ("문서번호", 3), ("발송일", 3),
            ("참조", 1),
        ],
        "smart_fields": [
            {"key": "sender", "label": "발신 기관", "placeholder": "OO시 교육청"},
            {"key": "receiver", "label": "수신 기관", "placeholder": "관내 각 학교장"},
            {"key": "title", "label": "제목", "placeholder": "2026년 하계 방과후 프로그램 운영 안내"},
        ],
    },
    "회의록": {
        "doc_names": ["회의록", "회의결과", "회의보고"],
        "keywords": [
            ("참석자", 3), ("안건", 3), ("결정사항", 3), ("회의일", 3),
            ("회의명", 3), ("토의내용", 3), ("불참자", 3), ("차기회의", 3),
            ("회의장소", 2),
        ],
        "smart_fields": [
            {"key": "meeting_name", "label": "회의명", "placeholder": "2026년 2분기 전략 회의"},
            {"key": "date", "label": "일시", "placeholder": "2026.04.05 14:00"},
            {"key": "attendees", "label": "참석자", "placeholder": "김팀장, 이대리, 박주임"},
            {"key": "agenda", "label": "주요 안건", "placeholder": "신규 서비스 런칭 일정 확정"},
        ],
    },
    "수료증": {
        "doc_names": ["수료증", "수료확인서", "이수증", "이수확인서"],
        "keywords": [
            ("수료자", 3), ("교육과정", 3), ("수료일", 3), ("수료번호", 3),
            ("이수시간", 3), ("교육기간", 2), ("교육명", 2), ("발급일", 1),
        ],
        "smart_fields": [
            {"key": "name", "label": "수료자 이름", "placeholder": "홍길동"},
            {"key": "course", "label": "교육과정명", "placeholder": "AI 활용 업무 자동화 과정"},
            {"key": "period", "label": "교육 기간", "placeholder": "2026.03.01 ~ 2026.03.30"},
        ],
    },
}


def _match_score(fields: list[str], keywords: list[tuple[str, int]]) -> int:
    """필드 목록에서 키워드 가중치 점수를 계산한다.

    짧은 키워드(3자 이하): 필드 전체와 정확 일치만
    긴 키워드(4자 이상): 필드 내 부분 매칭 허용
    """
    score = 0
    matched = set()
    for field in fields:
        fc = field.strip()
        if not fc:
            continue
        for kw, weight in keywords:
            if kw in matched:
                continue  # 같은 키워드 중복 카운트 방지
            if len(kw) <= 3:
                if fc == kw:
                    score += weight
                    matched.add(kw)
            else:
                if kw in fc:
                    score += weight
                    matched.add(kw)
    return score


def detect_doc_type(fields: list[str]) -> dict:
    """양식 필드 목록에서 문서 종류를 추론한다.

    우선순위:
    1. 문서명 직접 매칭 (fields에 "사업계획서" 등 포함)
    2. 가중치 키워드 점수 비교

    Returns:
        {"type": "사업계획서" | None,
         "confidence": 0.0~1.0,
         "smart_fields": [{key, label, placeholder}]}
    """
    if not fields:
        return {"type": None, "confidence": 0.0, "smart_fields": []}

    # 1단계: 문서명 직접 매칭 (최우선)
    for field in fields:
        fc = field.strip()
        for doc_type, info in DOC_TYPES.items():
            for name in info.get("doc_names", []):
                if name in fc:
                    return {
                        "type": doc_type,
                        "confidence": 1.0,
                        "smart_fields": info["smart_fields"],
                    }

    # 2단계: 가중치 키워드 점수 비교
    best_type = None
    best_score = 0
    best_max_possible = 1

    for doc_type, info in DOC_TYPES.items():
        score = _match_score(fields, info["keywords"])
        max_possible = sum(w for _, w in info["keywords"])
        if score > best_score:
            best_score = score
            best_type = doc_type
            best_max_possible = max_possible

    # 최소 5점 이상이어야 유효
    if best_score < 5:
        return {"type": None, "confidence": 0.0, "smart_fields": []}

    confidence = min(best_score / max(best_max_possible, 1), 1.0)
    return {
        "type": best_type,
        "confidence": round(confidence, 2),
        "smart_fields": DOC_TYPES[best_type]["smart_fields"],
    }
