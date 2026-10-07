import os
import random

import streamlit as st
from dotenv import load_dotenv
from google import genai


# ==================================================
# LOAD API KEY
# ==================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        api_key = None

# Create the Gemini client
if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None


# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(
    page_title="Escape the Castle",
    page_icon="🏰",
    layout="centered"
)

st.title("🏰 Escape the Castle")


# ==================================================
# GAME SETUP FUNCTIONS
# ==================================================

def start_game(name):
    """Start a new game."""

    st.session_state.game_started = True
    st.session_state.player_name = name

    st.session_state.health = 5
    st.session_state.max_health = 5

    st.session_state.inventory = [
        "Torch"
    ]

    st.session_state.rooms = [
        "cell",
        "corridor",
        "crypt",
        "library",
        "guard_room",
        "dungeon",
        "castle_gate"
    ]

    st.session_state.room_number = 0

    st.session_state.result_type = ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""

    st.session_state.action_complete = False


def restart_game():
    """Restart the game."""

    st.session_state.clear()
    st.rerun()


def get_current_room():
    """Return the current room."""

    return st.session_state.rooms[
        st.session_state.room_number
    ]


def continue_game():
    """Move to the next room."""

    st.session_state.result_type = ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""

    st.session_state.action_complete = False

    st.session_state.room_number += 1

    st.rerun()


# ==================================================
# PLAYER FUNCTIONS
# ==================================================

def take_damage(amount):
    """Remove health from the player."""

    st.session_state.health -= amount

    if st.session_state.health < 0:
        st.session_state.health = 0


def heal_player(amount):
    """Restore health."""

    old_health = st.session_state.health

    st.session_state.health = min(
        st.session_state.max_health,
        st.session_state.health + amount
    )

    amount_healed = (
        st.session_state.health - old_health
    )

    return amount_healed


def add_item(item):
    """Add an item to the inventory."""

    if item not in st.session_state.inventory:
        st.session_state.inventory.append(item)


def remove_item(item):
    """Remove an item from the inventory."""

    if item in st.session_state.inventory:
        st.session_state.inventory.remove(item)


def has_item(item):
    """Check whether the player has an item."""

    return item in st.session_state.inventory


# ==================================================
# AI FUNCTION
# ==================================================

def generate_story(
    room,
    action,
    outcome,
    fallback_message
):
    """Ask Gemini to narrate an event."""

    if client is None:
        return fallback_message

    inventory_text = ", ".join(
        st.session_state.inventory
    )

    prompt = f"""
You are the storyteller for a dark fantasy
adventure game called Escape the Castle.

Player: {st.session_state.player_name}
Room: {room}
Health: {st.session_state.health}/{st.session_state.max_health}
Inventory: {inventory_text}

Action:
{action}

Outcome:
{outcome}

Describe what happens in 30-50 words.

Use second person.
Use atmospheric dark fantasy language.
Do not change the outcome.
Do not change health or inventory.
Do not introduce new choices.
"""

    try:

        interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            input=prompt,
            generation_config={
                "thinking_level": "minimal"
            }
        )

        if interaction.output_text:
            return interaction.output_text

        return fallback_message

    except Exception as error:

        st.error(
            f"Gemini error: {error}"
        )

        return fallback_message


# ==================================================
# GAME FUNCTIONS
# ==================================================

def roll_dice():
    """Roll a six-sided dice."""

    return random.randint(1, 6)


def set_result(
    result_type,
    message,
    value=""
):
    """Save the result of an action."""

    st.session_state.result_type = (
        result_type
    )

    st.session_state.result_message = (
        message
    )

    st.session_state.result_value = (
        value
    )

    st.session_state.action_complete = True


def chance_encounter(
    button_text,
    room,
    action,
    success_number,
    success_outcome,
    success_fallback,
    failure_outcome,
    failure_fallback,
    damage,
    bonus_item=""
):
    """
    Run an encounter decided by Python.

    Gemini narrates the result.
    """

    if st.button(button_text):

        roll = roll_dice()

        # An item can improve the dice roll
        if bonus_item != "":

            if has_item(bonus_item):
                roll += 2

        # SUCCESS
        if roll >= success_number:

            story = generate_story(
                room,
                action,
                success_outcome,
                success_fallback
            )

            set_result(
                "success",
                story
            )

        # FAILURE
        else:

            take_damage(damage)

            story = generate_story(
                room,
                action,
                failure_outcome,
                failure_fallback
            )

            set_result(
                "damage",
                story,
                damage
            )

        st.rerun()


