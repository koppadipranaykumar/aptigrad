import json
import sys
from pathlib import Path

from fastapi import HTTPException

# Allow importing main.py from the same backend folder
sys.path.insert(0, str(Path(__file__).parent))

from main import _grade_answer


# ============================================================
# FILE PATHS
# ============================================================

BASE_DIR = Path(__file__).parent.parent

EVAL_SET_PATH = (
    BASE_DIR
    / "data"
    / "eval-set"
    / "answers.json"
)

RESULTS_PATH = (
    BASE_DIR
    / "data"
    / "eval-set"
    / "results.json"
)


# ============================================================
# MAIN EVALUATION FUNCTION
# ============================================================

def run_eval():

    print("\n===================================")
    print("       APTIGRAD GRADER EVALUATION")
    print("===================================\n")

    # --------------------------------------------------------
    # LOAD EVALUATION DATA
    # --------------------------------------------------------

    if not EVAL_SET_PATH.exists():
        print(f"ERROR: Evaluation file not found:\n{EVAL_SET_PATH}")
        return

    try:
        with open(
            EVAL_SET_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            eval_set = json.load(f)

    except json.JSONDecodeError as e:

        print(
            f"ERROR: answers.json contains invalid JSON.\n{e}"
        )

        return


    # --------------------------------------------------------
    # VALIDATE DATA
    # --------------------------------------------------------

    if not isinstance(eval_set, list):

        print(
            "ERROR: answers.json must contain a JSON array."
        )

        return

    if len(eval_set) == 0:

        print(
            "ERROR: Evaluation dataset is empty."
        )

        return


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    results = []

    exact_matches = 0
    within_one = 0
    total_abs_error = 0

    successful_examples = 0
    failed_examples = 0


    # --------------------------------------------------------
    # RUN EVALUATION
    # --------------------------------------------------------

    print(f"Loaded {len(eval_set)} evaluation examples.\n")

    for index, item in enumerate(eval_set, start=1):

        item_id = item.get(
            "id",
            f"example-{index}"
        )

        print(
            f"Evaluating [{item_id}] "
            f"({index}/{len(eval_set)})..."
        )

        # Validate required fields
        required_fields = [
            "domain",
            "difficulty",
            "question",
            "answer",
            "human_score",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in item
        ]

        if missing_fields:

            print(
                f"  FAILED: Missing fields: "
                f"{', '.join(missing_fields)}"
            )

            failed_examples += 1

            results.append({
                "id": item_id,
                "status": "failed",
                "error": (
                    "Missing required fields: "
                    + ", ".join(missing_fields)
                )
            })

            continue


        # ----------------------------------------------------
        # CALL AI GRADER
        # ----------------------------------------------------

        try:

            grading = _grade_answer(

                domain=item["domain"],

                difficulty=item["difficulty"],

                question_text=item["question"],

                answer_text=item["answer"],
            )

            model_score = grading["score"]

            human_score = item["human_score"]

            error = abs(
                model_score - human_score
            )


        except HTTPException as e:

            print(
                f"  FAILED: {e.detail}"
            )

            failed_examples += 1

            results.append({

                "id": item_id,

                "question": item["question"],

                "human_score": item["human_score"],

                "status": "failed",

                "error": str(e.detail),
            })

            continue


        except Exception as e:

            print(
                f"  FAILED: {str(e)}"
            )

            failed_examples += 1

            results.append({

                "id": item_id,

                "question": item["question"],

                "human_score": item["human_score"],

                "status": "failed",

                "error": str(e),
            })

            continue


        # ----------------------------------------------------
        # CALCULATE METRICS
        # ----------------------------------------------------

        successful_examples += 1

        if error == 0:

            exact_matches += 1

        if error <= 1:

            within_one += 1

        total_abs_error += error


        # ----------------------------------------------------
        # SAVE RESULT
        # ----------------------------------------------------

        results.append({

            "id": item_id,

            "question": item["question"],

            "domain": item["domain"],

            "difficulty": item["difficulty"],

            "human_score": human_score,

            "model_score": model_score,

            "model_reasoning": grading.get(
                "reasoning",
                ""
            ),

            "abs_error": error,

            "status": "success",
        })


        print(
            f"  SUCCESS → "
            f"Human={human_score} | "
            f"Model={model_score} | "
            f"Error={error}"
        )


    # ========================================================
    # PRINT SUMMARY
    # ========================================================

    print("\n===================================")
    print("         EVALUATION SUMMARY")
    print("===================================")

    print(
        f"Total examples:      {len(eval_set)}"
    )

    print(
        f"Successful examples: {successful_examples}"
    )

    print(
        f"Failed examples:     {failed_examples}"
    )


    if successful_examples > 0:

        exact_rate = (
            100
            * exact_matches
            / successful_examples
        )

        within_one_rate = (
            100
            * within_one
            / successful_examples
        )

        mean_absolute_error = (
            total_abs_error
            / successful_examples
        )


        print(
            f"\nExact match rate: "
            f"{exact_matches}/{successful_examples} "
            f"({exact_rate:.1f}%)"
        )

        print(
            f"Within-1 agreement: "
            f"{within_one}/{successful_examples} "
            f"({within_one_rate:.1f}%)"
        )

        print(
            f"Mean absolute error: "
            f"{mean_absolute_error:.2f}"
        )

    else:

        print(
            "\nNo successful evaluations."
        )


    # ========================================================
    # WRITE RESULTS FILE
    # ========================================================

    try:

        RESULTS_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            RESULTS_PATH,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                results,
                f,
                indent=2,
                ensure_ascii=False
            )

        print(
            f"\nDetailed results written to:\n"
            f"{RESULTS_PATH}"
        )

    except Exception as e:

        print(
            f"\nWARNING: Could not write results file:\n"
            f"{str(e)}"
        )


# ============================================================
# RUN SCRIPT
# ============================================================

if __name__ == "__main__":

    run_eval()