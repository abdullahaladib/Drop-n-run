from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import shapes
import menu
from spawnprotection import SpawnProtection

# Initialize spawn protection system
protection = SpawnProtection()

PLAYER_SCORE = 0
DAMAGE = 1
MOB_HP = 5
PLAYER_SKIN_COLOR = (0,1,1)

camera_pos = (0,700,400)
player1_x = 0
player1_z = 0
player1_y = 575  # start at center of pitch
mobs = [{'x': 0, 'y': -600, 'z': 20, 'delay': 0},
        {'x': 0, 'y': -600, 'z': 20, 'delay': 30},
        {'x': 0, 'y': -600, 'z': 20, 'delay': 60},
        {'x': 0, 'y': -600, 'z': 20, 'delay': 90},
        {'x': 0, 'y': -600, 'z': 20, 'delay': 120}]
PITCH_HALF = 600
# The player model is scaled by 150. The body is a cube scaled by (0.4, 0.6, 0.2).
# This means the visual radius is different for X and Y axes.
# Y-radius = (0.6 * 150) / 2 = 45
# X-radius = (0.4 * 150) / 2 = 30
PLAYER_RADIUS_Y = 45
PLAYER_RADIUS_X = 30

is_jumping = False
jump_velocity = 0
is_crouching = False
ground_level = 0

def keyboard(key, x, y):
    global player1_x, player1_y, player1_z, is_jumping, jump_velocity, is_crouching
    key = key.decode("utf-8").lower()

    step = 10

    if key == 'w':
        player1_y -= step
    elif key == 's':
        player1_y += step
    elif key == 'a':
        player1_x += step
    elif key == 'd':
        player1_x -= step
    elif key == ' ' and not is_jumping and is_crouching == False:
        is_jumping = True
        jump_velocity = 25
    elif key == 'c':
        is_crouching = not is_crouching
    elif key == 'f':
        shoot()
    
    # Clamp using calculated constants with larger margin
    max_x = PITCH_HALF - PLAYER_RADIUS_X - 50
    min_x = -PITCH_HALF + PLAYER_RADIUS_X + 50
    max_y = PITCH_HALF - PLAYER_RADIUS_Y - 20
    min_y = -PITCH_HALF + PLAYER_RADIUS_Y + 20
    
    if player1_x > max_x:
        player1_x = max_x
    if player1_x < min_x:
        player1_x = min_x
    if player1_y > max_y:
        player1_y = max_y
    if player1_y < min_y:
        player1_y = min_y


def shoot():
    print("Shoot!")

def update_player():
    global player1_z, player1_x, player1_y, is_jumping, jump_velocity
    if is_jumping:
        player1_z += jump_velocity
        jump_velocity -= 1 # Gravity
        if player1_z < ground_level:
            player1_z = ground_level
            is_jumping = False
            jump_velocity = 0
    
    # Clamp using calculated constants with larger margin
    max_x = PITCH_HALF - PLAYER_RADIUS_X - 50
    min_x = -PITCH_HALF + PLAYER_RADIUS_X + 50
    max_y = PITCH_HALF - PLAYER_RADIUS_Y - 50
    min_y = -PITCH_HALF + PLAYER_RADIUS_Y + 50
    
    if player1_x > max_x:
        player1_x = max_x
    if player1_x < min_x:
        player1_x = min_x
    if player1_y > max_y:
        player1_y = max_y
    if player1_y < min_y:
        player1_y = min_y

def draw_player():
  glPushMatrix()
  glTranslatef(player1_x, player1_y, player1_z)
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
  
  r,g,b = PLAYER_SKIN_COLOR
  glColor3f(r,g,b)
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
    glColor3f(1,0,0)
    glTranslatef(mob['x'],mob['y'],mob['z'])
    glutSolidCube(100)
    glPopMatrix()

def setup_camera():
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()
  gluPerspective(120, 1.25, 0.1, 1500)
  glMatrixMode(GL_MODELVIEW)
  cam_x = player1_x
  cam_y = 700
  cam_z = 400
  gluLookAt(cam_x, cam_y, cam_z,
            player1_x, 0, 0,
            0,0,1)

def check_collision():
  # Player collision box
  player_x_min = player1_x - PLAYER_RADIUS_X
  player_x_max = player1_x + PLAYER_RADIUS_X
  player_y_min = player1_y - PLAYER_RADIUS_Y
  player_y_max = player1_y + PLAYER_RADIUS_Y
  player_z_min = player1_z
  # Reduce height when crouching
  if is_crouching:
    player_z_max = player1_z + 70
  else:
    player_z_max = player1_z + 100
  
  # Check collision with all enemies
  for idx, mob in enumerate(mobs):
    # Enemy collision box (cube of size 100)
    enemy_x_min = mob['x'] - 50
    enemy_x_max = mob['x'] + 50
    enemy_y_min = mob['y'] - 50
    enemy_y_max = mob['y'] + 50
    enemy_z_min = mob['z'] - 50
    enemy_z_max = mob['z'] + 50
    
    # Check collision
    if (player_x_min < enemy_x_max and player_x_max > enemy_x_min and
        player_y_min < enemy_y_max and player_y_max > enemy_y_min and
        player_z_min < enemy_z_max and player_z_max > enemy_z_min):
      # Use spawn protection to handle collision with this specific mob
      if protection.handle_collision_detected(idx):
        # Player is protected, phase through obstacle
        continue  # Don't process damage, check next mob
      else:
        # Player not protected, collision takes effect
        return False
  return True

def spawn_mobs():
  for mob in mobs:
    if mob['delay'] > 0:
      mob['delay'] -= 1
      continue
    if mob['y'] != 575:
      mob['y'] += 10
    if mob['y'] >= 575:
      mob['y'] = -600
      mob['x'] = random.randrange(-580,580)
      mob['z'] = random.choice([0,145])
      mob['delay'] = random.randrange(60, 120)
def idle():
    protection.update()  # Update protection timer
    spawn_mobs()
    check_collision()
    update_player()
    glutPostRedisplay()

def game():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    setup_camera()
    
    shapes.pitch()
    shapes.wall()
    shapes.background()
    
    draw_player()
    draw_enemy()
    glutSwapBuffers()
def showScreen():
    game()
    #menu.menuScreen()
    
glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(1000, 800)
wind = glutCreateWindow(b"Drop 'n' Run")
glutDisplayFunc(showScreen)
glutIdleFunc(idle)
glutKeyboardFunc(keyboard)
glutInitWindowPosition(0,0)
glutMainLoop()