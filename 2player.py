from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import sys
import os
import shapes

# Game state
GAME_STATE = "MENU"  # Can be "MENU", "PLAYING", or "GAME_OVER"
TARGET_FPS = 60.0
frame_scale = 1.0
last_time = None

# Player 1 data
PLAYER1_HP = 3
player1_x = -200
player1_z = 0
player1_y = 575
player1_is_jumping = False
player1_jump_velocity = 0
player1_is_crouching = False
player1_spawn_protection_time = 0
PLAYER1_COLOR = (0, 1, 1)  # Cyan

# Player 2 data
PLAYER2_HP = 3
player2_x = 200
player2_z = 0
player2_y = 575
player2_is_jumping = False
player2_jump_velocity = 0
player2_is_crouching = False
player2_spawn_protection_time = 0
PLAYER2_COLOR = (1, 0, 1)  # Magenta
player1_shoot_cooldown = 0
player2_shoot_cooldown = 0

camera_pos = (0, 700, 400)
mobs = [{'x': 0, 'y': -600, 'z': 30, 'delay': 0, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 30, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 60, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 90, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5},
        {'x': 0, 'y': -600, 'z': 30, 'delay': 120, 'colliding_p1': False, 'colliding_p2': False, 'hp': 5}]
bullets = []  # List to store active bullets from both players
PITCH_HALF = 600
PLAYER_RADIUS_Y = 45
PLAYER_RADIUS_X = 30

ground_level = 0

# Key state tracking for simultaneous input
keys_down = set()
special_down = set()

def keyboard(key, x, y):
    global player1_x, player1_y, player1_z, player1_is_jumping, player1_jump_velocity, player1_is_crouching
    global player2_x, player2_y, player2_z, player2_is_jumping, player2_jump_velocity, player2_is_crouching
    global GAME_STATE, PLAYER1_HP, PLAYER2_HP, keys_down
    k = key.decode("utf-8").lower()

    # Handle ESC key to return to menu from playing
    if k == '\x1b' and GAME_STATE == "PLAYING":
        GAME_STATE = "MENU"
        print("Returned to menu!")
        return

    # Handle 'm' key to return to menu from game over
    if k == 'm' and GAME_STATE == "GAME_OVER":
        reset_game()
        GAME_STATE = "MENU"
        print("Returning to menu!")
        return

    # Only process game controls if playing
    if GAME_STATE != "PLAYING":
        return

    # Track held keys for continuous movement
    keys_down.add(k)

    # Player 1 one-shot actions (only if alive)
    if PLAYER1_HP > 0:
        if k == ' ' and not player1_is_jumping and not player1_is_crouching:
            player1_is_jumping = True
            player1_jump_velocity = 25
        elif k == 'c':
            player1_is_crouching = not player1_is_crouching

    # Player 2 one-shot actions (only if alive)
    if PLAYER2_HP > 0:
        if k == ',' and not player2_is_jumping and not player2_is_crouching:
            player2_is_jumping = True
            player2_jump_velocity = 25
        elif k == '.':
            player2_is_crouching = not player2_is_crouching

def special_keys(key, x, y):
    """Handle special keys (arrow keys) for player 2"""
    global GAME_STATE, PLAYER2_HP, special_down
    
    if GAME_STATE != "PLAYING":
        return
    if PLAYER2_HP <= 0:
        return
    
    special_down.add(key)

def special_keys_up(key, x, y):
    global special_down
    special_down.discard(key)

def keyboard_up(key, x, y):
    """Handle key release events"""
    global keys_down
    k = key.decode("utf-8").lower()
    keys_down.discard(k)

def clamp_player_position(player_num):
    """Clamp player position within bounds"""
    global player1_x, player1_y, player2_x, player2_y
    
    max_x = PITCH_HALF - PLAYER_RADIUS_X - 50
    min_x = -PITCH_HALF + PLAYER_RADIUS_X + 50
    max_y = PITCH_HALF - PLAYER_RADIUS_Y - 20
    min_y = -PITCH_HALF + PLAYER_RADIUS_Y + 20
    
    if player_num == 1:
        if player1_x > max_x: player1_x = max_x
        if player1_x < min_x: player1_x = min_x
        if player1_y > max_y: player1_y = max_y
        if player1_y < min_y: player1_y = min_y
    else:
        if player2_x > max_x: player2_x = max_x
        if player2_x < min_x: player2_x = min_x
        if player2_y > max_y: player2_y = max_y
        if player2_y < min_y: player2_y = min_y

