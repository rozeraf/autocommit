# autocommit

A Python utility for automatically generating commit messages using AI. The script analyzes staged code changes and creates a meaningful commit message in English that follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## Key Features

- **Automatic Commit Generation:** Creates a commit title and description based on the analysis of `git diff --staged`.
- **Conventional Commits Support:** Generated messages adhere to the widely accepted standard, improving the readability of commit history.
- **Works with AI Models:** Integrates with various models via APIs (OpenRouter by default).
- **Handles Large Changes:** Compresses the `diff` before sending it to the AI if it exceeds a certain limit.
- **Dynamic Adaptation:** Automatically detects the model's maximum context size and adjusts the amount of data sent.
- **Interactive Confirmation:** Displays the generated message for user confirmation before creating the commit.

## How It Works

1.  The script retrieves changes from the Git index (`git diff --staged`).
2.  The prepared `diff` is sent to an AI model for analysis.
3.  The AI generates a commit message in English.
4.  A preview of the message is displayed to the user with a confirmation prompt.
5.  After confirmation, the commit is created.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/rozeraf/autocommit.git
    cd autocommit
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment variables. Create a `.env` file in the project root and add your API key. For example:
    ```env
    # Get your free key from https://openrouter.ai/
    OPENROUTER_API_KEY="sk-or-v1-..."
    ```

## Supported API Providers

### Tested providers:

| Provider | Endpoint URL | Documentation |
|---|---|---|
| OpenRouter | `https://openrouter.ai/api/v1/` | [Docs](https://openrouter.ai/docs) |

You can configure the API endpoint and model by setting the following environment variables:
```env
OPENROUTER_API_BASE="https://openrouter.ai/api/v1"
OPENROUTER_MODEL="meta-llama/llama-3.1-8b-instruct"
```

## Usage

1.  Stage files for commit:
    ```bash
    git add <file1> <file2> ...
    ```
2.  Run the script:
    ```bash
    python main.py
    ```
3.  Review the generated message and confirm the commit.
