"""양식 타입별 processor 모듈.

현재 지원:
- invoice_processor: 견적서/세금계산서/납품확인서 등 인보이스형
- form_classifier: 양식 타입 자동 분류

향후 확장:
- contract_processor: 근로계약서/사업제안서
- government_processor: 정부공문
- section_processor: 자기소개서 (현재 ai_mapper에 통합됨)
"""
from .form_classifier import classify_form
from .invoice_processor import InvoiceProcessor

__all__ = ["classify_form", "InvoiceProcessor"]
