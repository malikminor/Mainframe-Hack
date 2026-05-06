import arcade
import random

# -------------------------
# Constants
# -------------------------
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
WINDOW_TITLE = "Level 1"

SPEED_GROWTH = 0.12
HIGH_SCORE = 0
BASE_PLAYER_SPEED = 3.0
BASE_ENEMY_SPEED = 110


# -------------------------
# Start Screen
# -------------------------
class StartScreen(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        self.time = 0
        self.code_lines = [
            "logger = logging.getLogger(__name__)",
            "logger.setLevel(logging.ERROR)",
            "",
            "frac_range = np.arange(10, 270, 50) / 100.0",
            "frac_range_in_g = range(50, 270, 50)",
            "",
            "log2n_range = range(7, 13, 1)",
            "",
            "def retrain_in_x_with_grid(name, label_p, label_n, oracle, n_features,",
            "                           ftype, test_x, test_y, benchmark):",
            "    print('--- retrain in X with grid ---')",
            "",
            "    for QSV in xrange(50, 601, 50):",
            "        online = OnlineBase(name, label_p, label_n, oracle,",
            "                          n_features, ftype, error=1)",
            "        online.collect_pts(QSV - 1)",
            "",
            "        ex = RBFKernelRetraining(name,",
            "                online.get_QSV(), online.get_QSV_labels(),",
            "                online.get_QSV(), online.get_QSV_labels(),",
            "                ftype, test_x, test_y, n_features)",
            "",
            "def escalate_privileges(token): token.flags |= 0x8000",
            "def patch_neural_bus(addr, value):",
            "    with open('/dev/neural0','wb') as bus: bus.seek(addr); bus.write(bytes([value]))",
            "if escalate_privileges(session.token): patch_neural_bus(0x1F4A, 0xFF)",
        ]

    def on_update(self, delta_time: float):
        self.time += delta_time

    def on_draw(self):
        self.clear()
        start_y = WINDOW_HEIGHT - 25
        line_height = 18

        y = start_y
        for i, line in enumerate(self.code_lines):
            y = start_y - i * line_height
            if y < 100:
                break
            arcade.draw_text(
                line,
                WINDOW_WIDTH * 0.08,
                y,
                arcade.color.GREEN,
                font_size=14,
                font_name="Consolas"
            )
            arcade.draw_text(
                "A/D move • W/Space jump • steal cache → return to USB",
                WINDOW_WIDTH * 0.08,
                48,
                arcade.color.DARK_GREEN,
                11,
                font_name="Consolas"
            )

        if int(self.time) % 2 == 0:
            arcade.draw_text(
                "PRESS ENTER TO INFILTRATE",
                WINDOW_WIDTH * 0.08,
                y - line_height,
                arcade.color.RED,
                font_size=14
            )

    def on_key_press(self, key, modifiers):
        if key == arcade.key.H:
            self.show_help = not self.show_help
            return

        if key in (arcade.key.ENTER, arcade.key.RETURN):
            view = Level1()
            view.setup()
            self.window.show_view(view)


# -------------------------
# Level 1
# -------------------------
class Level1(arcade.View):
    def __init__(self):
        super().__init__()

        # Time & state
        self.time = 0
        self.score_count = 0
        self.difficulty = 1
        self.carrying_data = False
        self.steals = 0

        # Cameras
        self.camera = None
        self.ui_camera = arcade.Camera2D()

        # Sprite lists
        self.player_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.cache_list = arcade.SpriteList()

        # Player & movement
        self.player = None
        self.player_dx = 0
        self.player_dy = 0
        self.gravity = 0.5
        self.move_speed = BASE_PLAYER_SPEED
        self.moving_left = False
        self.moving_right = False
        self.horizontal = 0
        self.is_on_ground = False

        # Jump QoL (coyote time + buffer)
        self.jump_speed = 11.5
        self.coyote_time_max = 0.12
        self.coyote_time_left = 0.0
        self.jump_buffer_max = 0.10
        self.jump_buffer_left = 0.0

        # World / gameplay
        self.spawn_point = (50, 180)
        self.scan_zones = []                 # (x_left, x_right, height)
        self.base_zone = [16, 96, 256]       # [x_left, x_right, height]

    # ---------- helpers ----------
    def add_detector(self, x, y_min, y_max, speed_px_per_s=BASE_ENEMY_SPEED,
                     texture_path="sprites/Fly_antivirus-1.png.png"):
        enemy = arcade.Sprite(texture_path, scale=2)
        enemy.center_x = x
        enemy.center_y = (y_min + y_max) / 2
        enemy.y_min = y_min
        enemy.y_max = y_max
        enemy.base_speed = speed_px_per_s

        scale = 1.0 + SPEED_GROWTH * (self.difficulty - 1)
        enemy.vy = enemy.base_speed * scale
        self.enemy_list.append(enemy)

    def recalc_speeds(self):
        scale = 1.2 + SPEED_GROWTH * (self.difficulty - 1)
        self.move_speed = BASE_PLAYER_SPEED * scale
        for e in self.enemy_list:
            base = getattr(e, "base_speed", BASE_ENEMY_SPEED)
            sign = 1 if e.vy >= 0 else -1
            e.vy = base * scale * sign

    def randomize_layout(self):
        # Clear random enemies (fixed ones will be added here too)
        self.enemy_list = arcade.SpriteList()

        rng = random.Random()
        count = min(2 + (self.difficulty - 1), 5)
        x_positions = [1040, 1168, 1264, 1360, 1488, 1600, 1744]
        rng.shuffle(x_positions)

        # Fixed, non-random detectors
        self.add_detector(x=416, y_min=96, y_max=272, speed_px_per_s=120,
                          texture_path="Sprites/Fly_antivirus-1.png.png")
        self.add_detector(x=560, y_min=96, y_max=336, speed_px_per_s=120,
                          texture_path="Sprites/Fly_antivirus-1.png.png")

        # Random second-half spawns
        for i in range(count):
            x = x_positions[i]
            y_min = rng.choice([128, 160])
            span = rng.randrange(128, 192)
            speed = rng.randrange(90, 150)
            self.add_detector(x, y_min, y_min + span, speed_px_per_s=speed)

    def complete_heist(self):
        self.score_count += 1
        self.difficulty += 1
        self.carrying_data = False
        self.player.set_texture(0)
        self.player.color = (255, 255, 255)

        self.randomize_layout()
        self.recalc_speeds()

        self.cache_list = arcade.SpriteList()
        cache = arcade.Sprite("Sprites/Data_Cube-1.png.png", scale=2)
        cache.center_x = 1792
        cache.center_y = 256
        self.cache_list.append(cache)

    def kill_and_restart(self):
        global HIGH_SCORE
        if self.score_count > HIGH_SCORE:
            HIGH_SCORE = self.score_count

        new = Level1()
        new.setup()
        self.window.show_view(new)

    # ---------- lifecycle ----------
    def setup(self):
        # World color
        arcade.set_background_color((10, 16, 22, 255))

        # Walls / geometry
        self.wall_list = arcade.SpriteList()

        # Floor
        for x in range(0, 10000, 32):
            wall = arcade.Sprite("sprites/Wall_Piskel-1.png.png", scale=2)
            wall.center_x = x + 16
            wall.center_y = 16
            self.wall_list.append(wall)

        # 3x3 start block
        y_coord = 48
        for _ in range(3):
            x_coord = 16
            for _ in range(3):
                wall = arcade.Sprite("sprites/Wall_Piskel-1.png.png", scale=2)
                wall.center_x = x_coord
                wall.center_y = y_coord
                self.wall_list.append(wall)
                x_coord += 32
            y_coord += 32

        # Left wall column
        for y in range(112, 800, 32):
            wall = arcade.Sprite("sprites/Wall_Piskel-1.png.png", scale=2)
            wall.center_x = 16
            wall.center_y = y
            self.wall_list.append(wall)

        # Column at x = 48..80
        for x in range(48, 81, 32):
            for y in range(288, 800, 32):
                wall = arcade.Sprite("sprites/Wall_Piskel-1.png.png", scale=2)
                wall.center_x = x
                wall.center_y = y
                self.wall_list.append(wall)

        # Ceiling
        for x in range(112, 10000, 32):
            wall = arcade.Sprite("sprites/Wall_Piskel-1.png.png", scale=2)
            wall.center_x = x
            wall.center_y = 592
            self.wall_list.append(wall)

        # Short platform (904..1032 @ 112)
        for x in range(904, 1032, 32):
            wall = arcade.Sprite("sprites/Wall_Piskel-1.png.png", scale=2)
            wall.center_x = x
            wall.center_y = 112
            self.wall_list.append(wall)

        # Single blocks / platforms
        for x, y in [
            (1128, 208), (1192, 208), (1224, 208), (1096, 208),
            (1288, 128), (336, 128), (496, 160), (624, 96),
            (1552, 192), (1424, 192), (1712, 224), (1792, 224),
        ]:
            wall = arcade.Sprite("sprites/Wall_Piskel-1.png.png", scale=2)
            wall.position = (x, y)
            self.wall_list.append(wall)

        # Right wall column
        for y in range(224, 592, 32):
            wall = arcade.Sprite("sprites/Wall_Piskel-1.png.png", scale=2)
            wall.center_x = 1824
            wall.center_y = y
            self.wall_list.append(wall)

        # Lasers (scan zones)
        self.scan_zones = [
            (1064, 1288, 72),
            (336, 688, 72),
            (1392, 1936, 72),
        ]

        # Cache
        self.cache_list = arcade.SpriteList()
        cache = arcade.Sprite("Sprites/Data_Cube-1.png.png", scale=2)
        cache.center_x = 1792
        cache.center_y = 256
        self.cache_list.append(cache)

        # Enemies
        self.randomize_layout()
        self.recalc_speeds()

        # Player
        self.player_list = arcade.SpriteList()
        self.player = arcade.Sprite("sprites/virus_mc-1.png.png", scale=2)
        self.player.center_x, self.player.center_y = self.spawn_point
        self.player_list.append(self.player)

        # normal + carrying textures
        self.player.textures = []
        self.player.append_texture(arcade.load_texture("sprites/virus_mc-1.png.png"))         # normal
        self.player.append_texture(arcade.load_texture("Sprites/virus_mc_carry-1.png.png"))   # carrying
        self.player.set_texture(0)

        # Camera
        self.camera = arcade.Camera2D()

    # ---------- draw ----------
    def on_draw(self):
        self.clear()

        # World
        self.camera.use()
        self.wall_list.draw()
        self.player_list.draw()
        self.enemy_list.draw()
        self.cache_list.draw()

        # Scan zones
        for x_left, x_right, h in self.scan_zones:
            arcade.draw_lbwh_rectangle_filled(x_left, 0, x_right - x_left, h, (255, 0, 0, 100))
            arcade.draw_lbwh_rectangle_filled(x_left, h - 2, x_right - x_left, 2, (255, 40, 40, 220))

        # USB graphic (world space)
        arcade.draw_lrbt_rectangle_filled(0, 100, 125, 270, (220, 220, 220))
        arcade.draw_lrbt_rectangle_filled(60, 80, 230, 250, arcade.color.BLACK)
        arcade.draw_lrbt_rectangle_filled(60, 80, 145, 165, arcade.color.BLACK)

        # HUD (camera-relative, using camera position)
        cam_x, cam_y = self.camera.position
        arcade.draw_text(f"High Score: {HIGH_SCORE}", cam_x - 390, cam_y + 280, arcade.color.WHITE, 20)
        arcade.draw_text(f"Score: {self.score_count}", cam_x - 390, cam_y + 255, arcade.color.WHITE, 20)

    # ---------- input ----------
    def on_key_press(self, key, _modifiers):
        if key in (arcade.key.D, arcade.key.RIGHT):
            self.moving_right = True
            self.horizontal = 1
        elif key in (arcade.key.A, arcade.key.LEFT):
            self.moving_left = True
            self.horizontal = -1
        elif key in (arcade.key.W, arcade.key.UP, arcade.key.SPACE):
            self.jump_buffer_left = self.jump_buffer_max

    def on_key_release(self, key, _modifiers):
        if key in (arcade.key.D, arcade.key.RIGHT):
            self.moving_right = False
            if self.horizontal == 1:
                self.horizontal = -1 if self.moving_left else 0
        elif key in (arcade.key.A, arcade.key.LEFT):
            self.moving_left = False
            if self.horizontal == -1:
                self.horizontal = 1 if self.moving_right else 0

    # ---------- update ----------
    def on_update(self, delta_time: float):
        # Coyote / buffer timers
        if self.is_on_ground:
            self.coyote_time_left = self.coyote_time_max
        else:
            self.coyote_time_left = max(0.0, self.coyote_time_left - delta_time)
        self.jump_buffer_left = max(0.0, self.jump_buffer_left - delta_time)

        # Jump if eligible
        if self.jump_buffer_left > 0.0 and (self.is_on_ground or self.coyote_time_left > 0.0):
            self.player_dy = self.jump_speed
            self.is_on_ground = False
            self.coyote_time_left = 0.0
            self.jump_buffer_left = 0.0

        # Enemy motion + bounce
        for e in self.enemy_list:
            e.center_y += e.vy * delta_time
            if e.top >= e.y_max:
                e.top = e.y_max
                e.vy *= -1
            elif e.bottom <= e.y_min:
                e.bottom = e.y_min
                e.vy *= -1

        # Kills (detectors / lasers)
        if arcade.check_for_collision_with_list(self.player, self.enemy_list):
            self.kill_and_restart()

        px_left = self.player.left
        px_right = self.player.right
        pbot = self.player.bottom
        for x_left, x_right, h in self.scan_zones:
            if px_right > x_left and px_left < x_right and pbot < h:
                self.kill_and_restart()
                break

        # Horizontal input → velocity
        self.player_dx = self.horizontal * self.move_speed

        # Camera follow (your original clamp: follow only between 400 and 1440)
        player_x, _ = self.player.position
        if 400 <= player_x <= 1440:
            self.camera.position = (player_x, self.camera.position[1])

        # Move X and resolve collisions
        self.player.center_x += self.player_dx
        hit_list = arcade.check_for_collision_with_list(self.player, self.wall_list)
        for wall in hit_list:
            if self.player_dx > 0:
                self.player.right = wall.left
            elif self.player_dx < 0:
                self.player.left = wall.right

        # Gravity + move Y
        self.player_dy -= self.gravity
        self.player.center_y += self.player_dy

        # Resolve vertical collisions
        self.is_on_ground = False
        hit_list = arcade.check_for_collision_with_list(self.player, self.wall_list)
        for wall in hit_list:
            if self.player_dy > 0:
                self.player.top = wall.bottom
                self.player_dy = 0
            elif self.player_dy < 0:
                self.player.bottom = wall.top
                self.player_dy = 0
                self.is_on_ground = True

        # Cache pickup / deposit
        if (not self.carrying_data and
                arcade.check_for_collision_with_list(self.player, self.cache_list)):
            self.carrying_data = True
            self.player.set_texture(1)
            self.player.color = (150, 255, 255)
            for c in self.cache_list:
                c.remove_from_sprite_lists()

        if self.carrying_data:
            bx_l, bx_r, bh = self.base_zone
            if self.player.right > bx_l and self.player.left < bx_r and self.player.bottom < bh:
                self.complete_heist()


# -------------------------
# Main
# -------------------------
def main():
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    window.show_view(StartScreen())
    arcade.run()


if __name__ == "__main__":
    main()
