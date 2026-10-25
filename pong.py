"""Pong - classic pygame version with 1-player (vs AI) and 2-player modes.

Install:  pip install pygame
Run:      python pong.py

Menu:     1 = play vs computer, 2 = two players
Controls: Left paddle  = W / S
          Right paddle = UP / DOWN (2-player mode; in 1-player mode the computer controls it)
          P = pause, M = back to menu, R = restart after a match, ESC = quit
First to 7 points wins.
"""
import math
import random
import sys

import pygame

WIDTH, HEIGHT, FPS = 900, 560, 60
WIN_SCORE = 7
BG, FG, ACCENT = (12, 14, 26), (235, 235, 240), (250, 205, 80)
PADDLE_W, PADDLE_H, BALL_SIZE = 14, 96, 14

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22)
mid_font = pygame.font.SysFont("consolas", 36, bold=True)
big_font = pygame.font.SysFont("consolas", 72, bold=True)


def text(msg, fnt, color, center):
    surf = fnt.render(msg, True, color)
    screen.blit(surf, surf.get_rect(center=center))


class Game:
    def __init__(self, two_players):
        self.two_players = two_players
        self.left = pygame.Rect(30, HEIGHT // 2 - PADDLE_H // 2, PADDLE_W, PADDLE_H)
        self.right = pygame.Rect(WIDTH - 30 - PADDLE_W, HEIGHT // 2 - PADDLE_H // 2, PADDLE_W, PADDLE_H)
        self.score = [0, 0]
        self.ball = pygame.Rect(0, 0, BALL_SIZE, BALL_SIZE)
        self.vel = pygame.math.Vector2()
        self.ball_speed = 7.0
        self.serve_at = 0
        self.paused = False
        self.winner = None
        self.reset_ball(direction=random.choice((-1, 1)))

    def reset_ball(self, direction):
        """Centre the ball and serve it toward `direction` (-1 = left, 1 = right) after a short pause."""
        self.ball.center = (WIDTH // 2, HEIGHT // 2)
        self.ball_speed = 7.0
        self.vel.update(0, 0)
        self.serve_dir = direction
        self.serve_at = pygame.time.get_ticks() + 900

    def serve(self):
        angle = math.radians(random.uniform(-30, 30))
        self.vel.update(math.cos(angle) * self.serve_dir, math.sin(angle))
        self.vel.scale_to_length(self.ball_speed)

    def move_paddles(self, keys):
        speed = 8
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * speed
        self.left.y += dy
        if self.two_players:
            self.right.y += (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * speed
        else:
            self.right.y += self.ai_move()
        for paddle in (self.left, self.right):
            paddle.clamp_ip(screen.get_rect())

    def ai_move(self):
        """Follow the ball only while it approaches, with a small dead zone so it isn't perfect."""
        target = self.ball.centery if self.vel.x > 0 else HEIGHT // 2
        diff = target - self.right.centery
        if abs(diff) < 18:
            return 0
        return max(-6, min(6, diff))

    def bounce_off(self, paddle, direction):
        offset = (self.ball.centery - paddle.centery) / (PADDLE_H / 2)
        angle = math.radians(max(-1, min(1, offset)) * 55)
        self.ball_speed = min(self.ball_speed + 0.5, 16)
        self.vel.update(math.cos(angle) * direction, math.sin(angle))
        self.vel.scale_to_length(self.ball_speed)

    def update(self, keys):
        if self.paused or self.winner:
            return
        self.move_paddles(keys)
        if self.vel.length_squared() == 0:
            if pygame.time.get_ticks() >= self.serve_at:
                self.serve()
            return

        # Move in sub-steps so a fast ball can never tunnel through a paddle
        steps = int(self.ball_speed // 6) + 1
        for _ in range(steps):
            self.ball.x += self.vel.x / steps
            self.ball.y += self.vel.y / steps
            if self.ball.top <= 0 or self.ball.bottom >= HEIGHT:
                self.vel.y *= -1
                self.ball.clamp_ip(screen.get_rect())
            if self.ball.colliderect(self.left) and self.vel.x < 0:
                self.ball.left = self.left.right
                self.bounce_off(self.left, 1)
            elif self.ball.colliderect(self.right) and self.vel.x > 0:
                self.ball.right = self.right.left
                self.bounce_off(self.right, -1)

        if self.ball.right < 0:
            self.point(1)
        elif self.ball.left > WIDTH:
            self.point(0)

    def point(self, scorer):
        self.score[scorer] += 1
        if self.score[scorer] >= WIN_SCORE:
            self.winner = scorer
            self.vel.update(0, 0)
        else:
            self.reset_ball(direction=-1 if scorer == 1 else 1)  # serve toward the player who conceded

    def draw(self):
        screen.fill(BG)
        for y in range(0, HEIGHT, 30):
            pygame.draw.rect(screen, (60, 64, 90), (WIDTH // 2 - 2, y, 4, 16))
        pygame.draw.rect(screen, FG, self.left, border_radius=5)
        pygame.draw.rect(screen, FG, self.right, border_radius=5)
        pygame.draw.ellipse(screen, ACCENT, self.ball)
        text(str(self.score[0]), big_font, FG, (WIDTH // 2 - 90, 60))
        text(str(self.score[1]), big_font, FG, (WIDTH // 2 + 90, 60))
        right_name = "P2" if self.two_players else "CPU"
        text("P1", font, (140, 150, 190), (WIDTH // 2 - 90, 115))
        text(right_name, font, (140, 150, 190), (WIDTH // 2 + 90, 115))
        if self.paused:
            text("PAUSED", mid_font, FG, (WIDTH // 2, HEIGHT // 2))
        if self.winner is not None:
            name = "P1" if self.winner == 0 else right_name
            text(f"{name} WINS!", big_font, ACCENT, (WIDTH // 2, HEIGHT // 2 - 20))
            text("R = rematch    M = menu", font, FG, (WIDTH // 2, HEIGHT // 2 + 40))


def draw_menu():
    screen.fill(BG)
    text("PONG", big_font, ACCENT, (WIDTH // 2, 150))
    text("1  -  Play vs Computer", mid_font, FG, (WIDTH // 2, 290))
    text("2  -  Two Players", mid_font, FG, (WIDTH // 2, 345))
    text("W / S  = left paddle      UP / DOWN = right paddle", font, (140, 150, 190), (WIDTH // 2, 450))
    text(f"First to {WIN_SCORE} wins   |   P = pause   |   ESC = quit", font, (140, 150, 190), (WIDTH // 2, 485))


def main():
    game = None  # None means we are on the menu
    while True:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if game is None:
                    if event.key == pygame.K_1:
                        game = Game(two_players=False)
                    elif event.key == pygame.K_2:
                        game = Game(two_players=True)
                elif event.key == pygame.K_m:
                    game = None
                elif event.key == pygame.K_p and not game.winner:
                    game.paused = not game.paused
                elif event.key == pygame.K_r and game.winner is not None:
                    game = Game(game.two_players)
        if game is None:
            draw_menu()
        else:
            game.update(pygame.key.get_pressed())
            game.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()
