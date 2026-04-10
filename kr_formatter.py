#!/usr/bin/env python3
"""
한국 서비스 포맷터 (k-skill)
HWPX 양식 채우기에서 한국 특화 자동 변환을 담당한다.
"""

import argparse
import json
import re
import sys
from datetime import datetime, date


_DIGITS = ["", "일", "이", "삼", "사", "오", "육", "칠", "팔", "구"]
_SMALL_UNITS = ["", "십", "백", "천"]
_BIG_UNITS = ["", "만", "억", "조", "경"]


class KrFormatter:
    """한국 서비스 포맷 변환기"""

    @staticmethod
    def _chunk_to_korean(n: int) -> str:
        if n == 0:
            return ""
        result = []
        s = str(n).zfill(4)
        for i, ch in enumerate(s):
            d = int(ch)
            if d == 0:
                continue
            unit_idx = 3 - i
            digit_str = _DIGITS[d] if not (d == 1 and unit_idx > 0) else ""
            result.append(digit_str + _SMALL_UNITS[unit_idx])
        return "".join(result)

    @classmethod
    def amount_korean(cls, amount: int) -> str:
        """숫자 -> 한글 금액 (예: 30000000 -> 삼천만)"""
        if amount == 0:
            return "영"
        if amount < 0:
            return "마이너스 " + cls.amount_korean(-amount)
        parts = []
        big_idx = 0
        remaining = amount
        while remaining > 0:
            chunk = remaining % 10000
            remaining //= 10000
            if chunk > 0:
                korean = cls._chunk_to_korean(chunk)
                unit = _BIG_UNITS[big_idx] if big_idx < len(_BIG_UNITS) else f"*10^{big_idx*4}"
                parts.append(korean + unit)
            big_idx += 1
        parts.reverse()
        return "".join(parts)

    @classmethod
    def amount_formal(cls, amount: int) -> str:
        """숫자 -> 일금 삼천만원정 (30,000,000)"""
        korean = cls.amount_korean(amount)
        comma = f"{amount:,}"
        return f"일금 {korean}원정 ({comma})"

    @staticmethod
    def amount_comma(amount: int) -> str:
        return f"{amount:,}"

    @staticmethod
    def amount_won(amount: int) -> str:
        return f"₩{amount:,}"

    @staticmethod
    def _parse_date(date_str: str) -> date:
        date_str = date_str.strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        if re.match(r"^\d{4}/\d{2}/\d{2}$", date_str):
            return datetime.strptime(date_str, "%Y/%m/%d").date()
        cleaned = re.sub(r"\s+", "", date_str).rstrip(".")
        if re.match(r"^\d{4}\.\d{1,2}\.\d{1,2}$", cleaned):
            parts = cleaned.split(".")
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        m = re.match(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", date_str)
        if m:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if re.match(r"^\d{8}$", date_str):
            return datetime.strptime(date_str, "%Y%m%d").date()
        raise ValueError(f"날짜 형식 인식 불가: {date_str}")

    @classmethod
    def date_kr(cls, date_str: str, style: str = "standard") -> str:
        """날짜 -> 한국식"""
        d = cls._parse_date(date_str)
        if style == "standard":
            return f"{d.year}년 {d.month}월 {d.day}일"
        elif style == "dot":
            return f"{d.year}. {d.month}. {d.day}."
        elif style == "short":
            return f"{d.year}.{d.month:02d}.{d.day:02d}"
        elif style == "month":
            return f"{d.year}년 {d.month}월"
        elif style == "formal":
            y = cls.amount_korean(d.year)
            mo = cls.amount_korean(d.month)
            da = cls.amount_korean(d.day)
            return f"{y}년 {mo}월 {da}일"
        return f"{d.year}년 {d.month}월 {d.day}일"

    @staticmethod
    def date_today(style: str = "standard") -> str:
        return KrFormatter.date_kr(date.today().isoformat(), style)

    @staticmethod
    def doc_number(dept: str, seq: int, year: int = None,
                   prefix: str = "제", suffix: str = "호") -> str:
        """문서번호 생성: 제2026-설계-0042호"""
        if year is None:
            year = date.today().year
        return f"{prefix}{year}-{dept}-{seq:04d}{suffix}"

    @staticmethod
    def validate_biz_number(biz_num: str) -> dict:
        """사업자등록번호 검증 (국세청 체크섬)"""
        digits_only = re.sub(r"[^0-9]", "", biz_num)
        if len(digits_only) != 10:
            return {"valid": False, "formatted": biz_num,
                    "error": f"10자리여야 함 (현재 {len(digits_only)}자리)"}
        weights = [1, 3, 7, 1, 3, 7, 1, 3, 5]
        total = 0
        for i in range(9):
            total += int(digits_only[i]) * weights[i]
        total += (int(digits_only[8]) * 5) // 10
        check = (10 - (total % 10)) % 10
        valid = check == int(digits_only[9])
        formatted = f"{digits_only[:3]}-{digits_only[3:5]}-{digits_only[5:]}"
        return {"valid": valid, "formatted": formatted,
                "error": None if valid else "체크섬 불일치"}

    @staticmethod
    def format_phone(phone: str) -> str:
        """전화번호 -> 하이픈 포맷"""
        digits = re.sub(r"[^0-9]", "", phone)
        if digits.startswith("02"):
            if len(digits) == 10:
                return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
            elif len(digits) == 9:
                return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
        elif len(digits) == 11:
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        return phone

    @staticmethod
    def _normalize_value(value) -> str:
        """엑셀/JSON에서 온 값을 안전한 문자열로 변환"""
        if value is None:
            return ""
        if isinstance(value, float):
            if value == int(value):
                return str(int(value))
            return str(value)
        return str(value).strip()

    @classmethod
    def auto_detect_and_format(cls, replacements: dict) -> dict:
        """치환 맵 값을 자동 감지하여 한국 포맷 적용 (clone_form 연동)

        Returns:
            dict: {"formatted": {포맷 적용된 치환 맵}, "log": [변환 로그]}
            formatted는 clone_form.clone(replacements=result["formatted"])으로 바로 전달 가능
        """
        AMOUNT_KEYS = re.compile(
            r"금액|합계|총액|단가|비용|가격|원가|수수료|급여|수당|세금|부가세|공급가",
            re.IGNORECASE)
        DATE_KEYS = re.compile(
            r"일자|날짜|일시|기간|발행일|작성일|시작일|종료일|마감|납기",
            re.IGNORECASE)
        PHONE_KEYS = re.compile(r"전화|연락|핸드폰|휴대|팩스|FAX", re.IGNORECASE)
        BIZ_KEYS = re.compile(r"사업자|등록번호", re.IGNORECASE)
        DATE_PATTERN = re.compile(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$")
        PURE_NUMBER = re.compile(r"^\d+$")
        result = {}
        applied = []
        for key, value in replacements.items():
            val_str = cls._normalize_value(value)
            if not val_str:
                result[key] = val_str
                continue
            new_val = val_str
            is_amount = AMOUNT_KEYS.search(key)
            is_date = DATE_KEYS.search(key)
            is_phone = PHONE_KEYS.search(key)
            is_biz = BIZ_KEYS.search(key)
            if is_amount and PURE_NUMBER.match(val_str):
                num = int(val_str)
                if num >= 1000:
                    new_val = f"{num:,}"
                    applied.append(f"[금액] {key}: {val_str} -> {new_val}")
            if is_date and DATE_PATTERN.match(val_str) and new_val == val_str:
                try:
                    new_val = cls.date_kr(val_str)
                    applied.append(f"[날짜] {key}: {val_str} -> {new_val}")
                except ValueError:
                    pass
            if is_phone and new_val == val_str:
                digits = re.sub(r"[^0-9]", "", val_str)
                if len(digits) in (10, 11):
                    new_val = cls.format_phone(val_str)
                    applied.append(f"[전화] {key}: {val_str} -> {new_val}")
            if is_biz and new_val == val_str:
                digits = re.sub(r"[^0-9]", "", val_str)
                if len(digits) == 10:
                    rb = cls.validate_biz_number(val_str)
                    new_val = rb["formatted"]
                    if not rb["valid"]:
                        applied.append(f"[경고] {key}: 사업자번호 체크섬 불일치")
                    else:
                        applied.append(f"[사업자] {key}: {val_str} -> {new_val}")
            result[key] = new_val
        return {"formatted": result, "log": applied}


def main():
    parser = argparse.ArgumentParser(description="한국 서비스 포맷터 (k-skill)")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("amount"); p.add_argument("value", type=int)
    p = sub.add_parser("amount-formal"); p.add_argument("value", type=int)
    p = sub.add_parser("date"); p.add_argument("value")
    p.add_argument("--style", default="standard", choices=["standard","dot","formal","short","month"])
    p = sub.add_parser("docnum"); p.add_argument("dept"); p.add_argument("seq", type=int)
    p.add_argument("--year", type=int, default=None)
    p = sub.add_parser("validate-biz"); p.add_argument("number")
    p = sub.add_parser("phone"); p.add_argument("number")
    p = sub.add_parser("auto-replace"); p.add_argument("input_json"); p.add_argument("output_json")
    args = parser.parse_args()
    fmt = KrFormatter()
    if args.command == "amount": print(fmt.amount_korean(args.value))
    elif args.command == "amount-formal": print(fmt.amount_formal(args.value))
    elif args.command == "date": print(fmt.date_kr(args.value, args.style))
    elif args.command == "docnum": print(fmt.doc_number(args.dept, args.seq, args.year))
    elif args.command == "validate-biz":
        print(json.dumps(fmt.validate_biz_number(args.number), ensure_ascii=False, indent=2))
    elif args.command == "phone": print(fmt.format_phone(args.number))
    elif args.command == "auto-replace":
        with open(args.input_json, "r", encoding="utf-8") as f: data = json.load(f)
        output = fmt.auto_detect_and_format(data)
        result = output["formatted"]
        log = output["log"]
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        for entry in log: print(f"  {entry}")
    else: parser.print_help()


if __name__ == "__main__":
    main()