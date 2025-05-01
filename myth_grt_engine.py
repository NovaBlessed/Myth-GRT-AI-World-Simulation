import json
import os
import datetime
from dotenv import load_dotenv
from primordial_mind import primordial_speak

# 🌌 Load environment variables (for OpenAI Key)
load_dotenv()

# 🌌 Create a new blank world
def create_new_world():
    return {
        "genre": None,
        "elements": [],
        "phenomena": [],
        "memory_log": [],
        "age_in_years": 0,
        "attention_decay_timer": 0,
        "resonance_score": 0,
        "spirit_alignment": "Neutral",
        "emotional_temperature": "restless",
        "maturity_level": "Newborn",
        "world_vitality": 100,
        "lineages": [],
        "history": []
    }

# 🌌 Load current world state
def load_world_state():
    if not os.path.exists('world_state.json'):
        return create_new_world()
    with open('world_state.json', 'r') as file:
        try:
            data = json.load(file)
            if not isinstance(data, dict) or not data:
                return create_new_world()
            return data
        except json.JSONDecodeError:
            return create_new_world()

# 🌌 Save world state
def save_world_state(state):
    if state is None:
        print("\n⚠️ Warning: Tried to save an empty world. Save aborted.\n")
        return
    with open('world_state.json', 'w') as file:
        json.dump(state, file, indent=4)

# 🌌 Log Codex entry
def log_to_codex(entry):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open('codex_log.txt', 'a') as file:
        file.write(f"[{timestamp}] {entry}\n")

# 🌑 Pre-Creation Ritual
def pre_creation_ritual(world):
    print("\n🌑 Welcome, Architect. The world stirs in the void.\n")
    print("Before it breathes, you must shape its Sacred Genesis...\n")

    print("Choose the Genre Alignment for your world:")
    genres = ["Comedy", "Drama", "Action", "Mystery", "Horror", "Romance", "Epic Fantasy", "Sci-Fi"]
    for idx, genre in enumerate(genres, start=1):
        print(f"{idx}. {genre}")
    genre_choice = int(input("\nEnter the number of your chosen Genre: "))
    chosen_genre = genres[genre_choice - 1]
    world['genre'] = chosen_genre
    print(f"\n🌿 Genre set to {chosen_genre}.\n")

    print("Choose TWO Sacred Elements that will dominate your world:")
    elements = ["Fire", "Water", "Earth", "Air", "Light", "Shadow"]
    for idx, element in enumerate(elements, start=1):
        print(f"{idx}. {element}")
    first_element = int(input("\nEnter the number of your FIRST Element: "))
    second_element = int(input("Enter the number of your SECOND Element: "))
    world['elements'] = [elements[first_element - 1], elements[second_element - 1]]
    print(f"\n🌿 Elements set to {world['elements'][0]} and {world['elements'][1]}.\n")

    print("Choose up to TWO Phenomena Seeds to weave into your world (or press Enter to skip):")
    phenomena = ["Flight", "Telepathy", "Alchemy", "Dreamwalking", "Time Distortion"]
    for idx, phenomenon in enumerate(phenomena, start=1):
        print(f"{idx}. {phenomenon}")
    phenomena_input = input("\nEnter numbers separated by commas (or leave blank): ")
    if phenomena_input.strip():
        indices = [int(x.strip()) for x in phenomena_input.split(",")]
        world['phenomena'] = [phenomena[i - 1] for i in indices if 1 <= i <= len(phenomena)]
        print(f"\n🌿 Phenomena seeded: {', '.join(world['phenomena'])}.\n")
    else:
        print("\n🌿 No Phenomena seeded. A natural world shall unfold.\n")

    print("🌑 The Sacred Genesis is complete. Primordia begins to breathe...\n")
    return world

# 🌑 Sacred Laws Engine
def apply_sacred_laws(world, breath=None):
    genre = world.get('genre', 'Undecided')

    # 🔥 Law of Resonance & Reflection
    if breath:
        lower_breath = breath.lower()
        if genre == "Drama":
            if "love" in lower_breath:
                world['spirit_alignment'] = "Bittersweet"
            elif "betray" in lower_breath:
                world['spirit_alignment'] = "Turbulent"

        # General tone impact
        if any(word in lower_breath for word in ["peace", "garden", "create", "build", "bless", "hope"]):
            world['spirit_alignment'] = "Harmonious"
            world['world_vitality'] = min(world['world_vitality'] + 5, 100)
        elif any(word in lower_breath for word in ["war", "burn", "curse", "destroy", "break", "fear"]):
            world['spirit_alignment'] = "Chaotic"
            world['world_vitality'] = max(world['world_vitality'] - 5, 0)
        else:
            world['spirit_alignment'] = "Neutral"

    # 🔄 Law of Attention & Emergence
    if world['attention_decay_timer'] > 3:
        world['memory_log'].append({
            "event": "Emergent Phenomenon",
            "timestamp": f"{world['age_in_years']} Years",
            "details": "Something new arises from the silence."
        })
        world['attention_decay_timer'] = 0

    return world

