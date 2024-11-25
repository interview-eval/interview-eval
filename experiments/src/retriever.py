import os
from typing import Dict, List, Union

import pandas as pd
from datasets import load_dataset
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever


class Retriever:
    def __init__(self, task_name: str) -> None:
        if task_name not in ["depth_qa", "math"]:
            raise ValueError(
                "Currently only task name 'depth_qa' and math are supported."
            )
        self.task_name = task_name
        if task_name == "depth_qa":

            self.data_path = f"./data/{task_name}_keyword.csv"

            self.df = pd.read_csv(self.data_path)
            self.df["content"] = (
                self.df["question"] + " " + self.df["answer"] + " " + self.df["keyword"]
            )
            self.embedding = self.get_embedding_model(model_name="thenlper/gte-base")
            self.retriever = self.get_chroma_db(
                texts=self.df["content"].tolist(), embedding=self.embedding
            )
        elif task_name == "math":
            ds = load_dataset("lighteval/MATH", "geometry")
            import pdb

            pdb.set_trace()
            self.df = pd.DataFrame(ds["test"])
            self.embedding = self.get_embedding_model(model_name="thenlper/gte-base")
            self.retriever = self.get_chroma_db(
                texts=self.df["solution"].tolist(), embedding=self.embedding
            )

    @staticmethod
    def get_embedding_model(
        model_name: str, cache_folder: str = None
    ) -> HuggingFaceEmbeddings:
        """Initialize the Huggingface Embedding model."""

        model_kwargs = {"device": "cuda:0", "model_kwargs": {"torch_dtype": "float16"}}

        embed_model = HuggingFaceEmbeddings(
            model_name=model_name, model_kwargs=model_kwargs
        )
        return embed_model

    def get_chroma_db(self, texts, embedding, db_path: Union[str, None] = None):
        if db_path is None:
            model_name = embedding.model_name.split("/")[-1]
            db_path = f"db/{self.task_name}/{model_name}"

        if not os.path.exists(db_path):
            vectorstore = Chroma.from_texts(
                texts,
                embedding,
                persist_directory=db_path,
            )
        else:
            vectorstore = Chroma(
                persist_directory=db_path,
                embedding_function=embedding,
            )

        return vectorstore

    def search(self, content: str, top_k: int = 5) -> List[Dict[str, str]]:
        results = self.retriever.similarity_search_with_score(content, k=top_k)

        similar_questions = []
        if self.task_name == "depth_qa":
            for doc, score in results:
                # Find the matching row in the DataFrame
                matching_row = self.df[self.df["content"] == doc.page_content].iloc[0]

                # Create a dictionary with the question information
                question_info = {
                    "qid": matching_row["qid"],
                    "question": matching_row["question"],
                    "answer": matching_row["answer"],
                    "keyword": matching_row["keyword"],
                }
                similar_questions.append(question_info)
        elif self.task_name == "math":
            for doc, score in results:
                # Find the matching row in the DataFrame
                matching_row = self.df[self.df["solution"] == doc.page_content].iloc[0]

                # Create a dictionary with the question information
                question_info = {
                    "problem": matching_row["problem"],
                    "level": matching_row["level"],
                    "type": matching_row["type"],
                    "solution": matching_row["solution"],
                }
                similar_questions.append(question_info)
        return similar_questions


if __name__ == "__main__":
    retriever = Retriever("depth_qa")

    similar_questions = retriever.search("What is the depth of the ocean?", top_k=10)

    for i, question in enumerate(similar_questions, 1):
        print(f"Similar Question {i}:")
        print(f"Question: {question['question']}")
        print(f"Answer: {question['answer']}")
        print(f"Keyword: {question['keyword']}")
        print()