def shoot(player_num, px, py, pz):
    """Fire a bullet from the player's position towards the wall"""
    if GAME_STATE == "PLAYING":
        bullet = {
            'x': px,
            'y': py - 50,
            'z': pz + 60,
            'vy': -15,
            'player': player_num
        }
        bullets.append(bullet)
        print(f"Player {player_num} fired!")

def update_bullets():
    """Update bullet positions and check collisions"""
    global bullets, mobs
    bullets_to_remove = []
    
    for i, bullet in enumerate(bullets):
        bullet['y'] += bullet['vy'] * frame_scale
        
        if bullet['y'] < -650:
            bullets_to_remove.append(i)
            continue
        
        for mob in mobs:
            mob_x_min = mob['x'] - 80
            mob_x_max = mob['x'] + 80
            mob_y_min = mob['y'] - 80
            mob_y_max = mob['y'] + 80
            mob_z_min = mob['z'] - 80
            mob_z_max = mob['z'] + 80
            
            bullet_x_min = bullet['x'] - 20
            bullet_x_max = bullet['x'] + 20
            bullet_y_min = bullet['y'] - 20
            bullet_y_max = bullet['y'] + 20
            bullet_z_min = bullet['z'] - 80
            bullet_z_max = bullet['z'] + 80
            
            if (mob_x_min < bullet_x_max and mob_x_max > bullet_x_min and
                mob_y_min < bullet_y_max and mob_y_max > bullet_y_min and
                mob_z_min < bullet_z_max and mob_z_max > bullet_z_min):
                mob['hp'] -= 1
                if i not in bullets_to_remove:
                    bullets_to_remove.append(i)
                
                if mob['hp'] <= 0:
                    mob['x'] = random.randrange(-580, 580)
                    mob['y'] = -600
                    mob['z'] = random.choice([0, 145])
                    mob['hp'] = 5
                    mob['colliding_p1'] = False
                    mob['colliding_p2'] = False
                    mob['delay'] = 0
                break
    
    for i in sorted(bullets_to_remove, reverse=True):
        if i < len(bullets):
            bullets.pop(i)

def draw_bullets():
    """Draw all active bullets"""
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(bullet['x'], bullet['y'], bullet['z'])
        if bullet['player'] == 1:
            glColor3f(0, 1, 1)  # Cyan for player 1
        else:
            glColor3f(1, 0, 1)  # Magenta for player 2
        glScalef(15, 15, 15)
        glutSolidCube(1)
        glPopMatrix()

def update_players():
    global player1_z, player1_is_jumping, player1_jump_velocity
    global player2_z, player2_is_jumping, player2_jump_velocity
    
    # Update player 1 jump
    if player1_is_jumping:
        player1_z += player1_jump_velocity * frame_scale
        player1_jump_velocity -= 1 * frame_scale
        if player1_z < ground_level:
            player1_z = ground_level
            player1_is_jumping = False
            player1_jump_velocity = 0
    
    # Update player 2 jump
    if player2_is_jumping:
        player2_z += player2_jump_velocity * frame_scale
        player2_jump_velocity -= 1 * frame_scale
        if player2_z < ground_level:
            player2_z = ground_level
            player2_is_jumping = False
            player2_jump_velocity = 0

