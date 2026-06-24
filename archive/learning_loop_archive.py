from .strategist_archive import write_json


def write_learning_loop_snapshot(cycle_dir, payload):
    return write_json(cycle_dir, "learning_loop_snapshot.json", payload)
