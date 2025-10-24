import os
import sys
import argparse
import random
import math
import time

import pandas as pd
import pygame


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
DEFAULT_WAV = os.path.join(ASSETS_DIR, "rain.wav")
CLOUD_WAV = os.path.join(ASSETS_DIR, "generated_audio_0.wav")


def map_range(v, a, b, x, y):
    if a == b:
        return (x + y) / 2
    return x + (v - a) * (y - x) / (b - a)


class Raindrop:
    def __init__(self, x, y, value, data_minmax, speed_range, size_range, alpha_range, mapping_exp=1.0):
        self.x = x
        self.y = y
        self.value = value
        data_min, data_max = data_minmax
        smin, smax = size_range
        amin, amax = alpha_range
        speed_min, speed_max = speed_range
        # normalize data value to 0..1
        if data_max == data_min:
            norm = 0.5
        else:
            norm = (value - data_min) / (data_max - data_min)
            norm = max(0.0, min(1.0, norm))
        # non-linear scaling to emphasize differences
        scaled = norm ** mapping_exp
        # map to visual properties
        self.vy = speed_min + scaled * (speed_max - speed_min)
        self.size = smin + scaled * (smax - smin)
        self.alpha = int(amin + scaled * (amax - amin))
        self.tail = []
        self.max_tail = max(4, int(self.size))
        self.alive = True

    def update(self, dt, height):
        self.tail.insert(0, (self.x, self.y))
        if len(self.tail) > self.max_tail:
            self.tail.pop()
        self.y += self.vy * dt
        if self.y > height - 6:
            self.alive = False


class SplashParticle:
    def __init__(self, x, y, angle, speed, life, color):
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed * 0.6
        self.life = life
        self.max_life = life
        self.color = color

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt  # gravity
        self.life -= dt
        return self.life > 0


class ClickRipple:
    """Visual ripple effect for mouse clicks: expanding ring that fades."""
    def __init__(self, x, y, max_radius=120, life=0.6, color=(180, 230, 255)):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.radius = 6
        self.life = life
        self.max_life = life
        self.color = color
        # compute a speed so the ripple reaches max_radius roughly when life ends
        self.speed = (self.max_radius - self.radius) / max(0.0001, self.max_life)

    def update(self, dt):
        # expand and decay
        self.radius += self.speed * dt
        # slightly faster fade than linear for snappier visuals
        self.life -= dt * 0.8
        return self.life > 0

    def draw(self, surf):
        if self.life <= 0:
            return
        t = max(0.0, min(1.0, self.life / self.max_life))
        # ease-out for stroke width and alpha
        a = int(220 * (t ** 1.2))
        r = int(self.radius)
        stroke = max(1, int(6 * (t ** 0.6)))
        ring_surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(ring_surf, (*self.color, a), (r + 4, r + 4), r, stroke)
        # subtle inner fade
        inner = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        inner_alpha = int(80 * (t ** 2))
        pygame.draw.circle(inner, (self.color[0], self.color[1], self.color[2], inner_alpha), (r + 4, r + 4), int(r * 0.6))
        ring_surf.blit(inner, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)
        surf.blit(ring_surf, (self.x - r - 4, self.y - r - 4))


class Cloud:
    def __init__(self, x, y, country, value, vmin, vmax, radius=48):
        self.x = x
        self.y = y
        self.country = country
        self.value = value
        self.radius = radius
        self.vmin = vmin
        self.vmax = vmax
        self.selected = False

    def draw(self, surf):
        # simple cloud made of circles
        base_color = (220, 230, 240)
        pygame.draw.circle(surf, base_color, (int(self.x - self.radius * 0.4), int(self.y)), int(self.radius * 0.7))
        pygame.draw.circle(surf, base_color, (int(self.x + self.radius * 0.2), int(self.y - self.radius * 0.3)), int(self.radius * 0.6))
        pygame.draw.circle(surf, base_color, (int(self.x + self.radius * 0.6), int(self.y)), int(self.radius * 0.5))
        pygame.draw.ellipse(surf, base_color, (self.x - self.radius, self.y - self.radius * 0.3, self.radius * 2, self.radius * 1.0))
        if self.selected:
            # outline
            pygame.draw.circle(surf, (180, 200, 230), (int(self.x), int(self.y)), int(self.radius), 2)

    def contains_point(self, px, py):
        return (px - self.x) ** 2 + (py - self.y) ** 2 <= (self.radius) ** 2