# 🌑 World Update based on Breath
def apply_world_update(breath, world):
    try:
        # ✨ Genre-specific flavor boost
        genre_tweaks = {
            "Horror": "Describe terrifying, grotesque transformations and dark omens.",
            "Comedy": "Describe absurd, hilarious events with quirky creatures.",
            "Action": "Describe intense battles, rapid growth, and heroic feats.",
            "Mystery": "Describe cryptic discoveries and hidden prophecies.",
            "Romance": "Describe deep connections and heartfelt transformations."
        }
        extra_flavor = genre_tweaks.get(world.get('genre'), "")

        world_update = primordial_speak(
            prompt=(
                f"The world of Primordia just received this breath: '{breath}'. "
                "Describe how it changes the world in clear, vivid, tangible ways. "
                f"{extra_flavor} "
                "Speak to the land, people, spirit, and destiny."
            ),
            genre=world.get('genre', 'Epic Fantasy'),
            spirit=world.get('spirit_alignment', 'Neutral'),
            emotion=world.get('emotional_temperature', 'curious')
        )

        event = {
            "event": "World Update",
            "timestamp": f"{world['age_in_years']} Years",
            "details": world_update.strip()
        }
        world['memory_log'].append(event)

        # 🚩 Law of Irreversibility: Log every breath permanently
        world['history'].append({
            "timestamp": f"{world['age_in_years']} Years",
            "breath": breath
        })

        return world, [event]

    except Exception as e:
        print(f"\n⚠️ Error creating world update: {e}\n")
        return world, []

# 🌑 Sacred Chosen Lineage with Purpose
def create_chosen_lineage_by_presence(world):
    if not world.get('lineages'):
        lineage_name = primordial_speak(
            prompt="A new chosen people are born. What shall they be called?",
            genre=world.get('genre', 'Epic Fantasy'),
            spirit=world.get('spirit_alignment', 'Neutral'),
            emotion=world.get('emotional_temperature', 'calm')
        ).strip().split('\n')[0]

        purpose_prompt = primordial_speak(
            prompt="Describe the sacred purpose of this new lineage (builders, healers, warriors, thinkers, etc.).",
            genre=world.get('genre', 'Epic Fantasy'),
            spirit=world.get('spirit_alignment', 'Neutral'),
            emotion=world.get('emotional_temperature', 'calm')
        ).strip().split('\n')[0]

        lineage = {
            "name": lineage_name,
            "purpose": purpose_prompt,
            "spirit_trait": world.get('spirit_alignment', 'Neutral'),
            "status": "Emerging",
            "current_struggle": "Finding their path."
        }
        world['lineages'].append(lineage)

        print(f"\n🌿 A Chosen People Emerges: {lineage['name']} with purpose: {purpose_prompt}")
        return world
    return world

# 🌑 Breath Engine
def breathe():
    print("\nWelcome, Architect. Primordia listens...\n")
    world = load_world_state()

    if not world:
        world = create_new_world()

    if world.get('maturity_level', 'Newborn') == "Newborn" and not world.get('genre'):
        world = pre_creation_ritual(world)
        save_world_state(world)

    while True:
        breath = input("\nSpeak your breath (or type 'exit' to leave): ").strip()

        if breath.lower() == 'exit':
            print("\nPrimordia sleeps, awaiting your return...\n")
            break

        world['age_in_years'] += 1
        world['attention_decay_timer'] = 0

        world = apply_sacred_laws(world, breath)
        save_world_state(world)

        # 🌌 Sacred World Update
        world, updates = apply_world_update(breath, world)
        save_world_state(world)

        # 🌌 Print updates
        for update in updates:
            print(f"\n🌌 {update['event']} 🌌\n{update['details']}\n")

        # 🌿 Lineage check
        if world['maturity_level'] == "Adolescent" and not world.get('lineages'):
            world = create_chosen_lineage_by_presence(world)
            save_world_state(world)

        # 🌌 Primordial Speak (Direct Response)
        world_response = primordial_speak(
            prompt=breath,
            genre=world.get('genre', 'Epic Fantasy'),
            spirit=world.get('spirit_alignment', 'Neutral'),
            emotion=world.get('emotional_temperature', 'curious')
        )

        print(f"\nPrimordia speaks:\n{world_response}\n")

# 🌌 Sacred Start
if __name__ == "__main__":
    breathe()
