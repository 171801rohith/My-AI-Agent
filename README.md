# My-AI-Agent

A Python-based AI agent platform designed for interactive chat and voice-based experiences. This repository provides the foundational components for building, configuring, and running conversational agents that can process text and audio inputs, generate intelligent responses, and interact using various tools and models.

## Features

- **Live Chat and Voice Chat**: Supports both real-time text-based and voice-based conversations.
- **Modular Agents**: Easily add or customize agents for different use cases.
- **Extensible Tools**: Integrate custom tools for enhanced agent capabilities.
- **Audio Input/Output**: Handles audio data for speech-to-text and text-to-speech.
- **Configurable Architecture**: Store and manage configuration and model data for flexible agent behavior.

## Repository Structure

```
.
├── Agents/           # Agent definitions and logic
├── Functions/        # Utility and processing functions
├── Tools/            # Tools and plugins for agent enhancement
├── config/           # Configuration files and settings
├── input_audios/     # Directory for input audio files
├── output_audios/    # Directory for output audio files
├── main_live_chat.py # Entry point for live chat interface
├── main_voice_chat.py# Entry point for voice chat interface
├── .gitignore
├── .python-version
├── pyproject.toml    # Dependencies and Python project configuration
├── uv.lock           # Package lock file
├── test.py           # Test scripts
└── README.md
```

## Getting Started

### Prerequisites

- Python (see `.python-version` for specific version)
- Dependencies listed in `pyproject.toml`

### Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/171801rohith/My-AI-Agent.git
    cd My-AI-Agent
    ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    Or use the preferred method from `pyproject.toml`.

### Usage

- **Live Chat**:  
  Run the following to start the live chat agent:
  ```bash
  python main_live_chat.py
  ```

- **Voice Chat**:  
  For interactive voice conversations:
  ```bash
  python main_voice_chat.py
  ```

## Customization

- Add or modify agents in the `Agents/` directory.
- Enhance agent abilities with new functions in `Functions/` or tools in `Tools/`.
- Adjust configuration in `config/`.
- The wake word is "Hey Jarvis" (openWakeWord, fully offline). Change `WAKE_WORD` and `THRESHOLD` in `Functions/wake_word.py`. The model files download automatically on the first run.

## Contributing

Pull requests and suggestions are welcome! Please fork the repository and submit your changes.

## License

This project currently does not specify a license.

## Author

- [171801rohith](https://github.com/171801rohith)
