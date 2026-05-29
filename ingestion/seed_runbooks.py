import hashlib
import re
from pathlib import Path

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ingestion.config import settings

RUNBOOKS_DIR = Path(__file__).parent.parent / "runbooks"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_embedding(client: AzureOpenAI, text: str) -> list[float]:
    response = client.embeddings.create(
        input=text,
        model=settings.AZURE_OPENAI_DEPLOYMENT_EMBED,
    )
    return response.data[0].embedding


def parse_severity(content: str) -> str:
    match = re.search(r"## Severity\s*\n(P[123])", content)
    return match.group(1) if match else "P2"


def parse_title(content: str) -> str:
    match = re.match(r"^#\s+(.+)", content.strip())
    return match.group(1).strip() if match else "Unknown"


def build_documents() -> list[dict]:
    docs = []
    for path in sorted(RUNBOOKS_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        docs.append(
            {
                "path": path,
                "title": parse_title(content),
                "content": content,
                "severity": parse_severity(content),
                "category": "kubernetes",
            }
        )
    return docs


def seed() -> None:
    openai_client = AzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version="2024-02-01",
    )
    search_client = SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=settings.AZURE_SEARCH_INDEX,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
    )

    raw_docs = build_documents()
    upload_batch = []

    for doc in raw_docs:
        # embed title + content so retrieval matches on both incident name and procedure text
        embed_input = f"{doc['title']}\n\n{doc['content']}"
        embedding = get_embedding(openai_client, embed_input)

        doc_id = hashlib.md5(doc["path"].name.encode()).hexdigest()
        upload_batch.append(
            {
                "id": doc_id,
                "title": doc["title"],
                "content": doc["content"],
                "severity": doc["severity"],
                "category": doc["category"],
                "embedding": embedding,
            }
        )
        print(f"  embedded: {doc['path'].name} [{doc['severity']}]")

    results = search_client.upload_documents(documents=upload_batch)
    succeeded = sum(1 for r in results if r.succeeded)
    print(f"\nuploaded {succeeded}/{len(upload_batch)} runbooks → {settings.AZURE_SEARCH_INDEX}")


if __name__ == "__main__":
    seed()