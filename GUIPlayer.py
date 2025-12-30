"""
GUI Player for Jaipur using pygame.
Click-based interface for playing against AI.
"""
import pygame
import pygame.freetype
import os
import sys

from Player import Player


class GUIPlayer(Player):
    """A pygame-based GUI player for Jaipur."""

    # Window and layout constants
    WINDOW_SIZE = (1100, 650)
    CARD_SIZE = (72, 100)
    CARD_SPACING = 10

    # Colors
    BG_COLOR = (34, 85, 51)  # Green felt table
    PANEL_COLOR = (45, 100, 62)
    TEXT_COLOR = (255, 255, 255)
    HIGHLIGHT_COLOR = (255, 215, 0)  # Gold
    BUTTON_COLOR = (139, 69, 19)  # Brown
    BUTTON_HOVER_COLOR = (160, 90, 40)
    BUTTON_TEXT_COLOR = (255, 255, 255)
    ERROR_COLOR = (255, 80, 80)
    CAMEL_BG_COLOR = (60, 110, 75)  # Slightly different green for camel area

    # Layout positions
    MARKET_Y = 250
    PLAYER_HAND_Y = 450
    PLAYER_CAMELS_Y = 450
    OPPONENT_HAND_Y = 50
    DECK_X = 60
    TOKEN_PANEL_X = 850
    BUTTON_Y = 580
    MAIN_AREA_X = 150  # Left margin for main card area

    # Card type to image file mapping
    CARD_IMAGES = {
        "leather": "cardleather.png",
        "spice": "cardspice.png",
        "cloth": "cardcloth.png",
        "silver": "cardsilver.png",
        "gold": "cardgold.png",
        "diamond": "carddiamonds.png",
        "camel": "cardcamelv.png",
        "back": "cardback.png"
    }

    def __init__(self, game_engine):
        super().__init__(game_engine)

        # Get asset directory
        self._base_dir = os.path.dirname(os.path.abspath(__file__))
        self._img_dir = os.path.join(self._base_dir, "game_pieces")

        # Initialize pygame
        pygame.init()
        pygame.freetype.init()

        self._screen = pygame.display.set_mode(self.WINDOW_SIZE)
        pygame.display.set_caption("Jaipur")
        self._clock = pygame.time.Clock()

        # Load fonts
        self._font = pygame.freetype.SysFont("Arial", 18)
        self._font_large = pygame.freetype.SysFont("Arial", 24)
        self._font_small = pygame.freetype.SysFont("Arial", 14)

        # Load card images
        self._card_images = {}
        for card_type, filename in self.CARD_IMAGES.items():
            path = os.path.join(self._img_dir, filename)
            img = pygame.image.load(path).convert_alpha()
            self._card_images[card_type] = pygame.transform.scale(img, self.CARD_SIZE)

        # Selection state
        self._selected_hand = []  # Indices of selected cards in hand (goods only)
        self._selected_market = []  # Indices of selected cards in market

        # UI state
        self._status_message = ""
        self._status_timer = 0
        self._action_complete = False

        # Create button rects
        self._buttons = self._create_buttons()

    def _create_buttons(self):
        """Create action button rectangles."""
        button_width = 110
        button_height = 40
        button_spacing = 15
        start_x = 100

        buttons = {
            "camels": pygame.Rect(start_x, self.BUTTON_Y, button_width, button_height),
            "grab": pygame.Rect(start_x + (button_width + button_spacing), self.BUTTON_Y, button_width, button_height),
            "sell": pygame.Rect(start_x + 2 * (button_width + button_spacing), self.BUTTON_Y, button_width, button_height),
            "trade": pygame.Rect(start_x + 3 * (button_width + button_spacing), self.BUTTON_Y, button_width, button_height),
        }
        return buttons

    def _split_hand(self, hand):
        """Split hand into goods and camels."""
        goods = [(i, card) for i, card in enumerate(hand) if card != "camel"]
        camels = [(i, card) for i, card in enumerate(hand) if card == "camel"]
        return goods, camels

    def take_action(self):
        """Main game loop for player's turn."""
        self._action_complete = False
        self._selected_hand = []
        self._selected_market = []
        self._status_message = "Your turn! Select an action."

        while not self._action_complete:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self._handle_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        # Clear selection
                        self._selected_hand = []
                        self._selected_market = []
                        self._status_message = "Selection cleared."

            # Update status timer
            if self._status_timer > 0:
                self._status_timer -= 1

            # Render
            self._render()
            pygame.display.flip()
            self._clock.tick(30)

    def _handle_click(self, pos):
        """Handle mouse click at position."""
        game_state = self.game_engine.get_state()

        # Check button clicks
        for button_name, rect in self._buttons.items():
            if rect.collidepoint(pos):
                self._handle_button_click(button_name, game_state)
                return

        # Check hand card clicks (goods only)
        goods, _ = self._split_hand(game_state['my_hand'])
        hand_rects = self._get_hand_card_rects(goods)
        for i, rect in enumerate(hand_rects):
            if rect.collidepoint(pos):
                original_idx = goods[i][0]  # Get original index in full hand
                card_type = goods[i][1]
                self._toggle_hand_selection_by_type(game_state['my_hand'], card_type)
                return

        # Check market card clicks
        market_rects = self._get_market_card_rects(game_state['market'])
        for i, rect in enumerate(market_rects):
            if rect.collidepoint(pos):
                self._toggle_market_selection(i)
                return

    def _toggle_hand_selection_by_type(self, hand, card_type):
        """Toggle selection of all cards of a type in hand."""
        # Get all indices of this card type (excluding camels)
        indices_of_type = [i for i, card in enumerate(hand) if card == card_type and card != "camel"]

        # Check if any of these are already selected
        any_selected = any(idx in self._selected_hand for idx in indices_of_type)

        if any_selected:
            # Deselect all of this type
            self._selected_hand = [idx for idx in self._selected_hand if idx not in indices_of_type]
        else:
            # Select all of this type
            for idx in indices_of_type:
                if idx not in self._selected_hand:
                    self._selected_hand.append(idx)

        self._selected_hand.sort()

    def _toggle_market_selection(self, index):
        """Toggle selection of a card in market."""
        if index in self._selected_market:
            self._selected_market.remove(index)
        else:
            self._selected_market.append(index)
        self._selected_market.sort()

    def _handle_button_click(self, button_name, game_state):
        """Handle action button click."""
        success = False

        if button_name == "camels":
            success = self.game_engine.do_action("c")
            if not success:
                self._show_error("No camels in market!")

        elif button_name == "grab":
            if len(self._selected_market) != 1:
                self._show_error("Select exactly 1 market card to grab.")
                return
            market_idx = self._selected_market[0]
            if game_state['market'][market_idx] == "camel":
                self._show_error("Can't grab a camel! Use Take Camels.")
                return
            success = self.game_engine.do_action("g", grab_idx=market_idx)
            if not success:
                self._show_error("Can't grab - hand full (7 cards)!")

        elif button_name == "sell":
            if len(self._selected_hand) == 0:
                self._show_error("Select cards from your hand to sell.")
                return
            success = self.game_engine.do_action("s", sell_idx=self._selected_hand)
            if not success:
                self._show_error("Invalid sell! Same type only, 2+ for gems.")

        elif button_name == "trade":
            if len(self._selected_hand) < 2 or len(self._selected_market) < 2:
                self._show_error("Select 2+ cards from hand AND market.")
                return
            if len(self._selected_hand) != len(self._selected_market):
                self._show_error("Must trade equal numbers!")
                return
            success = self.game_engine.do_action(
                "t",
                trade_in=self._selected_market,
                trade_out=self._selected_hand
            )
            if not success:
                self._show_error("Invalid trade! Check rules.")

        if success:
            self._action_complete = True
            self._selected_hand = []
            self._selected_market = []

    def _show_error(self, message):
        """Show an error message."""
        self._status_message = message
        self._status_timer = 90  # 3 seconds at 30 FPS

    def _get_hand_card_rects(self, goods):
        """Get rectangles for goods cards in hand."""
        rects = []
        if not goods:
            return rects

        total_width = len(goods) * (self.CARD_SIZE[0] + self.CARD_SPACING) - self.CARD_SPACING
        start_x = self.MAIN_AREA_X

        for i in range(len(goods)):
            x = start_x + i * (self.CARD_SIZE[0] + self.CARD_SPACING)
            y = self.PLAYER_HAND_Y
            original_idx = goods[i][0]
            if original_idx in self._selected_hand:
                y -= 20  # Raise selected cards
            rects.append(pygame.Rect(x, y, self.CARD_SIZE[0], self.CARD_SIZE[1]))
        return rects

    def _get_market_card_rects(self, market):
        """Get rectangles for cards in market."""
        rects = []
        if not market:
            return rects

        total_width = len(market) * (self.CARD_SIZE[0] + self.CARD_SPACING) - self.CARD_SPACING
        start_x = self.MAIN_AREA_X

        for i in range(len(market)):
            x = start_x + i * (self.CARD_SIZE[0] + self.CARD_SPACING)
            y = self.MARKET_Y
            if i in self._selected_market:
                y -= 20  # Raise selected cards
            rects.append(pygame.Rect(x, y, self.CARD_SIZE[0], self.CARD_SIZE[1]))
        return rects

    def _render(self):
        """Render the game state."""
        game_state = self.game_engine.get_state()

        # Background
        self._screen.fill(self.BG_COLOR)

        # Draw sections
        self._render_opponent(game_state)
        self._render_market(game_state)
        self._render_hand(game_state)
        self._render_deck(game_state)
        self._render_tokens(game_state)
        self._render_buttons()
        self._render_status(game_state)
        self._render_scores(game_state)

    def _render_opponent(self, game_state):
        """Render opponent's hand - goods as card backs, camels shown separately."""
        num_goods = game_state['enemy_num_goods']
        num_camels = game_state['enemy_num_camels']

        start_x = self.MAIN_AREA_X

        # Label
        self._font.render_to(self._screen, (start_x, self.OPPONENT_HAND_Y - 25),
                            f"Opponent: {num_goods} goods, {num_camels} camels", self.TEXT_COLOR)

        # Draw goods as card backs
        for i in range(num_goods):
            x = start_x + i * (self.CARD_SIZE[0] + self.CARD_SPACING)
            self._screen.blit(self._card_images["back"], (x, self.OPPONENT_HAND_Y))

        # Draw camels separately (shown face up since camels are public info)
        camel_start_x = start_x + num_goods * (self.CARD_SIZE[0] + self.CARD_SPACING) + 30
        if num_camels > 0:
            # Draw camel area background
            camel_area = pygame.Rect(camel_start_x - 5, self.OPPONENT_HAND_Y - 5,
                                     num_camels * (self.CARD_SIZE[0] + self.CARD_SPACING) + 5,
                                     self.CARD_SIZE[1] + 10)
            pygame.draw.rect(self._screen, self.CAMEL_BG_COLOR, camel_area)

            for i in range(num_camels):
                x = camel_start_x + i * (self.CARD_SIZE[0] + self.CARD_SPACING)
                self._screen.blit(self._card_images["camel"], (x, self.OPPONENT_HAND_Y))

    def _render_market(self, game_state):
        """Render the market cards."""
        market = game_state['market']
        rects = self._get_market_card_rects(market)

        if not rects:
            return

        # Label
        label_x = self.MAIN_AREA_X
        self._font.render_to(self._screen, (label_x, self.MARKET_Y - 25),
                            "Market (click to select for grab/trade)", self.TEXT_COLOR)

        for i, (card_type, rect) in enumerate(zip(market, rects)):
            # Draw selection highlight
            if i in self._selected_market:
                highlight_rect = rect.inflate(6, 6)
                pygame.draw.rect(self._screen, self.HIGHLIGHT_COLOR, highlight_rect, 3)

            self._screen.blit(self._card_images[card_type], rect.topleft)

    def _render_hand(self, game_state):
        """Render the player's hand - goods and camels separately."""
        hand = game_state['my_hand']
        goods, camels = self._split_hand(hand)

        # Render goods
        rects = self._get_hand_card_rects(goods)

        # Label
        label_x = self.MAIN_AREA_X
        self._font.render_to(self._screen, (label_x, self.PLAYER_HAND_Y - 25),
                            "Your Goods (click to select all of type)", self.TEXT_COLOR)

        for i, ((original_idx, card_type), rect) in enumerate(zip(goods, rects)):
            # Draw selection highlight
            if original_idx in self._selected_hand:
                highlight_rect = rect.inflate(6, 6)
                pygame.draw.rect(self._screen, self.HIGHLIGHT_COLOR, highlight_rect, 3)

            self._screen.blit(self._card_images[card_type], rect.topleft)

        # Render camels separately
        if camels:
            camel_start_x = self.MAIN_AREA_X + len(goods) * (self.CARD_SIZE[0] + self.CARD_SPACING) + 40

            # Camel area background
            camel_area = pygame.Rect(camel_start_x - 10, self.PLAYER_HAND_Y - 30,
                                     len(camels) * (self.CARD_SIZE[0] + self.CARD_SPACING) + 15,
                                     self.CARD_SIZE[1] + 40)
            pygame.draw.rect(self._screen, self.CAMEL_BG_COLOR, camel_area)
            pygame.draw.rect(self._screen, self.TEXT_COLOR, camel_area, 1)

            # Camel label
            self._font_small.render_to(self._screen, (camel_start_x, self.PLAYER_HAND_Y - 25),
                                       f"Your Camels ({len(camels)})", self.TEXT_COLOR)

            for i, (original_idx, card_type) in enumerate(camels):
                x = camel_start_x + i * (self.CARD_SIZE[0] + self.CARD_SPACING)
                self._screen.blit(self._card_images[card_type], (x, self.PLAYER_HAND_Y))

    def _render_deck(self, game_state):
        """Render the deck with card count."""
        deck_x = self.DECK_X
        deck_y = self.MARKET_Y

        # Draw card back for deck
        self._screen.blit(self._card_images["back"], (deck_x, deck_y))

        # Draw card count
        count_text = str(game_state['num_deck'])
        text_surface, text_rect = self._font_large.render(count_text, self.TEXT_COLOR)
        text_x = deck_x + self.CARD_SIZE[0] // 2 - text_rect.width // 2
        text_y = deck_y + self.CARD_SIZE[1] + 10
        self._font_large.render_to(self._screen, (text_x, text_y), count_text, self.TEXT_COLOR)

        # Label
        self._font_small.render_to(self._screen, (deck_x, deck_y - 20), "Deck", self.TEXT_COLOR)

    def _render_tokens(self, game_state):
        """Render token counts panel."""
        x = self.TOKEN_PANEL_X
        y = 30

        # Panel background
        panel_rect = pygame.Rect(x - 10, y - 10, 230, 300)
        pygame.draw.rect(self._screen, self.PANEL_COLOR, panel_rect)
        pygame.draw.rect(self._screen, self.TEXT_COLOR, panel_rect, 2)

        self._font_large.render_to(self._screen, (x, y), "Tokens Left", self.TEXT_COLOR)
        y += 35

        # Token counts by type
        tokens = game_state['tokens_left']
        for good_type in ["leather", "spice", "cloth", "silver", "gold", "diamond"]:
            count = len(tokens.get(good_type, []))
            color = self.TEXT_COLOR if count > 0 else (128, 128, 128)
            self._font.render_to(self._screen, (x, y), f"{good_type.capitalize()}: {count}", color)
            y += 25

        # Bonus tokens
        y += 10
        self._font.render_to(self._screen, (x, y), "Bonus Tokens:", self.TEXT_COLOR)
        y += 25
        bonus = game_state['bonus_num_left']
        self._font_small.render_to(self._screen, (x, y),
                                   f"3-card: {bonus.get(3, 0)}  4-card: {bonus.get(4, 0)}  5+: {bonus.get(5, 0)}",
                                   self.TEXT_COLOR)

    def _render_buttons(self):
        """Render action buttons."""
        mouse_pos = pygame.mouse.get_pos()

        button_labels = {
            "camels": "Take Camels",
            "grab": "Grab",
            "sell": "Sell",
            "trade": "Trade"
        }

        for button_name, rect in self._buttons.items():
            # Check hover
            is_hover = rect.collidepoint(mouse_pos)
            color = self.BUTTON_HOVER_COLOR if is_hover else self.BUTTON_COLOR

            # Draw button
            pygame.draw.rect(self._screen, color, rect)
            pygame.draw.rect(self._screen, self.TEXT_COLOR, rect, 2)

            # Draw label
            label = button_labels[button_name]
            text_surface, text_rect = self._font.render(label, self.BUTTON_TEXT_COLOR)
            text_x = rect.centerx - text_rect.width // 2
            text_y = rect.centery - text_rect.height // 2
            self._font.render_to(self._screen, (text_x, text_y), label, self.BUTTON_TEXT_COLOR)

    def _render_status(self, game_state):
        """Render status message."""
        # Status bar at bottom
        status_y = self.BUTTON_Y + 5
        status_x = 620

        color = self.ERROR_COLOR if self._status_timer > 0 else self.TEXT_COLOR
        self._font.render_to(self._screen, (status_x, status_y), self._status_message, color)

        # Instructions
        self._font_small.render_to(self._screen, (status_x, status_y + 22),
                                   "ESC to clear selection", (180, 180, 180))

    def _render_scores(self, game_state):
        """Render score information."""
        x = self.TOKEN_PANEL_X
        y = 350

        # Panel
        panel_rect = pygame.Rect(x - 10, y - 10, 230, 130)
        pygame.draw.rect(self._screen, self.PANEL_COLOR, panel_rect)
        pygame.draw.rect(self._screen, self.TEXT_COLOR, panel_rect, 2)

        self._font_large.render_to(self._screen, (x, y), "Scores (tokens)", self.TEXT_COLOR)
        y += 30

        # Always show from consistent perspective: You vs Opponent
        my_tokens = sum(game_state['my_tokens'])
        my_bonus = game_state['my_bonus_num_tokens']
        my_bonus_count = sum(my_bonus.values())

        enemy_tokens = sum(game_state['enemy_tokens'])
        enemy_bonus = game_state['enemy_bonus_num_tokens']
        enemy_bonus_count = sum(enemy_bonus.values())

        self._font.render_to(self._screen, (x, y),
                            f"You: {my_tokens} pts ({my_bonus_count} bonus)", self.HIGHLIGHT_COLOR)
        y += 25
        self._font.render_to(self._screen, (x, y),
                            f"Opponent: {enemy_tokens} pts ({enemy_bonus_count} bonus)", self.TEXT_COLOR)

        y += 30
        self._font_small.render_to(self._screen, (x, y),
                                   "(Final scores include camel bonus)", (180, 180, 180))

    def show_game_over(self, scores, winner):
        """Display game over screen."""
        # Render final state first
        self._render()

        # Darken background
        overlay = pygame.Surface(self.WINDOW_SIZE)
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self._screen.blit(overlay, (0, 0))

        # Game over box
        box_rect = pygame.Rect(self.WINDOW_SIZE[0]//2 - 200, self.WINDOW_SIZE[1]//2 - 120, 400, 240)
        pygame.draw.rect(self._screen, self.PANEL_COLOR, box_rect)
        pygame.draw.rect(self._screen, self.HIGHLIGHT_COLOR, box_rect, 3)

        # Title
        title = "GAME OVER"
        text_surface, text_rect = self._font_large.render(title, self.HIGHLIGHT_COLOR)
        self._font_large.render_to(self._screen, (box_rect.centerx - text_rect.width // 2, box_rect.y + 20),
                                   title, self.HIGHLIGHT_COLOR)

        # Determine which player is which
        # The GUI player is always player 0 in the players list
        # scores[0] is player 0, scores[1] is player 1
        your_score = scores[0]
        opponent_score = scores[1]

        # Scores
        y = box_rect.y + 70
        self._font.render_to(self._screen, (box_rect.x + 50, y),
                            f"Your Final Score: {your_score}", self.HIGHLIGHT_COLOR)
        y += 30
        self._font.render_to(self._screen, (box_rect.x + 50, y),
                            f"Opponent Final Score: {opponent_score}", self.TEXT_COLOR)

        # Winner
        y += 50
        if winner == 0:
            result = "YOU WIN!"
            color = self.HIGHLIGHT_COLOR
        elif winner == 1:
            result = "YOU LOSE!"
            color = self.ERROR_COLOR
        else:
            result = "IT'S A TIE!"
            color = self.TEXT_COLOR

        text_surface, text_rect = self._font_large.render(result, color)
        self._font_large.render_to(self._screen, (box_rect.centerx - text_rect.width // 2, y), result, color)

        # Instructions
        y += 50
        self._font_small.render_to(self._screen, (box_rect.centerx - 70, y),
                                   "Press any key to exit", (180, 180, 180))

        pygame.display.flip()

        # Wait for key press
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                elif event.type == pygame.KEYDOWN:
                    waiting = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
