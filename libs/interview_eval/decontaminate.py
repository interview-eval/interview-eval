import logging
from enum import Enum
from typing import Literal, Optional, TypedDict

from openai import OpenAI

DecontaminationType = Literal["unclarifying", "paraphrasing", "modifying"]


class DecontaminatedQuestion(TypedDict):
    question: str
    reference_answer: str
    original_question: str
    original_answer: str
    method: DecontaminationType


def decontaminate_unclarifying(
    question: str, reference_answer: str, client: OpenAI, model: str
) -> dict:
    prompt = """Remove some necessary information from this question while keeping it grammatically correct. 
    The removed info should be required to provide a complete answer. Return JSON with:
    - transformed_question: Question with key info removed
    - transformed_answer: Same as original reference answer"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Question: {question}\nReference Answer: {reference_answer}",
            },
        ],
        response_format={"type": "json_object"},
    )
    return eval(response.choices[0].message.content)


def decontaminate_paraphrasing(
    question: str, reference_answer: str, client: OpenAI, model: str
) -> dict:
    prompt = """Paraphrase this question and answer while preserving exact meaning. 
    Use different words and sentence structure. Return JSON with:
    - transformed_question: Paraphrased question 
    - transformed_answer: Paraphrased answer"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Question: {question}\nReference Answer: {reference_answer}",
            },
        ],
        response_format={"type": "json_object"},
    )
    return eval(response.choices[0].message.content)


def decontaminate_modifying(
    question: str, reference_answer: str, client: OpenAI, model: str
) -> dict:
    prompt = """Create a new but related question that can be answered using similar knowledge from the reference answer.
    Keep domain and difficulty similar. Return JSON with:
    - transformed_question: New related question
    - transformed_answer: Modified answer based on original reference"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": f"Question: {question}\nReference Answer: {reference_answer}",
            },
        ],
        response_format={"type": "json_object"},
    )
    return eval(response.choices[0].message.content)


def decontaminate_question(
    question: str,
    reference_answer: str,
    method: DecontaminationType = "modifying",
    client: Optional[OpenAI] = None,
    model: str = "gpt-4o",
    logger: Optional[logging.Logger] = None,
) -> DecontaminatedQuestion:
    client = client or OpenAI()
    logger = logger or logging.getLogger(__name__)

    decontamination_methods = {
        "unclarifying": decontaminate_unclarifying,
        "paraphrasing": decontaminate_paraphrasing,
        "modifying": decontaminate_modifying,
    }

    try:
        transformed = decontamination_methods[method](
            question, reference_answer, client, model
        )

        return DecontaminatedQuestion(
            question=transformed["transformed_question"],
            reference_answer=transformed["transformed_answer"],
            original_question=question,
            original_answer=reference_answer,
            method=method,
        )

    except Exception as e:
        logger.error(f"Decontamination failed: {str(e)}")
        return DecontaminatedQuestion(
            question=question,
            reference_answer=reference_answer,
            original_question=question,
            original_answer=reference_answer,
            method=method,
        )


def batch_decontaminate(
    questions: list[dict],
    method: DecontaminationType = "modifying",
    client: Optional[OpenAI] = None,
    model: str = "gpt-4o",
    logger: Optional[logging.Logger] = None,
) -> list[DecontaminatedQuestion]:
    client = client or OpenAI()
    logger = logger or logging.getLogger(__name__)

    return [
        decontaminate_question(
            q["question"],
            q["reference_answer"],
            method=method,
            client=client,
            model=model,
            logger=logger,
        )
        for q in questions
    ]
