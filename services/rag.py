from __future__ import annotations

from typing import List, Optional, Tuple

from services.classifier import IntentClassifier
from services.code_runner import CodeRunner
from services.generator import CodeGenerator
from services.memory import ConversationMemory
from services.relevance import RelevanceChecker
from services.retriever import VectorStoreService
from utils.logger import logger


class AssistantService:
    """Coordinates intent classification, explain/generate, retrieval, execution, and memory."""

    def __init__(self) -> None:
        self.classifier = IntentClassifier()
        self.retriever = VectorStoreService()
        self.relevance_checker = RelevanceChecker()
        self.generator = CodeGenerator()
        self.runner = CodeRunner()
        self.memory = ConversationMemory()

    def handle_message(self, message: str) -> Tuple[str, str, List[dict], str]:
        """Process a user message and return intent, answer, retrieved docs, and execution result."""
        intent = self.classifier.classify(message)
        self.memory.add_user_message(message)

        if intent == "Explain":
            answer = self._explain_code(message)
            self.memory.add_ai_message(answer)
            return intent, answer, [], ""

        docs = self._retrieve_docs(message)
        retrieved_texts = [doc.page_content for doc in docs]
        relevant = self.relevance_checker.is_relevant(message, "\n\n".join(retrieved_texts))

        if not relevant:
            answer = "I couldn't find enough information. Please provide the correct solution. I will learn from it."
            self.memory.add_ai_message(answer)
            return intent, answer, [doc.metadata for doc in docs], ""

        generated_code = self.generator.generate(message, retrieved_texts)
        execution_status, execution_output = self.runner.run(generated_code)
        answer = f"{generated_code}\n\nExecution: {execution_status}\n{execution_output}".strip()
        self.memory.add_ai_message(answer)
        return intent, answer, [doc.metadata for doc in docs], f"{execution_status}\n{execution_output}"

    def _explain_code(self, message: str) -> str:
        prompt = (
            "Explain this code. Explain line by line. Mention Purpose, Logic, Complexity, and Possible improvements.\n\n"
            f"Code:\n{message}"
        )
        answer = self.generator.generate(prompt, [])
        return answer

    def _retrieve_docs(self, message: str) -> List[object]:
        try:
            retriever = self.retriever.get_retriever(top_k=5)
            return retriever.get_relevant_documents(message)
        except Exception as exc:  # pragma: no cover
            logger.warning("Document retrieval failed: %s", exc)
            return []

    def learn_solution(self, question: str, solution: str) -> str:
        """Store a user-provided solution in the vector DB for future retrieval."""
        self.retriever.add_document(question, solution)
        self.memory.add_user_message(f"Learned solution for: {question}")
        self.memory.add_ai_message("Solution stored for future retrieval.")
        return "Solution stored successfully."

    def rebuild_database(self) -> str:
        """Rebuild the Chroma vector database."""
        self.retriever.rebuild()
        return "Vector database rebuilt successfully."
