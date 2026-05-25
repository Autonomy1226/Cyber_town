from PIL import Image
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "godot", "assets", "sprites")
os.makedirs(OUT, exist_ok=True)
os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)

def solid(path, size, color):
    img = Image.new("RGBA", size, color)
    img.save(path)

def rect_border(path, size, fill, border_color, border_w=1):
    img = Image.new("RGBA", size, fill)
    pixels = img.load()
    w, h = size
    for x in range(w):
        for y in range(h):
            if x < border_w or x >= w - border_w or y < border_w or y >= h - border_w:
                pixels[x, y] = border_color
    img.save(path)

# Player - blue
solid(os.path.join(OUT, "player.png"), (32, 32), (60, 120, 220, 255))

# NPCs - distinct colors
colors = {
    "npc_zara": (200, 60, 60, 255),
    "npc_kron": (60, 180, 60, 255),
    "npc_nyx":  (40, 40, 40, 255),
    "npc_vex":  (200, 160, 40, 255),
    "npc_pip":  (220, 120, 220, 255),
}
for name, color in colors.items():
    solid(os.path.join(OUT, f"{name}.png"), (32, 32), color)

# Tiles
tiles = os.path.join(OUT, "tiles")
solid(os.path.join(tiles, "floor.png"), (32, 32), (42, 42, 42, 255))
solid(os.path.join(tiles, "wall.png"), (32, 32), (25, 25, 28, 255))
solid(os.path.join(tiles, "desk.png"), (64, 32), (100, 70, 40, 255))
solid(os.path.join(tiles, "plant.png"), (32, 32), (40, 140, 60, 255))
solid(os.path.join(tiles, "server_rack.png"), (32, 64), (50, 50, 55, 255))

print("Sprites generated in", OUT)
