"""
Sanity check for the synthetic task generator.

This creates a tiny synthetic dataset and saves it to JSON.
It is not the full pilot experiment yet.
"""

from src.task_generator import generate_synthetic_tasks, save_tasks_to_json


def main() -> None:
    tasks = generate_synthetic_tasks(num_tasks=5, seed=42)

    output_path = "data/synthetic/sanity_tasks.json"
    save_tasks_to_json(tasks, output_path)

    print(f"Generated tasks: {len(tasks)}")
    print(f"Saved to: {output_path}")

    first_task = tasks[0]

    print("\nFirst task preview:")
    print("Task ID:", first_task["task_id"])
    print("Question:", first_task["question"])
    print("Original evidence:", first_task["original_evidence"])
    print("Gold answer:", first_task["gold_answer"])
    print("Required unit count:", len(first_task["required_units"]))

    assert len(tasks) == 5
    assert len(first_task["required_units"]) == 3
    assert first_task["gold_answer"] in {"eligible", "not eligible"}

    print("\nTask generator sanity check passed.")


if __name__ == "__main__":
    main()