import ast
import csv
import json
import random
import re

from json_repair import repair_json


def extract_boxed_str(x):
    # This regex captures text inside \boxed{\text{ }}

    try:
        try:
            pattern = r"\\boxed\{(.*?)\}(?:\n|\$|\.|,)"
            match = re.search(pattern, x["solution"])
            x["answer"] = match.group(1)
        except:
            pattern = r"\\boxed\{(.*?)\}(?:\n|\$|\.)"
            match = re.search(pattern, x["solution"])
            x["answer"] = match.group(1)
    except:
        x["answer"] = None
    return x


def select_queries(query_list, history, current_index, flag):
    selected_queries = []

    # Check if all queries have been selected
    if all(idx in history[i] for i, sublist in enumerate(query_list) for idx in range(len(sublist))):
        return None, history, current_index

    # If index out of bounds, return "FIN"
    if current_index < 0 or current_index >= len(query_list):
        return None, history, current_index

    # Count the number of selected queries in the current index
    selected_count = len(history[current_index])
    if flag == 1:
        if selected_count < 2:
            query = select_random_query_from_index(query_list, history, current_index, selected_queries)

        else:
            current_index += 1
            query = (
                select_random_query_from_index(query_list, history, current_index, selected_queries)
                if current_index < len(query_list)
                else None
            )
    else:
        current_index -= 1
        query = (
            select_random_query_from_index(query_list, history, current_index, selected_queries)
            if current_index >= 0
            else None
        )

    if query is None:
        return None, history, current_index
    # history[current_index].append(query)
    return query, history, current_index


def select_random_query_from_index(query_list, history, index, selected_queries):
    available_queries = [idx for idx in range(len(query_list[index])) if idx not in history[index]]
    if available_queries:
        query_idx = random.choice(available_queries)
        history[index].append(query_idx)
        selected_queries.append(query_list[index][query_idx])
        return query_list[index][query_idx]
    return None


def write_csv_row(values, filename):
    open_trial = 0

    while True:
        if open_trial > 10:
            raise Exception("something wrong")

        try:

            with open(filename, "a", encoding="utf-8") as f:

                writer = csv.writer(f)
                writer.writerow(values)
            break
        except:
            print("open failed")
            continue


def extract_json(text):
    # Define the regex pattern to extract the JSON part
    text = text.replace("\n", "")
    text = text.split("```json")[-1]
    text = text.split("```")[0]
    text = f"""{text}"""
    text = repair_json(text)
    text = text.replace("\\", "\\\\")
    # pattern = r"\{[^{}]*\}"
    # match = re.findall(pattern, text)

    try:
        output = json.loads(text)
        return output
    except:
        pass
    try:
        output = json.loads(re.sub(r"(?<=\{|\s)'|(?<=\s|:)'|(?<=\d)'(?!:)|'(?=\s|,|}|:)", '"', text))
        return output
    except:
        pass
    try:
        output = ast.literal_eval(text)
        return output
    except:
        pass
    # match = re.findall(pattern, text)
    # try:
    #     output = json.loads(re.sub(r"(?<=\{|\s)'|(?<=\s|:)'|(?<=\d)'(?!:)|'(?=\s|,|}|:)", '"', text))
    #     return output
    # except:
    #     pass
    # try:
    #     output = json.loads(json.dumps(text))
    #     return output
    # except:
    #     pass
    # try:
    #     output = json.loads(json.dumps(text))
    #     return output
    # except:
    #     pass
    # try:
    #     output = json.loads(re.sub(r"(?<=\{|\s)'|(?<=\s|:)'|(?<=\d)'(?!:)|'(?=\s|,|}|:)", '"', text))
    #     return output
    # except:
    #     pass
    return text


def load_jsonl_file(filepath):
    json_list = []
    with open(filepath, "r") as file:
        for line in file:
            # Load each line as a JSON object
            json_obj = json.loads(line.strip())
            json_list.append(json_obj)
    return json_list


if __name__ == "__main__":
    query_list = [["q1", "q2", "q3"], ["q4", "q5", "q6"], ["q7", "q8", "q9"]]
    history = {i: [] for i in range(len(query_list))}  # Use index-based history tracking
    current_index = 1
    flag = True
    select_queries(query_list, history, current_index, flag)
