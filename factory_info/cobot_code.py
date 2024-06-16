import cv2
import numpy as np
from pymycobot.mycobot import MyCobot
import time

#mc.send_angles([0,-25,-40,-15,90,90],40) 잡을 위치

mc = MyCobot('COM3',115200)

mc.set_gripper_mode(0)
mc.init_eletric_gripper()

def init():
    mc.send_angles([0,0,0,0,90,0],40)
    time.sleep(4)

def gripper_open():
    print("OPEN")
    mc.set_eletric_gripper(0)
    mc.set_gripper_value(100,30) # 그리퍼 열기
    time.sleep(2)
    
def gripper_close(): #block에서만 쓸것.
    print("CLOSE")
    mc.set_eletric_gripper(1)
    mc.set_gripper_value(45,30) # 그리퍼 닫기
    time.sleep(2)
    
def wait():
    mc.send_angles([0,-23,-40,-17,90,90],40)
    time.sleep(3)
    
def up_release():
    mc.send_angles([0,0,0,0,90,90],40)
    time.sleep(3)

    mc.send_angles([100,0,0,0,90,90],40)
    time.sleep(3)

    mc.send_angles([100,-40,-35,-0,90,90],40)
    time.sleep(3)
    
def stand():
    mc.send_angles([100,0,0,0,90,90],40)
    time.sleep(3)

    mc.send_angles([0,0,0,0,90,90],40)
    time.sleep(3)
init()
wait()

while True:
    err = input("err : ")
    if err == "T":
        wait()
        gripper_open()
        gripper_close()
        up_release()
        gripper_open()
        stand()
        wait()