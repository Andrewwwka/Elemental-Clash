import pygame
import random
import sys
import cv2
import numpy as np
#import openai
# openai.api_key = "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"

pygame.init()

# Screen settings
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Elemental Clash - Wild Card Update")

pygame.mixer.init()
pygame.mixer.music.load("assets/music.mp3")
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)

font = pygame.font.SysFont("Sans Serif", 40)
small_font = pygame.font.SysFont("Sans Serif", 30)  # Smaller font for text under the cards

# Elements and colors
ELEMENTS = ["Fire", "Water", "Earth", "Wild"]
element_colors = {
    "Fire": (255, 100, 100),
    "Water": (100, 100, 255),
    "Earth": (100, 200, 100),
    "Wild": (255, 255, 100)
}

# Load background and menu images
background = pygame.image.load("assets/background.png")
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

menu_bg = pygame.image.load("assets/main_menu.png")
menu_bg = pygame.transform.scale(menu_bg, (WIDTH, HEIGHT))

# Load card images
fire_card_img = pygame.image.load("assets/fire_card.png")
water_card_img = pygame.image.load("assets/water_card.png")
earth_card_img = pygame.image.load("assets/earth_card.png")
wild_card_img = pygame.image.load("assets/wild_card.png")

# Resize the images to ensure they fit within the card dimensions (100x150)
fire_card_img = pygame.transform.scale(fire_card_img, (120, 165))
water_card_img = pygame.transform.scale(water_card_img, (120, 165))
earth_card_img = pygame.transform.scale(earth_card_img, (120, 165))
wild_card_img = pygame.transform.scale(wild_card_img, (120, 165))

# Game state
player_hand = []
player_wins = {e: 0 for e in ELEMENTS[:-1]}
ai_wins = {e: 0 for e in ELEMENTS[:-1]}
selected_card = None
ai_card = None
round_result = ""
game_over = False
winner_text = ""
choose_element_mode = False
running = True
in_main_menu = True
in_rules_screen = False

# Battle zone
battle_box = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 100, 400, 200)

