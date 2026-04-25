"""이력서/자기소개서 전용 processor.

대상 양식:
- 한국형 이력서 (인적사항/학력/자격증/기술/경력)
- 자기소개서 (지원동기/성격/직무적합성/포부)
- 통합 양식 (이력서 + 자소서 동시 포함)

특징:
- 한국 이력서 5섹션 표준 (rules/resume-design-rules.md 자산화 기반)
- 인적사항: 표 그리드 (이름/전화/이메일/주소)
- 학력/경력: 시간 역순 반복 행 (기간/학교/학과/위치)
- 자격증·면허: 반복 행
- 보유 기술·도구: 카테고리별 그룹
- 자소서 섹션: 긴 서술 텍스트

원칙:
- 한국 표준 라벨 사전 → AI extra_labels 전달
- 회사명/직무명은 자소서 섹션에만 (이력서 부분에는 추측 정보 금지)
- 학력/경력 시간 역순 (현재 → 과거)
"""
from __future__ import annotations
import re


# ─────────────────────────────────────────────────────────
# 라벨 사전 (한국 이력서 표준 5섹션)
# ─────────────────────────────────────────────────────────

# 1. 인적사항
_PERSONAL_LABELS = {
    "이름", "성명", "성  명",
    "한글이름", "한글 이름", "한글", "국문명",
    "영문이름", "영문 이름", "영문명", "영문",
    "생년월일", "생  년  월  일", "주민등록번호",
    "전화번호", "전화", "휴대전화", "핸드폰", "연락처", "연 락 처",
    "이메일", "이 메 일", "E-mail", "Email", "메일",
    "주소", "주    소", "거주지", "현 주소",
    "포트폴리오", "Portfolio", "URL", "홈페이지", "블로그", "GitHub",
    "성별", "병역", "보훈", "장애",
    "사진",
}

# 2. 학력
_EDUCATION_LABELS = {
    "학력", "학력사항", "학 력 사 항",
    "학교명", "학  교  명", "교명",
    "학과", "전공", "학과/전공", "전공/학과",
    "재학기간", "재학 기간", "기간",
    "졸업여부", "졸업/수료", "재학상태", "졸업구분",
    "학위", "학점", "성적", "GPA",
    "고등학교", "대학교", "대학원", "박사",
}

# 3. 자격증·면허
_CERT_LABELS = {
    "자격증", "자  격  증", "자격증·면허", "자격증/면허",
    "면허", "자격명", "자격명·면허",
    "발급기관", "발급일", "취득일", "발급",
    "어학", "어학시험", "어학성적",
    "TOEIC", "TOEFL", "OPIc", "TEPS", "JLPT", "HSK",
    "공인", "민간",
}

# 4. 보유 기술·도구
_SKILL_LABELS = {
    "기술", "보유기술", "보유 기술", "보유 기술·도구",
    "도구", "툴", "Tools",
    "프로그램", "프로그래밍", "언어",
    "Skills", "Stack",
    "자격", "능력",
    "OA", "한컴", "MS Office", "엑셀", "워드", "파워포인트",
    "디자인", "포토샵", "일러스트레이터",
}

# 5. 경력 사항
_CAREER_LABELS = {
    "경력", "경력사항", "경 력 사 항", "경력 사항",
    "회사", "회사명", "회 사 명", "근무처", "근  무  처",
    "직무", "직위", "직책", "담당업무", "담당 업무",
    "근무기간", "근무 기간", "재직기간", "재직 기간",
    "역할", "업무내용", "업무 내용",
    "프로젝트", "프 로 젝 트",
    "성과", "주요 성과", "주요성과",
    "퇴사사유", "퇴사 사유", "퇴직사유",
    "인턴", "정규직", "계약직", "파트타임",
}

# 6. 자기소개서
_SELF_INTRO_LABELS = {
    "자기소개서", "자  기  소  개  서",
    "지원동기", "지 원 동 기",
    "성격", "성격의 장단점", "성격의 장점", "성격의 단점", "장점", "단점",
    "성장과정", "성 장 과 정",
    "직무적합성", "직무 적합성", "직무적합도",
    "입사후포부", "입사 후 포부", "포부",
    "특기사항", "특 기 사 항",
    "경험", "주요경험", "프로젝트경험",
    "지원분야", "지원 분야", "지원직무", "지원 직무",
    "회사명", "지원회사",  # 자소서에서만 회사 명시
}

# 7. 보조 (원래 학교/회사 위치, 기간 등)
_AUXILIARY_LABELS = {
    "위치", "지역", "소재지", "근무지",
    "시작일", "종료일", "퇴사일", "입사일",
    "기간", "년월", "년월일",
    "구분",
}

RESUME_LABELS = (
    _PERSONAL_LABELS | _EDUCATION_LABELS | _CERT_LABELS
    | _SKILL_LABELS | _CAREER_LABELS | _SELF_INTRO_LABELS
    | _AUXILIARY_LABELS
)


def _normalize(text: str) -> str:
    """공백 제거 + 소문자화."""
    return re.sub(r"\s+", "", text).lower()


_NORMALIZED_LABELS = {_normalize(lbl) for lbl in RESUME_LABELS}


def is_resume_label(text: str) -> bool:
    """텍스트가 이력서/자소서 라벨인지 판정."""
    if not text:
        return False
    t = text.strip()
    if len(t) > 30:
        return False
    norm = _normalize(t)
    if not norm:
        return False
    if norm in _NORMALIZED_LABELS:
        return True
    # 콜론 형태 ("학력 :", "경력 :")
    base_match = re.match(r"^([가-힣A-Za-z\s/·∙()]+?)\s*[:：]", t)
    if base_match:
        base = _normalize(base_match.group(1))
        if base in _NORMALIZED_LABELS:
            return True
    return False


# ─────────────────────────────────────────────────────────
# ResumeProcessor
# ─────────────────────────────────────────────────────────

class ResumeProcessor:
    """이력서/자기소개서 전용 processor.

    한국 이력서가 표 기반인 경우가 많아 build_header_slot_map 폴백 활용.
    핵심 가치는 RESUME_LABELS를 AI extra_labels로 전달하여 라벨 보호 + 매핑 정확도 향상.
    """

    def __init__(self, hwpx_path: str, structured: dict):
        self.hwpx_path = hwpx_path
        self.structured = structured

    def build_slot_map(self) -> dict:
        """빈 dict 반환 (form.py가 build_header_slot_map으로 폴백).

        이력서는 표 기반 헤더가 많아 기존 build_header_slot_map이 충분히 작동.
        ResumeProcessor의 주 역할은 RESUME_LABELS를 ai_mapper에 전달하는 것.
        """
        return {}
