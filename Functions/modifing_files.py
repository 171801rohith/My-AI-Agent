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


def write_txt_file(content: str, path: str):
    i = 1
    file_name = f"File_{i}.txt"
    output_path = os.path.join(path, file_name)
    while os.path.exists(output_path):
        i += 1
        file_name = f"File_{i}.txt"
        output_path = os.path.join(path, file_name)
    with open(output_path, "w") as file:
        file.write(content)

    return f"Successfully Noted down to a text file."
