import ast
import os
from collections import Counter

import numpy as np
import pandas as pd
from utils import write_csv_row


def find_files_with_pattern(directory, pattern):
    matching_files = []

    # Walk through the directory
    for root, dirs, files in os.walk(directory):
        for file in files:
            if pattern in file:
                # If the pattern is found in the filename, add to the list
                matching_files.append(os.path.join(root, file))

    return matching_files


def count_error_types(df, task):
    # Initialize a list to collect all error types
    all_error_types = []

    # Iterate through each row of the DataFrame
    for idx, row in df.iterrows():
        error_type_str = row["error_type"]
        if "[" in error_type_str[1:-1]:
            error_type_str = error_type_str.replace("[", "")
            error_type_str = error_type_str.replace("]", "")

        # Convert the string representation of the list into an actual list using ast.literal_eval
        try:
            error_types = ast.literal_eval(error_type_str)
            if isinstance(error_types, list):
                all_error_types += error_types
        except (ValueError, SyntaxError):

            # If there's an issue with converting the string, skip this row
            continue
    try:
        # Use Counter to count occurrences of each error type
        error_type_counts = Counter(all_error_types)
    except:
        import pdb

        pdb.set_trace()
    return error_type_counts


def calculate_src_cov_num(data):
    total_facts = len(data)
    try:
        try:
            relevant_yes = sum(1 for fact in data if fact["relevance"].lower() == "yes")
        except:
            relevant_yes = sum(
                1
                for fact in data
                if fact["reference_solution_coverage"].lower() == "yes"
            )
    except:
        relevant_yes = sum(
            1 for fact in data if fact["reference solution coverage"].lower() == "yes"
        )
    # Calculate the ratio
    return relevant_yes


