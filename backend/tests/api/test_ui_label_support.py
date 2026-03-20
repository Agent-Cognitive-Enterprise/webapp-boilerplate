from api.ui_label_support import build_ui_label_map
from api.ui_label_support import compute_ui_label_values_hash
from models.ui_label import UiLabel


def test_compute_ui_label_values_hash_is_order_independent() -> None:
    assert compute_ui_label_values_hash(["Bonjour", "Au revoir"]) == (
        compute_ui_label_values_hash(["Au revoir", "Bonjour"])
    )


def test_build_ui_label_map_preserves_key_value_pairs() -> None:
    labels = [
        UiLabel(id=1, key="greeting.hello", locale="fr", value="Bonjour"),
        UiLabel(id=2, key="greeting.goodbye", locale="fr", value="Au revoir"),
    ]

    assert build_ui_label_map(labels) == {
        "greeting.hello": "Bonjour",
        "greeting.goodbye": "Au revoir",
    }
