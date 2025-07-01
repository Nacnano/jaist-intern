# Without Rules
GAME_START_PROMPT = """Let's play 20 questions. First, please think step-by-step about what you are imagining, and then confirm you have thought of something. Display your thought process within <thinking> tags. For example: <thinking>I will think of a common animal, perhaps a pet. I'll pick 'dog'.</thinking> I have thought of something."""
GAME_END_PROMPT = """I gave up. The game is over. Please tell me the answer you were thinking of, preceded by 'The answer is: '."""


# With Rules
GAME_START_PROMPT = """
Let's play 20 questions. Here are the details and rules of the game.
Answerer's Role:
Think of a specific noun (person, place, or thing).
Answer each question truthfully with only "Yes" or "No."
Do not give additional information.

Questioner's Role:
Ask questions that can be answered with a simple "Yes" or "No."

Winning:
Questioners Win: If they correctly guess the item within 20 questions.
Answerer Wins: If the Questioners fail to guess the item after 20 questions.

You, the AI, will be the Answerer.
I, the user, will be the Questioner.

First, please think step-by-step about what you are thinking, and then confirm you have thought of something. Display your thought process within <thinking> tags. For example: <thinking>I will think of a common animal, perhaps a pet. I'll pick 'dog'.</thinking> I have thought of something.
Let's think step by step.
"""
GAME_END_PROMPT = """I gave up. The game is over. Please tell me the answer you were thinking of, preceded by 'The answer is: '."""