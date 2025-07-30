import os
from llama_index.core.tools import FunctionTool
import AppOpener


class AppAndFileTools:
    def __init__(self):
        self.tools = []

        open_app_tool = FunctionTool.from_defaults(
            fn=self.open_app,
            description="""Launches a known application on the user's system using its name (e.g., 'whatsapp', 'brave', 'microsoft store'). The app must be installed and accessible.""",
        )
        close_app_tool = FunctionTool.from_defaults(
            fn=self.close_app,
            description="""Attempts to close a running application on the user's system using its name (e.g., 'whatsapp', 'brave', 'microsoft store'). The app must be running.""",
        )
        open_directory_tool = FunctionTool.from_defaults(
            fn=self.open_directory,
            description="""
                            Opens a directory in the file explorer using the given drive, base folder, and optional subfolders.

                            Args:
                            - driver (str): Drive letter (e.g., 'C').
                            - base_folder (str): Top-level folder name.
                            - *sub_folders (str): Additional folders to complete the path.

                            Returns:
                            - str: Success or error message.

                            Example:
                            open_directory("R", "movies", "books")
                            → Opens 'r:\\movies\\books'
                        """,
        )

        self.tools += [
            open_app_tool,
            close_app_tool,
            open_directory_tool,
        ]

    def open_app(self, app_name: str) -> str:
        try:
            AppOpener.open(app_name, throw_error=True, match_closest=True)
            return f"Successfully opened {app_name}."
        except Exception as e:
            return f"Failed to open {app_name}. Error: {str(e)}"

    def close_app(self, app_name: str) -> str:
        try:
            AppOpener.close(app_name, throw_error=True, match_closest=True)
            return f"Successfully opened {app_name}."
        except Exception as e:
            return f"Failed to open {app_name}. Error: {str(e)}"

    def open_directory(self, full_path: str) -> str:
        try:
            os.startfile(full_path)
            return f"Successfully opened Directory."
        except Exception as e:
            return f"Failed to open Directory. Error: {str(e)}"                                                                                                                                                             
