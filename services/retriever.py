from __future__ import annotations

import os
from typing import List, Optional

import chromadb
from langchain_core.documents import Document
from langchain_text_splitters import TokenTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from datasets import load_dataset

from config import settings
from utils.logger import logger


class VectorStoreService:
    """Ingests the dataset, chunks it, and builds a persistent Chroma vector DB."""

    def __init__(self, persist_directory: Optional[str] = None) -> None:
        self.persist_directory = persist_directory or str(settings.CHROMA_PERSIST_DIRECTORY)
        self.embedding_model = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection_name = settings.CHROMA_COLLECTION_NAME
        self._splitter = TokenTextSplitter(chunk_size=300, chunk_overlap=50)

    def _build_documents(self) -> List[Document]:
        dataset = load_dataset("openai/openai_humaneval", split="test")
        docs: List[Document] = []
        for item in dataset:
            content = f"Task ID: {item['task_id']}\nPrompt: {item['prompt']}\nCanonical Solution: {item.get('canonical_solution', 'N/A')}\nTests: {item.get('test', 'N/A')}"
            metadata = {
                "task_id": item.get("task_id", ""),
                "entry_point": item.get("entry_point", ""),
                "source": item.get("source", ""),
                "dataset": "openai/openai_humaneval",
            }
            docs.append(Document(page_content=content, metadata=metadata))
        return docs

    def rebuild(self) -> None:
        """Delete any existing collection and recreate the vector store."""
        try:
            self.client.delete_collection(name=self.collection_name)
        except Exception:
            pass
        documents = self._build_documents()
        chunks = []
        for document in documents:
            chunks.extend(self._splitter.split_documents([document]))

        Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_model,
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
        )
        logger.info("Rebuilt Chroma DB with %s chunks", len(chunks))

    def get_retriever(self, top_k: int = 5):
        """Return a similarity-search retriever."""
        vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory,
        )
        return vector_store.as_retriever(search_kwargs={"k": top_k})

    def add_document(self, question: str, solution: str, metadata: Optional[dict] = None) -> None:
        """Add a new learned document to the vector store."""
        payload = f"Question: {question}\nSolution: {solution}"
        document = Document(page_content=payload, metadata={
            "source": "user",
            "timestamp": str(__import__("datetime").datetime.utcnow()),
            "task": "user_solution",
            **(metadata or {}),
        })
        chunks = self._splitter.split_documents([document])
        vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory,
        )
        vector_store.add_documents(chunks)
