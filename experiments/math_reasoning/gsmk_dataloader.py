import json
from collections import defaultdict
from typing import Dict, List, Set

import pandas as pd
from datasets import load_dataset


class HFMATHLoader:
    def __init__(self, hf_repo: str = "openai/GSM8K", split: str = "train", category: str = "main"):
        self.hf_repo = hf_repo
        self.split = split
        self.category = category

    def add_messages(self, df):
        message_format = [
            {"content": df["initial_question"], "role": "user"},
            {"content": df["answer"], "role": "assistant"},
        ]
        return message_format

    def load_data(self, except_questions: bool = False, remove_unused_columns: bool = True):
        print(f"Loading data from {self.hf_repo}...")
        self.ds = pd.DataFrame(load_dataset(self.hf_repo, self.category)[self.split])

        self.ds = self.ds.rename(columns={"question": "initial_question"})
        self.ds["messages"] = self.ds.apply(self.add_messages, axis=1)

        return self.ds


if __name__ == "__main__":

    loader_train = HFMATHLoader(split="train")

    loaded_data = loader_train.load_data()[:2000]

    import pdb

    pdb.set_trace()

    samples_1 = pd.DataFrame(loader_test_algebra.load_samples(1000))
    samples_2 = pd.DataFrame(loader_test_intermediate_algebra.load_samples(900))
    samples_2_1 = pd.DataFrame(loader_test_prealgebra.load_samples(100))

    samples_3 = pd.DataFrame(loader_train_algebra.load_samples(1000))
    samples_4 = pd.DataFrame(loader_train_intermediate_algebra.load_samples(900))
    samples_4_1 = pd.DataFrame(loader_train_prealgebra.load_samples(100))

    samples_1 = samples_1.to_dict(orient="records")
    samples_2 = samples_2.to_dict(orient="records")
    samples_2_1 = samples_2_1.to_dict(orient="records")

    samples_3 = samples_3.to_dict(orient="records")
    samples_4 = samples_4.to_dict(orient="records")
    samples_4_1 = samples_4_1.to_dict(orient="records")

    # Export the samples as jsonl
    samples_jsonl = "data/math_algebra_test.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_1))
    samples_jsonl = "data/math_algebra_inter_test.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_2))
    samples_jsonl = "data/math_algebra_pre_test.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_2_1))

    samples_jsonl = "data/math_algebra_train.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_3))

    samples_jsonl = "data/math_algebra_inter_train.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_4))

    samples_jsonl = "data/math_algebra_pre_train.jsonl"
    with open(samples_jsonl, "w") as f:
        f.write(json.dumps(samples_4_1))
