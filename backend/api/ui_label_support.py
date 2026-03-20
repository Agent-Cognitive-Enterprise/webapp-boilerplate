from collections.abc import Iterable

from models.ui_label import UiLabel
from utils.murmur3 import murmurhash3_32


def compute_ui_label_values_hash(values: Iterable[str]) -> str:
    return murmurhash3_32("".join(sorted(values)))


def build_ui_label_map(labels: Iterable[UiLabel]) -> dict[str, str]:
    return {label.key: label.value for label in labels}
