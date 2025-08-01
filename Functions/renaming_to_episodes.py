import os


def rename_to_episodes(full_path: str) -> str:
    os.startfile(full_path)
    episodes = os.listdir(full_path)
    for i, episode in enumerate(episodes, start=1):
        old_name = os.path.join(full_path, episode)
        file_name = f"E0{i}" if i <= 9 else f"E{i}"
        extension = episode[episode.index(".") :]
        new_name = os.path.join(full_path, file_name + extension)
        os.rename(old_name, new_name)

    return f"Successfully renamed to Episodes"
