"""Any ONNX model honouring the documented contract plugs in through config alone."""

from pathlib import Path

import onnx
import pytest
from onnx import TensorProto, helper

from kenji.adapters.onnx_classifier import OnnxBackchannelClassifier
from kenji.config import Settings
from kenji.container import build_classifier
from kenji.domain.turn import TurnPolicy, TurnVerdict

POLICY = TurnPolicy(min_interruption_score=0.5)


def _save_urgent_character_model(path: Path) -> Path:
    """P(interruption) = 1 if the utterance contains 待 or 違, else 0."""
    nodes = [
        helper.make_node(
            "TfIdfVectorizer",
            ["characters"],
            ["counts"],
            mode="TF",
            min_gram_length=1,
            max_gram_length=1,
            max_skip_count=0,
            ngram_counts=[0],
            ngram_indexes=[0, 1],
            pool_strings=["待", "違"],
        ),
        helper.make_node("ReduceSum", ["counts", "axes"], ["total"], keepdims=1),
        helper.make_node("Min", ["total", "one"], ["probability"]),
    ]
    graph = helper.make_graph(
        nodes,
        "urgent-characters",
        inputs=[helper.make_tensor_value_info("characters", TensorProto.STRING, [1, None])],
        outputs=[helper.make_tensor_value_info("probability", TensorProto.FLOAT, [1, 1])],
        initializer=[
            helper.make_tensor("axes", TensorProto.INT64, [1], [1]),
            helper.make_tensor("one", TensorProto.FLOAT, [1], [1.0]),
        ],
    )
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 17)], ir_version=9)
    onnx.save(model, str(path))
    return path


@pytest.fixture
def model_path(tmp_path: Path) -> Path:
    return _save_urgent_character_model(tmp_path / "urgent.onnx")


def test_model_scores_through_the_classifier_protocol(model_path: Path) -> None:
    classifier = OnnxBackchannelClassifier(model_path)

    assert classifier.classify("ちょっと待ってください", POLICY).verdict is TurnVerdict.INTERRUPTION
    assert classifier.classify("はい", POLICY).verdict is TurnVerdict.BACKCHANNEL


def test_model_is_chosen_by_configuration_only(
    model_path: Path, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    for key in ("OPENAI_API_KEY", "SONIOX_API_KEY", "CARTESIA_API_KEY"):
        monkeypatch.setenv(key, "test")
    monkeypatch.setenv("BACKCHANNEL_CLASSIFIER", "onnx")
    monkeypatch.setenv("BACKCHANNEL_ONNX_PATH", str(model_path))

    assert isinstance(build_classifier(Settings()), OnnxBackchannelClassifier)


def test_missing_model_fails_at_startup(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="not found"):
        OnnxBackchannelClassifier(tmp_path / "absent.onnx")
