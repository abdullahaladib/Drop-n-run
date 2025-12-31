from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random


def setup_camera():
  glMatrixMode(GL_PROJECTION)
  glLoadIdentity()
  gluPerspective(120, 1.25, 0.1, 1500)
  glMatrixMode(GL_MODELVIEW)
  gluLookAt(0, 10, 400,
            0, 0, 0,
            0,0,1)

def menuScreen():
  glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
  glLoadIdentity()
  glViewport(0, 0, 1000, 800)

  setup_camera()

  glLineWidth(10)
  glColor3f(1,1,1)

  glBegin(GL_LINES)
  
  glVertex3f(-600, 600, 0)
  glVertex3f(-600, -600, 0)
  
  glEnd()

  glBegin(GL_LINES)
  
  glVertex3f(600, 600, 0)
  glVertex3f(600, -600, 0)
  
  glEnd()

  glBegin(GL_LINES)
  
  glVertex3f(600, 600, 0)
  glVertex3f(-600, 600, 0)
  
  glEnd()

  glBegin(GL_LINES)
  
  glVertex3f(600, -600, 0)
  glVertex3f(-600, -600, 0)
  
  glEnd()
  
  glutSwapBuffers()