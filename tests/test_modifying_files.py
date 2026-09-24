import pytest

from Functions import modifing_files
from Functions.modifing_files import rename_to_episodes, write_txt_file


def make_files(folder, names):
    for name in names:
        (folder / name).write_text(name)


def test_rename_to_episodes_renames_all_files(tmp_path, no_startfile):
    make_files(tmp_path, ["a.mkv", "b.mkv", "c.srt"])

    assert rename_to_episodes(str(tmp_path)).startswith("Successfully")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["E01.mkv", "E02.mkv", "E03.srt"]


def test_rename_to_episodes_two_digit_numbers(tmp_path, no_startfile):
    make_files(tmp_path, [f"ep_{i:03d}.mp4" for i in range(1, 12)])

    rename_to_episodes(str(tmp_path))

    names = sorted(p.name for p in tmp_path.iterdir())
    assert names[0] == "E01.mp4"
    assert names[-1] == "E11.mp4"


@pytest.mark.xfail(reason="os.listdir order is used as-is; files are not naturally sorted")
def test_rename_to_episodes_uses_natural_order(tmp_path, no_startfile, monkeypatch):
    make_files(tmp_path, ["Show 1.mkv", "Show 2.mkv", "Show 10.mkv"])
    # Simulate an unordered directory listing, as os.listdir does not guarantee order.
    monkeypatch.setattr(
        modifing_files.os, "listdir", lambda _: ["Show 10.mkv", "Show 2.mkv", "Show 1.mkv"]
    )

    rename_to_episodes(str(tmp_path))

    assert (tmp_path / "E03.mkv").read_text() == "Show 10.mkv"


@pytest.mark.xfail(reason="sub-directories are renamed as if they were episodes")
def test_rename_to_episodes_skips_directories(tmp_path, no_startfile):
    make_files(tmp_path, ["a.mkv"])
    (tmp_path / "Subs").mkdir()

    rename_to_episodes(str(tmp_path))

    assert (tmp_path / "Subs").is_dir()


@pytest.mark.xfail(reason="an existing E01.* makes the rename fail halfway, leaving a mixed state")
def test_rename_to_episodes_handles_existing_target_names(tmp_path, no_startfile, monkeypatch):
    # Renaming A.mkv -> E01.mkv collides with the file that is already called E01.mkv.
    make_files(tmp_path, ["A.mkv", "E01.mkv"])
    monkeypatch.setattr(modifing_files.os, "listdir", lambda _: ["A.mkv", "E01.mkv"])

    rename_to_episodes(str(tmp_path))

    assert sorted(p.name for p in tmp_path.iterdir()) == ["E01.mkv", "E02.mkv"]
    assert {(tmp_path / n).read_text() for n in ["E01.mkv", "E02.mkv"]} == {"A.mkv", "E01.mkv"}


def test_write_txt_file_picks_next_free_name(tmp_path):
    write_txt_file("first", str(tmp_path))
    write_txt_file("second", str(tmp_path))

    assert (tmp_path / "File_1.txt").read_text() == "first"
    assert (tmp_path / "File_2.txt").read_text() == "second"


def test_write_txt_file_missing_folder_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        write_txt_file("x", str(tmp_path / "missing"))
