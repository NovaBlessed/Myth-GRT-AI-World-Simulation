from myth_grt.cli import main
from myth_grt.world import load_world


def test_demo_runs_offline_and_saves(tmp_path):
    save = tmp_path / "demo.json"
    svg = tmp_path / "demo.svg"
    code = main([
        "demo", "--offline", "--genre", "Mystery", "--elements", "Shadow", "Air",
        "--save", str(save), "--svg", str(svg),
        "whisper a secret to the wind", "open a hidden door",
    ])
    assert code == 0
    world = load_world(save)
    assert world.age_in_years == 2
    assert svg.read_text().startswith("<svg")


def test_status_without_a_world(tmp_path, capsys):
    assert main(["status", "--world", str(tmp_path / "none.json")]) == 1
