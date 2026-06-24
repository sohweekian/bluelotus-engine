from .strategist_archive import write_json


def write_disagreement_log(cycle_dir, payload):
    return write_json(cycle_dir, "disagreement_log.json", payload)
