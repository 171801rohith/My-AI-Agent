import os


def open_path(driver: str, base_folder: str, *sub_folders: str):
    full_path = os.path.join(f"{driver}:", base_folder, *sub_folders)
    print(full_path)
    return full_path


os.startfile(open_path("c", "program files", "java", "jdk-17"))