import structlog
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict

log = structlog.get_logger()


class RetrieverSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_API_KEY: str
    AZURE_SEARCH_INDEX: str = "sre-runbooks"
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_DEPLOYMENT_EMBED: str = "text-embedding-3-small"


class RunbookRetriever:
    def __init__(self) -> None:
        settings = RetrieverSettings()

        self._search_client = SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX,
            credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
        )

        self._openai_client = AzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version="2025-01-01-preview",
        )

        self._embed_deployment = settings.AZURE_OPENAI_DEPLOYMENT_EMBED

    def _embed(self, text: str) -> list[float]:
        response = self._openai_client.embeddings.create(
            input=text,
            model=self._embed_deployment,
        )
        return response.data[0].embedding

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        log.info("retrieval_started", query=query, top_k=top_k)

        query_vector = self._embed(query)

        # at 5 documents, approximate HNSW gives 100% recall — exhaustive scan adds latency with no benefit
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="embedding",
            exhaustive=False,
        )

        results = self._search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["id", "title", "content", "severity", "category"],
            top=top_k,
        )

        hits = []
        for r in results:
            hits.append({
                "id": r["id"],
                "title": r["title"],
                "content": r["content"],
                "severity": r["severity"],
                "score": r["@search.score"],
            })

        log.info(
            "retrieval_complete",
            hits=len(hits),
            top_score=hits[0]["score"] if hits else 0,
        )
        return hits