# ==================================================
# DISPLAY FUNCTIONS
# ==================================================

def show_room(
    title,
    description
):
    """Display a room."""

    st.header(title)

    st.write(description)


def show_player_info():
    """Display player information."""

    st.sidebar.header(
        st.session_state.player_name
    )

    # Health
    st.sidebar.write(
        f"❤️ Health: "
        f"{st.session_state.health}/"
        f"{st.session_state.max_health}"
    )

    # Inventory
    st.sidebar.write(
        "🎒 Inventory"
    )

    for item in st.session_state.inventory:

        st.sidebar.write(
            f"• {item}"
        )

    st.sidebar.divider()

    # Progress
    st.sidebar.write(
        f"Room "
        f"{st.session_state.room_number + 1}"
        f" of "
        f"{len(st.session_state.rooms)}"
    )

    # AI status
    if client is not None:

        st.sidebar.success(
            "✨ AI Storyteller connected"
        )

    else:

        st.sidebar.warning(
            "AI Storyteller unavailable"
        )


def show_result():
    """Display the result of an action."""

    result_type = (
        st.session_state.result_type
    )

    message = (
        st.session_state.result_message
    )

    value = (
        st.session_state.result_value
    )

    if result_type == "item":

        st.success(
            f"🎒 NEW ITEM: {value}"
        )

    elif result_type == "damage":

        st.error(
            f"💔 DAMAGE: "
            f"You lose {value} health."
        )

    elif result_type == "heal":

        st.success(
            f"💚 HEALED: "
            f"You recover {value} health."
        )

    elif result_type == "success":

        st.success(
            "✅ Success!"
        )

    elif result_type == "story":

        st.info(
            "The journey continues..."
        )

    st.write(message)


def show_continue_button(
    text="Continue"
):
    """Display a continue button."""

    if st.button(text):

        continue_game()


# ==================================================
# INITIAL STATE
# ==================================================

if "game_started" not in st.session_state:

    st.session_state.game_started = False


# ==================================================
# START SCREEN
# ==================================================

if not st.session_state.game_started:

    st.write(
        """
        You wake in a cold stone cell beneath
        an ancient castle.

        You don't know why you are here.

        You know only one thing.
        """
    )

    st.subheader(
        "You need to escape."
    )

    player_name = st.text_input(
        "What is your name?"
    )

    if st.button(
        "Enter the Castle"
    ):

        if player_name.strip():

            start_game(
                player_name.strip()
            )

            st.rerun()

        else:

            st.warning(
                "Enter your name before starting."
            )


# ==================================================
# MAIN GAME
# ==================================================

