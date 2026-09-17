import yaml


def load_params() -> dict:
    with open("params.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["embeed"]
