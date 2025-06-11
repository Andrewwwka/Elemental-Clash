import pygame
import random
import sys
import cv2
import numpy as np
from transformers import pipeline
import os

# --- AI Library Initialization ---
# Initialize the text generation pipeline. This will run once at startup.
print("Loading AI text generation model (distilgpt2)...")
generator = None
try:
    # Using distilgpt2 as it's a good balance of speed and quality for this task.
    generator = pipeline('text-generation', model='distilgpt2')
    print("AI Model loaded successfully.")
except Exception as e:
    # If the model fails to load (e.g., no internet for first download), the game can still run.
    print(f"FATAL: Could not load AI model. Text generation will be disabled. Error: {e}")

pygame.init()

# Screen settings
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Elemental Clash - Wild Card Update")

# Sound and Music
try:
    pygame.mixer.init()
    pygame.mixer.music.load("assets/music.mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
except pygame.error as e:
    print(f"Warning: Could not load or play music. Error: {e}")

# Fonts
font = pygame.font.SysFont("Sans Serif", 40)
small_font = pygame.font.SysFont("Sans Serif", 30)

# Game Constants
ELEMENTS = ["Fire", "Water", "Earth", "Wild"]
element_colors = {
    "Fire": (255, 100, 100),
    "Water": (100, 100, 255),
    "Earth": (100, 200, 100),
    "Wild": (255, 255, 100)
}


# --- Asset Loading Function ---
def load_image(path, size):
    try:
        image = pygame.image.load(path)
        return pygame.transform.scale(image, size)
    except pygame.error as e:
        print(f"Error loading image {path}: {e}")
        # Return a gray box as a placeholder if an image is missing
        placeholder = pygame.Surface(size)
        placeholder.fill((128, 128, 128))
        return placeholder


# Load all images
background = load_image("assets/background.png", (WIDTH, HEIGHT))
menu_bg = load_image("assets/main_menu.png", (WIDTH, HEIGHT))
fire_card_img = load_image("assets/fire_card.png", (120, 165))
water_card_img = load_image("assets/water_card.png", (120, 165))
earth_card_img = load_image("assets/earth_card.png", (120, 165))
wild_card_img = load_image("assets/wild_card.png", (120, 165))

# --- Game State Variables ---
player_hand = []
player_wins = {}
ai_wins = {}
selected_card = None
ai_card = None
winner_text = ""
game_over = False
choose_element_mode = False
running = True
in_main_menu = True
in_rules_screen = False

# --- UI Element Rectangles ---
battle_box = pygame.Rect(WIDTH // 2 - 200, HEIGHT // 2 - 100, 400, 200)
play_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 50)
rules_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 50)
main_menu_quit_button = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50)
quit_button = pygame.Rect(WIDTH - 150, HEIGHT // 2 - 20, 100, 40)
back_button = pygame.Rect(WIDTH // 2 - 50, HEIGHT - 100, 100, 40)
reset_button = pygame.Rect(50, HEIGHT // 2 - 20, 100, 40)
fire_button = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 160, 80, 40)
water_button = pygame.Rect(WIDTH // 2 - 40, HEIGHT // 2 + 160, 80, 40)
earth_button = pygame.Rect(WIDTH // 2 + 70, HEIGHT // 2 + 160, 80, 40)


# --- AI Message Generation with Advanced Prompting ---
def generate_ai_message(winner):
    # If the AI model failed to load at startup, return a simple default message.
    if generator is None:
        return f"{winner} is victorious!"

    # --- New, Long, Detailed "Few-Shot" Prompts ---
    if winner == "Player":
        # This prompt shows the AI exactly how to behave by giving it high-quality examples to copy.
        prompt = """
You are a machine that generates inspiring quotes for game winners. You must follow the format exactly.

---
Instruction: Provide a quote about overcoming great odds.
Quote: "The difference between the impossible and the possible lies in a person's determination."
---
Instruction: Provide a quote about the reward for hard work.
Quote: "The fruits of victory are sweetest to those who have known the bitterness of toil."
---
Instruction: Provide a quote about a player's triumphant victory.
Quote:"""
        default_fallback = "A well-earned victory!"

    else:  # AI wins
        # This prompt trains the AI to be cold and logical by showing it examples.
        prompt = """
You are a machine that generates cold, logical statements for an AI that has won a game. You must follow the format exactly.

---
Instruction: Provide a statement about the certainty of your calculations.
Statement: "Every outcome was simulated; this victory was the only statistical probability."
---
Instruction: Provide a statement dismissing the opponent's effort.
Statement: "Hope is not a viable strategy against a superior processing power."
---
Instruction: Provide a statement about your inevitable win.
Statement:"""
        default_fallback = "Victory was the only logical outcome."

    try:
        outputs = generator(
            prompt,
            max_new_tokens=25,  # Max length for the *new* text only
            num_return_sequences=1,
            truncation=True,
            pad_token_id=generator.tokenizer.eos_token_id,
            temperature=0.65  # Lower temperature for more focused, less random output
        )

        # --- Clean up the AI's complex output ---
        full_text = outputs[0]['generated_text']
        new_text = full_text.replace(prompt, "").strip()
        final_quote = new_text.split('\n')[0].split('---')[0].strip()
        final_quote = final_quote.strip(' "')

        # If the result is too short, it's likely an error, so use the fallback.
        if len(final_quote.split()) < 3:
            print(f"AI output '{final_quote}' was too short, using fallback.")
            return default_fallback

        return final_quote

    except Exception as e:
        print(f"Error during AI text generation: {e}")
        return default_fallback  # Return fallback on any error


# --- Game Logic and Drawing Functions ---

def draw_wrapped_text(surface, text, color, rect, font, aa=True):
    rect = pygame.Rect(rect)
    y = rect.top
    line_spacing = -2
    font_height = font.size("Tg")[1]
    while text:
        i = 1
        if y + font_height > rect.bottom: break
        while font.size(text[:i])[0] < rect.width and i < len(text): i += 1
        if i < len(text): i = text.rfind(" ", 0, i) + 1
        image = font.render(text[:i], aa, color)
        surface.blit(image, (rect.left, y))
        y += font_height + line_spacing
        text = text[i:]


def create_random_card_data():
    if random.random() < 0.05:  # Slightly higher chance for Wild cards
        return {"element": "Wild", "number": random.randint(1, 10)}
    else:
        return {"element": random.choice(ELEMENTS[:-1]), "number": random.randint(1, 10)}


def create_card(card_data, x, y):
    return {"rect": pygame.Rect(x, y, 100, 150), "data": card_data}


def draw_card(card):
    if card["data"]["element"] == "Fire":
        image = fire_card_img
    elif card["data"]["element"] == "Water":
        image = water_card_img
    elif card["data"]["element"] == "Earth":
        image = earth_card_img
    else:
        image = wild_card_img

    screen.blit(image, card["rect"].topleft)
    number_font = pygame.font.SysFont("Sans Serif", 30, bold=True)
    number_text = number_font.render(str(card["data"]["number"]), True, (255, 255, 255))
    # Corrected number placement as per user preference
    num_x = card["rect"].x + (38 - number_text.get_width()) // 2
    num_y = card["rect"].y + 8
    screen.blit(number_text, (num_x, num_y))


def draw_text(text, x, y, color=(255, 255, 255), font_to_use=font):
    screen.blit(font_to_use.render(text, True, color), (x, y))


def get_result(player, ai):
    e1, n1 = player["element"], player["number"]
    e2, n2 = ai["element"], ai["number"]
    if e1 == "Wild" and e2 != "Wild": return "Player Wins"
    if e2 == "Wild" and e1 != "Wild": return "AI Wins"
    if e1 == e2: return "Player Wins" if n1 > n2 else "AI Wins" if n2 > n1 else "Draw"
    wins = {"Fire": "Earth", "Water": "Fire", "Earth": "Water"}
    return "Player Wins" if wins.get(e1) == e2 else "AI Wins"


def play_cutscene(video_path):
    if not os.path.exists(video_path):
        print(f"Warning: Cutscene file not found at {video_path}")
        return
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video file: {video_path}")
        return
    # Use the video's actual FPS for correct playback speed
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    clock = pygame.time.Clock()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        for event in pygame.event.get():
            if event.type in [pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]:
                cap.release()
                return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pygame_frame = pygame.surfarray.make_surface(np.rot90(frame_rgb))
        scaled_frame = pygame.transform.scale(pygame_frame, (WIDTH, HEIGHT))
        screen.blit(scaled_frame, (0, 0))
        pygame.display.update()
        clock.tick(fps)
    cap.release()


def deal_hand():
    global player_hand
    card_spacing = (WIDTH - 6 * 100) // 7
    player_hand = [create_card(create_random_card_data(), card_spacing + i * (100 + card_spacing), HEIGHT - 220) for i
                   in range(6)]


def check_winner():
    if any(v >= 3 for v in player_wins.values()) or all(v >= 1 for v in player_wins.values()): return "Player"
    if any(v >= 3 for v in ai_wins.values()) or all(v >= 1 for v in ai_wins.values()): return "AI"
    return None


def main_menu():
    screen.blit(menu_bg, (0, 0))
    draw_text("Elemental Clash", WIDTH // 2 - 150, HEIGHT // 2 - 200)
    pygame.draw.rect(screen, (100, 200, 100), play_button)
    draw_text("Play", play_button.centerx - 40, play_button.centery - 20)
    pygame.draw.rect(screen, (100, 100, 200), rules_button)
    draw_text("Rules", rules_button.centerx - 45, rules_button.centery - 20)
    pygame.draw.rect(screen, (200, 100, 100), main_menu_quit_button)
    draw_text("Quit", main_menu_quit_button.centerx - 40, main_menu_quit_button.centery - 20)


def rules_screen():
    screen.fill((30, 30, 60))
    draw_text("Rules", WIDTH // 2 - 60, 50)
    rules_rect = pygame.Rect(50, 150, WIDTH - 100, HEIGHT - 250)
    rules_text = "Elemental Clash has Fire, Water, Earth, & Wild cards. Fire beats Earth, Earth beats Water, and Water beats Fire. Each card also has a number (1-10) for tiebreaks. If elements are the same, the higher number wins. Wild cards beat any other element. After a Wild card wins, you pick which element win to claim. First to get 3 wins of one element, OR 1 of each, wins the game!"
    draw_wrapped_text(screen, rules_text, (255, 255, 255), rules_rect, small_font)
    pygame.draw.rect(screen, (200, 200, 200), back_button)
    draw_text("Back", back_button.centerx - 40, back_button.centery - 20, color=(0, 0, 0))


def reset_game():
    global player_wins, ai_wins, selected_card, ai_card, winner_text, game_over, choose_element_mode
    player_wins, ai_wins = {e: 0 for e in ELEMENTS[:-1]}, {e: 0 for e in ELEMENTS[:-1]}
    selected_card, ai_card, winner_text = None, None, ""
    game_over, choose_element_mode = False, False
    deal_hand()


# --- Main Game Setup ---
reset_game()
clock = pygame.time.Clock()

# ==================================
# =========== MAIN LOOP ============
# ==================================
while running:
    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if in_main_menu:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    play_cutscene("assets/card-cutscene.mp4")
                    in_main_menu, in_rules_screen = False, False
                    reset_game()
                elif rules_button.collidepoint(event.pos):
                    in_main_menu, in_rules_screen = False, True
                elif main_menu_quit_button.collidepoint(event.pos):
                    running = False
        elif in_rules_screen:
            if event.type == pygame.MOUSEBUTTONDOWN and back_button.collidepoint(event.pos):
                in_rules_screen, in_main_menu = False, True
        else:  # Main Game Logic
            def handle_win_condition(winner):
                global game_over, winner_text
                if winner:
                    game_over = True
                    winner_text = generate_ai_message(winner)


            if game_over:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if reset_button.collidepoint(event.pos): reset_game()
                    if quit_button.collidepoint(event.pos): running = False
            elif choose_element_mode:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    element_chosen = None
                    if fire_button.collidepoint(event.pos):
                        element_chosen = "Fire"
                    elif water_button.collidepoint(event.pos):
                        element_chosen = "Water"
                    elif earth_button.collidepoint(event.pos):
                        element_chosen = "Earth"
                    if element_chosen:
                        player_wins[element_chosen] += 1
                        choose_element_mode = False
                        handle_win_condition(check_winner())
            else:  # Regular round
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, card in enumerate(player_hand):
                        if card and card["rect"].collidepoint(event.pos):
                            selected_card = create_card(card["data"], battle_box.x + 50, battle_box.y + 25)
                            ai_card_data = create_random_card_data()
                            ai_card = create_card(ai_card_data, battle_box.x + 250, battle_box.y + 25)
                            result = get_result(card["data"], ai_card_data)
                            if result == "Player Wins":
                                if card["data"]["element"] == "Wild":
                                    choose_element_mode = True
                                else:
                                    player_wins[card["data"]["element"]] += 1
                            elif result == "AI Wins":
                                if ai_card_data["element"] == "Wild":
                                    ai_wins[random.choice(ELEMENTS[:-1])] += 1
                                else:
                                    ai_wins[ai_card_data["element"]] += 1
                            player_hand[i] = create_card(create_random_card_data(), card["rect"].x, card["rect"].y)
                            if not choose_element_mode: handle_win_condition(check_winner())
                            break

    # --- Drawing to Screen ---
    if in_main_menu:
        main_menu()
    elif in_rules_screen:
        rules_screen()
    else:
        screen.blit(background, (0, 0))
        draw_text(
            f"Player Wins - Fire: {player_wins['Fire']} | Water: {player_wins['Water']} | Earth: {player_wins['Earth']}",
            10, 10, font_to_use=small_font)
        draw_text(f"AI Wins     - Fire: {ai_wins['Fire']} | Water: {ai_wins['Water']} | Earth: {ai_wins['Earth']}", 10,
                  40, font_to_use=small_font)

        pygame.draw.rect(screen, (50, 50, 50, 128), battle_box)
        pygame.draw.rect(screen, (255, 255, 255), battle_box, 2)
        draw_text("Battle Zone", battle_box.centerx - 90, battle_box.y - 40)

        for card in player_hand:
            if card: draw_card(card)
        if selected_card: draw_card(selected_card)
        if ai_card: draw_card(ai_card)

        if choose_element_mode:
            draw_text("Your Wild Card Won! Claim a win for:", WIDTH // 2 - 280, HEIGHT // 2 + 120)
            pygame.draw.rect(screen, element_colors["Fire"], fire_button);
            draw_text("Fire", fire_button.centerx - 25, fire_button.centery - 15, color=(0, 0, 0),
                      font_to_use=small_font)
            pygame.draw.rect(screen, element_colors["Water"], water_button);
            draw_text("Water", water_button.centerx - 30, water_button.centery - 15, color=(0, 0, 0),
                      font_to_use=small_font)
            pygame.draw.rect(screen, element_colors["Earth"], earth_button);
            draw_text("Earth", earth_button.centerx - 30, earth_button.centery - 15, color=(0, 0, 0),
                      font_to_use=small_font)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA);
            overlay.fill((0, 0, 0, 180));
            screen.blit(overlay, (0, 0))
            text_rect = pygame.Rect(100, HEIGHT // 2 - 100, WIDTH - 200, 200)
            draw_wrapped_text(screen, winner_text, (255, 215, 0), text_rect, font)
            pygame.draw.rect(screen, (100, 200, 100), reset_button);
            draw_text("Reset", reset_button.centerx - 40, reset_button.centery - 20)
            pygame.draw.rect(screen, (200, 100, 100), quit_button);
            draw_text("Quit", quit_button.centerx - 35, quit_button.centery - 20)

    pygame.display.flip()
    clock.tick(60)

# --- Cleanup ---
pygame.quit()
sys.exit()