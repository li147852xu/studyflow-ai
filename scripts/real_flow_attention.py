import os
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import load_dotenv

from infra.models import init_db
from service.chat_service import ChatConfigError, chat
from service.document_service import save_document_bytes
from service.workspace_service import create_workspace


PDF_URL = "https://arxiv.org/pdf/1706.03762.pdf"


def download_pdf() -> bytes:
    response = requests.get(PDF_URL, timeout=60)
    response.raise_for_status()
    return response.content


def run_real_flow() -> str:
    load_dotenv()
    init_db()
    workspace_id = create_workspace("realflow-attention")
    pdf_bytes = download_pdf()
    save_document_bytes(workspace_id, "attention_is_all_you_need.pdf", pdf_bytes)

    prompt = (
        "Summarize the paper 'Attention Is All You Need' in 5 bullet points, "
        "then list 3 key innovations."
    )
    response = chat(
        prompt=prompt,
        base_url=os.getenv("STUDYFLOW_LLM_BASE_URL"),
        api_key=os.getenv("STUDYFLOW_LLM_API_KEY"),
        model=os.getenv("STUDYFLOW_LLM_MODEL"),
    )
    return response


def main() -> int:
    try:
        result = run_real_flow()
        print("Real flow result:")
        print(result)
        return 0
    except ChatConfigError as exc:
        print(f"SKIP: {exc}")
        return 0
    except requests.RequestException as exc:
        print(f"FAILED: PDF download error: {exc}")
        return 1
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
