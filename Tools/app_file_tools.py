from llama_index.core.tools import FunctionTool
import AppOpener


class AppAndFileTools:
    def __init__(self):
        self.tools = []

        open_app_tool = FunctionTool.from_defaults(
            fn=self.open_app,
            description="""Opens a known app (e.g., 'whatsapp', 'brave', 'microsoft store', etc..) in the user's system if exists using the app_name string.""",
        )
        close_app_tool = FunctionTool.from_defaults(
            fn=self.close_app,
            description="""Closes a known app (e.g., 'whatsapp', 'brave', 'microsoft store', etc..) in the user's system if it is opened using the app_name string.""",
        )

        self.tools += [
            open_app_tool,
            close_app_tool,                                                                                          
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