# Buttons
play_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 - 100, 200, 50)
rules_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2, 200, 50)
main_menu_quit_button = pygame.Rect(WIDTH//2 - 100, HEIGHT//2+100, 200, 50)
quit_button = pygame.Rect(WIDTH - 150, HEIGHT//2 - 20, 100, 40)
back_button = pygame.Rect(WIDTH//2 - 50, HEIGHT - 100, 100, 40)
reset_button = pygame.Rect(50, HEIGHT//2 - 20, 100, 40)
fire_button = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 160, 80, 40)
water_button = pygame.Rect(WIDTH//2 - 40, HEIGHT//2 + 160, 80, 40)
earth_button = pygame.Rect(WIDTH//2 + 70, HEIGHT//2 + 160, 80, 40)
back_to_menu_button = pygame.Rect(WIDTH - 90, 10, 80, 40)

def create_random_card_data():
    if random.random() < 0.03:
        return {"element": "Wild", "number": random.randint(1, 10)}
    else:
        return {"element": random.choice(ELEMENTS[:-1]), "number": random.randint(1, 10)}

def create_card(card_data, x, y):
    rect = pygame.Rect(x, y, 100, 150)
    return {"rect": rect, "data": card_data}

def draw_card(card):
    # Determine the image based on the element type
    if card["data"]["element"] == "Fire":
        image = fire_card_img
    elif card["data"]["element"] == "Water":
        image = water_card_img
    elif card["data"]["element"] == "Earth":
        image = earth_card_img
    elif card["data"]["element"] == "Wild":
        image = wild_card_img
    else:
        image = fire_card_img  # Default to fire if unknown

    # Draw the card image first
    screen.blit(image, card["rect"].topleft)

    # Choose the number color and style
    number_color = (255, 255, 255)  # White for contrast
    number_font = pygame.font.SysFont("Sans Serif", 30, bold=False)  # Bigger and bold

    # Render the number
    number_text = number_font.render(str(card["data"]["number"]), True, number_color)

    # Calculate position to place the number on top of the card art
    num_x = card["rect"].x + (38 - number_text.get_width()) // 2  # Centered horizontally
    num_y = card["rect"].y + 8  # Slightly down from the top

    # Blit the number on top of the card
    screen.blit(number_text, (num_x, num_y))


def draw_text(text, x, y, color=(255, 255, 255)):
    screen.blit(font.render(text, True, color), (x, y))

def get_result(player, ai):
    e1, e2 = player["element"], ai["element"]
    n1, n2 = player["number"], ai["number"]
    if e1 == "Wild" and e2 != "Wild":
        return "Player Wins"
    if e2 == "Wild" and e1 != "Wild":
        return "AI Wins"
    if e1 == e2:
        return "Player Wins" if n1 > n2 else "AI Wins" if n2 > n1 else "Draw"
    wins = {"Fire": "Earth", "Water": "Fire", "Earth": "Water"}
    return "Player Wins" if wins.get(e1) == e2 else "AI Wins"

def play_cutscene(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video file")
        return

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, (WIDTH, HEIGHT))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pygame_frame = pygame.surfarray.make_surface(np.rot90(frame))
        screen.blit(pygame_frame, (0, 0))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()

        pygame.time.delay(33)

    cap.release()


def deal_hand():
    global player_hand
    card_spacing = (WIDTH - 6 * 100) // 7
    player_hand = []
    for i in range(6):
        x = card_spacing + i * (100 + card_spacing)
        player_hand.append(create_card(create_random_card_data(), x, HEIGHT-220))

def check_winner():
    for wins in (player_wins, ai_wins):
        if any(v >= 3 for v in wins.values()) or all(v >= 1 for v in wins.values()):
            return "Player" if wins is player_wins else "AI"
    return None

def main_menu():
    # Use the separate main menu background
    screen.blit(menu_bg, (0, 0))
    draw_text("Elemental Clash", WIDTH//2 - 100, HEIGHT//2 - 200)
    pygame.draw.rect(screen, (100, 200, 100), play_button)
    pygame.draw.rect(screen, (100, 100, 200), rules_button)
    pygame.draw.rect(screen, (200, 100, 100), main_menu_quit_button)
    draw_text("Play", play_button.x + 70, play_button.y + 10)
    draw_text("Rules", rules_button.x + 65, rules_button.y + 10)
    draw_text("Quit", main_menu_quit_button.x + 70, main_menu_quit_button.y + 10)

def rules_screen():
    screen.fill((30, 30, 60))
    draw_text("Rules", WIDTH//2 - 30, 50)
    rules_text = [
        "In Elemental Clash, each card has an element: Fire, Water, Earth, & Wild",
        "Fire beats Earth, Earth beats Water, Water beats Fire.",
        "Each card also has a number (1-10).",
        "Cards are given numbers for tiebreaks.",
        "Wild cards can beat any card.",
        "After a Wild card wins, pick any element it counts towards",
        "The goal is to win with 1 of each element or 3 of a single element.",
    ]
    y_offset = 100
    for line in rules_text:
        draw_text(line, WIDTH//5 - 200, y_offset)
        y_offset += 50
    pygame.draw.rect(screen, (200, 200, 200), back_button)
    draw_text("Back", back_button.x + 20, back_button.y + 10)

deal_hand()
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.mixer.music.stop()
            running = False
        if in_main_menu:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(event.pos):
                    play_cutscene("assets/card-cutscene.mp4")
                    in_main_menu = False
                elif rules_button.collidepoint(event.pos):
                    in_rules_screen = True
                    in_main_menu = False
                elif main_menu_quit_button.collidepoint(event.pos):
                    running = False
        elif in_rules_screen:
            if event.type == pygame.MOUSEBUTTONDOWN and back_button.collidepoint(event.pos):
                in_rules_screen = False
                in_main_menu = True
        else:
            if not game_over and event.type == pygame.MOUSEBUTTONDOWN:
                if choose_element_mode:
                    if fire_button.collidepoint(event.pos):
                        player_wins["Fire"] += 1
                        choose_element_mode = False
                        winner = check_winner()
                        if winner:
                            game_over = True
                            winner_text = f"{winner} Wins the Game!"
                    elif water_button.collidepoint(event.pos):
                        player_wins["Water"] += 1
                        choose_element_mode = False
                        winner = check_winner()
                        if winner:
                            game_over = True
                            winner_text = f"{winner} Wins the Game!"
                    elif earth_button.collidepoint(event.pos):
                        player_wins["Earth"] += 1
                        choose_element_mode = False
                        winner = check_winner()
                        if winner:
                            game_over = True
                            winner_text = f"{winner} Wins the Game!"
                else:
                    for i, card in enumerate(player_hand):
                        if card and card["rect"].collidepoint(event.pos):
                            selected_card = create_card(card["data"], battle_box.x + 50, battle_box.y + 25)
                            ai_card_data = create_random_card_data()
                            ai_card = create_card(ai_card_data, battle_box.x + 250, battle_box.y + 25)
                            player_card_data = card["data"]
                            result = get_result(player_card_data, ai_card_data)
                            round_result = f"{player_card_data['element']} {player_card_data['number']} vs {ai_card_data['element']} {ai_card_data['number']}: {result}"
                            if result == "Player Wins":
                                if player_card_data["element"] == "Wild":
                                    choose_element_mode = True
                                else:
                                    player_wins[player_card_data["element"]] += 1
                                    winner = check_winner()
                                    if winner:
                                        game_over = True
                                        winner_text = f"{winner} Wins the Game!"
                            elif result == "AI Wins":
                                if ai_card_data["element"] == "Wild":
                                    ai_wins[random.choice(["Fire", "Water", "Earth"])] += 1
                                else:
                                    ai_wins[ai_card_data["element"]] += 1
                                winner = check_winner()
                                if winner:
                                    game_over = True
                                    winner_text = f"{winner} Wins the Game!"
                            player_hand[i] = create_card(create_random_card_data(), card["rect"].x, card["rect"].y)
                            break
            elif game_over and event.type == pygame.MOUSEBUTTONDOWN:
                if reset_button.collidepoint(event.pos):
                    player_wins = {e: 0 for e in ELEMENTS[:-1]}
                    ai_wins = {e: 0 for e in ELEMENTS[:-1]}
                    selected_card = ai_card = None
                    round_result = ""
                    winner_text = ""
                    game_over = False
                    deal_hand()
                if quit_button.collidepoint(event.pos):
                    running = False
                    pygame.quit()
                    sys.exit()


    if in_main_menu:
        main_menu()
    elif in_rules_screen:
        rules_screen()
    else:
        screen.blit(background, (0, 0))
        draw_text(f"Fire: {player_wins['Fire']} | Water: {player_wins['Water']} | Earth: {player_wins['Earth']}", 10, 10)
        draw_text(f"AI Fire: {ai_wins['Fire']} | AI Water: {ai_wins['Water']} | AI Earth: {ai_wins['Earth']}", 10, 40)
        pygame.draw.rect(screen, (50, 50, 50), battle_box)
        pygame.draw.rect(screen, (255, 255, 255), battle_box, 2)
        draw_text("Battle Zone", battle_box.x + 130, battle_box.y - 30)
        for card in player_hand:
            if card:
                draw_card(card)
        if selected_card:
            draw_card(selected_card)
        if ai_card:
            draw_card(ai_card)
        if choose_element_mode:
            pygame.draw.rect(screen, element_colors["Fire"], fire_button)
            pygame.draw.rect(screen, element_colors["Water"], water_button)
            pygame.draw.rect(screen, element_colors["Earth"], earth_button)
            draw_text("Fire", fire_button.x + 10, fire_button.y + 5)
            draw_text("Water", water_button.x + 5, water_button.y + 5)
            draw_text("Earth", earth_button.x + 5, earth_button.y + 5)
        if game_over:
            draw_text(winner_text, WIDTH//2 - 135, HEIGHT//2 - 225,(255,255,0))
            pygame.draw.rect(screen, (100, 200, 100), reset_button)
            pygame.draw.rect(screen, (200, 100, 100), quit_button)
            draw_text("Reset", reset_button.x + 20, reset_button.y + 10)
            draw_text("Quit", quit_button.x + 30, quit_button.y + 10)


    pygame.display.flip()
    clock.tick(60)
