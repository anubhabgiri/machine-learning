from langgraph.graph import StateGraph
from pydantic import BaseModel
from typing import List, Optional, Literal, Dict
import torch

from retriever import Retriever
from models import qa_pipeline, synthesize, classifier
from web_search import web_search

LABELS = ["extractive", "compositional", "missing_info"]

# ---------- State ----------
class QAState(BaseModel):
    question: str
    query_type: Optional[Literal["extractive", "compositional", "missing_info"]] = None
    retrieved_chunks: List[str] = []
    qa_answers: List[dict] = []
    final_answer: Optional[str] = None
    confidence: Optional[float] = None
    classifier_scores: Optional[Dict[str, float]] = None
    use_web: bool = False


# ---------- Nodes ----------

def classify_question(state: QAState) -> QAState:
    """
    Classify the question into one of the following categories:
    - extractive: The answer is a short factual span explicitly stated in the paper.
    - compositional: The answer requires summarizing, explaining, or combining multiple parts of the paper.
    - missing_info: The answer is not contained in the paper and requires external sources.

    Args: state (QAState): The state of the query.
    Returns: QAState: The updated state of the query.
    """
    hypotheses = {
        "extractive": "The answer is a short factual span explicitly stated in the paper.",
        "compositional": "The answer requires summarizing, explaining, or combining multiple parts of the paper.",
        "missing_info": "The answer is not contained in the paper and requires external sources."
    }

    result = classifier(
        state.question,
        candidate_labels=list(hypotheses.values()),
        multi_label=True
    )

    hypotheses_inv = {v: k for k, v in hypotheses.items()}

    scores = {
        hypotheses_inv[label]: score
        for label, score in zip(result["labels"], result["scores"])
    }

    # Pick highest-scoring label
    best_label = max(scores, key=scores.get)
    best_score = scores[best_label]

    # Safety threshold
    if best_score < 0.5:
        state.query_type = "compositional"
    else:
        state.query_type = best_label

    state.classifier_scores = scores
    print("Identified label for the question:", state.query_type)
    return state


def retrieve_chunks(state: QAState) -> QAState:
    """
    Retrieve chunks from the retriever.

    Args: state (QAState): The state of the query.
    Returns: QAState: The updated state of the query.
    """
    retriever = app.config["retriever"]
    state.retrieved_chunks = retriever.retrieve(state.question)
    print("Retrieved chunks:", state.retrieved_chunks)
    if not state.retrieved_chunks:
        state.use_web = True
    return state


def extractive_qa(state: QAState) -> QAState:
    """
    Perform extractive QA on the retrieved chunks.

    Args: state (QAState): The state of the query.
    Returns: QAState: The updated state of the query.
    """
    answers = []
    for chunk in state.retrieved_chunks:
        out = qa_pipeline({
            "question": state.question,
            "context": chunk
        })
        if out["score"] > 0.15:
            answers.append(out)

    if answers:
        best = max(answers, key=lambda x: x["score"])
        state.final_answer = best["answer"]
        state.confidence = best["score"]
    else:
        state.use_web = True
    
    # torch.cuda.empty_cache() # empty cuda cache

    return state


def synthesize_answer(state: QAState):
    context = "\n\n".join(state.retrieved_chunks)
    prompt = f"""
    You are answering a scientific question.
    ONLY use the context below.
    If the answer is not present, say "Not found".

    Context:
    {context}

    Question:
    {state.question}
    """
    state.final_answer = synthesize(prompt)
    state.confidence = 0.5
    return state


def web_fallback(state: QAState):
    state.retrieved_chunks = web_search(state.question)
    return state


# ---------- Build Graph ----------

graph = StateGraph(QAState)

graph.add_node("classify", classify_question)
graph.add_node("retrieve", retrieve_chunks)
graph.add_node("qa", extractive_qa)
graph.add_node("synthesize", synthesize_answer)
graph.add_node("web", web_fallback)

graph.set_entry_point("classify")
graph.add_edge("classify", "retrieve")

graph.add_conditional_edges(
    "retrieve",
    lambda s: s.query_type,
    {
        "extractive": "qa",
        "compositional": "synthesize",
        "missing_info": "web"
    }
)

graph.add_conditional_edges(
    "qa",
    lambda s: s.use_web,
    {
        True: "web",
        False: "__end__"
    }
)

graph.add_edge("web", "synthesize")

app = graph.compile()
