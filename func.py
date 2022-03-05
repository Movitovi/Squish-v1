import pygame, os, time

class game():
    # Initialize everything for the game
    def __init__(self):
        pygame.init()
        
        # Varius variables
        self.alive_cnt = 2
        self.alive_ind = 0
        self.font = pygame.font.SysFont("couriernew", 64, False)
        self.big_font = pygame.font.SysFont("couriernew", 96, False)
        self.running = 1
        
        # Connect joysticks
        self.joysticks = []
        for i in range(0, pygame.joystick.get_count()):
            self.joysticks.append(pygame.joystick.Joystick(i))
            self.joysticks[-1].init()
        
        # Load game.txt file
        file = open(os.path.join(os.getcwd(), 'game.txt'))
        game_file = file.readlines()
        file.close()
        file = open(os.path.join(os.getcwd(), 'save.txt'), 'r+')
        save_file = file.readlines()
        file.close()
        
        # Set title
        pygame.display.set_caption(game_file[1][8:-2])
        
        # Set window size
        self.display_info = pygame.display.Info()
        self.display_size = [self.display_info.current_w, self.display_info.current_h]
        self.size = findxy(game_file[2])
        self.surface = pygame.Surface(self.size)
        self.display = pygame.display.set_mode(self.display_size)

        # Create clock
        self.clock = pygame.time.Clock()
        self.tick = 60
        
        # Load objects from game.txt file
        self.objects = objects(game_file, save_file, self)

    # Read inputs
    def get_inputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = 0
            if event.type == pygame.KEYDOWN:
                for player in self.objects.players:
                    if event.key == pygame.K_RETURN:
                        player.set_controls(self)
                    for i in range(0, len(player.controls)):
                        if event.key == player.controls[i]:
                            player.inputs[i] = 1
            if event.type == pygame.KEYUP:
                for player in self.objects.players:
                    for i in range(0, len(player.controls)):
                        if event.key == player.controls[i]:
                            player.inputs[i] = 0

    # Process objects
    def move_objects(self):
        for player in self.objects.players:
            # Set desired speed [x, y]
            player.target_speed = [0, player.gravity]
            if player.inputs[0]:
                player.target_speed[0] += -player.base_speed
            if player.inputs[1]:
                player.target_speed[0] += player.base_speed
            
            # Set new speeds
            for i in range(0, len(player.speed)):
                if player.speed[i] < player.target_speed[i]:
                    player.speed[i] += player.acceleration
                elif player.speed[i] > player.target_speed[i]:
                    player.speed[i] += -player.acceleration
            if player.inputs[2]:
                if self.objects.on_ground(player):
                    player.speed[1] = -player.jump_strength
            
            # If shielding don't move
            if player.inputs[3] and not player.shield_broken:
                player.color = player.shield_color
                player.speed = [0, 0]
                if player.shield_health <= 0:
                    player.shield_broken = 1
                else:
                    player.shield_health += -1
            else:
                player.color = player.base_color
                if player.shield_health < player.base_shield_health:
                    player.shield_health += player.shield_regen
                else:
                    player.shield_broken = 0
            
            # Set new positions
            i = player.speed[0] < player.speed[1]
            player.pos[i] = self.objects.new_pos(player, i)
            player.pos[not i] = self.objects.new_pos(player, not i)

    # Update the game state
    def update(self):
        for player in self.objects.players:
            if player.pos[1] >= self.size[1]:
                #player.pos[1] = -player.size[1]
                player.alive = 0
            if player.alive:
                self.objects.kill_player(player)
        self.alive_cnt = 0
        self.alive_ind = 0
        for i in range(0, len(self.objects.players)):
            if self.objects.players[i].alive:
                self.alive_cnt += 1
                self.alive_ind = i
        for block in self.objects.blocks:
            pygame.draw.rect(self.surface, block.color, [block.pos, block.size])
        for player in self.objects.players:
            if player.alive:
                pygame.draw.rect(self.surface, player.color, [player.pos, player.size])
        if self.alive_cnt <= 1:
            # Game over
            self.win_image = self.font.render(self.objects.players[self.alive_ind].name + ' wins!', True, (0, 0, 0))
            self.surface.blit(self.win_image, [84, 64])
            self.display.blit(pygame.transform.scale(self.surface, self.display_size), [0, 0])
            pygame.display.update()
            time.sleep(1.5)
            self.__init__()
        self.display.blit(pygame.transform.scale(self.surface, self.display_size), [0, 0])
        pygame.display.update()
        self.clock.tick(self.tick)
    
    # Close the game
    def close(self):
        pygame.quit()
        save_file = open(os.getcwd() + '\\save.txt', mode = 'w')
        for player in self.objects.players:
            save_file.write(player.name + '\n')
            for control in player.controls:
                save_file.write(str(control) + '\n')
        save_file.close()

