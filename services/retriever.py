from __future__ import annotations

import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import numpy as np
from datasets import load_dataset
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import TokenTextSplitter

from config import settings
from utils.logger import logger


@dataclass
class _StoredChunk:
    page_content: str
    metadata: dict
    embedding: list[float]


class VectorStoreService:
    """Persistent lightweight vector index backed by pickle and numpy."""

    def __init__(self, persist_directory: Optional[str] = None) -> None:
        self.persist_directory = Path(persist_directory or settings.CHROMA_PERSIST_DIRECTORY)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.index_path = self.persist_directory / "vector_index.pkl"
        self.embedding_model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self._splitter = TokenTextSplitter(chunk_size=300, chunk_overlap=50)

    def _build_documents(self) -> List[Document]:
        dataset = load_dataset("openai/openai_humaneval", split="test")
        docs: List[Document] = []
        for item in dataset:
            content = (
                f"Task ID: {item['task_id']}\n"
                f"Prompt: {item['prompt']}\n"
                f"Canonical Solution: {item.get('canonical_solution', 'N/A')}\n"
                f"Tests: {item.get('test', 'N/A')}"
            )
            metadata = {
                "task_id": item.get("task_id", ""),
                "entry_point": item.get("entry_point", ""),
                "source": item.get("source", ""),
                "dataset": "openai/openai_humaneval",
            }
            docs.append(Document(page_content=content, metadata=metadata))
        return docs

    def _encode(self, texts: List[str]) -> np.ndarray:
        vectors = self.embedding_model.embed_documents(texts)
        return np.asarray(vectors, dtype=np.float32)

    def _load_index(self) -> List[_StoredChunk]:
        if not self.index_path.exists():
            return []
        with self.index_path.open("rb") as handle:
            data = pickle.load(handle)
        return data if isinstance(data, list) else []

    def _save_index(self, chunks: List[_StoredChunk]) -> None:
        with self.index_path.open("wb") as handle:
            pickle.dump(chunks, handle)

    def rebuild(self) -> None:
        documents = self._build_documents()
        chunks: List[Document] = []
        for document in documents:
            chunks.extend(self._splitter.split_documents([document]))

        embeddings = self._encode([chunk.page_content for chunk in chunks])
        stored = [
            _StoredChunk(
                page_content=chunk.page_content,
                metadata=chunk.metadata,
                embedding=embedding.tolist(),
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        self._save_index(stored)
        logger.info("Rebuilt vector index with %s chunks", len(stored))

    def get_retriever(self, top_k: int = 5):
        store = self._load_index()

        class _Retriever:
            def __init__(self, outer: "VectorStoreService", chunks: List[_StoredChunk], k: int) -> None:
                self.outer = outer
                self.chunks = chunks
                self.k = k

            def get_relevant_documents(self, query: str) -> List[Document]:
                if not self.chunks:
                    return []
                query_vector = self.outer._encode([query])[0]
                matrix = np.asarray([chunk.embedding for chunk in self.chunks], dtype=np.float32)
                norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query_vector)
                norms = np.where(norms == 0, 1e-9, norms)
                scores = matrix @ query_vector / norms
                ranked_indices = np.argsort(scores)[::-1][: self.k]
                return [
                    Document(page_content=self.chunks[index].page_content, metadata=self.chunks[index].metadata)
                    for index in ranked_indices
                ]

        return _Retriever(self, store, top_k)

    def add_document(self, question: str, solution: str, metadata: Optional[dict] = None) -> None:
        payload = f"Question: {question}\nSolution: {solution}"
        document = Document(
            page_content=payload,
            metadata={
                "source": "user",
                "timestamp": str(datetime.utcnow()),
                "task": "user_solution",
                **(metadata or {}),
            },
        )
        chunks = self._splitter.split_documents([document])
        embeddings = self._encode([chunk.page_content for chunk in chunks])
        store = self._load_index()
        store.extend(
            _StoredChunk(
                page_content=chunk.page_content,
                metadata=chunk.metadata,
                embedding=embedding.tolist(),
            )
            for chunk, embedding in zip(chunks, embeddings)
        )
        self._save_index(store)
