import json
from collections import defaultdict
from typing import Dict, List, Set

from datasets import load_dataset
import pandas as pd


class HFMATHLoader:
    def __init__(self, hf_repo: str = "allenai/tulu-v3.1-mix-preview-4096-OLMoE", split: str = "train"):
        self.hf_repo = hf_repo
        self.split = split
      


    def load_data(self, except_questions: bool = False, remove_unused_columns: bool = True):
        print(f"Loading data from {self.hf_repo}...")
        self.ds = pd.DataFrame(load_dataset(self.hf_repo)[self.split])
        
        

        return self.ds




if __name__ == "__main__":

    loader_train = HFMATHLoader(split ="train")

    loaded_data = loader_train.load_data()
    
    import pdb;pdb.set_trace()
    random_sample = loaded_data.sample(n=2000, random_state=42)
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

    
