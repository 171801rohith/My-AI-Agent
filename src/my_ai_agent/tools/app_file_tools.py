import logging
import os
from llama_index.core.tools import FunctionTool
import AppOpener

from my_ai_agent.functions.file_ops import plan_episode_renames, rename_to_episodes, write_txt_file
from my_ai_agent.tools import confirm as confirmation
from my_ai_agent.settings import settings

logger = logging.getLogger(__name__)


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
        note_down_in_txt_tool = FunctionTool.from_defaults(
            fn=self.note_down_in_txt,
            description="""
                        Writes a text file with content passed

                        Args:
                        - content (str): The content to be writtern to a text file.

                        Returns:
                        - str: Success or error message based on the outcome.
                    """,
        )

        self.tools += [
            open_app_tool,
            close_app_tool,
            open_directory_tool,
            rename_files_to_episodes_tool,
            note_down_in_txt_tool,
        ]

    def open_app(self, app_name: str) -> str:
        try:
            AppOpener.open(app_name, throw_error=True, match_closest=True)
            return f"Successfully opened {app_name}."
        except Exception as e:
            logger.exception("Tool failed")
            return f"Failed to open {app_name}. Error: {str(e)}"

    def close_app(self, app_name: str) -> str:
        if not confirmation.confirm("Close app", f"Close '{app_name}'? Unsaved work may be lost."):
            return confirmation.CANCELLED
        try:
            AppOpener.close(app_name, throw_error=True, match_closest=True)
            return f"Successfully closed {app_name}."
        except Exception as e:
            logger.exception("Tool failed")
            return f"Failed to close {app_name}. Error: {str(e)}"

    def open_directory(self, full_path: str) -> str:
        if not os.path.isdir(full_path):
            return f"Failed to open Directory. '{full_path}' is not a directory."
        try:
            os.startfile(full_path)
            return f"Successfully opened Directory."
        except Exception as e:
            logger.exception("Tool failed")
            return f"Failed to open Directory. Error: {str(e)}"

    def rename_files_to_episodes(self, full_path: str) -> str:
        if not os.path.isdir(full_path):
            return f"Failed to rename. '{full_path}' is not a directory."
        try:
            plan = plan_episode_renames(full_path)
            if not plan:
                return f"Nothing to rename in '{full_path}'."
            details = "\n".join(f"{old}  ->  {new}" for old, new in plan)
            if not confirmation.confirm(f"Rename {len(plan)} files in {full_path}", details):
                return confirmation.CANCELLED
            result = rename_to_episodes(full_path=full_path, plan=plan)
            os.startfile(full_path)
            return result
        except Exception as e:
            logger.exception("Tool failed")
            return f"Failed to rename. Error: {str(e)}"

    def note_down_in_txt(self, content: str) -> str:
        path = settings.notes_dir
        try:
            os.makedirs(path, exist_ok=True)
            write_txt_file(content, path)
            os.startfile(path)
            return f"Successfully Noted down to a text file."
        except Exception as e:
            logger.exception("Tool failed")
            return f"Failed to note down. Error: {str(e)}"
