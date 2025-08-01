import os
from llama_index.core.tools import FunctionTool
import AppOpener

from Functions.renaming_to_episodes import rename_to_episodes


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
                        Opens a directory in the system's file explorer using the provided full path.

                        Args:
                        - full_path (str): The absolute path to the directory (e.g., 'C:\\Users\\Rohit\\Documents').

                        Returns:
                        - str: Success or error message based on the outcome.
                    """,
        )
        rename_files_to_episodes_tool = FunctionTool.from_defaults(
            fn=self.rename_files_to_episodes,
            description="""
                        Opens a directory in the system's file explorer using the provided full path.
                        And renames the files (episodes) to certain format.

                        Args:
                        - full_path (str): The absolute path to the directory (e.g., 'C:\\Users\\Rohit\\Documents').

                        Returns:
                        - str: Success or error message based on the outcome.
                    """,
        )

        self.tools += [
            open_app_tool,
            close_app_tool,
            open_directory_tool,
            rename_files_to_episodes_tool,
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

    def rename_files_to_episodes(self, full_path: str) -> str:
        try:
            rename_to_episodes(full_path=full_path)
            return f"Successfully renamed to Episodes."
        except Exception as e:
            return f"Failed to rename. Error: {str(e)}"
