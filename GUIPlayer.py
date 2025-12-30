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

        # Track which player index we are (set on first take_action call)
        self._my_player_index = None

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
        # Track our player index on first call
        if self._my_player_index is None:
            self._my_player_index = self.game_engine.whos_turn

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

        # Check hand card clicks (goods - select all of type)
        goods, camels = self._split_hand(game_state['my_hand'])
        hand_rects = self._get_hand_card_rects(goods)
        for i, rect in enumerate(hand_rects):
            if rect.collidepoint(pos):
                card_type = goods[i][1]
                self._toggle_hand_selection_by_type(game_state['my_hand'], card_type)
                return

        # Check camel clicks (for trading - select individual camels)
        camel_rects = self._get_camel_card_rects(goods, camels)
        for i, rect in enumerate(camel_rects):
            if rect.collidepoint(pos):
                original_idx = camels[i][0]
                self._toggle_single_hand_selection(original_idx)
                return

        # Check market card clicks
        market_rects = self._get_market_card_rects(game_state['market'])
        for i, rect in enumerate(market_rects):
            if rect.collidepoint(pos):
                self._toggle_market_selection(i)
                return

    def _toggle_hand_selection_by_type(self, hand, card_type):
        """Toggle selection of all cards of a type in hand (for goods)."""
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

    def _toggle_single_hand_selection(self, index):
        """Toggle selection of a single card in hand (for camels in trading)."""
        if index in self._selected_hand:
            self._selected_hand.remove(index)
        else:
            self._selected_hand.append(index)
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

        start_x = self.MAIN_AREA_X

        for i in range(len(goods)):
            x = start_x + i * (self.CARD_SIZE[0] + self.CARD_SPACING)
            y = self.PLAYER_HAND_Y
            original_idx = goods[i][0]
            if original_idx in self._selected_hand:
                y -= 20  # Raise selected cards
            rects.append(pygame.Rect(x, y, self.CARD_SIZE[0], self.CARD_SIZE[1]))
        return rects

    def _get_camel_card_rects(self, goods, camels):
        """Get rectangles for camel cards in hand (stacked if too many)."""
        rects = []
        if not camels:
            return rects

        # Camels start after goods with a gap
        camel_start_x = self.MAIN_AREA_X + len(goods) * (self.CARD_SIZE[0] + self.CARD_SPACING) + 40

        max_camels_full = 4  # Show up to 4 fully spaced, then stack
        for i in range(len(camels)):
            if i < max_camels_full:
                x = camel_start_x + i * (self.CARD_SIZE[0] + self.CARD_SPACING)
            else:
                # Stack remaining camels with small offset
                x = camel_start_x + max_camels_full * (self.CARD_SIZE[0] + self.CARD_SPACING) + (i - max_camels_full) * 15

            y = self.PLAYER_HAND_Y
            original_idx = camels[i][0]
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
        """Render opponent's hand as card backs (only show goods, camels are hidden)."""
        num_goods = game_state['enemy_num_goods']

        start_x = self.MAIN_AREA_X

        # Label - only show goods count
        self._font.render_to(self._screen, (start_x, self.OPPONENT_HAND_Y - 25),
                            f"Opponent's Goods: {num_goods}", self.TEXT_COLOR)

        # Draw only goods as backs (camels completely hidden)
        for i in range(num_goods):
            x = start_x + i * (self.CARD_SIZE[0] + self.CARD_SPACING)
            self._screen.blit(self._card_images["back"], (x, self.OPPONENT_HAND_Y))

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

        # Render camels separately (clickable for trading)
        if camels:
            camel_rects = self._get_camel_card_rects(goods, camels)
            camel_start_x = self.MAIN_AREA_X + len(goods) * (self.CARD_SIZE[0] + self.CARD_SPACING) + 40

            # Calculate camel area width (stacked camels take less space)
            max_camels_full = 4  # Show up to 4 camels fully, stack the rest
            if len(camels) <= max_camels_full:
                camel_width = len(camels) * (self.CARD_SIZE[0] + self.CARD_SPACING)
            else:
                camel_width = max_camels_full * (self.CARD_SIZE[0] + self.CARD_SPACING) + 20

            # Camel area background - positioned to not overlap labels
            camel_area = pygame.Rect(camel_start_x - 10, self.PLAYER_HAND_Y - 5,
                                     camel_width + 15,
                                     self.CARD_SIZE[1] + 15)
            pygame.draw.rect(self._screen, self.CAMEL_BG_COLOR, camel_area)
            pygame.draw.rect(self._screen, self.TEXT_COLOR, camel_area, 1)

            # Camel label - above the camel area
            self._font_small.render_to(self._screen, (camel_start_x, self.PLAYER_HAND_Y - 20),
                                       f"Camels ({len(camels)}) - click to trade", self.TEXT_COLOR)

            for i, ((original_idx, card_type), rect) in enumerate(zip(camels, camel_rects)):
                # Draw selection highlight
                if original_idx in self._selected_hand:
                    highlight_rect = rect.inflate(6, 6)
                    pygame.draw.rect(self._screen, self.HIGHLIGHT_COLOR, highlight_rect, 3)

                self._screen.blit(self._card_images[card_type], rect.topleft)

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

    def _format_last_action(self):
        """Format the last action as a human-readable string."""
        last_action = self.game_engine.get_last_action()
        if last_action is None:
            return "Game just started"

        action_type = last_action.get("top", "")
        types = ["leather", "spice", "cloth", "silver", "gold", "diamond", "camel"]

        if action_type == "c":
            n = last_action.get("n_camels", 0)
            return f"Opponent took {n} camel(s)"
        elif action_type == "g":
            grab_type = last_action.get("grab_type", 0)
            return f"Opponent grabbed {types[grab_type]}"
        elif action_type == "s":
            sell_type = last_action.get("sell_type", 0)
            n = last_action.get("n_sold", 0)
            return f"Opponent sold {n} {types[sell_type]}"
        elif action_type == "t":
            trade_out = last_action.get("trade_out", [])
            trade_in = last_action.get("trade_in", [])
            out_names = [types[t] for t in trade_out]
            in_names = [types[t] for t in trade_in]
            return f"Opponent traded {out_names} for {in_names}"
        return ""

    def _render_status(self, game_state):
        """Render status message and opponent's last move."""
        # Status bar at bottom
        status_y = self.BUTTON_Y + 5
        status_x = 620

        color = self.ERROR_COLOR if self._status_timer > 0 else self.TEXT_COLOR
        self._font.render_to(self._screen, (status_x, status_y), self._status_message, color)

        # Instructions
        self._font_small.render_to(self._screen, (status_x, status_y + 22),
                                   "ESC to clear selection", (180, 180, 180))

        # Opponent's last move - display near opponent's area
        last_action_text = self._format_last_action()
        if last_action_text:
            # Display below opponent's hand
            self._font.render_to(self._screen, (self.MAIN_AREA_X, self.OPPONENT_HAND_Y + self.CARD_SIZE[1] + 15),
                                f"Last move: {last_action_text}", (200, 200, 100))

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
        """Display game over screen. Returns True to play again, False to exit."""
        # Render final state first
        self._render()

        # Darken background
        overlay = pygame.Surface(self.WINDOW_SIZE)
        overlay.fill((0, 0, 0))
        overlay.set_alpha(180)
        self._screen.blit(overlay, (0, 0))

        # Game over box
        box_rect = pygame.Rect(self.WINDOW_SIZE[0]//2 - 200, self.WINDOW_SIZE[1]//2 - 140, 400, 280)
        pygame.draw.rect(self._screen, self.PANEL_COLOR, box_rect)
        pygame.draw.rect(self._screen, self.HIGHLIGHT_COLOR, box_rect, 3)

        # Title
        title = "GAME OVER"
        text_surface, text_rect = self._font_large.render(title, self.HIGHLIGHT_COLOR)
        self._font_large.render_to(self._screen, (box_rect.centerx - text_rect.width // 2, box_rect.y + 20),
                                   title, self.HIGHLIGHT_COLOR)

        # Use tracked player index to correctly assign scores
        my_idx = self._my_player_index if self._my_player_index is not None else 0
        opp_idx = 1 - my_idx

        your_score = scores[my_idx]
        opponent_score = scores[opp_idx]

        # Determine if we won based on our player index
        if winner == my_idx:
            result = "YOU WIN!"
            result_color = self.HIGHLIGHT_COLOR
        elif winner == opp_idx:
            result = "YOU LOSE!"
            result_color = self.ERROR_COLOR
        else:
            result = "IT'S A TIE!"
            result_color = self.TEXT_COLOR

        # Scores
        y = box_rect.y + 70
        self._font.render_to(self._screen, (box_rect.x + 50, y),
                            f"Your Final Score: {your_score}", self.HIGHLIGHT_COLOR)
        y += 30
        self._font.render_to(self._screen, (box_rect.x + 50, y),
                            f"Opponent Final Score: {opponent_score}", self.TEXT_COLOR)

        # Winner
        y += 50
        text_surface, text_rect = self._font_large.render(result, result_color)
        self._font_large.render_to(self._screen, (box_rect.centerx - text_rect.width // 2, y), result, result_color)

        # Buttons
        y += 60
        new_game_rect = pygame.Rect(box_rect.centerx - 150, y, 130, 40)
        exit_rect = pygame.Rect(box_rect.centerx + 20, y, 130, 40)

        pygame.draw.rect(self._screen, self.BUTTON_COLOR, new_game_rect)
        pygame.draw.rect(self._screen, self.TEXT_COLOR, new_game_rect, 2)
        pygame.draw.rect(self._screen, self.BUTTON_COLOR, exit_rect)
        pygame.draw.rect(self._screen, self.TEXT_COLOR, exit_rect, 2)

        # Button labels
        text_surface, text_rect = self._font.render("New Game", self.BUTTON_TEXT_COLOR)
        self._font.render_to(self._screen, (new_game_rect.centerx - text_rect.width // 2,
                                            new_game_rect.centery - text_rect.height // 2),
                            "New Game", self.BUTTON_TEXT_COLOR)

        text_surface, text_rect = self._font.render("Exit", self.BUTTON_TEXT_COLOR)
        self._font.render_to(self._screen, (exit_rect.centerx - text_rect.width // 2,
                                            exit_rect.centery - text_rect.height // 2),
                            "Exit", self.BUTTON_TEXT_COLOR)

        pygame.display.flip()

        # Wait for button click
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if new_game_rect.collidepoint(event.pos):
                        return True
                    elif exit_rect.collidepoint(event.pos):
                        return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return False
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        return True
