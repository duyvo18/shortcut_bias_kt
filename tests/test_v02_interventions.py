import json
import pandas as pd

from shortcut_bias_pilot.concept_relations import ConceptRelations
from shortcut_bias_pilot.probes import ProbeSpec, build_lgt_pair
from shortcut_bias_pilot.train_interventions import select_iap_arms, write_iap_arm


def test_lgt_rejects_any_related_skill():
    relations = ConceptRelations.from_parent_pairs([("child", "parent"), ("sibling", "parent")])
    prefix = pd.DataFrame([
        {"event_id": "e0", "question_id": "x", "concept_id": "child", "concept_ids": ("child", "far"), "response": 0},
        {"event_id": "e1", "question_id": "y", "concept_id": "other", "concept_ids": ("other",), "response": 0},
        {"event_id": "e2", "question_id": "z", "concept_id": "other2", "concept_ids": ("other2",), "response": 1},
    ])
    target = pd.Series({"question_id": "target", "concept_id": "sibling", "concept_ids": ("sibling",), "target_label": 1})
    variants, audit = build_lgt_pair(prefix, target, ProbeSpec("LGT-01", remote_fraction=1.0), relations)
    assert audit["changed_event_ids"] == ["e1", "e2"]
    assert variants["plus"].loc[0, "response"] == 0
    assert audit["relation_mode"] == "hierarchy_aware"


def test_iap_edits_only_listed_event_ids(tmp_path):
    events = pd.DataFrame({"question_id": ["q", "q"], "response": [0, 1], "event_id": ["train:0", "train:1"]})
    high = next(arm for arm in select_iap_arms(events, "q", seed=1) if arm.arm == "prior_high")
    source = tmp_path / "train.csv"
    pd.DataFrame({"questions": ["q,q"], "concepts": ["1,1"], "responses": ["0,1"], "fold": [1]}).to_csv(source, index=False)
    destination = tmp_path / "arm.csv"; manifest = tmp_path / "manifest.json"
    write_iap_arm(source, destination, high, manifest, test_hash="fixed", fold=0)
    assert pd.read_csv(destination).loc[0, "responses"] == "1,1"
    assert json.loads(manifest.read_text())["changed_event_ids"] == ["train:0"]
