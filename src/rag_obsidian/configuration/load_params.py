import yaml


def load_params(section: str) -> dict:
    with open("params.yaml", encoding="utf-8") as f:
        all_params = yaml.safe_load(f)

    return all_params[section]
