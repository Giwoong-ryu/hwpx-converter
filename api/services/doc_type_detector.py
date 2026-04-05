"""양식 필드 키워드 기반 문서 종류 추론 + 스마트 입력 필드 생성"""

DOC_TYPES = {
    "사업계획서": {
        "keywords": [
            "사업개요", "사업내용", "시장분석", "매출계획", "자금계획", "사업목적",
            "사업명", "사업배경", "경쟁분석", "마케팅전략", "수익모델", "투자계획",
            "사업비전", "사업전략", "성장전략", "목표시장", "사업규모",
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
        "keywords": [
            "성명", "생년월일", "학력", "경력사항", "자격증", "병역",
            "주소", "연락처", "지원분야", "희망연봉", "자기소개",
            "경력기술", "교육사항", "어학능력", "특기사항",
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
        "keywords": [
            "품명", "규격", "수량", "단가", "금액", "합계",
            "견적일", "납품일", "유효기간", "공급가액", "부가세",
            "견적번호", "거래처", "공급자",
        ],
        "smart_fields": [
            {"key": "vendor", "label": "발행 업체", "placeholder": "주식회사 웹스타"},
            {"key": "client", "label": "고객사", "placeholder": "ABC 무역"},
            {"key": "items", "label": "주요 항목/금액", "placeholder": "디자인 300만원, 개발 500만원, 유지보수 월 50만원"},
            {"key": "due_date", "label": "납품 예정일", "placeholder": "2026.05.30"},
        ],
    },
    "보고서": {
        "keywords": [
            "보고일", "작성자", "실적", "목표", "달성률",
            "보고서", "현황", "분석", "개선방안", "향후계획",
            "결론", "요약", "배경", "성과",
        ],
        "smart_fields": [
            {"key": "department", "label": "부서", "placeholder": "영업팀"},
            {"key": "author", "label": "작성자", "placeholder": "이팀장"},
            {"key": "period", "label": "보고 기간", "placeholder": "2026년 1분기"},
            {"key": "topic", "label": "보고 주제", "placeholder": "매출 실적 보고 (목표 5억, 달성 4.2억)"},
        ],
    },
    "계약서": {
        "keywords": [
            "계약금액", "계약기간", "갑", "을", "계약일",
            "계약내용", "해지", "위약금", "손해배상", "분쟁",
            "계약조건", "납부", "이행",
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
        "keywords": [
            "수신", "발신", "시행일", "시행", "경유",
            "제목", "참조", "관인", "발송일", "문서번호",
        ],
        "smart_fields": [
            {"key": "sender", "label": "발신 기관", "placeholder": "OO시 교육청"},
            {"key": "receiver", "label": "수신 기관", "placeholder": "관내 각 학교장"},
            {"key": "title", "label": "제목", "placeholder": "2026년 하계 방과후 프로그램 운영 안내"},
        ],
    },
    "회의록": {
        "keywords": [
            "참석자", "안건", "결정사항", "회의일", "회의명",
            "토의내용", "회의장소", "불참자", "차기회의",
        ],
        "smart_fields": [
            {"key": "meeting_name", "label": "회의명", "placeholder": "2026년 2분기 전략 회의"},
            {"key": "date", "label": "일시", "placeholder": "2026.04.05 14:00"},
            {"key": "attendees", "label": "참석자", "placeholder": "김팀장, 이대리, 박주임"},
            {"key": "agenda", "label": "주요 안건", "placeholder": "신규 서비스 런칭 일정 확정"},
        ],
    },
    "수료증": {
        "keywords": [
            "수료자", "교육과정", "수료일", "교육기간",
            "수료번호", "교육명", "이수시간", "발급일",
        ],
        "smart_fields": [
            {"key": "name", "label": "수료자 이름", "placeholder": "홍길동"},
            {"key": "course", "label": "교육과정명", "placeholder": "AI 활용 업무 자동화 과정"},
            {"key": "period", "label": "교육 기간", "placeholder": "2026.03.01 ~ 2026.03.30"},
        ],
    },
}


def detect_doc_type(fields: list[str]) -> dict:
    """양식 필드 목록에서 문서 종류를 추론한다.

    Returns:
        {"type": "사업계획서" | None,
         "confidence": 0.0~1.0,
         "smart_fields": [{key, label, placeholder}]}
    """
    if not fields:
        return {"type": None, "confidence": 0.0, "smart_fields": []}

    joined = " ".join(fields)
    best_type = None
    best_count = 0
    best_total = 0

    for doc_type, info in DOC_TYPES.items():
        count = sum(1 for kw in info["keywords"] if kw in joined)
        if count > best_count:
            best_count = count
            best_type = doc_type
            best_total = len(info["keywords"])

    if best_count < 2:
        return {"type": None, "confidence": 0.0, "smart_fields": []}

    confidence = min(best_count / max(best_total, 1), 1.0)
    return {
        "type": best_type,
        "confidence": round(confidence, 2),
        "smart_fields": DOC_TYPES[best_type]["smart_fields"],
    }
