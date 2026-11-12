"""
Tetris – pygame-ce
------------------
Installera:
    python -m pip install pygame-ce

Starta:
    python tetris.py

Kontroller:
    Vänster/höger  Flytta blocket
    Ned             Snabbare fall
    Upp eller X     Rotera medurs
    Z               Rotera moturs
    Mellanslag      Släpp blocket direkt
    P               Pausa/fortsätt
    R               Starta om
    Esc             Avsluta
"""

import random
import sys

import pygame

# --- Inställningar ---------------------------------------------------------
CELL = 30
COLS, ROWS = 10, 20
BOARD_W, BOARD_H = COLS * CELL, ROWS * CELL
PANEL_W = 190
WIDTH, HEIGHT = BOARD_W + PANEL_W, BOARD_H
FPS = 60

BG = (17, 22, 34)
BOARD_BG = (24, 31, 46)
GRID = (39, 49, 67)
WHITE = (238, 243, 250)
MUTED = (155, 169, 190)
ACCENT = (100, 210, 190)
COLORS = [
    (64, 190, 210),   # I
    (65, 105, 220),   # J
    (235, 155, 65),   # L
    (235, 205, 75),   # O
    (90, 195, 115),   # S
    (165, 105, 210),  # T
    (220, 85, 105),   # Z
]

# Varje form är en lista med koordinater i ett 4x4-rutnät.
SHAPES = [
    [(0, 1), (1, 1), (2, 1), (3, 1)],
    [(0, 0), (0, 1), (1, 1), (2, 1)],
    [(2, 0), (0, 1), (1, 1), (2, 1)],
    [(1, 0), (2, 0), (1, 1), (2, 1)],
    [(1, 0), (2, 0), (0, 1), (1, 1)],
    [(1, 0), (0, 1), (1, 1), (2, 1)],
    [(0, 0), (1, 0), (1, 1), (2, 1)],
]
LINE_POINTS = (0, 100, 300, 500, 800)


def rotate(shape, clockwise=True):
    """Rotera en form runt dess 4x4-rutnät."""
    if clockwise:
        return [(3 - y, x) for x, y in shape]
    return [(y, 3 - x) for x, y in shape]


class Tetris:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.fall_timer = 0
        self.paused = False
        self.game_over = False
        self.next_piece = self.new_piece()
        self.spawn_piece()

    @staticmethod
    def new_piece():
        index = random.randrange(len(SHAPES))
        return {"shape": SHAPES[index][:], "color": COLORS[index]}

    def spawn_piece(self):
        self.piece = self.next_piece
        self.next_piece = self.new_piece()
        self.x, self.y = 3, 0
        if not self.valid(self.x, self.y, self.piece["shape"]):
            self.game_over = True

    def valid(self, px, py, shape):
        for sx, sy in shape:
            x, y = px + sx, py + sy
            if x < 0 or x >= COLS or y >= ROWS:
                return False
            if y >= 0 and self.board[y][x] is not None:
                return False
        return True

    def move(self, dx, dy):
        if self.valid(self.x + dx, self.y + dy, self.piece["shape"]):
            self.x += dx
            self.y += dy
            return True
        return False

    def rotate_piece(self, clockwise=True):
        rotated = rotate(self.piece["shape"], clockwise)
        # Enkla väggjusteringar gör rotation nära kanten smidigare.
        for offset in (0, -1, 1, -2, 2):
            if self.valid(self.x + offset, self.y, rotated):
                self.x += offset
                self.piece["shape"] = rotated
                return

    def hard_drop(self):
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.score += distance * 2
        self.lock_piece()

    def lock_piece(self):
        for sx, sy in self.piece["shape"]:
            x, y = self.x + sx, self.y + sy
            if 0 <= y < ROWS:
                self.board[y][x] = self.piece["color"]

        full_rows = [row for row in self.board if all(cell is not None for cell in row)]
        if full_rows:
            self.lines += len(full_rows)
            self.score += LINE_POINTS[len(full_rows)] * self.level
            self.board = (
                [[None for _ in range(COLS)] for _ in full_rows]
                + [row for row in self.board if not all(cell is not None for cell in row)]
            )
            self.level = self.lines // 10 + 1

        self.spawn_piece()

    def update(self, dt):
        if self.paused or self.game_over:
            return
        self.fall_timer += dt
        interval = max(80, 650 - (self.level - 1) * 50)
        if self.fall_timer >= interval:
            self.fall_timer = 0
            if not self.move(0, 1):
                self.lock_piece()


