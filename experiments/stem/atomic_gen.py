import json
import sys
from collections import defaultdict
from typing import Dict, List, Set

import pandas as pd
from datasets import load_dataset

sys.path.append(".")
import os

from src.models import ChatModel
from src.utils import write_csv_row
from stem.prompt import STEM_ATOMIC_FACT_GENERATOR_PROMPT_TEMPLATE

dataset = load_dataset("scottsuk0306/DepthQA", split="test")
dataset = pd.DataFrame(dataset)
solution_atom = []
saved_log = pd.read_csv("solution_atom.csv")
for item in dataset.iterrows():
    if item[1]["nodeid"] in saved_log["nodeid"]:
        continue
    prompt = STEM_ATOMIC_FACT_GENERATOR_PROMPT_TEMPLATE.format(input=item[1]["solution"])
    model = ChatModel.create_model("gpt-4o")
    try:
        output = model.invoke(prompt)
        item[1]["solution_atom"] = output.content
        print(output.content)
    except:
        continue
    # if os.path.exists('solution_atom.csv'):
    #     write_csv_row(item[1],'solution_atom.csv')
    # else:
    # write_csv_row(['nodeid', 'qid', 'question', 'level', 'solution', 'domain', 'messages', 'solution_atom'],'solution_atom.csv')
    write_csv_row(item[1], "solution_atom.csv")