class objects():
    def __init__(self, game_file, save_file, game):
        self.players = []
        self.blocks = []
        i = 4
        while i < len(game_file):
            if game_file[i] == 'type = player\n':
                # Read player data
                self.players.append(player_object(game_file[i+1:i+11], save_file, game))
                i += 11
            elif game_file[i] == 'type = block\n':
                # Read block data
                self.blocks.append(block_object(game_file[i+1:i+8]))
                i += 8
            else:
                i += 1
    
    def on_ground(self, obj):
        for sub in self.blocks + self.players:
            if sub.alive and sub.solid and sub.name != obj.name:
                if sub.pos[1] + sub.size[1] >= obj.pos[1] + obj.size[1]:
                    if obj.pos[1] + obj.size[1] >= sub.pos[1]:
                        if sub.pos[0] + sub.size[0] >= obj.pos[0]:
                            if obj.pos[0] + obj.size[0] >= sub.pos[0]:
                                return 1
        return 0

    def kill_player(self, obj):
        for sub in self.players:
            if sub.alive and sub.solid and sub.name != obj.name:
                if sub.pos[1] + 0.1 * sub.size[1] >= obj.pos[1] + obj.size[1]:
                    if obj.pos[1] + obj.size[1] >= sub.pos[1]:
                        if sub.pos[0] + 0.1 * sub.size[0] >= obj.pos[0]:
                            if obj.pos[0] + 0.1 * obj.size[0] >= sub.pos[0]:
                                # NOTE: if the color is 0x000000 then the player is invincible
                                if sub.color != 0:
                                    sub.alive = 0

    def new_pos(self, obj, i):
        # Find new position without overlapping any solid objects
        new_i = obj.pos[i] + obj.speed[i]
        if obj.speed[i] != 0:
            k = not i
            for sub in self.blocks + self.players:
                if sub.alive and sub.solid and sub.name != obj.name:
                    if obj.pos[k] + obj.size[k] > sub.pos[k]:
                        if sub.pos[k] + sub.size[k] > obj.pos[k]:
                            # This means the subject is on the same opposite dimensional line as the object
                            if new_i + obj.size[i] > sub.pos[i]:
                                if sub.pos[i] + sub.size[i] > new_i:
                                    if obj.pos[i] < new_i:
                                        new_i = sub.pos[i] - obj.size[i]
                                    else:
                                        new_i = sub.pos[i] + sub.size[i]
                                    obj.speed[i] = 0
        return new_i
        
class block_object():
    def __init__(self, data):
        self.name = data[0][8:-2]
        self.color = int(data[1][8:16], 16)
        self.pos = findxy(data[2])
        self.size = findxy(data[3])
        self.solid = float(data[4][8:])
        self.movable = float(data[5][10:])
        self.gravity = float(data[6][10:])
        self.alive = 1

class player_object():
    def __init__(self, data, save_file, game):
        self.name = data[0][8:-2]
        self.base_color = int(data[1][8:16], 16)
        self.color = self.base_color
        self.shield_color = 0
        self.base_pos = findxy(data[2])
        self.pos = self.base_pos
        self.size = findxy(data[3])
        self.base_speed = float(data[4][8:])
        self.target_speed = [0, 0]
        self.speed = [0, 0]
        self.acceleration = float(data[5][15:])
        self.jump_strength = float(data[6][16:])
        self.gravity = float(data[7][10:])
        self.base_shield_health = float(data[8][16:])
        self.shield_health = self.base_shield_health
        self.shield_regen = float(data[9][15:])
        self.shield_broken = 0
        self.solid = 1
        self.alive = 1
        # Check if inputs exist for this player
        for i in range(0, len(save_file)):
            if save_file[i][0:-1] == self.name:
                self.controls = []
                for ii in range(1, 5):
                    self.controls.append(int(save_file[i+ii]))
                break
        else:
            self.set_controls(game)
        self.inputs = [0, 0, 0, 0]

    def set_controls(self, game):
        self.controls = []
        # Need left, right, jump, Shield
        print("Press Left Key")
        self.controls.append(self.set_key(game, 'Left'))
        print("Press Right Key")
        self.controls.append(self.set_key(game, 'Right'))
        print("Press Jump Key")
        self.controls.append(self.set_key(game, 'Jump'))
        print("Press Shield Key")
        self.controls.append(self.set_key(game, 'Shield'))

    def set_key(self, game, button):
        game.surface.fill(0xffffff)
        game.map_image = game.big_font.render(self.name + ': Press ' + button, True, (0, 0, 0))
        game.surface.blit(game.map_image, [256, game.display_size[1]/2])
        game.display.blit(pygame.transform.scale(game.surface, game.display_size), [0, 0])
        pygame.display.update()
        while 1:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    return event.key

# Find [x,y] in 'word = [x,y]'
def findxy(string):
    i = 0
    while 1:
        if string[i] == '[':
            ii = i
            while 1:
                if string[ii] == ',':
                    x = int(string[i+1:ii])
                    i = ii
                    break
                ii += 1
            while 1:
                if string[ii] == ']':
                    y = int(string[i+1:ii])
                    break
                ii += 1
            break
        i += 1
    return [x,y]
