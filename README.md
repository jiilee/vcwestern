# Western Shooter

A simple point-and-click shooter game set in the Wild West. Shoot bandits, avoid civilians, manage your ammo and health, and try to get the highest score!

## How to Run

1.  **Ensure you have Python installed.**
2.  **Install Pygame:**
    ```bash
    pip install pygame
    ```
3.  **Run the game:**
    ```bash
    python main.py
    ```

## Controls

*   **Mouse:** Aim the crosshair.
*   **Left Click:**
    *   Shoot at the targeted location.
    *   Click on a dead bandit (fallen figure) to collect ammo.
    *   Click on a health pack (white square with red cross) to collect health.

## Features

*   **Scoring:** Earn cash for shooting bandits.
*   **Health:** Start with 3 health points. Lose health when shot by bandits. Can collect health packs (dropped by bandits) to increase health (up to a maximum of 5).
*   **Ammo:** Start with 6 bullets. Collect ammo by clicking on dead bandits (2 bullets per pickup). Running out of ammo when no bandits (dead or alive) are on screen results in game over.
*   **Bandits:** Appear randomly and will shoot at the player after a random delay.
*   **Civilians:** Walk across the screen. Shooting a civilian results in an immediate game over.
*   **Health Packs:** Have a chance to drop from defeated bandits. Disappear after a short time if not collected.
*   **Difficulty Scaling:** Bandit spawn rate increases as you kill more bandits (progress through levels).
*   **Game Over Conditions:**
    *   Player health reaches 0.
    *   Player shoots a civilian.
    *   Player runs out of ammo with no bandits left on screen (dead or alive) to replenish from.
*   **Visuals & Audio:** Includes basic graphics for characters, buildings, and effects. Optional background music and image assets enhance the experience (requires specific files in the same directory).

## Assets (Optional)

The game will attempt to load the following files if they exist in the same directory as `main.py`:

*   `background.png`
*   `building.png`
*   `bandit.png`
*   `civilian.png`
*   `dead_bandit.png`
*   `start_background.png`
*   `background.mp3` (Background Music)

If these files are not found, the game will use fallback colored shapes and run without music.

## Dependencies

*   Python 3.x
*   Pygame
