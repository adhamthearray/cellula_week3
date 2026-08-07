from services.classifier import IntentClassifier
from services.code_runner import CodeRunner


def test_classifier_fallback_explain() -> None:
    classifier = IntentClassifier(api_key=None)
    assert classifier.classify("Explain this function line by line") == "Explain"


def test_code_runner_executes_python() -> None:
    runner = CodeRunner()
    status, output = runner.run("print('hello')")
    assert status == "Execution succeeded"
    assert output == "hello"