def draw_player(player_num, px, py, pz, is_crouching, spawn_protection_time, color):
    # Skip drawing during blink off phase of spawn protection
    if spawn_protection_time > 0:
        if (spawn_protection_time // 10) % 2 == 0:
            return
    
    glPushMatrix()
    glTranslatef(px, py, pz)
    glRotatef(90, 1, 0, 0)
    if is_crouching:
        glScalef(150, 150 * 0.7, 150)
    else:
        glScalef(150, 150, 150)

    glColor3f(0, 0, 1)
    for i in [-0.2, 0.2]:
        glPushMatrix()
        glTranslatef(i, 0.4, 0)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 0.1, 0.05, 0.4, 10, 10)
        glPopMatrix()
    
    r, g, b = color
    glColor3f(r, g, b)
    glPushMatrix()
    glTranslatef(0, 1, 0)
    glScalef(0.4, 0.6, 0.2)
    glutSolidCube(1)
    glPopMatrix()

    glColor3f(0.96, 0.8, 0.69)
    for o in [-0.15, 0.15]:
        glPushMatrix()
        glTranslatef(o, 1.2, 0.1)
        gluCylinder(gluNewQuadric(), 0.1, 0.05, 0.4, 10, 10)
        glPopMatrix()

    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(0, 1.2, 0.1)
    gluCylinder(gluNewQuadric(), 0.08, 0, 0.8, 10, 10)
    glPopMatrix()

    glColor3f(0, 0, 0)
    glPushMatrix()
    glTranslatef(0, 1.65, 0)
    gluSphere(gluNewQuadric(), 0.2, 10, 10)
    glPopMatrix()

    glPopMatrix()

def draw_enemy():
    for mob in mobs:
        glPushMatrix()
        glColor3f(1, 0, 0)
        glTranslatef(mob['x'], mob['y'], mob['z'])
        glutSolidCube(100)
        glPopMatrix()

