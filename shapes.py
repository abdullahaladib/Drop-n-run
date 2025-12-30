from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random


def pitch():
  glBegin(GL_QUADS)

  glColor3f(1,1,1)
  glVertex3f(600, 600, 0)
  glVertex3f(-600, 600, 0)
  glVertex3f(-600, -600, 0)
  glVertex3f(600, -600, 0)  
  
  glEnd()

def wall():
    glBegin(GL_QUADS)
    glColor3f(0,0.65,1)
    glVertex3f(-10000,-600, 0)
    glVertex3f(10000,-600, 0)
    glVertex3f(10000,-600, 10000)
    glVertex3f(-10000,-600, 10000)

    glEnd()
    
    glLineWidth(40)
    glBegin(GL_LINES)
    glColor3f(0,0,0)
    glVertex3f(-10000,-600, 0)
    glVertex3f(10000,-600,0)
    glEnd()

def background():
    glBegin(GL_QUADS)
    glColor3f(0,0.45,0)
    glVertex3f(-10000,600, 0)
    glVertex3f(-600,600, 0)
    glVertex3f(-600,-600, 0)
    glVertex3f(-10000,-600, 0)

    glEnd()

    glBegin(GL_QUADS)
    glColor3f(0,0.45,0)
    glVertex3f(10000,600, 0)
    glVertex3f(600,600, 0)
    glVertex3f(600,-600, 0)
    glVertex3f(10000,-600, 0)

    glEnd()
    glLineWidth(40)
    glBegin(GL_LINES)
    glColor3f(0,0,0)
    glVertex3f(-600,-600, 0)
    glVertex3f(-600,600,0)
    glEnd()

    glBegin(GL_LINES)
    glColor3f(0,0,0)
    glVertex3f(600,-600, 0)
    glVertex3f(600,600,0)
    glEnd()