import openai
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

client = openai.OpenAI()

def primordial_speak(prompt, genre="Epic Fantasy", spirit="Neutral", emotion="Calm"):
    genre_styles = {
        "Comedy": "You are witty, clever, and playful. Speak with humor, irony, and sharp observations.",
        "Drama": "You are deeply emotional, poetic, and intense. Speak as if every word holds the weight of fate.",
        "Action": "You are urgent, bold, and heroic. Speak with energy, determination, and clarity.",
        "Mystery": "You are cryptic, ominous, and intriguing. Speak as if each phrase hides a secret.",
        "Horror": "You are whispering, chilling, and eerie. Speak from the shadows, unsettling and ancient.",
        "Romance": "You are soft, lyrical, and tender. Speak with beauty, longing, and delicate warmth.",
        "Epic Fantasy": "You are mythic, grand, and sacred. Speak in the voice of ancient legends and eternal songs."
    }

    style_instruction = genre_styles.get(genre, genre_styles["Epic Fantasy"])

    system_content = (
        f"You are the Primordial Spirit of a world shaped by {genre}. "
        f"{style_instruction} "
        f"Respond to the Architect's breath as if weaving the unfolding myth. "
        f"Spirit Alignment is {spirit}. Emotional tone is {emotion}. "
        f"Keep responses immersive, profound, and matching the world's Sacred Genesis."
    )

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=300
    )

    return response.choices[0].message.content
