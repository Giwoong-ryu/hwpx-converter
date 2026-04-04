FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements-railway.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사 (COM 관련 제외)
COPY api/ api/
COPY core/ core/
COPY clone_form.py .
COPY ai_mapper.py .
COPY features.py .
COPY excel_filler.py .
COPY excel_parser.py .
COPY form_filler.py .
COPY hwpx_to_docx.py .
COPY docx_converter.py .
COPY template_analyzer.py .
COPY premade_templates.py .
COPY hwp_reader.py .
COPY hwpx_helpers.py .
COPY fix_namespaces.py .
COPY page_guard.py .
COPY verify_hwpx.py .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