else:

    show_player_info()

    room = get_current_room()


    # ==================================================
    # GAME OVER
    # ==================================================

    if st.session_state.health <= 0:

        show_room(
            "💀 Game Over",
            """
            Your strength finally gives out.

            The darkness of the castle
            closes around you.

            The castle has claimed
            another victim.
            """
        )

        st.error(
            "You did not escape the castle."
        )

        if st.button(
            "🔄 Try Again"
        ):

            restart_game()

        st.stop()


    # ==================================================
    # ROOM 1 - CELL
    # ==================================================

    if room == "cell":

        show_room(
            "🔒 The Cell",
            """
            You wake on the cold stone floor
            of a prison cell.

            You remember nothing about how
            you arrived here.

            Outside the bars, a torch burns
            weakly on the wall.

            You push against the iron door.

            To your surprise, it slowly
            creaks open.
            """
        )

        show_continue_button(
            "🚪 Leave the cell"
        )


    # ==================================================
    # ROOM 2 - CORRIDOR
    # ==================================================

    elif room == "corridor":

        show_room(
            "🕯️ The Corridor",
            """
            You step into a narrow stone corridor.

            At the far end, a staircase leads
            deeper into the castle.

            Beside you is an old wooden cabinet.
            """
        )

        if not st.session_state.action_complete:

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "🔎 Search the cabinet"
                ):

                    add_item(
                        "Rusty Dagger"
                    )

                    story = generate_story(
                        "The Corridor",
                        "search an old wooden cabinet",
                        (
                            "The player finds a "
                            "Rusty Dagger."
                        ),
                        (
                            "Inside the cabinet you "
                            "discover a rusty dagger. "
                            "It isn't much, but it is "
                            "better than nothing."
                        )
                    )

                    set_result(
                        "item",
                        story,
                        "Rusty Dagger"
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "➡️ Ignore it"
                ):

                    story = generate_story(
                        "The Corridor",
                        "ignore the wooden cabinet",
                        (
                            "Nothing happens. The player "
                            "continues safely."
                        ),
                        (
                            "You decide not to risk "
                            "making noise and continue "
                            "towards the staircase."
                        )
                    )

                    set_result(
                        "story",
                        story
                    )

                    st.rerun()

        else:

            show_result()

            show_continue_button()


    # ==================================================
    # ROOM 3 - CRYPT
    # ==================================================

    elif room == "crypt":

        show_room(
            "⚰️ The Crypt",
            """
            The staircase leads into
            an ancient crypt.

            Stone coffins line the walls.

            Something metallic glints
            beside one of them.
            """
        )

        if not st.session_state.action_complete:

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "🔎 Investigate"
                ):

                    roll = roll_dice()

                    if roll >= 3:

                        add_item(
                            "Iron Key"
                        )

                        story = generate_story(
                            "The Crypt",
                            (
                                "investigate the object "
                                "beside a stone coffin"
                            ),
                            (
                                "The player safely finds "
                                "an Iron Key."
                            ),
                            (
                                "You carefully approach "
                                "the coffin. On the floor "
                                "beside it lies a heavy "
                                "iron key."
                            )
                        )

                        set_result(
                            "item",
                            story,
                            "Iron Key"
                        )

                    else:

                        take_damage(1)

                        story = generate_story(
                            "The Crypt",
                            (
                                "investigate the object "
                                "beside a stone coffin"
                            ),
                            (
                                "A skeletal hand attacks "
                                "the player. The player "
                                "loses 1 health."
                            ),
                            (
                                "A skeletal hand bursts "
                                "from the coffin and "
                                "claws your arm!"
                            )
                        )

                        set_result(
                            "damage",
                            story,
                            1
                        )

                    st.rerun()

            with col2:

                if st.button(
                    "🚪 Leave the crypt"
                ):

                    story = generate_story(
                        "The Crypt",
                        "leave without investigating",
                        (
                            "The player leaves safely "
                            "without finding anything."
                        ),
                        (
                            "You decide the crypt is "
                            "best left undisturbed."
                        )
                    )

                    set_result(
                        "story",
                        story
                    )

                    st.rerun()

        else:

            show_result()

            show_continue_button()


    # ==================================================
    # ROOM 4 - LIBRARY
    # ==================================================

    elif room == "library":

        show_room(
            "📚 The Forgotten Library",
            """
            Beyond the crypt you discover
            an enormous library.

            Most of the books have
            rotted away.

            One book appears untouched.

            A faint green light shines
            from its pages.
            """
        )

        if not st.session_state.action_complete:

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "📖 Read the book"
                ):

                    roll = roll_dice()

                    if roll >= 3:

                        healed = heal_player(1)

                        if healed > 0:

                            story = generate_story(
                                "The Forgotten Library",
                                "read the glowing book",
                                (
                                    "The book magically "
                                    "heals the player by "
                                    "1 health."
                                ),
                                (
                                    "Warm light flows from "
                                    "the pages and your "
                                    "injuries begin to heal."
                                )
                            )

                            set_result(
                                "heal",
                                story,
                                healed
                            )

                        else:

                            story = generate_story(
                                "The Forgotten Library",
                                "read the glowing book",
                                (
                                    "The player is already "
                                    "at full health, so "
                                    "nothing changes."
                                ),
                                (
                                    "The book glows warmly, "
                                    "but you are already "
                                    "at full health."
                                )
                            )

                            set_result(
                                "story",
                                story
                            )

                    else:

                        take_damage(1)

                        story = generate_story(
                            "The Forgotten Library",
                            "read the glowing book",
                            (
                                "The book is cursed and "
                                "the player loses 1 health."
                            ),
                            (
                                "The writing twists across "
                                "the page. A sharp pain "
                                "tears through your head."
                            )
                        )

                        set_result(
                            "damage",
                            story,
                            1
                        )

                    st.rerun()

            with col2:

                if st.button(
                    "🚪 Leave it alone"
                ):

                    story = generate_story(
                        "The Forgotten Library",
                        "leave the glowing book alone",
                        (
                            "The player leaves the book "
                            "and continues safely."
                        ),
                        (
                            "You decide that glowing "
                            "books in abandoned castles "
                            "are best left alone."
                        )
                    )

                    set_result(
                        "story",
                        story
                    )

                    st.rerun()

        else:

            show_result()

            show_continue_button()


    # ==================================================
    # ROOM 5 - GUARD ROOM
    # ==================================================

    elif room == "guard_room":

        show_room(
            "⚔️ The Guard Room",
            """
            You enter what was once
            the castle guard room.

            An armoured figure stands
            beside the opposite door.

            Pale blue light suddenly
            appears inside its helmet.

            "No prisoner leaves this castle."
            """
        )

        if has_item(
            "Rusty Dagger"
        ):

            st.info(
                "⚔️ You grip your Rusty Dagger."
            )

        if not st.session_state.action_complete:

            col1, col2 = st.columns(2)

            with col1:

                chance_encounter(
                    "⚔️ Fight the knight",
                    "The Guard Room",
                    "fight the ghostly knight",
                    4,
                    (
                        "The player defeats the "
                        "ghostly knight and can "
                        "continue."
                    ),
                    (
                        "You dodge the knight's "
                        "sword and strike back. "
                        "The empty armour crashes "
                        "to the floor."
                    ),
                    (
                        "The knight hits the player. "
                        "The player loses 2 health "
                        "but escapes the fight."
                    ),
                    (
                        "The knight is too fast. "
                        "Its sword strikes you before "
                        "you manage to escape."
                    ),
                    2,
                    "Rusty Dagger"
                )

            with col2:

                chance_encounter(
                    "🏃 Run past",
                    "The Guard Room",
                    (
                        "attempt to run past the "
                        "ghostly knight"
                    ),
                    4,
                    (
                        "The player successfully "
                        "runs past the knight."
                    ),
                    (
                        "You sprint past the knight "
                        "and escape through the "
                        "doorway."
                    ),
                    (
                        "The player escapes but is "
                        "hit while running and loses "
                        "1 health."
                    ),
                    (
                        "You escape, but the knight's "
                        "blade catches you as you run."
                    ),
                    1
                )

        else:

            show_result()

            if st.session_state.health > 0:

                show_continue_button()


    # ==================================================
    # ROOM 6 - DUNGEON
    # ==================================================

    elif room == "dungeon":

        show_room(
            "⛓️ The Dungeon",
            """
            The passage descends into
            the castle's old dungeon.

            Among a pile of abandoned
            belongings you spot a small
            bottle filled with red liquid.
            """
        )

        if not st.session_state.action_complete:

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "🧪 Take the bottle"
                ):

                    add_item(
                        "Healing Potion"
                    )

                    story = generate_story(
                        "The Dungeon",
                        (
                            "pick up the bottle "
                            "of red liquid"
                        ),
                        (
                            "The player finds a "
                            "Healing Potion."
                        ),
                        (
                            "You pick up the bottle. "
                            "A faded label identifies "
                            "it as a Healing Potion."
                        )
                    )

                    set_result(
                        "item",
                        story,
                        "Healing Potion"
                    )

                    st.rerun()

            with col2:

                if st.button(
                    "➡️ Leave it"
                ):

                    story = generate_story(
                        "The Dungeon",
                        "leave the bottle behind",
                        (
                            "The player leaves the "
                            "potion and continues."
                        ),
                        (
                            "You leave the strange "
                            "bottle behind."
                        )
                    )

                    set_result(
                        "story",
                        story
                    )

                    st.rerun()

        else:

            show_result()

            # USE HEALING POTION
            if has_item(
                "Healing Potion"
            ):

                if (
                    st.session_state.health
                    < st.session_state.max_health
                ):

                    if st.button(
                        "🧪 Drink Healing Potion"
                    ):

                        healed = heal_player(2)

                        remove_item(
                            "Healing Potion"
                        )

                        story = generate_story(
                            "The Dungeon",
                            "drink the Healing Potion",
                            (
                                f"The potion heals the "
                                f"player by {healed} "
                                f"health."
                            ),
                            (
                                "You drink the potion. "
                                "Warmth spreads through "
                                "your body."
                            )
                        )

                        set_result(
                            "heal",
                            story,
                            healed
                        )

                        st.rerun()

            show_continue_button()


    # ==================================================
    # ROOM 7 - CASTLE GATE
    # ==================================================

    elif room == "castle_gate":

        show_room(
            "🌙 The Castle Gate",
            """
            Cold night air hits your face.

            You've reached the castle courtyard.

            Ahead stands an enormous iron gate.

            Beyond it you can see the forest.

            Freedom.
            """
        )


        # ==================================================
        # PLAYER HAS THE KEY
        # ==================================================

        if has_item(
            "Iron Key"
        ):

            st.success(
                "🔑 You have the Iron Key."
            )

            if (
                not st.session_state.action_complete
            ):

                if st.button(
                    "🔑 Unlock the gate"
                ):

                    story = generate_story(
                        "The Castle Gate",
                        (
                            "use the Iron Key to "
                            "unlock the castle gate"
                        ),
                        (
                            "The key works. The gate "
                            "opens and the player "
                            "escapes the castle."
                        ),
                        (
                            "The key turns in the "
                            "ancient lock. The gates "
                            "slowly swing open and you "
                            "step into the forest."
                        )
                    )

                    set_result(
                        "success",
                        story
                    )

                    st.rerun()

            else:

                show_result()

                st.balloons()

                st.header(
                    "🏆 YOU ESCAPED THE CASTLE!"
                )

                st.success(
                    "You survived the castle."
                )


        # ==================================================
        # PLAYER DOES NOT HAVE THE KEY
        # ==================================================

        else:

            st.error(
                "🔒 The gate is locked."
            )

            st.write(
                """
                You desperately search
                for another way out.

                Then you notice a narrow
                opening in the castle wall.

                It looks dangerous.

                But it may be your only chance.
                """
            )

            if (
                not st.session_state.action_complete
            ):

                chance_encounter(
                    (
                        "🧗 Climb through "
                        "the opening"
                    ),
                    "The Castle Gate",
                    (
                        "climb through a dangerous "
                        "opening in the ruined wall"
                    ),
                    4,
                    (
                        "The player successfully "
                        "climbs through the wall "
                        "and escapes the castle."
                    ),
                    (
                        "You squeeze through the "
                        "ruined wall and drop to "
                        "the ground outside."
                    ),
                    (
                        "The player slips while "
                        "climbing and loses 1 health. "
                        "The player does not escape."
                    ),
                    (
                        "Your foot slips and you "
                        "crash painfully against "
                        "the stone wall."
                    ),
                    1
                )

            else:

                if (
                    st.session_state.result_type
                    == "success"
                ):

                    show_result()

                    st.balloons()

                    st.header(
                        "🏆 YOU ESCAPED THE CASTLE!"
                    )

                    st.success(
                        "You survived the castle."
                    )

                else:

                    show_result()

                    if (
                        st.session_state.health > 0
                    ):

                        if st.button(
                            "🧗 Try Again"
                        ):

                            st.session_state.action_complete = False

                            st.session_state.result_type = ""
                            st.session_state.result_message = ""
                            st.session_state.result_value = ""

                            st.rerun()


        st.divider()

        if st.button(
            "🔄 Play Again"
        ):

            restart_game()
