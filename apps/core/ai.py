"""
Future AI service boundary.

AI is intentionally excluded from the MVP. This module exists so later
document processing, embeddings, RAG, and LLM-assisted reports can be
added without rewriting the evidence-first core.

The AI layer must never replace the Evidence model. Any future answer
must be able to cite: source, document, page, evidence, and claim.
"""


class AINotImplemented(NotImplementedError):
    """Raised because AI features are deferred."""


class AIService:
    """Interface for a future AI service. Not implemented."""

    def answer_question(self, question, *, project=None, evidence_queryset=None):
        raise AINotImplemented(
            "AI question answering is deferred. Use project evidence records."
        )

    def analyze_document(self, document):
        raise AINotImplemented("AI document analysis is deferred.")

    def retrieve_passages(self, query, *, project=None):
        raise AINotImplemented("Embeddings and RAG are deferred.")

    def assist_investigation(self, investigation):
        raise AINotImplemented("AI-assisted investigations are deferred.")

    def assist_report(self, report):
        raise AINotImplemented("AI-assisted reports are deferred.")
