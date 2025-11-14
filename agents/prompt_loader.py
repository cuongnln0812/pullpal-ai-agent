import os

def load_prompt(filename: str) -> str:
    """
    Load a prompt from the 'prompts' directory.

    Args:
        filename (str): The name of the prompt file.

    Returns:
        str: The content of the prompt file.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    prompts_dir = os.path.join(current_dir, '..', 'prompts')
    prompt_path = os.path.join(prompts_dir, filename)
    with open(prompt_path, 'r', encoding='utf-8') as f:
        return f.read()