def load_data(csv_path, column, year=None):
    df = pd.read_csv(csv_path)
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in CSV. Available: {list(df.columns)}")
    # pick the latest year per country unless year specified
    if 'Year' in df.columns and year is None:
        df_latest = df.sort_values('Year').groupby('Entity', as_index=False).last()
    elif year is not None:
        df_latest = df[df['Year'] == year].copy()
    else:
        df_latest = df.copy()

    # drop NaN and non-numeric
    df_latest = df_latest[pd.to_numeric(df_latest[column], errors='coerce').notnull()].copy()
    df_latest[column] = pd.to_numeric(df_latest[column], errors='coerce')
    values = df_latest[["Entity", column]].values.tolist()
    return values


def main():
    parser = argparse.ArgumentParser(description='Rain visualization from CSV (maps a numeric column to raindrops)')
    parser.add_argument('--csv', default=os.path.join(os.path.dirname(__file__), 'cross-country-literacy-rates.csv'), help='Path to CSV')
    parser.add_argument('--column', default='Literacy rate', help='Numeric column to map to rain (default: "Literacy rate")')
    parser.add_argument('--year', type=int, default=None, help='If provided, use only this year')
    parser.add_argument('--width', type=int, default=1000)
    parser.add_argument('--height', type=int, default=700)
    parser.add_argument('--clouds', type=str, default=None, help='Comma-separated list of 5 country names to create clouds for')
    args = parser.parse_args()

    if not os.path.exists(args.csv):
        print(f"CSV file not found: {args.csv}")
        sys.exit(1)

    try:
        data = load_data(args.csv, args.column, args.year)
    except Exception as e:
        print("Failed to load CSV:", e)
        sys.exit(1)

    if len(data) == 0:
        print("No numeric rows found in CSV for the given column/year.")
        sys.exit(1)

    values = [v for _, v in data]
    vmin, vmax = min(values), max(values)

    pygame.init()
    screen = pygame.display.set_mode((args.width, args.height))
    clock = pygame.time.Clock()
    pygame.display.set_caption('Data Rain — each drop = a country')

    # mixer for sound
    sound = None
    try:
        pygame.mixer.init()
        if os.path.exists(DEFAULT_WAV):
            sound = pygame.mixer.Sound(DEFAULT_WAV)
        else:
            print(f"No WAV file at {DEFAULT_WAV}. Clicks will be silent. Place a WAV at that path to enable sound.")
    except Exception as e:
        print("Audio unavailable:", e)

    # cloud audio
    cloud_sound = None
    try:
        if os.path.exists(CLOUD_WAV):
            cloud_sound = pygame.mixer.Sound(CLOUD_WAV)
            print(f"Loaded cloud audio: {CLOUD_WAV}")
        else:
            print(f"No cloud audio at {CLOUD_WAV}. Cloud clicks will be silent or fallback to default.")
    except Exception as e:
        print("Cloud audio unavailable:", e)

    drops = []
    splashes = []
    ripples = []
    spawn_index = 0
    countries = data.copy()

    # prepare clouds: choose 5 countries with wide spread in the selected value
    entity_map = {ent: val for ent, val in data}
    sorted_data = sorted(data, key=lambda t: t[1])
    clouds = []
    if args.clouds:
        cloud_names = [c.strip() for c in args.clouds.split(',') if c.strip()]
        # use provided names if present, otherwise fall back to selection below
        chosen = [name for name in cloud_names if name in entity_map]
    else:
        chosen = []
    if not chosen:
        # pick values at 0%, 25%, 50%, 75%, 100% positions to maximize spread
        n = len(sorted_data)
        indices = [0, int(n * 0.25), int(n * 0.5), int(n * 0.75), max(0, n - 1)]
        # dedupe indices while preserving order
        sel = []
        for i in indices:
            i = max(0, min(n - 1, i))
            ent, val = sorted_data[i]
            if ent not in sel:
                sel.append(ent)
        chosen = sel[:5]

    # place clouds across top evenly
    margin = 80
    count = min(5, len(chosen))
    spacing = max(1, (args.width - 2 * margin) / max(1, count - 1))
    for i, name in enumerate(chosen[:5]):
        val = entity_map.get(name, values[0])
        x = margin + i * spacing
        y = 80
        clouds.append(Cloud(x, y, name, val, vmin, vmax, radius=56))

    active_cloud = None
    info_display = None
    info_time = 0

    # visual mapping ranges
    v_minmax = (vmin, vmax)
    size_minmax = (1, 12)
    speed_minmax = (150, 900)  # pixels / second
    alpha_minmax = (100, 255)

    # Audio and spawn mapping parameters (tunable)
    # We'll use a non-linear exponent to exaggerate differences
    AUDIO_VOL_MIN = 0.03
    AUDIO_VOL_MAX = 1.0
    SPAWN_INT_MAX = 0.12   # when value is minimal (sparser rain)
    SPAWN_INT_MIN = 0.002  # when value is maximal (very dense)
    MAPPING_EXP = 2.2      # exponent >1 emphasizes larger values

    running = True
    last_spawn = 0.0
    default_spawn_interval = 0.02  # base spawn interval (not used for no-cloud small rain)
    # start with sparse small rain when no cloud is selected
    current_spawn_interval = SPAWN_INT_MAX

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                clicked_cloud = None
                for c in clouds:
                    if c.contains_point(mx, my):
                        clicked_cloud = c
                        break
                if clicked_cloud:
                        # select cloud and update spawn density and play cloud audio scaled by value
                    for c in clouds:
                        c.selected = (c is clicked_cloud)
                    active_cloud = clicked_cloud
                    info_display = (clicked_cloud.country, clicked_cloud.value)
                    info_time = time.time()
                    # map value to spawn interval: higher value -> smaller interval (denser rain)
                    # map value (vmin..vmax) -> normalized (0..1)
                    if vmin == vmax:
                        norm = 0.5
                    else:
                        norm = (clicked_cloud.value - vmin) / (vmax - vmin)
                        norm = max(0.0, min(1.0, norm))
                    # emphasize using power curve
                    scaled = norm ** MAPPING_EXP
                    # spawn interval: higher value -> smaller interval -> denser rain
                    current_spawn_interval = SPAWN_INT_MAX - scaled * (SPAWN_INT_MAX - SPAWN_INT_MIN)
                    # audio volume mapping (non-linear)
                    vol = AUDIO_VOL_MIN + scaled * (AUDIO_VOL_MAX - AUDIO_VOL_MIN)
                    try:
                        if cloud_sound:
                            cloud_sound.set_volume(max(0.0, min(1.0, vol)))
                            print(f"Playing {CLOUD_WAV} at volume {max(0.0, min(1.0, vol))}")
                            cloud_sound.play()
                        elif sound:
                            # fallback to small click sound with scaled volume
                            sound.set_volume(max(0.0, min(1.0, vol)))
                            print(f"Playing fallback {DEFAULT_WAV} at volume {max(0.0, min(1.0, vol))}")
                            sound.play()
                    except Exception as e:
                        print("Error playing cloud sound:", e)
                else:
                    # click was not on a cloud: reset to initial state (deselect) and then
                        # allow drop-click behavior to still create splashes
                        active_cloud = None
                        for c in clouds:
                            c.selected = False
                        info_display = None
                        current_spawn_interval = SPAWN_INT_MAX
                        # check drops (clicking drops also produces splash)
                        mx, my = event.pos
                        for d in list(drops):
                            dx = mx - d.x
                            dy = my - d.y
                            if dx * dx + dy * dy <= (d.size * 2) ** 2:
                                if sound:
                                    try:
                                        sound.play()
                                    except Exception:
                                        pass
                                # small visual reaction: create a splash
                                for _ in range(8):
                                    ang = random.uniform(0, math.pi * 2)
                                    sp = SplashParticle(d.x, d.y, ang, random.uniform(80, 220), random.uniform(0.2, 0.6), (180, 220, 255))
                                    splashes.append(sp)
                # always create a ripple at the click position for visual feedback
                try:
                    ripples.append(ClickRipple(mx, my, max_radius=140, life=0.7))
                except Exception:
                    pass
            elif event.type == pygame.KEYDOWN:
                # debug key: press P to play cloud audio at full volume for the active cloud (or overall)
                if event.key == pygame.K_p:
                    try:
                        if active_cloud and cloud_sound:
                            cloud_sound.set_volume(1.0)
                            print(f"[DEBUG] Manual play {CLOUD_WAV} at volume 1.0 for {active_cloud.country}")
                            cloud_sound.play()
                        elif cloud_sound:
                            cloud_sound.set_volume(1.0)
                            print(f"[DEBUG] Manual play {CLOUD_WAV} at volume 1.0")
                            cloud_sound.play()
                        elif sound:
                            sound.set_volume(1.0)
                            print(f"[DEBUG] Manual play fallback {DEFAULT_WAV} at volume 1.0")
                            sound.play()
                    except Exception as e:
                        print("Error during manual debug play:", e)

        # spawn drops (density influenced by active cloud)
        last_spawn += dt
        while last_spawn >= current_spawn_interval and len(drops) < 1200:
            last_spawn -= current_spawn_interval
            # if a cloud is active, spawn drops that use that cloud's value so sizes are consistent
            if active_cloud:
                ent = active_cloud.country
                val = active_cloud.value
                x = random.uniform(max(10, active_cloud.x - active_cloud.radius), min(args.width - 10, active_cloud.x + active_cloud.radius))
            else:
                # no active cloud: produce light small rain using the minimum data value
                ent = None
                val = vmin
                # spread drops across the whole screen
                x = random.uniform(20, args.width - 20)
            # create Raindrop using data min/max and mapping exponent for size/velocity
            d = Raindrop(x, random.uniform(-60, -10), val, (vmin, vmax), speed_minmax, size_minmax, alpha_minmax, mapping_exp=MAPPING_EXP)
            drops.append(d)

        # update drops
        for d in list(drops):
            d.update(dt, args.height)
            if not d.alive:
                # create splash
                for _ in range(6 + int(d.size / 2)):
                    ang = random.uniform(-math.pi, 0)
                    sp = SplashParticle(d.x, args.height - 6, ang, random.uniform(60, 220) * (d.size / 6), random.uniform(0.3, 0.8), (200, 230, 255))
                    splashes.append(sp)
                drops.remove(d)

        # update splashes
        for sp in list(splashes):
            alive = sp.update(dt)
            if not alive:
                splashes.remove(sp)

        # update ripples
        for rp in list(ripples):
            alive = rp.update(dt)
            if not alive:
                ripples.remove(rp)

        # draw
        screen.fill((10, 14, 20))
        # draw clouds behind drops
        for c in clouds:
            c.draw(screen)
    # draw drops with tails
        for d in drops:
            # tail
            for i, (tx, ty) in enumerate(d.tail):
                talpha = int(d.alpha * (1 - (i / max(1, len(d.tail)))))
                color = (120, 180, 255, talpha)
                s = max(1, int(d.size * (1 - i / max(1, len(d.tail)))))
                surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (s, s), s)
                screen.blit(surf, (tx - s, ty - s))
            # head
            s = int(max(1, d.size))
            surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (100, 170, 255, d.alpha), (s, s), s)
            screen.blit(surf, (d.x - s, d.y - s))

        # draw splashes
        for sp in splashes:
            t = max(0, sp.life / sp.max_life)
            alpha = int(255 * t)
            r = int(2 + (1 - t) * 8)
            surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (200, 230, 255, alpha), (r, r), r, 1)
            screen.blit(surf, (sp.x - r, sp.y - r))

        # draw click ripples on top of splashes
        for rp in ripples:
            rp.draw(screen)

        # draw cloud label only on hover (show country, value, example drop size)
        # NOTE: if a cloud is active (clicked), suppress hover labels per user request
        small_font = pygame.font.SysFont(None, 16)
        mx, my = pygame.mouse.get_pos()
        if active_cloud is None:
            for c in clouds:
                if c.contains_point(mx, my):
                    # compute sample drop size using same mapping as Raindrop
                    if vmin == vmax:
                        norm = 0.5
                    else:
                        norm = (c.value - vmin) / (vmax - vmin)
                        norm = max(0.0, min(1.0, norm))
                    scaled = norm ** MAPPING_EXP
                    sample_size = size_minmax[0] + scaled * (size_minmax[1] - size_minmax[0])
                    info_text = f"{c.country}: {c.value}  size≈{sample_size:.1f}"
                    lbl = small_font.render(info_text, True, (230, 230, 230))
                    # draw semi-transparent background for readability
                    bg = pygame.Surface((lbl.get_width() + 8, lbl.get_height() + 6), pygame.SRCALPHA)
                    bg.fill((20, 20, 30, 180))
                    screen.blit(bg, (c.x - bg.get_width() // 2, c.y + c.radius + 8))
                    screen.blit(lbl, (c.x - lbl.get_width() // 2, c.y + c.radius + 10))

        # HUD
        font = pygame.font.SysFont(None, 20)
        txt = font.render(f"Drops: {len(drops)}  Splashes: {len(splashes)}  Data rows: {len(countries)}  Column: {args.column}", True, (200, 200, 200))
        screen.blit(txt, (8, 8))
        # show info of last clicked cloud
        if info_display and time.time() - info_time < 2.5:
            name, val = info_display
            info_txt = font.render(f"{name}: {val}", True, (255, 255, 220))
            # draw near active cloud
            if active_cloud:
                screen.blit(info_txt, (active_cloud.x - info_txt.get_width() // 2, active_cloud.y + active_cloud.radius + 6))
            else:
                screen.blit(info_txt, (8, 30))

        pygame.display.flip()

    pygame.quit()


if __name__ == '__main__':
    main()
