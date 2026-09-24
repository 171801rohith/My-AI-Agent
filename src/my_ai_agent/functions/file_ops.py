import os
import re


def _natural_key(name: str) -> list:
    """Sort key that orders 'Ep 2' before 'Ep 10'."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


def plan_episode_renames(full_path: str) -> list[tuple[str, str]]:
    """Return (old_name, new_name) pairs for every visible file in the folder,
    in natural order. Sub-folders and hidden files are left alone."""
    files = [
        name
        for name in os.listdir(full_path)
        if os.path.isfile(os.path.join(full_path, name)) and not name.startswith(".")
    ]
    files.sort(key=_natural_key)
    return [
        (name, f"E{i:02d}{os.path.splitext(name)[1]}")
        for i, name in enumerate(files, start=1)
    ]


def rename_to_episodes(full_path: str, plan: list[tuple[str, str]] | None = None) -> str:
    """Rename files to E01, E02, ... (see apply_renames for the safety guarantees)."""
    if plan is None:
        plan = plan_episode_renames(full_path)
    apply_renames(full_path, plan)
    return f"Successfully renamed {len(plan)} files to Episodes"


def apply_renames(full_path: str, plan: list[tuple[str, str]]) -> None:
    """Rename (old, new) pairs in two phases so that existing names such as E01.mkv
    cannot collide. If anything fails, completed renames are rolled back."""
    done = []  # (current_path, original_path) for rollback
    try:
        temp_paths = []
        for i, (old_name, _) in enumerate(plan):
            old_path = os.path.join(full_path, old_name)
            temp_path = os.path.join(full_path, f".renaming_{i}.tmp")
            os.rename(old_path, temp_path)
            done.append((temp_path, old_path))
            temp_paths.append(temp_path)

        for temp_path, (old_name, new_name) in zip(temp_paths, plan):
            new_path = os.path.join(full_path, new_name)
            os.rename(temp_path, new_path)
            done.append((new_path, temp_path))
    except OSError:
        for current, previous in reversed(done):
            os.rename(current, previous)
        raise


def write_txt_file(content: str, path: str) -> str:
    """Write content to the next free File_N.txt in path and return the file's path."""
    i = 1
    file_name = f"File_{i}.txt"
    output_path = os.path.join(path, file_name)
    while os.path.exists(output_path):
        i += 1
        file_name = f"File_{i}.txt"
        output_path = os.path.join(path, file_name)
    with open(output_path, "w") as file:
        file.write(content)

    return output_path
