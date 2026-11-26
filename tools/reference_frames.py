#!/usr/bin/env python3
"""Render reference frames from the real desktop game for Android parity checks.

Runs the pygame game headless with a fixed timestep and replays the scripted
inputs in tools/scenarios.json. Every "snap" step saves the 1200x850 frame as a
PNG. The Android debug runner replays the same script, so the two sets of PNGs
can be diffed with tools/compare_frames.py.

Usage (from the repo root):  python tools/reference_frames.py OUT_DIR
"""

import json
import logging
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
logging.disable(logging.CRITICAL)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from src.the_floor_is_a_lie import game as game_module  # noqa: E402
from src.the_floor_is_a_lie.ui import (  # noqa: E402
    CONTINUE_TO_NEXT_LEVEL_EVENT,
    RESTART_FROM_LEVEL_1_EVENT,
    RESTART_GAME_EVENT,
    START_MUSIC_EVENT,
)

KEYS = {
    "space": pygame.K_SPACE,
    "m": pygame.K_m,
    "r": pygame.K_r,
    "c": pygame.K_c,
    "e": pygame.K_e,
    "b": pygame.K_b,
    "u": pygame.K_u,
    "escape": pygame.K_ESCAPE,
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
}


class HeldKeys:
    def __init__(self):
        self.held = set()

    def __getitem__(self, key):
        return key in self.held


held = HeldKeys()
mouse_pos = [0, 0]
pygame.key.get_pressed = lambda: held
pygame.mouse.get_pos = lambda: tuple(mouse_pos)
# The music timer is wall-clock based and has no visual effect; keep runs deterministic.
pygame.time.set_timer = lambda *a, **k: None


def tick(g, dt):
    """One iteration of Game.run(), with a fixed dt (mirrors game.py)."""
    for event in pygame.event.get():
        g.ui_manager.process_events(event)
        g.ui.handle_ui_events(event)
        if event.type == START_MUSIC_EVENT and g.music:
            g.music.play()
        if g.game_state == "menu":
            g.handle_menu_events(event)
        elif g.game_state == "playing":
            g.handle_game_events(event)
        elif g.game_state == "level_editor":
            g.handle_editor_events(event)
        elif g.game_state == "game_over":
            if (
                event.type == pygame.KEYDOWN and event.key == pygame.K_r
            ) or event.type == RESTART_GAME_EVENT:
                g.restart_game()
            elif event.type == RESTART_FROM_LEVEL_1_EVENT:
                g.restart_from_level_1()
            elif event.type == CONTINUE_TO_NEXT_LEVEL_EVENT:
                g.continue_to_next_level()
        elif g.game_state == "level_clear":
            if event.type == pygame.KEYDOWN:
                g.continue_to_next_level()
            elif event.type == CONTINUE_TO_NEXT_LEVEL_EVENT:
                g.continue_to_next_level()
    if g.game_state == "playing":
        g.update_playing(dt)
    elif g.game_state == "dying":
        g.update_dying(dt)
    elif g.game_state == "level_editor":
        g.level_editor.update(dt)
    g.ui_manager.update(dt)
    g.ui.update_color_cycle(dt)
    g.render()


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "reference_frames"
    os.makedirs(out_dir, exist_ok=True)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "tools", "scenarios.json")) as f:
        script = json.load(f)
    os.chdir(root)
    dt = script["dt"]
    g = game_module.Game()
    for step in script["steps"]:
        op = step["op"]
        if op == "frames":
            for _ in range(step["n"]):
                tick(g, dt)
        elif op == "key":
            key = KEYS[step["key"]]
            pygame.event.post(
                pygame.event.Event(
                    pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0
                )
            )
            pygame.event.post(
                pygame.event.Event(pygame.KEYUP, key=key, mod=0, unicode="", scancode=0)
            )
        elif op == "hold":
            key = KEYS[step["key"]]
            held.held.add(key)
            pygame.event.post(
                pygame.event.Event(
                    pygame.KEYDOWN, key=key, mod=0, unicode="", scancode=0
                )
            )
        elif op == "release":
            key = KEYS[step["key"]]
            held.held.discard(key)
            pygame.event.post(
                pygame.event.Event(pygame.KEYUP, key=key, mod=0, unicode="", scancode=0)
            )
        elif op == "mouse":
            pos = (step["x"], step["y"])
            rel = (pos[0] - mouse_pos[0], pos[1] - mouse_pos[1])
            mouse_pos[:] = pos
            if step["action"] == "move":
                pygame.event.post(
                    pygame.event.Event(
                        pygame.MOUSEMOTION,
                        pos=pos,
                        rel=rel,
                        buttons=(0, 0, 0),
                        touch=False,
                    )
                )
            elif step["action"] == "down":
                pygame.event.post(
                    pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN, pos=pos, button=1, touch=False
                    )
                )
            else:
                pygame.event.post(
                    pygame.event.Event(
                        pygame.MOUSEBUTTONUP, pos=pos, button=1, touch=False
                    )
                )
        elif op == "snap":
            path = os.path.join(out_dir, step["name"] + ".png")
            pygame.image.save(g.screen, path)
            print(
                f"{step['name']}: state={g.game_state} player={g.player.get_grid_position()} "
                f"anim={g.player.animation_state.name} frame={g.player.current_animation.current_frame}"
            )


if __name__ == "__main__":
    main()