def draw_cell(surface, x, y, color, size=CELL):
    rect = pygame.Rect(x, y, size, size)
    pygame.draw.rect(surface, color, rect.inflate(-2, -2), border_radius=5)
    # Liten ljus kant ger blocken djup utan att göra gränssnittet rörigt.
    highlight = tuple(min(255, c + 35) for c in color)
    pygame.draw.line(surface, highlight, rect.topleft, (rect.right - 4, rect.top), 2)


def draw_text(surface, font, text, x, y, color=WHITE):
    surface.blit(font.render(str(text), True, color), (x, y))


def main():
    pygame.init()
    pygame.display.set_caption("Tetris")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("arial", 20, bold=True)
    small = pygame.font.SysFont("arial", 15)
    title_font = pygame.font.SysFont("arial", 27, bold=True)

    game = Tetris()
    running = True
    key_repeat = 0
    pygame.key.set_repeat(150, 55)

    while running:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    game.reset()
                elif event.key == pygame.K_p and not game.game_over:
                    game.paused = not game.paused
                elif not game.paused and not game.game_over:
                    if event.key == pygame.K_LEFT:
                        game.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        if game.move(0, 1):
                            game.score += 1
                    elif event.key in (pygame.K_UP, pygame.K_x):
                        game.rotate_piece(True)
                    elif event.key == pygame.K_z:
                        game.rotate_piece(False)
                    elif event.key == pygame.K_SPACE:
                        game.hard_drop()

        game.update(dt)

        # Bakgrund och spelplan
        screen.fill(BG)
        pygame.draw.rect(screen, BOARD_BG, (0, 0, BOARD_W, BOARD_H))
        for x in range(COLS + 1):
            pygame.draw.line(screen, GRID, (x * CELL, 0), (x * CELL, BOARD_H))
        for y in range(ROWS + 1):
            pygame.draw.line(screen, GRID, (0, y * CELL), (BOARD_W, y * CELL))

        for row in range(ROWS):
            for col in range(COLS):
                color = game.board[row][col]
                if color:
                    draw_cell(screen, col * CELL, row * CELL, color)

        if not game.game_over:
            # Spökposition visar var blocket landar.
            ghost_y = game.y
            while game.valid(game.x, ghost_y + 1, game.piece["shape"]):
                ghost_y += 1
            ghost_color = tuple(max(35, c // 3) for c in game.piece["color"])
            for sx, sy in game.piece["shape"]:
                draw_cell(screen, (game.x + sx) * CELL, (ghost_y + sy) * CELL, ghost_color)
            for sx, sy in game.piece["shape"]:
                draw_cell(screen, (game.x + sx) * CELL, (game.y + sy) * CELL,
                          game.piece["color"])

        # Sidopanel
        panel_x = BOARD_W + 20
        draw_text(screen, title_font, "TETRIS", panel_x, 24, ACCENT)
        draw_text(screen, small, "POÄNG", panel_x, 90, MUTED)
        draw_text(screen, font, f"{game.score:07d}", panel_x, 112)
        draw_text(screen, small, "RADER", panel_x, 160, MUTED)
        draw_text(screen, font, game.lines, panel_x, 182)
        draw_text(screen, small, "NIVÅ", panel_x, 230, MUTED)
        draw_text(screen, font, game.level, panel_x, 252)

        draw_text(screen, small, "NÄSTA", panel_x, 315, MUTED)
        preview_size = 22
        for sx, sy in game.next_piece["shape"]:
            draw_cell(screen, panel_x + sx * preview_size,
                      350 + sy * preview_size, game.next_piece["color"], preview_size)

        draw_text(screen, small, "KONTROLLER", panel_x, 445, ACCENT)
        controls = [
            "← →  Flytta",
            "↓     Snabbare",
            "↑ / X Rotera",
            "Z     Rotera bakåt",
            "Space Släpp",
            "P     Pausa",
            "R     Börja om",
            "Esc   Avsluta",
        ]
        for i, line in enumerate(controls):
            draw_text(screen, small, line, panel_x, 472 + i * 22, MUTED)

        if game.paused or game.game_over:
            overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
            overlay.fill((5, 9, 18, 185))
            screen.blit(overlay, (0, 0))
            message = "PAUS" if game.paused else "SPELET ÄR SLUT"
            sub = "Tryck P för att fortsätta" if game.paused else "Tryck R för att spela igen"
            main_surf = title_font.render(message, True, WHITE)
            sub_surf = small.render(sub, True, WHITE)
            screen.blit(main_surf, main_surf.get_rect(center=(BOARD_W // 2, BOARD_H // 2 - 14)))
            screen.blit(sub_surf, sub_surf.get_rect(center=(BOARD_W // 2, BOARD_H // 2 + 22)))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
