
# autocommit

**autocommit** is a Python utility for automatically generating smart commit messages using AI. It analyzes your staged code changes and creates a meaningful commit message in English that follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.


## Features

- **Automatic Commit Generation:** Instantly creates a commit title and description based on your staged changes.
- **Conventional Commits:** Messages follow the popular Conventional Commits standard for better commit history.
- **AI Model Integration:** Works with various AI models via API (OpenRouter by default, easily extendable).
- **Handles Large Diffs:** Compresses and summarizes large diffs before sending to the AI.
- **Smart Context Adaptation:** Automatically detects the model's context size and adjusts the data sent.
- **Interactive Confirmation:** Always shows you the generated message for review and confirmation before committing.


## How It Works

1.  The script retrieves changes from the Git index (`git diff --staged`).
2.  The prepared diff is sent to an AI model for analysis.
3.  The AI generates a commit message in English.
4.  You preview the message and confirm or cancel the commit.
5.  After confirmation, the commit is created automatically.


## Requirements

- Python 3 and Git must be installed.
- It is recommended to use this tool on Linux for best performance and compatibility.


## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/rozeraf/autocommit.git
    cd autocommit
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure environment variables:**
    Create a `.env` file in the project root and add your API key. For example:
    ```env
    # Get your free key from https://openrouter.ai/
    OPENROUTER_API_KEY="sk-or-v1-..."
    # Optionally, set a specific model and endpoint:
    OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
    OPENROUTER_API_URL="https://openrouter.ai/api/v1/chat/completions"
    ```


## Supported API Providers

### Tested providers

| Provider    | Endpoint URL                      | Documentation                  |
|-------------|-----------------------------------|---------------------------------|
| OpenRouter  | `https://openrouter.ai/api/v1/`   | [Docs](https://openrouter.ai/docs) |

You can configure the API endpoint and model by setting these variables in your `.env`:
```env
OPENROUTER_API_URL="https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL="meta-llama/llama-3.1-8b-instruct"
```


## Usage

1.  **Stage files for commit:**
    ```bash
    git add <file1> <file2> ...
    ```
2.  **Run the script:**
    ```bash
    python main.py
    ```
3.  **Review and confirm:**
    The generated commit message will be shown. Confirm to create the commit, or cancel to abort.

You can also use `python main.py --test-api` to check your API key and connection.