def setup_camera():
    """Fixed camera for 2-player mode - positioned for better enemy visibility"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(120, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    gluLookAt(0, 800, 500,
              0, 0, 0,
              0, 0, 1)

def check_collision():
    global player1_x, player1_y, player1_z, player1_spawn_protection_time, PLAYER1_HP
    global player2_x, player2_y, player2_z, player2_spawn_protection_time, PLAYER2_HP
    global player1_is_crouching, player2_is_crouching
    
    # Check player 1 collisions
    if player1_spawn_protection_time <= 0:
        player1_x_min = player1_x - PLAYER_RADIUS_X
        player1_x_max = player1_x + PLAYER_RADIUS_X
        player1_y_min = player1_y - PLAYER_RADIUS_Y
        player1_y_max = player1_y + PLAYER_RADIUS_Y
        player1_z_min = player1_z
        player1_z_max = player1_z + (70 if player1_is_crouching else 100)
        
        for mob in mobs:
            enemy_x_min = mob['x'] - 50
            enemy_x_max = mob['x'] + 50
            enemy_y_min = mob['y'] - 50
            enemy_y_max = mob['y'] + 50
            enemy_z_min = mob['z'] - 50
            enemy_z_max = mob['z'] + 50
            
            is_colliding = (player1_x_min < enemy_x_max and player1_x_max > enemy_x_min and
                           player1_y_min < enemy_y_max and player1_y_max > enemy_y_min and
                           player1_z_min < enemy_z_max and player1_z_max > enemy_z_min)
            
            if is_colliding:
                if not mob['colliding_p1']:
                    PLAYER1_HP -= 1
                    player1_x = -200
                    player1_y = 575
                    player1_z = 0
                    player1_spawn_protection_time = 180
                    mob['colliding_p1'] = True
                mob['colliding_p1'] = True
            else:
                mob['colliding_p1'] = False
    
    # Check player 2 collisions
    if player2_spawn_protection_time <= 0:
        player2_x_min = player2_x - PLAYER_RADIUS_X
        player2_x_max = player2_x + PLAYER_RADIUS_X
        player2_y_min = player2_y - PLAYER_RADIUS_Y
        player2_y_max = player2_y + PLAYER_RADIUS_Y
        player2_z_min = player2_z
        player2_z_max = player2_z + (70 if player2_is_crouching else 100)
        
        for mob in mobs:
            enemy_x_min = mob['x'] - 50
            enemy_x_max = mob['x'] + 50
            enemy_y_min = mob['y'] - 50
            enemy_y_max = mob['y'] + 50
            enemy_z_min = mob['z'] - 50
            enemy_z_max = mob['z'] + 50
            
            is_colliding = (player2_x_min < enemy_x_max and player2_x_max > enemy_x_min and
                           player2_y_min < enemy_y_max and player2_y_max > enemy_y_min and
                           player2_z_min < enemy_z_max and player2_z_max > enemy_z_min)
            
            if is_colliding:
                if not mob['colliding_p2']:
                    PLAYER2_HP -= 1
                    player2_x = 200
                    player2_y = 575
                    player2_z = 0
                    player2_spawn_protection_time = 180
                    mob['colliding_p2'] = True
                mob['colliding_p2'] = True
            else:
                mob['colliding_p2'] = False

def spawn_mobs():
    for mob in mobs:
        if mob['delay'] > 0:
            mob['delay'] -= frame_scale
            continue
        if mob['y'] != 575:
            mob['y'] += 10 * frame_scale
        if mob['y'] >= 575:
            mob['y'] = -600
            mob['x'] = random.randrange(-580, 580)
            mob['z'] = random.choice([0, 145])
            mob['delay'] = random.randrange(60, 120)

def apply_held_movement():
    """Apply continuous movement based on held keys (supports simultaneous input)."""
    global player1_x, player1_y, player2_x, player2_y, frame_scale
    global player1_shoot_cooldown, player2_shoot_cooldown
    step = 10 * frame_scale

    if PLAYER1_HP > 0:
        if 'w' in keys_down:
            player1_y -= step
        if 's' in keys_down:
            player1_y += step
        if 'a' in keys_down:
            player1_x += step
        if 'd' in keys_down:
            player1_x -= step
        # Shooting with cooldown
        if 'f' in keys_down and player1_shoot_cooldown <= 0:
            shoot(1, player1_x, player1_y, player1_z)
            player1_shoot_cooldown = 10
        clamp_player_position(1)

    if PLAYER2_HP > 0:
        if GLUT_KEY_UP in special_down:
            player2_y -= step
        if GLUT_KEY_DOWN in special_down:
            player2_y += step
        if GLUT_KEY_LEFT in special_down:
            player2_x += step
        if GLUT_KEY_RIGHT in special_down:
            player2_x -= step
        # Shooting with cooldown (L key)
        if 'l' in keys_down and player2_shoot_cooldown <= 0:
            shoot(2, player2_x, player2_y, player2_z)
            player2_shoot_cooldown = 10
        clamp_player_position(2)

def idle():
    global player1_spawn_protection_time, player2_spawn_protection_time, GAME_STATE, frame_scale, last_time
    global player1_shoot_cooldown, player2_shoot_cooldown

    current_time = glutGet(GLUT_ELAPSED_TIME) / 1000.0
    if last_time is None:
        last_time = current_time
        delta_time = 1.0 / TARGET_FPS
    else:
        delta_time = max(0.0, current_time - last_time)
        last_time = current_time

    frame_scale = delta_time * TARGET_FPS
    
    # Decrease shoot cooldowns
    if player1_shoot_cooldown > 0:
        player1_shoot_cooldown -= frame_scale
    if player2_shoot_cooldown > 0:
        player2_shoot_cooldown -= frame_scale
    
    if GAME_STATE == "PLAYING":
        apply_held_movement()
        spawn_mobs()
        check_collision()
        update_players()
        update_bullets()
        
        if player1_spawn_protection_time > 0:
            player1_spawn_protection_time -= frame_scale
            if player1_spawn_protection_time < 0:
                player1_spawn_protection_time = 0
        if player2_spawn_protection_time > 0:
            player2_spawn_protection_time -= frame_scale
            if player2_spawn_protection_time < 0:
                player2_spawn_protection_time = 0
        
        # Game over when BOTH players are dead
        if PLAYER1_HP <= 0 and PLAYER2_HP <= 0:
            GAME_STATE = "GAME_OVER"
    
    glutPostRedisplay()

def game():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    setup_camera()
    
    shapes.pitch()
    shapes.wall()
    shapes.background()
    
    draw_bullets()
    if PLAYER1_HP > 0:
        draw_player(1, player1_x, player1_y, player1_z, player1_is_crouching, player1_spawn_protection_time, PLAYER1_COLOR)
    if PLAYER2_HP > 0:
        draw_player(2, player2_x, player2_y, player2_z, player2_is_crouching, player2_spawn_protection_time, PLAYER2_COLOR)
    draw_enemy()
    
    # Draw HP on screen
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glDisable(GL_DEPTH_TEST)
    
    # Player 1 HP (left side, cyan or gray if dead)
    if PLAYER1_HP > 0:
        glColor3f(0, 1, 1)
    else:
        glColor3f(0.5, 0.5, 0.5)  # Gray when dead
    glRasterPos2f(20, 30)
    hp_text = f"P1 HP: {PLAYER1_HP}" if PLAYER1_HP > 0 else "P1 HP: 0 (DEAD)"
    for char in hp_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Player 2 HP (right side, magenta or gray if dead)
    if PLAYER2_HP > 0:
        glColor3f(1, 0, 1)
    else:
        glColor3f(0.5, 0.5, 0.5)  # Gray when dead
    glRasterPos2f(800, 30)
    hp_text = f"P2 HP: {PLAYER2_HP}" if PLAYER2_HP > 0 else "P2 HP: 0 (DEAD)"
    for char in hp_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glEnable(GL_DEPTH_TEST)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def draw_menu():
    """Draw the main menu screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw background
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.3)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    # Draw title
    glColor3f(1, 1, 1)
    glRasterPos2f(300, 200)
    title = "2 PLAYER MODE"
    for char in title:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw PLAY button
    glColor3f(0, 1, 1)
    glRasterPos2f(450, 350)
    play_text = "PLAY"
    for char in play_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw BACK TO MENU button
    glColor3f(1, 0.5, 0)
    glRasterPos2f(400, 450)
    back_text = "BACK TO MENU"
    for char in back_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def draw_game_over():
    """Draw the game over screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 800, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw background
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.2, 0.3)
    glVertex2f(0, 0)
    glVertex2f(1000, 0)
    glVertex2f(1000, 800)
    glVertex2f(0, 800)
    glEnd()
    
    # Draw GAME OVER text
    glColor3f(1, 0, 0)
    glRasterPos2f(350, 300)
    game_over_text = "GAME OVER"
    for char in game_over_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    # Draw return to menu instruction
    glColor3f(1, 1, 1)
    glRasterPos2f(300, 500)
    instruction_text = "Press 'm' to return to menu"
    for char in instruction_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    
    glEnable(GL_DEPTH_TEST)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    
    glutSwapBuffers()

def reset_game():
    """Reset all game variables"""
    global PLAYER1_HP, PLAYER2_HP
    global player1_x, player1_y, player1_z, player1_is_jumping, player1_jump_velocity, player1_is_crouching, player1_spawn_protection_time
    global player2_x, player2_y, player2_z, player2_is_jumping, player2_jump_velocity, player2_is_crouching, player2_spawn_protection_time
    global bullets, mobs
    
    PLAYER1_HP = 3
    PLAYER2_HP = 3
    
    player1_x = -200
    player1_y = 575
    player1_z = 0
    player1_is_jumping = False
    player1_jump_velocity = 0
    player1_is_crouching = False
    player1_spawn_protection_time = 0
    
    player2_x = 200
    player2_y = 575
    player2_z = 0
    player2_is_jumping = False
    player2_jump_velocity = 0
    player2_is_crouching = False
    player2_spawn_protection_time = 0
    
    bullets.clear()
    
    for mob in mobs:
        mob['x'] = 0
        mob['y'] = -600
        mob['z'] = 30
        mob['delay'] = random.randrange(0, 121)
        mob['colliding_p1'] = False
        mob['colliding_p2'] = False
        mob['hp'] = 5

def mouse(button, state, x, y):
    """Handle mouse clicks"""
    global GAME_STATE
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        # Check if click is within PLAY button area
        if 430 < x < 530 and 335 < y < 365 and GAME_STATE == "MENU":
            reset_game()
            GAME_STATE = "PLAYING"
            print("2 Player mode started!")
        
        # Check if click is within BACK TO MENU button area
        elif 400 < x < 600 and 435 < y < 465 and GAME_STATE == "MENU":
            print("Returning to main menu...")
            os._exit(0)

def showScreen():
    global GAME_STATE
    
    if GAME_STATE == "MENU":
        draw_menu()
    elif GAME_STATE == "PLAYING":
        game()
    elif GAME_STATE == "GAME_OVER":
        draw_game_over()

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(1000, 800)
wind = glutCreateWindow(b"Drop 'n' Run - 2 Player")
glutDisplayFunc(showScreen)
glutIdleFunc(idle)
glutKeyboardFunc(keyboard)
glutKeyboardUpFunc(keyboard_up)
glutSpecialFunc(special_keys)  # Add special keys handler for arrow keys
glutSpecialUpFunc(special_keys_up)
glutMouseFunc(mouse)
glutInitWindowPosition(0, 0)
glutMainLoop()
