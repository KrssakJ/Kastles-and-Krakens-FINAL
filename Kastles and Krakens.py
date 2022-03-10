import pygame, pytmx
import time as t
import math as m
import random as r
import os, csv, json

pygame.init() # initialize pygame

pygame.display.set_caption("Kastles and Krakens") # sets the window caption to Kastles and Krakens

class MainGame():
    def __init__(self):
        self.load_variables() # creates and loads all basic variables
        self.load_rooms() # creates and loads all rooms into memory

    def load_variables(self):
        # basic pygame variables
        self.running = True
        self.game_WIDTH = 1280
        self.game_HEIGHT = 960
        self.main_screen = pygame.display.set_mode((self.game_WIDTH, self.game_HEIGHT))
        self.clock = pygame.time.Clock()
        self.prev_time = t.time()
        
        # movement key variables
        self.key_w = False
        self.key_a = False
        self.key_s = False
        self.key_d = False

        # initial player commit, prevents duplication of player sprite
        self.player = Player(self, "player", 624, 600, 0, 4)
        
        # battle text variables: font, text list, etc.
        self.font = pygame.font.SysFont("arial", 40)
        self.medium_font = pygame.font.SysFont("arial", 150)
        self.big_font = pygame.font.SysFont("arial", 300)
        self.text_list = []
        self.text_delay = 0
        self.battle_bg_file = pygame.image.load("battle_background.png")
        self.cur_battle_bg = pygame.Surface((1280,960))
        self.cur_battle_bg.blit(self.battle_bg_file,(0,0))
        self.game_battle_sprites = pygame.sprite.Group()
        
        # other battle variables
        self.battleloop_var = 1
        self.battleloop_phase_delay = 0
        self.drinking_potion = False

        # in-game variables: health, stamina, special points, etc.
        self.player_health = 100
        self.enemy_health = 100
        
        # player's current position in relation to the overworld, X and Y variables
        self.ow_posX = 2
        self.ow_posY = 1
        self.prev_ow_pos = []
        
        # switch between overworld phase and battle phase
        self.roaming = True
    
    def load_rooms(self):
        # loads every room in the game into the world_data list
        # world_data is split into lists (rows), which contain Room objects
        mapdata = self.load_mapfile()
        self.world_data = []
        room_dir = os.path.join("room_bgs")
        self.enemy_count = 0
        void = Room("void", room_dir)

        for f in mapdata:
            rowlist = []
            for r in f:
                if r == "void":
                    roomdata = void
                    rowlist.append(roomdata)
                else:
                    roomdata = Room(r, room_dir)
                    self.enemy_count += len(roomdata.enemy_list)
                    rowlist.append(roomdata)
            self.world_data.append(rowlist)
        
    def load_mapfile(self):
        # loads the map file (.csv) that contains the layout of the map
        with open("maplist.csv") as r:
            loaded = csv.reader(r)  # reads the file, returns map data
            mapdata = list(loaded)  # takes this data and turns it into a list (that we can work with)
        return mapdata

    def game_loop(self):
        # basic game loop, this function causes the game to run in the first place
        while self.running:
            self.clock.tick(60) # set an FPS limit (currently 60FPS)
            self.get_dt() # get delta time, used in various movement functions
            self.get_events() # check events - key presses, etc.
            self.change_pos() # check if the player moved to another room
            if self.roaming == True: # Roaming Phase
                self.main_screen.blit(self.cur_map_image, (0,0)) # draw the background map using the cur_map_image variable
                self.victory_banner() # check if the player defeated every enemy
                self.game_sprites.update() # trigger the update function for every sprite in game_sprites
                self.game_sprites.draw(self.main_screen) # draw all of the sprites in game_sprites on the screen
            else: # Battle Phase
                self.check_for_battle() # check if every enemy has been defeated
                self.main_screen.blit(self.cur_battle_bg, (0,0)) # draw the battle background
                self.game_battle_sprites.update() # trigger the update function for every sprite in game_battle_sprites
                self.game_battle_sprites.draw(self.main_screen) # draw all of the sprites in game_battle_sprites on the screen
                self.battle_loop() # move along the battle loop
            pygame.display.flip() # update the screen

    # Source: CDcodes - Pygame Framerate Independence Tutorial: Delta Time Movement
    # https://www.youtube.com/watch?v=XuyrHE6GIsc
    def get_dt(self):
        now = t.time()
        self.dt = now - self.prev_time # tiny difference between both variables, comes up to approx. 1/60 of a second
        self.prev_time = now

    def get_events(self):
        # basic pygame function, records unique events such as key/button presses, etc.
        for event in pygame.event.get():
            if event.type == pygame.QUIT: # X button in the top right corner of the window
                self.running = False # stops the program from running
            elif event.type == pygame.KEYDOWN: # keystroke, key has been pressed down
                if event.key == pygame.K_w:
                    self.key_w = True
                    self.attack(0) # only relevant when in battle phase
                elif event.key == pygame.K_a:
                    self.key_a = True
                    self.attack(1) # only relevant when in battle phase
                elif event.key == pygame.K_s:
                    self.key_s = True
                    self.attack(2) # only relevant when in battle phase
                elif event.key == pygame.K_d:
                    self.key_d = True
                    self.attack(3) # only relevant when in battle phase
                elif event.key == pygame.K_j:
                    self.attack(4) # only relevant when in battle phase
                    self.select_action_from_menu() # only relevant when in battle phase
                elif event.key == pygame.K_k:
                    self.attack(5) # only relevant when in battle phase
            elif event.type == pygame.KEYUP: # keystroke, key has been lifted
                if event.key == pygame.K_w:
                    self.key_w = False
                elif event.key == pygame.K_a:
                    self.key_a = False
                elif event.key == pygame.K_s:
                    self.key_s = False
                elif event.key == pygame.K_d:
                    self.key_d = False

    def change_pos(self):
        # checks if the player has gone into a different room
        cur_ow_pos = [self.ow_posX, self.ow_posY]
        if cur_ow_pos == self.prev_ow_pos:
            # prevents the program from loading the same room over and over again
            return
        # if the player has moved between rooms, the function loads a new room from scratch
        self.cur_room = self.world_data[self.ow_posY][self.ow_posX]
        self.cur_map_image = self.cur_room.map.load_map()
        self.cur_wall_list = self.cur_room.wall_list
        self.load_player_sprite()
        self.load_enemies(self.cur_room.enemy_list)
        self.prev_ow_pos = cur_ow_pos

    def load_player_sprite(self):
        # creates new sprite group and adds the player sprite
        self.game_sprites = pygame.sprite.Group()
        self.game_sprites.add(self.player)

    def load_enemies(self, enemy_list):
        # loads all the enemies in a room
        # enemy_data = [object.x, object.y, object.properties["enemy_sprite"], object.properties["enemy_type"], object.properties["movement_range"], object.properties["movement_speed"], object.id]
        for enemy in enemy_list:
            if enemy[3] == "walker":
                enemy = Walker(self, enemy[2], enemy[0], enemy[1], enemy[4], 4, enemy[5], enemy[6])
            elif enemy[3] == "charger":
                enemy = Charger(self, enemy[2], enemy[0], enemy[1], enemy[4], 8, enemy[5], enemy[6])
            self.game_sprites.add(enemy)

    def victory_banner(self):
        if self.enemy_count != 0: # checks if all enemies have been defeated
            return
        # deletes every overworld sprite and displays a congratulatory meassage
        self.game_sprites.empty()
        pygame.display.set_caption("Congratulations!") # changes the window caption
        
        # renders the congratulatory text
        text1 = self.medium_font.render("Congratulations!", True, (200,200,0))
        text1_width = text1.get_width()
        text2 = self.medium_font.render("You win!", True, (200,200,0))
        text2_width = text2.get_width()

        # draws the text on the screen
        self.main_screen.blit(text1, (self.game_WIDTH//2-text1_width//2, 150))
        self.main_screen.blit(text2, (self.game_WIDTH//2-text2_width//2, 450))

    def attack(self, input_var):
        if self.roaming:
            return
        # if passed => the player is in the battle phase
        if self.B_player.state_idle: # the player is in the menu, picking an attack
            if input_var == 1: # player pressed A, cursor moves left
                self.menu.selection -= 1
            elif input_var == 3: # player pressed D, cursor moves right
                self.menu.selection += 1
        elif self.menu.active_attack: # player is currently attacking/being attacked
            self.menu.combo.append(input_var) # add the last keystroke to self.combo
            num_pos = len(self.menu.combo)-1
            if num_pos >= len(self.menu.qt_event): # check if the combo is over
                return
            elif input_var != self.menu.qt_event[num_pos]: # check if the last keystroke was correct or not
                self.menu.combo_feedback(input_var, num_pos, False) # 1 failed hit
            else:
                self.menu.combo_feedback(input_var, num_pos, True) # 1 successful hit

    def select_action_from_menu(self):
        #  this function triggers the Attack/Heavy Attack/Potion action during the battle phase using the Menu object
        if self.roaming: # check if player is in the roaming phase
            return
        # passed => the player is in the battle phase
        if self.battleloop_var == 1: # check if player is in the first phase of battle loop
            self.battleloop_var += 1
            func = self.menu.menu_list[self.menu.selection]
            func() # trigger the function

    def check_for_battle(self):
        # checks to see if the player is still in a fight
        if self.B_enemy not in self.game_battle_sprites and len(self.text_list) == 0:
            self.game_battle_sprites.empty()
            self.roaming = True

    def battle_loop(self):
        ## Battle phase has 5 different parts that cycle endlessly until one character dies
        ## since battle_loop() triggers every frame, integer/time-sensitive variables should be handled by individual classes to prevent a softlock
        if self.B_player.state_death:
            # obvious death trigger is obvious
            self.game_over()
            
        # 1) Menu phase: player controls a menu and picks what they want to do
        if self.battleloop_var == 1:
            self.B_player.state_idle = True # player idle animation trigger
            self.B_enemy.state_idle = True # enemy idle animation trigger
        # 2) Attack phase: player plays a short quick-time event while an attack animation plays
        elif self.battleloop_var == 2:
            self.B_player.state_idle = False # player idle animation reset
            if not self.drinking_potion: # check if the player is NOT drinking a potion
                self.menu.active_attack = True # menu attack trigger
        # 3) Tally phase 1: health is updated, text appears on screen
        elif self.battleloop_var == 3:
            self.B_player.state_idle = True # player idle animation trigger
            self.B_player.state_lightattack = False # reset attack animation
            self.B_player.state_heavyattack = False # reset attack animation
            self.menu.active_attack = False # menu attack reset
            self.draw_text() # draw everything in self.text_list
        # 4) Defend phase: enemy attacks the player, player plays a quick-time event to defend against the attack 
        elif self.battleloop_var == 4:
            self.B_player.state_idle = False # player idle animation reset
            self.B_enemy.state_idle = False # enemy idle animation reset
            self.B_enemy.state_attackA = True # enemy attack animation trigger
            self.menu.active_attack = True # menu attack trigger
        # 5) Tally phase 2: health is updated, text appears on screen
        elif self.battleloop_var == 5:
            if not self.B_player.state_death: # check if the player has NOT died
                self.B_player.state_idle = True # player idle animation trigger
            self.B_enemy.state_idle = True # enemy idle animation trigger
            self.B_enemy.state_attackA = False # enemy attack animation reset
            self.menu.active_attack = False # menu attack reset
            self.draw_text() # draw everything in self.text_list
        else:
            ## At the end of Tally phase 2, battle_loop loops back to the start
            self.battleloop_var = 1

    def game_over(self):
        # creates a simple game over screen
        # the only way to get out of this screen is to reset the program
        pygame.display.set_caption("GAME OVER") # changes the window caption

        # renders the game over text
        text1 = self.big_font.render("GAME", True, (200,0,0))
        text1_width = text1.get_width()
        text2 = self.big_font.render("OVER", True, (200,0,0))
        text2_width = text2.get_width()
        
        # draws the text on the screen
        self.main_screen.blit(text1, (self.game_WIDTH//2-text1_width//2, 150))
        self.main_screen.blit(text2, (self.game_WIDTH//2-text2_width//2, 450))

    def draw_text(self):
        now = pygame.time.get_ticks()
        if self.B_player.state_idle and now - self.text_delay > 1500: # check if the player is idle, and if the text has been on the screen for more than 1.5 seconds
            self.text_list.clear() # clear the text list
            self.battleloop_var += 1 # move to the next phase in battle loop
            self.drinking_potion = False # reset the drinking_potion variable
            if self.B_enemy.state_death: # check if the enemy has been defeated
                self.game_battle_sprites.remove(self.B_enemy) # remove the enemy from game_battle_sprites
                self.battleloop_var = 1 # reset the battle loop
            elif self.battleloop_var == 4: # check if the enemy is about to attack
                # not a text function, but it works here because it only triggers once
                self.menu.defend()
                self.B_player.cur_frame = 0
                self.B_enemy.cur_frame = 0
        for i in self.text_list: # draw every text object in text list
            self.main_screen.blit(i.text, (i.coords[0],i.coords[1]))

    def trigger_battle_phase(self, enemy):
        # triggered when overworld enemy objects touch the player
        self.enemy = enemy # loads the enemy object into memory
        self.roaming = not self.roaming # switches to battle phase
        self.load_battle_sprites()

    def load_battle_sprites(self):
        # loads battle sprites to the battle_sprites sprite group
        # done at the start of every battle in order to prevent duplication
        self.B_player = BattlePlayer(self, 100, 800)
        self.game_battle_sprites.add(self.B_player)
        self.menu = BattleMenu(self, self.player_health)
        self.game_battle_sprites.add(self.menu)

        if self.enemy.sourcefile == "goblin_sprites.png":
            self.B_enemy = BattleGoblin(self, 1150, 800)
        elif self.enemy.sourcefile == "skeleton_sprites.png":
            self.B_enemy = BattleSkeleton(self, 1240, 800)
        elif self.enemy.sourcefile == "fireworm_sprites.png":
            self.B_enemy = BattleWorm(self,1300, 800)
        else: # default sourcefile
            self.B_enemy = BattleGoblin(self, 1000, 800)
        self.game_battle_sprites.add(self.B_enemy)

        self.fireball = BattleFireball(self, -200, 675)
        self.game_battle_sprites.add(self.fireball)

    

    def tally(self, maxdmg_enemy, maxdmg_player, target):
        # triggered by BattlePlayer/BattleEnemy classes after their animations end
        if not self.drinking_potion: # check if the player is NOT drinking a potion
            success_hits = self.menu.hits # the amount of inputs the player hit correctly
            combo_length = len(self.menu.qt_event) # the total amount of input in the combo

        ## Targets: 1 = enemy, 2 = player, 3 = potion
        if target == 1: # player deals damage to enemy
            hit_ratio = success_hits/combo_length # ratio of successful hits to length of combo
            dmg_multipler = 1 # default damage multiplier, only used when enemies take damage
            if hit_ratio == 1: # perfect combo, player hit every input
                self.animate_text("Critical hit!", 2)
                dmg_multipler = 1.5 # increased damage multiplier
            dmg_total = int(maxdmg_player*hit_ratio*dmg_multipler) # total damage
            self.enemy_health += dmg_total # subtract from enemy health
            self.animate_text(dmg_total, 1)
        elif target == 2: # enemy deals damage to player
            hit_ratio = success_hits/combo_length # ratio of successful hits to length of combo
            if hit_ratio == 1: # perfect dodge, player avoided the full attack
                self.animate_text("Perfect!", 3)
            elif hit_ratio == 0: # critical miss, player failed every input
                self.animate_text("Critical hit!", 3)
            dmg_total = int(maxdmg_enemy*(1-hit_ratio))
            self.player_health += dmg_total
            self.animate_text(dmg_total, 0)
        elif target == 3: # player drinks a potion
            self.animate_text(30, 4)
            self.player_health += 30 # restore 30 HP
            if self.player_health > 100: # ensure that player HP is capped at 100
                self.player_health = 100
        
        # checks if either character has died during the fight
        if self.enemy_health <= 0: # checks if enemy died
            self.animate_text("Victory!", 5)
            self.B_enemy.state_idle = False # enemy idle animation reset
            self.B_enemy.state_death = True # enemy death animation trigger
            self.B_enemy.cur_frame = 0 # enemy animation reset
            self.enemy.alive = False # remove the enemy from the list of enemies
        
        elif self.player_health <= 0: # checks if player died
            self.B_player.state_idle = False # player idle animation reset
            self.B_player.state_death = True # player death animation trigger
            self.B_player.cur_frame = 0 # player animation reset
            self.game_over() # game over trigger

    def animate_text(self, damage, text_type):
        # adds text objects into text list
        self.text_delay = pygame.time.get_ticks()
        colour = (200,0,0) # red text

        # text types: 0-player damaged, 1-enemy damaged, 2-critical hit player, 3-critical hit enemy, 4-potion, 5-victory text
        if text_type == 4 > 0 or damage == "Perfect!":
            colour = (0,200,0) # green text
        elif text_type == 5:
            colour = (212,175,55) # golden text

        text = self.font.render(str(damage), True, colour)
        textsize = text.get_size()

        if text_type == 0 or text_type == 4: # player took damage or drank a potion
            text_coords = [210,535]
        elif text_type == 1: # enemy took damage
            text_coords = [1000,450]
        elif text_type == 2: # player dealt a critical hit
            text_coords = [1000,400]
        elif text_type == 3: # enemy dealt a critical hit
            text_coords = [210,485]
        elif text_type == 5: # battle victory text
            text_coords = [self.game_WIDTH//2-textsize[0]//2, self.game_HEIGHT//2-textsize[1]//2]
        else: # default text coordinates
            text_coords = [0,0]
        textfile = Text(text, textsize, text_coords)
        self.text_list.append(textfile)    
        
class Text():
    def __init__(self, text, size, coords):
        #Text structure: str(actual text), [size of text], [position of text]
        self.text = text
        self.size = size
        self.coords = coords

# Source: CDcodes - Pygame Sprite Sheet Tutorial: How to Load, Parse, and Use Sprite Sheets
# https://www.youtube.com/watch?v=XuyrHE6GIsc
class Spritesheet():
    def __init__(self, filename):
        jsonfilename = filename.replace("png","json")
        sprite_dir = os.path.join("spritesheets")
        self.sprite_sheet = pygame.image.load(os.path.join(sprite_dir, filename)).convert()
        meta_data = os.path.join(sprite_dir, jsonfilename)
        with open(meta_data) as f:
            self.data = json.load(f)
        f.close()

    def get_sprite(self, x, y, width, height):
        # Draws the sprite on a small surface
        sprite = pygame.Surface((width, height))
        sprite.set_colorkey((0,0,0)) # Sets the sprite alpha channel
        sprite.blit(self.sprite_sheet, (0,0), (x,y,width,height))
        return sprite
        
    def parse_sprite(self, name):
        # Cuts out the sprite image from the spritesheet
        # Returns the image
        sprite = self.data["frames"][name]["frame"]
        x = sprite["x"]
        y = sprite["y"]
        width = sprite["w"]
        height = sprite["h"]
        image = self.get_sprite(x, y, width, height)
        return image

class Room():
    # Room object, stores info about walls/enemies/room properties (mainly for the purposes of readibility)
    def __init__(self, roomname, room_dir):
        room_data = os.path.join(room_dir, (roomname + ".tmx")) # finds the room data in the room_bgs directory
        self.map = TileMap(room_data)
        self.map.render_objects()
        
        self.wall_list = self.map.wall_list
        self.enemy_list = self.map.enemy_list

# Source: KidsCanCode - Tile-based game part 12: Loading Tiled Maps
# https://www.youtube.com/watch?v=QIXyj3WeyZM
class TileMap():
    # uses pytmx to load rooms from .tmx sourcefiles into memory
    # dedicated list of walls/enemies
    def __init__(self, mapfile):
        self.wall_list = []
        self.enemy_list = []
        tm = pytmx.load_pygame(mapfile, pixelalpha = True)
        self.width = tm.width * tm.tilewidth # total width of background surface = number of tiles * width of tile
        self.height = tm.height * tm.tileheight # total height of background surface = number of tiles * width of tile
        self.tmxdata = tm
    
    def render_objects(self):
        for object in self.tmxdata.objects:
            # object properties: id (integer); name,type (strings); x,y,width,height (floats); object.properties (dictionary)
            # object.properties is a dictionary that displays pairs of data
            if object.type == "wall":
                temp_rect = pygame.Rect(object.x, object.y, object.width, object.height)
                self.wall_list.append(temp_rect)
            if object.type == "enemy":
                enemy_data = [object.x, object.y, object.properties["enemy_sprite"], object.properties["enemy_type"], object.properties["movement_range"], object.properties["movement_speed"], object.id]
                self.enemy_list.append(enemy_data)
    
    def load_map(self):
        # loads the background image on a surface and returns it
        temp_surface = pygame.Surface((self.width, self.height))
        self.draw_map(temp_surface)
        return temp_surface

    def draw_map(self, surface):
        # draws the tilemap onto a surface using the tile layer data
        tilecommand = self.tmxdata.get_tile_image_by_gid
        for layer in self.tmxdata.visible_layers: # multiple tile layers for complex textures, multiple layers can overlap
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = tilecommand(gid)
                    if tile:
                        surface.blit(tile, (x*self.tmxdata.tilewidth, y*self.tmxdata.tileheight))
                        
class NPC(pygame.sprite.Sprite):
    # Parent class for every overworld character in the game (player, enemies, etc.)
    # Contains basic spritesheet functions, basic animation functions, collision with walls
    def __init__(self, game, sourcefile, anch_x, anch_y, range, frames_per_side):
        super().__init__()
        self.game = game
        self.sourcefile = sourcefile + "_sprites.png"
        
        # basic NPC variables
        # position_x and position_y act separately from rect.x and rect.y to ensure smoother movement
        self.state_idle = True
        self.direction_x = 0
        self.position_x = anch_x
        self.direction_y = 0
        self.position_y = anch_y
        self.animation_time = 0
        self.size_coef = 3 # default sprite size

        self.load_frames(sourcefile, frames_per_side)
        self.rect = self.image.get_rect(topleft = (anch_x, anch_y), width=(self.size[0]*self.size_coef), height =(self.size[1]*self.size_coef))

    def load_frames(self, sourcefile, frames_per_side):
        # key animation function
        # loads the spritesheet into memory, cuts it up and binds the individual sprites to specific lists
        # these lists are stored in the memory and switch around based on the character's actions
        spritesheet = Spritesheet(self.sourcefile)
        self.frames_down = []
        self.frames_up = []
        self.frames_left = []
        self.frames_right = []
        frames = [self.frames_down, self.frames_up, self.frames_left, self.frames_right]
        sides = ["_front","_back","_left","_right"]
        side_list_pos = 0
        for framelist in frames:
            for frame in range(frames_per_side):
                parsed_frame = spritesheet.parse_sprite(sourcefile + sides[side_list_pos] + str(frame+1) + ".png")
                framelist.append(parsed_frame)
            side_list_pos += 1
        self.cur_frame = 0
        self.image = self.frames_down[self.cur_frame]
        self.cur_sprlist = self.frames_down
        self.size = self.image.get_size()

    def update(self):
        # basic Sprite function, updates the sprite every frame
        self.check_for_death()
        self.draw_NPC()
        self.move()

    def check_for_death(self):
        # check to see if the character has died (only relevant to enemy characters, player death is treated separately)
        pass

    def draw_NPC(self):
        # checks if the NPC is moving;
        # if they are, it begins to iterate through the list of frames
        self.set_state()
        self.animate()
        bigger_sprite = pygame.transform.scale(self.base_sprite, (self.size[0]*self.size_coef, self.size[1]*self.size_coef)) # most sprites are 48*48px, worms are 64*64
        self.image = bigger_sprite

    def set_state(self):
        # Detects whether the NPC is moving or not
        if self.direction_x != 0 or self.direction_y != 0:
            self.state_idle = False
        else:
            self.state_idle = True

    def animate(self):
        # If the NPC is idle, the program doesn't iterate through the list of frames
        if self.state_idle:
            self.cur_frame = 0
        else:
            # Updates the current frame/cur_frame variable based on the amount of time that has passed
            now = pygame.time.get_ticks()
            if now - self.animation_time > 200:
                self.animation_time = now
                self.cur_frame = (self.cur_frame + 1) % len(self.cur_sprlist)

            if self.direction_x > 0:
                self.cur_sprlist = self.frames_right
            elif self.direction_x < 0:
                self.cur_sprlist = self.frames_left
            elif self.direction_y > 0:
                self.cur_sprlist = self.frames_down
            elif self.direction_y < 0:
                self.cur_sprlist = self.frames_up
        self.base_sprite = self.cur_sprlist[self.cur_frame]

    def move(self):
        # this function varies based on each subclass
        pass

    def check_wallsX(self):
        # check if the NPC has hit a wall on the X axis
        for wall in self.cur_wall_list:
            if self.rect.colliderect(wall):
                if self.direction_x > 0:
                    self.rect.right = wall.left
                    self.position_x = wall.left-self.rect.width
                elif self.direction_x < 0:
                    self.rect.left = wall.right
                    self.position_x = wall.right
                elif self.direction_x == 0:
                    # workaround for an issue with pygame's collision, likely permanent
                    self.rect.right = wall.left
                    self.position_x = wall.left-self.rect.width
                    

    def check_wallsY(self):
        # check if the NPC has hit a wall on the Y axis
        for wall in self.cur_wall_list:
            if self.rect.colliderect(wall):
                if self.direction_y > 0:
                    self.rect.bottom = wall.top
                    self.position_y = wall.top-self.rect.height
                elif self.direction_y < 0:
                    self.rect.top = wall.bottom
                    self.position_y = wall.bottom
                elif self.direction_y == 0:
                    # similar workaround to the one found in check_wallsX
                    self.rect.bottom = wall.top
                    self.position_y = wall.top-self.rect.height

class Player(NPC):
    def __init__(self, game, sourcefile, anch_x, anch_y, range, frames_per_side):
        super().__init__(game, sourcefile, anch_x, anch_y, range, frames_per_side)
        # player object doesn't actually use the range variable

    # Source: CDcodes - Pygame Game States Tutorial
    # https://www.youtube.com/watch?v=b_DkQrJxpck
    def move(self):
        self.cur_wall_list = self.game.cur_wall_list # updates every frame in case the player moves to a different room
        self.direction_x = self.game.key_d - self.game.key_a
        self.direction_y = self.game.key_s - self.game.key_w
        
        # separate calculations for X and Y axis, prevents wallclipping
        # position and rect coords act separately, position is a float while rect is an integer
        self.position_x += self.direction_x * 3 * self.game.dt * 60
        self.rect.x = int(self.position_x)
        self.check_wallsX()

        self.position_y += self.direction_y * 3 * self.game.dt * 60
        self.rect.y = int(self.position_y)
        self.check_wallsY()
        
        self.check_edge()

    def check_edge(self):
        # check if the player has come too close to the edge of the screen
        # updates the ow_pos variables accordingly
        if self.position_x <= 16: #player approaches left side
            self.game.ow_posX -= 1
            self.position_x = 1180
            self.rect.x = 1180
        elif self.position_x >= 1232: #player approaches right side
            self.game.ow_posX += 1
            self.position_x = 80
        elif self.position_y <= 8: #player approaches top side
            self.game.ow_posY -= 1
            self.position_y = 880
            self.rect.y = 880
        elif self.position_y >= 920: #player approaches bottom side
            self.game.ow_posY += 1
            self.position_y = 48
            self.rect.y = 48

class Enemy(NPC):
    # anch_x and anch_y represent the enemy's anchor point;
    # range represents how far away the enemy can move from its anchor point
    # frames_per_side is related to the enemy's animation
    # movement speed represents how fast the enemy can move
    # id is used to remove the enemy from memory once it dies
    def __init__(self, game, sourcefile, anch_x, anch_y, range, frames_per_side, movement_speed, id):
        super().__init__(game, sourcefile, anch_x, anch_y, range, frames_per_side)

        # basic enemy variables
        self.range = int(range)
        self.anch_x = int(anch_x)
        self.anch_y = int(anch_y)
        self.id = id

        # basic movement variables
        self.at_home = True
        self.player_spotted = False
        self.wandering = False
        self.wander_delay = False
        self.wander_time = 0.0

        # special variables - charging, alive
        self.charge_delay = True
        self.alive = True

    def check_for_death(self):
        # check if the enemy is still alive, if it isn't, delete it from memory
        if self.alive == False:
            self.kill()
            for entity in self.game.cur_room.enemy_list:
                if entity[6] == self.id:
                    self.game.cur_room.enemy_list.remove(entity)
                    self.game.enemy_count -= 1

    def move(self):
        self.check_for_home() # check if enemy is within range of anchor point, update the at_home variable
        self.check_for_player() # check if player is within range of anchor point, update the player_spotted variable
        if self.player_spotted == True:
            self.reset_timers() # resets timers related to wandering
            self.chase_player() # chasing method varies from enemy to enemy
            self.check_for_collision() # check if enemy has touched player
        else:
            if self.at_home == False: # enemy is too far from anchor point
                self.return_home()
            else:
                self.wander() # wander randomly
    
    def check_for_home(self):
        if ((self.anch_x - self.range) <= self.position_x <= (self.anch_x + self.range)) and ((self.anch_y - self.range) <= self.rect.y <= (self.anch_y + self.range)):
            self.at_home = True
        else:
            self.at_home = False

    def check_for_player(self):
        # calculates the distance between the enemy's rect and the player's rect
        self.distance = m.hypot(self.position_x - self.game.player.rect.x, self.position_y - self.game.player.rect.y)
        if self.distance <= self.range:
            self.player_spotted = True
        else:
            self.player_spotted = False

    def reset_timers(self):
        self.wander_delay = False
        self.wander_time = 0

    def chase_player(self):
        pass

    def check_for_collision(self):
        if self.rect.colliderect(self.game.player) and self.alive == True:
            self.game.trigger_battle_phase(self)
    
    def return_home(self):
        self.new_pos = [self.anch_x, self.anch_y]
        self.move_to_new_pos()
    
    def move_to_new_pos(self):
        # check if the target has been reached
        if ((self.new_pos[0]-2) <= self.rect.x <= (self.new_pos[0]+2)) and (self.new_pos[1]-2) <= self.rect.y <= (self.new_pos[1]+2):
            # reset directions
            self.direction_x = 0
            self.direction_y = 0
            self.wandering = False
            if self.charge_delay == False: # only relevant for Chargers
                self.charge_delay = True
            self.time_delay()
        else:
            if self.player_spotted == False:
                self.wandering = True
            self.create_new_direction()
            self.approximate_direction()
            self.move_enemy()
    
    def time_delay(self):
        time_delay = 1
        dt = self.game.dt
        self.wander_time += dt
        if self.wander_time > time_delay: # it has been more than 1 second
            self.reset_timers()
        else:
            self.wander_delay = True
    
    def create_new_direction(self):
        # use rough_direction to determine which way the enemy should move
        # separate X and Y axes
        rough_direction_x = self.new_pos[0] - self.rect.x
        if rough_direction_x > 0:
            self.direction_x = 1
        elif rough_direction_x == 0:
            self.direction_x = 0
        else:
            self.direction_x = -1

        rough_direction_y = self.new_pos[1] - self.rect.y
        if rough_direction_y > 0:
            self.direction_y = 1
        elif rough_direction_y == 0:
            self.direction_y = 0
        else:
            self.direction_y = -1
    
    def approximate_direction(self):
        # stops the sprite from "vibrating" (a.k.a. oscillating)
        if self.new_pos[0]-2 <= self.position_x <= self.new_pos[0]+2: # close enough on X coord
            self.direction_x = 0
        if self.new_pos[1]-2 <= self.position_y <= self.new_pos[1]+2: # close enough to Y coord
            self.direction_y = 0

    def move_enemy(self):
        pass

    def wander(self):
        if self.wander_delay == True:
            self.time_delay()
        elif self.wandering == False:
            self.find_pos()
            self.move_to_new_pos()
        else:
            self.move_to_new_pos()

    def find_pos(self):
        # finds a new target position within range of anchor
        direction = self.find_direction() # picks a random direction - up, down, left or right
        self.find_distance(direction) # picks a random position within range that corresponds to the chosen direction

    def find_direction(self):
        directions = ["up", "down", "left", "right"]
        new_direction = r.choice(directions)
        return new_direction

    def find_distance(self, direction):
        ## creates self.new_pos variable that the enemy will move to
        # slightly different calculations for every direction

        # the purpose of bottom_range/top_range is to ensure that the sprite doesn't walk off screen
        # if they are Below Zero (check your oxygen) or above the game window's width/height, the program will forcefully put them back in place
        if direction == "up":
            bottom_range = int(self.anch_y-self.range)
            if bottom_range < 0:
                bottom_range = 0
            random_pos = r.randint(bottom_range, self.rect.y)
            self.new_pos = [self.rect.x, random_pos]
        elif direction == "down":
            top_range = int(self.anch_y+self.range)
            if top_range > (self.game.game_HEIGHT - (self.size[1]*self.size_coef)):
                top_range = self.game.game_HEIGHT - (self.size[1]*self.size_coef)
            random_pos = r.randint(self.rect.y, top_range)
            self.new_pos = [self.rect.x, random_pos]
        elif direction == "left":
            bottom_range = int(self.anch_x-self.range)
            if bottom_range < 0:
                bottom_range = 0
            random_pos = r.randint(bottom_range, self.rect.x)
            self.new_pos = [random_pos, self.rect.y]
        elif direction == "right":
            top_range = int(self.anch_x+self.range)
            if top_range > (self.game.game_WIDTH - (self.size[0]*self.size_coef)):
                top_range = self.game.game_WIDTH - (self.size[0]*self.size_coef)
            random_pos = r.randint(self.rect.x, top_range)
            self.new_pos = [random_pos, self.rect.y]

class Walker(Enemy):
    # Simple enemy; if the player is spotted, it will follow the player in a straight line
    # Skeleton: slow walker, movement speed 1.5
    # Goblin: fast walker, movement speed 2.0
    def __init__(self, game, sourcefile, anch_x, anch_y, range, frames_per_side, movement_speed, id):
        super().__init__(game, sourcefile, anch_x, anch_y, range, frames_per_side, movement_speed, id)
        self.mvms = movement_speed

    def chase_player(self):
        # marks the player's position and moves towards it
        self.new_pos = [self.game.player.rect.x, self.game.player.rect.y]
        self.move_to_new_pos()

    def move_enemy(self):
        # a general movement function, direction depends on whether the enemy is chasing or idle
        self.cur_wall_list = self.game.cur_wall_list

        # X and Y axes are handled separately, similarly to the player class
        self.position_x += self.direction_x * self.mvms * self.game.dt * 60
        self.rect.x = int(self.position_x)
        self.check_wallsX()

        self.position_y += self.direction_y * self.mvms * self.game.dt * 60
        self.rect.y = int(self.position_y)
        self.check_wallsY()

class Charger(Enemy):
     # Complicated enemy; if the player is spotted, it will stay in place for 2 seconds, mark the player's location, and charge in a straight line
     # Worm: medium charger, medium size, movement speed 1.5/3.0
    def __init__(self, game, sourcefile, anch_x, anch_y, range, frames_per_side, movement_speed, id):
        super().__init__(game, sourcefile, anch_x, anch_y, range, frames_per_side, movement_speed, id)
        self.mvms = movement_speed
        # basic movement speed variables
        self.size_coef = 4
        self.charge_time = 0.0
        
    def load_frames(self, sourcefile, frames_per_side):
        # unique load_frames function, made specifically to use left/right sprites
        spritesheet = Spritesheet(self.sourcefile)
        self.frames_left = []
        self.frames_right = []
        frames = [self.frames_left, self.frames_right]
        sides = ["_left","_right"]
        side_list_pos = 0
        for framelist in frames:
            for frame in range(frames_per_side):
                parsed_frame = spritesheet.parse_sprite(sourcefile + sides[side_list_pos] + str(frame+1) + ".png")
                framelist.append(parsed_frame)
            side_list_pos += 1
        self.cur_frame = 0
        self.image = self.frames_right[self.cur_frame]
        self.cur_sprlist = self.frames_right
        self.size = self.image.get_size()

    def animate(self):
        # unique animation function, made specifically to use left/right sprites
        if self.state_idle:
            self.cur_frame = 0
        else:
            now = pygame.time.get_ticks()
            if now - self.animation_time > 200:
                self.animation_time = now
                self.cur_frame = (self.cur_frame + 1) % len(self.cur_sprlist)
            if self.direction_x > 0:
                self.cur_sprlist = self.frames_right
            elif self.direction_x < 0:
                self.cur_sprlist = self.frames_left
        self.base_sprite = self.cur_sprlist[self.cur_frame]

    def move_enemy(self):
        # a general movement function, direction depends on whether the enemy is chasing or idle
        self.cur_wall_list = self.game.cur_wall_list

        if self.player_spotted == True:
            mvms = self.mvms*2.5
        else:
            mvms = self.mvms
        self.position_x += self.direction_x * mvms * self.game.dt * 60
        self.rect.x = int(self.position_x)
        self.check_wallsX()

        self.position_y += self.direction_y * mvms * self.game.dt * 60
        self.rect.y = int(self.position_y)
        self.check_wallsY()

    def chase_player(self):
        if self.charge_delay == True: # check if enemy waited for 2 seconds, True = wait a bit longer
            self.check_for_charge()
        else:
            self.charge()

    def check_for_charge(self):
        self.set_sprite()
        dt = self.game.dt
        self.charge_time += dt
        if self.charge_time > 1.5:
            # reset charge variables
            self.charge_delay = False
            self.charge_time = 0
            self.new_pos = [self.game.player.rect.x, self.game.player.rect.y]
        else:
            self.charge_delay = True
    
    def set_sprite(self):
        if self.game.player.position_x - self.position_x < 0:
            self.cur_sprlist = self.frames_left
        else:
            self.cur_sprlist = self.frames_right
        self.base_sprite = self.cur_sprlist[3]

    def charge(self): # move towards the player
        self.move_to_new_pos()

class BattleNPC(pygame.sprite.Sprite):
    def __init__(self, game, anch_x, anch_y):
        # this is the basic battleNPC class
        # contains basic functions that load frames, play idle animations, contain basic attack functions (that then blossom out based on enemy types)
        # only handles animations, combo/QTE/damage are handled by Menu/MainGame classes
        super().__init__()
        self.game = game
        self.sourcefile = "goblin" # default spritesheet
        self.anch_x = anch_x
        self.anch_y = anch_y
        # self.anch_y is stable, represents the "ground" level for battleNPC objects

        # basic animation variables
        self.state_idle = True
        self.direction_x = 0
        self.direction_y = 0
        self.animation_time = 0
        self.animation_cur = 0
        self.delay_var = 0
        self.size_coef = 6
        self.frame_delay = 200
        self.state_death = False
           

    def load_frames(self): 
        # much more complicated and thought-out compared to the old load_frames function
        # works for animations with uneven lengths
        spritesheet = Spritesheet(self.sourcefile+"_battle.png")
        spritelist = list(spritesheet.data["frames"])

        self.frames_idle = []
        self.frames_move_left = []
        self.frames_move_right = []
        self.frames_attackA = []
        self.frames_attackB = []
        self.frames_attackC = []
        self.frames_hit = []
        self.frames_death = []
        self.frames_duck = []
        self.frames_roll = []
        frames = [self.frames_idle, self.frames_move_left, self.frames_move_right, self.frames_attackA, self.frames_attackB, self.frames_attackC, self.frames_hit, self.frames_death, self.frames_duck, self.frames_roll]
        framesuffixes = ["_idle", "_move_left", "_move_right", "_attackA", "_attackB", "_attackC", "_hit", "_death", "_duck", "_roll"]
        suffvar = 0
        
        for framelist in frames:
            frame_prefix = self.sourcefile+framesuffixes[suffvar]
            max_var = 0
            counting_var = 1
            for i in spritelist: # finds the last frame of an animation sequence, marks the number down as max_var
                if frame_prefix in i:
                    inumtemp = i.replace(frame_prefix, "")
                    inum = inumtemp.replace(".png", "")
                    if int(inum) > int(max_var):
                        max_var = int(inum)
            while len(framelist) != max_var: # binds the specific frames to framelists in correct order
                for i in spritelist:
                    if i == frame_prefix + str(counting_var) + ".png":
                        parsed_frame = spritesheet.parse_sprite(i)
                        framelist.append(parsed_frame)
                        counting_var+=1
            suffvar+=1 # moves to the next animation type
        self.cur_frame = 0
        self.image = self.frames_idle[self.cur_frame]
        self.cur_sprlist = self.frames_idle
        self.size = self.image.get_size()

    def update(self):
        self.set_state()
        self.draw_BattleNPC()
    
    def draw_BattleNPC(self):
        self.set_state()
        self.animate()
        bigger_sprite = pygame.transform.scale(self.base_sprite, (self.size[0]*self.size_coef, self.size[1]*self.size_coef))
        self.calibrate_x()
        self.rect.y = self.anch_y - self.size[1]*self.size_coef # sets a stable ground level by changing the sprite's Y coordinate based on its height
        self.image = bigger_sprite

    def set_state(self): # varies based on different subclasses
        pass
    
    def animate(self):
        if self.state_idle: # checks if the NPC is idle
            self.cur_sprlist = self.frames_idle
        now = pygame.time.get_ticks()
        if now - self.animation_time > self.frame_delay and not (self.state_death and self.cur_frame == len(self.frames_death)-1):
            # The second part of the if statement is to make sure that the death animation only plays once
            self.animation_time = now
            self.cur_frame = (self.cur_frame + 1) % len(self.cur_sprlist)
        self.base_sprite = self.cur_sprlist[self.cur_frame]
        self.size = self.base_sprite.get_size()
        
    def calibrate_x(self): # only applies to enemy classes
        pass
    
    def death(self):
        self.cur_sprlist = self.frames_death
        self.frame_delay = 500
        
class BattlePlayer(BattleNPC):
    def __init__(self, game, anch_x, anch_y):
        super().__init__(game, anch_x, anch_y)
        self.sourcefile = "knight"
        self.size_coef = 6
        self.load_frames()
        self.rect = self.image.get_rect(bottomleft = (anch_x, anch_y), width = self.size[0], height = self.size[1])

        # basic animation variables
        # each animation is made up of various sub_animations
        self.state_lightattack = False
        self.lightattack_states = [self.frames_move_right, self.frames_attackA, self.frames_move_left]
        
        self.state_heavyattack = False
        self.heavyattack_states = [self.frames_move_right, self.frames_roll, self.frames_move_right, self.frames_attackC, self.frames_move_left]

        self.state_duck = False
        self.state_counterattack = False
        self.state_roll = False

    def set_state(self): # chooses the correct animation based on the variable
        if self.state_death:
            self.death()
        elif self.state_lightattack:
            self.light_attack()
        elif self.state_heavyattack:
            self.heavy_attack()
        elif self.state_roll:
            self.roll()
        elif self.state_duck:
            self.duck()
        elif self.state_counterattack:
            self.counterattack()
        else:
            self.cur_sprlist = self.frames_idle

    def light_attack(self):
        # this is the light attack animation
        # player moves to the enemy, swipes and moves back
        self.cur_sprlist = self.lightattack_states[self.animation_cur]
        if self.animation_cur == 0:
            # player moves to the enemy
            if self.rect.x <= 750:
                self.rect.x += 4
                self.frame_delay = 150
            else:
                self.rect.x = 750
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 200
        elif self.animation_cur == 1:
            # player swipes at the enemy
            if self.cur_frame == 3:
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 150
        elif self.animation_cur == 2:
            # player moves away from the enemy
            if self.rect.x >= 100:
                self.rect.x -=4
            else:
                self.frame_delay = 200
                self.rect.x = 100
                self.cur_frame = 0
                self.animation_cur = 0
                self.game.battleloop_var += 1
                self.game.tally(0,-50,1)

    def heavy_attack(self):
        #this is the heavy attack animation
        #player rolls to the enemy, swipes twice, and runs back
        self.cur_sprlist = self.heavyattack_states[self.animation_cur]
        if self.animation_cur == 0:
            # player moves to enemy
            if self.rect.x <= 200:
                self.rect.x += 4
            else:
                self.rect.x = 200
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 65
        elif self.animation_cur == 1:
            # player rolls towards the enemy
            self.rect.x += 4
            if self.cur_frame == 11:
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 200
        elif self.animation_cur == 2:
            # first swipe
            if self.rect.x <= 750:
                self.rect.x += 4
            else:
                self.rect.x = 750
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 100
        elif self.animation_cur == 3:
            # second swipe
            if self.cur_frame == 9:
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 200
        elif self.animation_cur == 4:
            # player moves away from the enemy
            if self.rect.x >= 100:
                self.rect.x -= 4
            else:
                self.rect.x = 100
                self.cur_frame = 0
                self.animation_cur = 0
                self.game.battleloop_var += 1
                self.game.tally(0,-150,1)

    def duck(self):
        # this is the duck animation
        self.cur_sprlist = self.frames_duck
        if self.cur_frame >= len(self.cur_sprlist): # this is here to prevent outofrange errors when called by other functions
            self.cur_frame = 0

        if self.cur_frame == 1:
            self.frame_delay = 1500
        elif self.cur_frame == 2:
            self.frame_delay = 200
            self.cur_frame = 0
            self.state_duck = False
            self.state_idle = True
        
    def counterattack(self):
        # this is the counterattack animation
        self.cur_sprlist = self.frames_attackA
        if self.cur_frame >= len(self.cur_sprlist): # this is here to prevent outofrange errors when called by other functions
            self.cur_frame = 0

        if self.cur_frame == 0:
            self.frame_delay = 1800
        elif self.cur_frame == 1:
            self.frame_delay = 200
        elif self.cur_frame == 3:
            self.cur_frame = 0
            self.state_counterattack = False
            self.state_idle = True

    def roll(self):
        # this is the roll animation
        self.cur_sprlist = self.frames_roll
        if self.cur_frame >= len(self.cur_sprlist): # this is here to prevent outofrange errors when called by other functions
            self.cur_frame = 0

        if self.cur_frame == 0:
            self.frame_delay = 125
        elif self.cur_frame == 11:
            self.cur_frame = 0
            self.frame_delay = 200
            self.state_roll = False
            self.state_idle = True

class BattleEnemy(BattleNPC):
    def __init__(self, game, anch_x, anch_y):
        super().__init__(game, anch_x, anch_y)

        # basic enemy variables
        self.game.enemy_health = 150
        self.state_idle = True
        self.state_attackA = False
        self.state_attackB = False
        self.pos_x = self.anch_x

    def calibrate_x(self):
        # ensures the enemy stays at a fixed point, even when using unevenly sized sprites
        # doesn't work perfectly, especially with sprites that contain massive swipe particles
        self.rect.x = self.pos_x - self.size[0]*self.size_coef

    def set_state(self): # evergreen state checker, useful in case I decide to add extra attacks
        if self.state_death:
            self.death()
        elif self.state_attackA:
            self.attackA()
        elif self.state_attackB:
            self.attackB()
        else:
            self.cur_sprlist = self.frames_idle

    def attackA(self): # handled by specific enemy subclasses
        pass
    def attackB(self): # handled by specific enemy subclasses
        pass

class BattleGoblin(BattleEnemy):
    def __init__(self, game, anch_x, anch_y):
        super().__init__(game, anch_x, anch_y)
        
        # basic goblin variables
        self.sourcefile = "goblin"
        self.size_coef = 4
        self.game.enemy_health = 125
        self.load_frames()
        self.rect = self.image.get_rect(bottomleft = (anch_x, anch_y), width = self.size[0], height = self.size[1])
        
        # basic animation variables
        self.attackA_states = [self.frames_move_left, self.frames_attackA, self.frames_attackB, self.frames_move_right]

    def attackA(self):
        # this is the attackA animation
        # goblin runs up to the player, swipes twice and runs away
        self.cur_sprlist = self.attackA_states[self.animation_cur]
        if self.animation_cur == 0:
            # goblin runs to player
            if self.pos_x >= 500:
                self.pos_x -= 5
            else:
                self.pos_x = 500
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 50
                # player animation triggers
                self.game.B_player.cur_frame = 0
                self.game.B_player.state_duck = True
        elif self.animation_cur == 1:
            # first swipe
            if self.cur_frame == 8:
                self.pos_x = 500
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 500
                # player defend triggers
                self.game.B_player.cur_frame = 0
                self.game.B_player.state_duck = False
                self.game.B_player.state_roll = True
        elif self.animation_cur == 2:
            # second swipe
            if self.cur_frame == 1:
                self.frame_delay = 100
            elif self.cur_frame == 8:
                self.frame_delay = 400
            elif self.cur_frame == 9:
                self.frame_delay = 200
                self.animation_cur+=1
                self.cur_frame = 0
                # player animation reset
                self.game.B_player.cur_frame = 0
        elif self.animation_cur == 3:
            # goblin runs away
            if self.pos_x <= self.anch_x:
                self.pos_x += 5
            else:
                self.pos_x = self.anch_x
                self.cur_frame = 0
                self.animation_cur = 0

                self.game.battleloop_var += 1
                self.game.tally(-40,0,2)
        
class BattleSkeleton(BattleEnemy):
    def __init__(self, game, anch_x, anch_y):
        super().__init__(game, anch_x, anch_y)
        # basic skeleton variables
        self.sourcefile = "skeleton"
        self.size_coef = 6
        self.game.enemy_health = 175
        self.load_frames()
        self.rect = self.image.get_rect(bottomleft = (anch_x, anch_y), width = self.size[0], height = self.size[1])

        # basic animation variables
        self.attackA_states = [self.frames_move_left, self.frames_attackA, self.frames_attackB, self.frames_move_right]

    def attackA(self):
        # this is the attackA animation
        # skeleton moves to the player, swipes twice, and moves away
        self.cur_sprlist = self.attackA_states[self.animation_cur]
        if self.animation_cur == 0:
            # skeleton moves to player
            if self.pos_x >= 680:
                self.pos_x -= 4
            else:
                self.pos_x = 680
                self.animation_cur+=1
                self.cur_frame = 0
                # player animation triggers
                self.game.B_player.cur_frame = 0
                self.game.B_player.state_duck = True
                self.frame_delay = 100
        elif self.animation_cur == 1:
            # first swipe
            if self.cur_frame == 7:
                self.animation_cur+=1
                self.cur_frame = 0
                self.frame_delay = 700
                # player defend triggers
                self.game.B_player.cur_frame = 0
                self.game.B_player.state_duck = False
                self.game.B_player.state_counterattack = True
        elif self.animation_cur == 2:
            # second swipe
            if self.cur_frame == 1:
                self.frame_delay = 100
            elif self.cur_frame == 8:
                self.frame_delay = 600
            elif self.cur_frame == 9:
                self.frame_delay = 200
                self.animation_cur+=1
                self.cur_frame = 0
                # player animation reset
                self.game.B_player.cur_frame = 0
                self.game.B_player.state_counterattack = False
                self.game.B_player.state_idle = True
        elif self.animation_cur == 3:
            # skeleton moves away
            if self.pos_x <= self.anch_x:
                self.pos_x += 4
            else:
                self.pos_x = self.anch_x
                self.cur_frame = 0
                self.animation_cur = 0
                
                self.game.battleloop_var += 1
                self.game.tally(-40,0,2)

class BattleWorm(BattleEnemy):
    def __init__(self, game, anch_x, anch_y):
        super().__init__(game, anch_x, anch_y)
        # basic fireworm variables
        self.sourcefile = "fireworm"
        self.size_coef = 8
        self.game.enemy_health = 250
        self.load_frames()
        self.rect = self.image.get_rect(bottomleft = (anch_x, anch_y), width = self.size[0], height = self.size[1])

        # basic animation variables
        self.attackA_states = [self.frames_attackA]

    def attackA(self):
        # simple animation, fireworm just shoots a fireball
        self.cur_sprlist = self.attackA_states[self.animation_cur]
        if self.cur_frame == 8:
            self.game.B_player.state_duck = True
        elif self.cur_frame == 10:
            self.game.fireball.rect.x = 900
        elif self.cur_frame == 15:
            self.cur_frame = 0
            self.animation_cur = 0
            self.game.battleloop_var+=1
            self.game.tally(-50,0,2)

    def death(self):
        super().death()
        self.frame_delay = 100

class BattleFireball(BattleNPC):
    def __init__(self, game, anch_x, anch_y):
        super().__init__(game, anch_x, anch_y)
        # basic fireball variables
        self.sourcefile = "fireball"
        self.size_coef = 6
        self.load_frames()
        self.rect = self.image.get_rect(bottomleft = (anch_x, anch_y), width = self.size[0], height = self.size[1])

    def set_state(self):
        if self.rect.x <= -200:
            return
        else:
            if self.rect.x >= -200:
                self.rect.x -= 8

class BattleMenu(pygame.sprite.Sprite):
    def __init__(self, game, player_health):
        super().__init__()
        self.game = game
        self.player_health = player_health
        self.load_variables() # loads all the basic variables
        self.load_spritevariables() # loads all the sprite-related variables
    
    def load_variables(self):
        self.selection = 0
        self.menu_list = [self.attack, self.heavy_attack, self.items]
        self.len_var = len(self.menu_list)
        self.font = self.game.font
        self.active_attack = False

    def load_spritevariables(self):
        self.rect = pygame.Rect(50, 50, 1180, 100)
        self.image = pygame.Surface((1180, 100))
        self.create_buttons()
        self.create_text()
        self.load_qtbuttons()

    def create_buttons(self):
        button_attack = pygame.Surface((250, 50))
        button_heavyattack = pygame.Surface((250, 50))
        button_items = pygame.Surface((250, 50))
        self.button_list = [button_attack, button_heavyattack, button_items]
        for i in self.button_list:
            i.fill((100,100,100)) # dark grey, background colour

    def create_text(self):
        name_list = ["Attack", "Heavy Attack", "Potion"]
        self.text_list = []
        for i in name_list:
            text = self.font.render(i, True, (0,0,0)) # bold text, black colour
            textwidth = text.get_size()
            self.text_list.append(text)
            self.text_list.append(textwidth)

    def load_qtbuttons(self):
        # works identically to the one found in BattleNPC
        spritesheet = Spritesheet("key_assets.png")
        spritelist = list(spritesheet.data["frames"])

        self.keys_correct = []
        self.keys_default = []
        self.keys_failed = []
        frames = [self.keys_correct, self.keys_default, self.keys_failed]
        framesuffixes = ["_correct", "_default", "_failed"]
        suffvar = 0

        for framelist in frames:
            frame_prefix = "key"+framesuffixes[suffvar]
            max_var = 0
            counting_var = 0
            for i in spritelist: # finds the last frame of a specific key type, marks the number down as max_var
                if frame_prefix in i:
                    inumtemp = i.replace(frame_prefix, "")
                    inum = inumtemp.replace(".png", "")
                    if int(inum) > int(max_var):
                        max_var = int(inum)
            while len(framelist) != max_var+1: # binds the specific frames to framelists in correct order
                for i in spritelist:
                    if i == frame_prefix + str(counting_var) + ".png":
                        parsed_frame = spritesheet.parse_sprite(i)
                        pf_size = parsed_frame.get_size()
                        bigger_frame = pygame.transform.scale(parsed_frame, (pf_size[0]*2,pf_size[1]*2))
                        framelist.append(bigger_frame)
                        counting_var+=1
            suffvar+=1 # moves to the next key type

    def update(self):
        # basic update function, found in every sprite file
        self.image.fill((30,55,150))
        self.check_selection()
        self.paint_buttons()

    def check_selection(self):
        # ensures that the selection variable remains within self.menu_list
        if self.selection < 0:
            self.selection = self.len_var - 1
        elif self.selection == self.len_var:
            self.selection = 0

    def paint_buttons(self):
        # if there is an active attack happening, paint the QTE buttons
        if self.active_attack:
            var = 18
            for key in self.key_sprites:
                self.image.blit(key, (var,16)) # second variable sets a ground level for every key
                var += self.gap
        else:
            var = 100
            text_var = 0
            for i in self.button_list:
                if i == self.button_list[self.selection]:
                    i.fill((100,100,100))
                else:
                    i.fill((200,200,200))
                pygame.draw.rect(i, (200,200,200), (5,5,240,40))
                self.image.blit(i, (var,25))
                text = self.text_list[text_var]
                t_size = self.text_list[text_var+1]
                self.image.blit(text, (var+125-t_size[0]/2, 50-t_size[1]/2))
                var += 365
                text_var+=2

    def attack(self):
        # light attack QTE, 6 keys
        self.hits = 0
        self.combo = []
        # W=0, A=1, S=2, D=3, J=4, K=5
        self.qt_event = r.choice([[3,0,3,4,5,1], [3,1,2,3,5,5], [1,3,1,3,4,5]])
        self.create_qtbuttons()
        self.game.B_player.state_lightattack = True # animation trigger

    def heavy_attack(self):
        # heavy attack QTE, 9 keys
        self.hits = 0
        self.combo = []
        # W=0, A=1, S=2, D=3, J=4, K=5
        self.qt_event = r.choice([[3,3,2,2,3,4,5,4,1], [3,0,1,3,2,3,4,5,5], [3,4,2,4,0,5,4,2,5]])
        self.create_qtbuttons()
        self.game.B_player.state_heavyattack = True # animation trigger

    def defend(self):
        # defend QTE, 6 keys
        self.hits = 0
        self.combo = []
        # W=0, A=1, S=2, D=3, J=4, K=5
        self.qt_event = r.choice([[1,1,2,3,2,1], [1,2,1,4,4,2], [0,2,2,1,3,5]])
        self.create_qtbuttons()
        # defend animation are handled by BattleEnemy subclasses

    def create_qtbuttons(self):
        # creates a list of keys on the screen
        self.key_sprites = []
        for i in self.qt_event:
            key = self.keys_default[i]
            self.key_sprites.append(key)
        key_num = len(self.key_sprites)
        self.gap = 1080//(key_num-1) # gap is an integer

    def items(self):
        self.game.drinking_potion = True
        self.game.tally(1,1,3)
        self.game.battleloop_var+=1

    def combo_feedback(self, button_val, button_pos, hit):
        ## checks if the player pressed the correct key
        # button_val is an integer that represents the value of the button
        # button_pos is an integer that represents the position of the button
        # hit is a bool that checks if the player successfully hit the button
        if hit:
            self.key_sprites[button_pos] = self.keys_correct[button_val] # replace the default key with a green key
            self.hits+=1
        else:
            self.key_sprites[button_pos] = self.keys_failed[button_val] # replace the default key with a red key

g = MainGame()
g.game_loop()