def calculate_accuracies(df, task):
    # Initialize counters for A, B, C
    correct_A = 0
    correct_B = 0
    correct_C = 0
    quality_A = 0
    quality_B = 0
    quality_C = 0
    recall_A = 0
    recall_B = 0
    recall_C = 0
    f1_A = 0
    f1_B = 0
    f1_C = 0
    total_rows = len(df)
    tot = 0
    for idx, row in df.iterrows():
        if task == "math":
            tot += 1
            state_flow = eval(row["state_flow"])
            correctness_main = row["correctness_main"]

            # Count occurrences of "QUESTION_SOLVING" in the state_flow
            question_solving_count = state_flow.count("QUESTION_SOLVING")

            # Accuracy A: str(correctness_main) == "True" and exactly one "QUESTION_SOLVING"
            if ("1" in correctness_main) and (question_solving_count == 1):
                correct_A += 1

            # Accuracy B: str(correctness_main) == "True" and 2 or 3 "QUESTION_SOLVING"
            if ("1" in correctness_main) and (question_solving_count in [1, 2]):
                correct_B += 1

            # Accuracy C: str(correctness_main) == "True", always counts as correct
            if "1" in correctness_main:
                correct_C += 1
        elif task == "stem":
            # reference solution coverage relevance
            state_flow = eval(row["state_flow"])
            correctness_main = row["correctness_main"]
            correctness_detail = eval(row["correctness_main_detial"])
            correctness_main_ls = eval(correctness_main)

            # Count occurrences of "QUESTION_SOLVING" in the state_flow
            question_solving_count = state_flow.count("QUESTION_SOLVING")
            try:
                src_num = correctness_detail[0]["solution_atomic_facts"][-1][
                    "fact_number"
                ]
            except:
                continue
            tot += 1
            # Accuracy A: str(correctness_main) == "True" and exactly one "QUESTION_SOLVING"
            # if calculate_src_cov_num( correctness_detail[0]['model_atomic_facts']) / src_num>1:
            #     import pdb;pdb.set_trace()
            if question_solving_count == 1:
                model_atomic_facts = correctness_detail[0]["model_atomic_facts"]
                recall_A += calculate_src_cov_num(model_atomic_facts) / len(
                    model_atomic_facts
                )
                recall_B += calculate_src_cov_num(model_atomic_facts) / len(
                    model_atomic_facts
                )
                recall_C += calculate_src_cov_num(model_atomic_facts) / len(
                    model_atomic_facts
                )

                correct_A += correctness_main_ls[0][0]
                correct_B += correctness_main_ls[0][0]
                correct_C += correctness_main_ls[0][0]
                quality_A += correctness_main_ls[0][1]
                quality_B += correctness_main_ls[0][1]
                quality_C += correctness_main_ls[0][1]
                # if (recall_A + correct_A) != 0:
                #     f1_A += 2*(recall_A*correct_A)/(recall_A + correct_A)
                # if (recall_B + correct_B) != 0:
                #     f1_B += 2*(recall_B*correct_B)/(recall_B + correct_B)
                # if (recall_C + correct_C) != 0:
                #     f1_C += 2*(recall_C*correct_C)/(recall_C + correct_C)
            elif question_solving_count == 2:
                model_atomic_facts = correctness_detail[0]["model_atomic_facts"]
                recall_A += calculate_src_cov_num(
                    correctness_detail[0]["model_atomic_facts"]
                ) / len(model_atomic_facts)
                model_atomic_facts = correctness_detail[1]["model_atomic_facts"]
                recall_B += calculate_src_cov_num(
                    correctness_detail[1]["model_atomic_facts"]
                ) / len(model_atomic_facts)
                recall_C += calculate_src_cov_num(
                    correctness_detail[1]["model_atomic_facts"]
                ) / len(model_atomic_facts)
                # import pdb;pdb.set_trace()
                correct_A += correctness_main_ls[0][0]
                correct_B += correctness_main_ls[1][0]
                correct_C += correctness_main_ls[1][0]
                quality_A += correctness_main_ls[0][1]
                quality_B += correctness_main_ls[1][1]
                quality_C += correctness_main_ls[1][1]
                if (recall_A + correct_A) != 0:
                    f1_A += 2 * (recall_A * correct_A) / (recall_A + correct_A)
                if (recall_B + correct_B) != 0:
                    f1_B += 2 * (recall_B * correct_B) / (recall_B + correct_B)
                if (recall_C + correct_C) != 0:
                    f1_C += 2 * (recall_C * correct_C) / (recall_C + correct_C)
            else:
                try:
                    model_atomic_facts = correctness_detail[0]["model_atomic_facts"]
                    recall_A += calculate_src_cov_num(
                        correctness_detail[0]["model_atomic_facts"]
                    ) / len(model_atomic_facts)
                    model_atomic_facts = correctness_detail[1]["model_atomic_facts"]
                    recall_B += calculate_src_cov_num(
                        correctness_detail[1]["model_atomic_facts"]
                    ) / len(model_atomic_facts)
                    model_atomic_facts = correctness_detail[2]["model_atomic_facts"]
                    recall_C += calculate_src_cov_num(
                        correctness_detail[2]["model_atomic_facts"]
                    ) / len(model_atomic_facts)
                except:
                    import pdb

                    pdb.set_trace()
                correct_A += correctness_main_ls[0][0]
                correct_B += correctness_main_ls[1][0]
                correct_C += correctness_main_ls[2][0]
                quality_A += correctness_main_ls[0][1]
                quality_B += correctness_main_ls[1][1]
                quality_C += correctness_main_ls[2][1]
                if (recall_A + correct_A) != 0:
                    f1_A += 2 * (recall_A * correct_A) / (recall_A + correct_A)
                if (recall_B + correct_B) != 0:
                    f1_B += 2 * (recall_B * correct_B) / (recall_B + correct_B)
                if (recall_C + correct_C) != 0:
                    f1_C += 2 * (recall_C * correct_C) / (recall_C + correct_C)
            # Accuracy B: str(correctness_main) == "True" and 2 or 3 "QUESTION_SOLVING"
    # Calculate accuracies as percentages

    accuracy_A = correct_A / tot if total_rows > 0 else 0
    accuracy_B = correct_B / tot if total_rows > 0 else 0
    accuracy_C = correct_C / tot if total_rows > 0 else 0
    recall_A = recall_A / tot if total_rows > 0 else 0
    recall_B = recall_B / tot if total_rows > 0 else 0
    recall_C = recall_C / tot if total_rows > 0 else 0
    f1_A = f1_A / tot if total_rows > 0 else 0
    f1_B = f1_B / tot if total_rows > 0 else 0
    f1_C = f1_C / tot if total_rows > 0 else 0
    quality_A = quality_A / tot if total_rows > 0 else 0
    quality_B = quality_B / tot if total_rows > 0 else 0
    quality_C = quality_C / tot if total_rows > 0 else 0
    return (
        accuracy_A,
        accuracy_B,
        accuracy_C,
    )  # ,recall_A,quality_A], [accuracy_B,recall_B,quality_B], [accuracy_C,recall_C,quality_C]


def convert_labels(input_dict, output_dict):
    for key, value in input_dict.items():
        label = value["label"]
        if key == "redundancy":
            # Special rule for redundancy
            if label == "high":
                if key in output_dict:
                    output_dict[key].append(-1)
                else:
                    output_dict[key] = [-1]
            elif label == "low":
                if key in output_dict:
                    output_dict[key].append(1)
                else:
                    output_dict[key] = [1]
            else:  # medium
                if key in output_dict:
                    output_dict[key].append(0)
                else:
                    output_dict[key] = [0]
        else:
            # General rule for all other features
            if label == "high":
                if key in output_dict:
                    output_dict[key].append(1)
                else:
                    output_dict[key] = [1]
            elif label == "low":
                if key in output_dict:
                    output_dict[key].append(-1)
                else:
                    output_dict[key] = [-1]
            else:  # medium
                if key in output_dict:
                    output_dict[key].append(0)
                else:
                    output_dict[key] = [0]
    return output_dict


def calculate_stats(data):
    result = {}
    for key, values in data.items():
        avg = np.mean(values)
        std = np.std(values)
        result[key] = {"average": avg, "std": std}
    return result


def analyze_feedback_distribution(df, task):
    # Initialize counters for feedback types in both cases
    feedback_true = []
    feedback_false = []
    output_dict_true = {}
    output_dict_false = {}
    # Iterate through the DataFrame rows
    for idx, row in df.iterrows():

        correctness_main = row["correctness_main"]
        if task == "math":
            feedback_type_str = row["feedback_types"]
            # Convert the string representation of the list to an actual list
            try:
                feedback_types = ast.literal_eval(feedback_type_str)
                if isinstance(feedback_types, list):
                    # Filter out "affirmation" feedback

                    feedback_types = [
                        fb for fb in feedback_types if "Affirmation" not in fb
                    ]

                    # Separate feedback types based on correctness_main
                    if correctness_main == True:
                        feedback_true.extend(feedback_types)
                    else:
                        feedback_false.extend(feedback_types)
            except (ValueError, SyntaxError):
                # Skip rows where there's an issue with the string conversion
                continue

        elif task == "stem":
            try:
                feedback_types = eval(row["correctness_main_detial"])[0]["assessment"]
            except:
                continue
            # Convert the string representation of the list to an actual list
            try:

                # Filter out "affirmation" feedback

                # feedback_types = [fb for fb in feedback_types if "Affirmation" not in fb ]

                # Separate feedback types based on correctness_main

                corr_list = eval(correctness_main)
                if corr_list[min(3, len(corr_list)) - 1] == 1:
                    output_dict_true = convert_labels(feedback_types, output_dict_true)
                else:

                    feedback_false.extend(feedback_types)
                    output_dict_false = convert_labels(
                        feedback_types, output_dict_false
                    )
            except (ValueError, SyntaxError):
                # Skip rows where there's an issue with the string conversion
                continue

    if task == "math":
        # Use Counter to count occurrences of feedback types for both True and False cases
        feedback_true_counts = Counter(feedback_true)
        feedback_false_counts = Counter(feedback_false)

        # Calculate total feedback types for normalization (rate calculation)
        total_true = sum(feedback_true_counts.values())
        total_false = sum(feedback_false_counts.values())

        # Convert counts to rates (percentage of total)
        feedback_true_rates = (
            {k: v / total_true for k, v in feedback_true_counts.items()}
            if total_true > 0
            else {}
        )
        feedback_false_rates = (
            {k: v / total_false for k, v in feedback_false_counts.items()}
            if total_false > 0
            else {}
        )
        feedback_true_rates_sorted = dict(
            sorted(feedback_true_rates.items(), key=lambda item: item[1], reverse=True)
        )
        feedback_false_rates_sorted = dict(
            sorted(feedback_false_rates.items(), key=lambda item: item[1], reverse=True)
        )
    else:
        feedback_true_rates_sorted = calculate_stats(output_dict_true)
        feedback_false_rates_sorted = calculate_stats(output_dict_false)
    return feedback_true_rates_sorted, feedback_false_rates_sorted


def calculate_followup_accuracy(df, task):
    # Filter the DataFrame for the two cases based on correctness_main
    main_true_df = df[df["correctness_main"].apply(lambda x: "1" in x)]
    main_false_df = df[df["correctness_main"].apply(lambda x: "1" not in x)]
    # Calculate accuracy for the followup in both cases (correctness_followup >= 1 is regarded as correct)
    # import pdb;pdb.set_trace()
    try:
        followup_accuracy_main_true = [
            (float(max(eval(i))) >= 1) if eval(i) != [] else 0
            for i in main_true_df["correctness_followup"]
        ].count(True) / len(main_true_df)
    except:
        followup_accuracy_main_true = 0
    try:
        followup_accuracy_main_false = [
            (float(max(eval(i))) >= 1) if eval(i) != [] else 0
            for i in main_false_df["correctness_followup"]
        ].count(True) / len(main_false_df)
    except:
        followup_accuracy_main_false = 0
    return followup_accuracy_main_true, followup_accuracy_main_false


# Example usage:
if __name__ == "__main__":
    task = "math"
    output_path = "./outputs/contam_math_final.csv"
    head = [
        "model",
        "acc_E1",
        "acc_E2",
        "acc_E3",
        "followup_accuracy_true",
        "followup_accuracy_false",
        "feedback_true",
        "feedback_false",
        "error_type",
    ]
    write_csv_row(head, output_path)
    files = find_files_with_pattern("./contam_final", "csv")
    for file in files:
        print(file)
        df = pd.read_csv(file)
        model = file.split(".csv")[0]

        accuracy_A, accuracy_B, accuracy_C = calculate_accuracies(df, task)
        feedback_true, feedback_false = analyze_feedback_distribution(df, task)
        if task == "math":
            try:
                error_type = count_error_types(df, task)
            except:
                import pdb

                pdb.set_trace()
            followup_accuracy_true, followup_accuracy_false = (
                calculate_followup_accuracy(df, task)
            )
            write_csv_row(
                [
                    model,
                    accuracy_A,
                    accuracy_B,
                    accuracy_C,
                    followup_accuracy_true,
                    followup_accuracy_false,
                    feedback_true,
                    feedback_false,
                    error_type,
                ],
                output_path,
            )
        else:
            write_csv_row(
                [model]
                + accuracy_A
                + accuracy_B
                + accuracy_C
                + [feedback_true, feedback_false],
                output_path,
            )

        level1 = pd.concat([df[:10], df[50:60]])
        level2 = pd.concat([df[10:20], df[60:70]])
        level3 = pd.concat([df[20:30], df[70:80]])
        level4 = pd.concat([df[30:40], df[80:90]])
        level5 = pd.concat([df[40:50], df[90:100]])
        for id, dfs in enumerate([level1, level2, level3, level4, level5]):
            accuracy_A, accuracy_B, accuracy_C = calculate_accuracies(dfs, task)
            feedback_true, feedback_false = analyze_feedback_distribution(dfs, task)
            if task == "math":
                try:
                    error_type = count_error_types(dfs, task)
                except:
                    import pdb

                    pdb.set_trace()
                followup_accuracy_true, followup_accuracy_false = (
                    calculate_followup_accuracy(dfs, task)
                )
                write_csv_row(
                    [
                        id,
                        accuracy_A,
                        accuracy_B,
                        accuracy_C,
                        followup_accuracy_true,
                        followup_accuracy_false,
                        feedback_true,
                        feedback_false,
                        error_type,
                    ],
                    output_path,
                )
            else:
                write_csv_row(
                    [id]
                    + accuracy_A
                    + accuracy_B
                    + accuracy_C
                    + [feedback_true, feedback_false],
                    output_path,
                )
