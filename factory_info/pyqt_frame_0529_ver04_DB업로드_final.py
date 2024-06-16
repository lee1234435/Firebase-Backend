import sys
import cv2
import os
import numpy as np
import time
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import datetime
import pyqtgraph as pg
from ultralytics import YOLO
from pymycobot.mycobot import MyCobot
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from firebase_admin import firestore
from uuid import uuid4

#================= DB CONFIG =================#
PROJECT_ID = "factory-info-a8045"
DB_IMG_DIR = "https://storage.googleapis.com/factory-info-a8045.appspot.com"

cred = credentials.Certificate('factory-info-a8045-firebase-adminsdk-e52rt-8d55b6c4ed.json')
default_app = firebase_admin.initialize_app(cred,{'storageBucket':f"{PROJECT_ID}.appspot.com"})

db = firestore.client()
bucket = storage.bucket()

collection_name = 'factory_info'

data = {}

#===========================================#

mc = MyCobot('COM3',115200)

mc.set_gripper_mode(0)
mc.init_eletric_gripper()

def fileUpload(file):
    blob = bucket.blob("images/" + file) #저장한 사진을 파이어베이스 storage의 image_store라는 이름의 디렉토리에 저장
    #new token and metadata 설정
    new_token = uuid4()
    metadata = {"firebaseStorageDownloadTokens": new_token} #access token이 필요하다.
    blob.metadata = metadata
 
    #upload file
    blob.upload_from_filename(filename= "images/" + file, content_type='image/png') #파일이 저장된 주소와 이미지 형식(jpeg도 됨)
    #debugging hello
    print("hello ")
    print(blob.public_url)

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

#===========================================#

step = 0
ser_num = "SN" + datetime.datetime.now().strftime("%Y%m%d") 
classNames = ['Grap', 'Pass', 'Product']
x1,x2,y1,y2 = 0,0,0,0
total_cnt = 0
nomal_cnt = 0
detc_cnt = 0

new_ = 1
action = 0

images_dir = "images"
image_filename = ""
image_path = ""
object_img = ""

class CameraThread(QThread):
    update_frame = pyqtSignal(QImage)
    update_product_info = pyqtSignal(str, str, str)
    update_bar_graph = pyqtSignal(int, int, int)


    def __init__(self, parent=None):
        super(CameraThread, self).__init__(parent)
        self.cap = cv2.VideoCapture(0)
        self.model = YOLO('Quality Control.pt')  # Load your custom YOLOv8 model
        self.running = True

    def run(self):
        global step, x1, x2, y1, y2, images_dir, image_filename, image_path, new_, object_img, total_cnt, nomal_cnt, detc_cnt, action, data
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                results = self.model(frame,conf = 0.9)
                annotated_frame = results[0].plot()

                detected_classes = []
                boxes_dict = {}
                
                
                color_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = color_frame.shape
                bytes_per_line = ch * w
                converted_frame = QImage(color_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.update_frame.emit(converted_frame) # gui 캠 업데이트
                
                
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        cls = int(box.cls[0])
                        cls_name = classNames[min(cls, len(classNames) - 1)]
                        detected_classes.append(cls_name)
                        boxes_dict[cls_name] = (x1, y1, x2, y2) # 박스의 좌표를 딕셔너리에 저장
                        
                        ############################################################3
                        
                        if 'Product' not in detected_classes:
                            print("product not in detected_classes")
                            serial_number = ''
                            qc_status = ""
                            txt_color = "Color : black"
                            self.update_product_info.emit(serial_number, qc_status, txt_color)
                            
                            step = 0
                            
                        if 'Product' in detected_classes and step == 0 and new_ == 1:
                        
                            image_filename = f'{ser_num}{total_cnt:03d}.jpg'
                            image_path = os.path.join(images_dir, image_filename)
                            step = 1
                            # time.sleep(0.1)
                            
                        elif 'Grap' in detected_classes and step == 1 and new_ == 1:
                            
                            x1, y1, x2, y2 = boxes_dict['Product']
                            object_img = annotated_frame[y1-15:y2+15, x1-15:x2+15]
                            serial_number = f'{ser_num}{total_cnt:03d}'
                            qc_status = "FAIL"
                            txt_color = "Color : red"
                            self.update_product_info.emit(serial_number, qc_status, txt_color)
                            
                            cv2.imwrite(image_path, object_img)
                            
                            data = {                                
                                'QC': qc_status,
                                'img': DB_IMG_DIR + "/images/" + image_filename
                            }
                            
                            # db에 데이터 저장
                            db.collection(collection_name).document(serial_number).set(data)
                            fileUpload(image_filename)
                            
                            new_ = 0
                            step = 2
                            detc_cnt += 1
                            total_cnt += 1
                            action = 1
                            
                            self.update_bar_graph.emit(total_cnt, nomal_cnt, detc_cnt)
                        
                        elif 'Pass' in detected_classes and step == 1 and new_ == 1:                            
                            serial_number = f'{ser_num}{total_cnt:03d}'
                            x1, y1, x2, y2 = boxes_dict['Product']
                            object_img = annotated_frame[y1-15:y2+15, x1-15:x2+15]
                            qc_status = "PASS"
                            txt_color = "Color : green"
                            self.update_product_info.emit(serial_number, qc_status,txt_color)

                            cv2.imwrite(image_path, object_img)
                            
                            data = {                                
                                'QC': qc_status,
                                'img': DB_IMG_DIR + "/images/" + image_filename
                            }
                            
                            # db에 데이터 저장
                            db.collection(collection_name).document(serial_number).set(data)
                            fileUpload(image_filename)
                            
                            step = 2
                            nomal_cnt += 1
                            total_cnt += 1
                            new_ = 0
                            action = 0
                            
                            self.update_bar_graph.emit(total_cnt, nomal_cnt, detc_cnt)
                        
                        if step == 2:
                            # db 추가 부분 코딩
                            # 로봇 동작 부분
                            print(detected_classes)
                            if action == 1:
                                wait()
                                gripper_open()
                                gripper_close()
                                up_release()
                                gripper_open()
                                stand()
                                wait()
                                action = 0
                                # new_ = 1
                            step = 0


                    if not detected_classes:
                        new_ = 1
                        serial_number = ''
                        qc_status = ""
                        txt_color = "Color : black"
                        self.update_product_info.emit(serial_number, qc_status,txt_color)
                        data = {}

                        ########################################################################
                        
                    detected_classes = []

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class Main(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        global nomal_cnt, detc_cnt, total_cnt
        
        self.setObjectName("Fctory Info")
        main_layout = QVBoxLayout()

        # Frame and Layout Initialization
        frame_1 = QFrame()
        frame_1.setFrameShape(QFrame.Panel | QFrame.Sunken)
        frame_2 = QFrame()
        frame_2.setFrameShape(QFrame.Panel | QFrame.Sunken)
        frame_3 = QFrame()
        frame_3.setFrameShape(QFrame.Panel | QFrame.Sunken)
        frame_4 = QFrame()
        frame_4.setFrameShape(QFrame.Panel | QFrame.Sunken)

        layout_1 = QVBoxLayout()
        layout_2 = QVBoxLayout()
        layout_3 = QVBoxLayout()
        layout_4 = QVBoxLayout()
        
        # Frame 1: Production line number, date, and time
        self.line_label = QLabel("Production Line: #1")
        self.date_label = QLabel("Date: " + datetime.datetime.now().strftime("%Y-%m-%d"))
        self.time_label = QLabel("Time: " + datetime.datetime.now().strftime("%H:%M:%S"))
        
        self.line_label.setFont(QtGui.QFont("고딕",20)) #폰트,크기 조절
        self.line_label.setStyleSheet("Color : black") #글자색 변환
        
        self.date_label.setFont(QtGui.QFont("고딕",20)) #폰트,크기 조절
        self.date_label.setStyleSheet("Color : black") #글자색 변환
        
        self.time_label.setFont(QtGui.QFont("고딕",20)) #폰트,크기 조절
        self.time_label.setStyleSheet("Color : black") #글자색 변환
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # update every second
        layout_1.addWidget(self.line_label)
        layout_1.addWidget(self.date_label)
        layout_1.addWidget(self.time_label)
        
        # Frame 2: Serial number, model name, and QC status
        self.serial_label = QLabel("Serial Number: ")
        self.model_label = QLabel("Model Name: 승우힘내줘")
        self.qc_label = QLabel("QC Status: ")
        
        self.serial_label.setFont(QtGui.QFont("고딕",20)) #폰트,크기 조절
        self.serial_label.setStyleSheet("Color : black") #글자색 변환
        
        self.model_label.setFont(QtGui.QFont("고딕",20)) #폰트,크기 조절
        self.model_label.setStyleSheet("Color : black") #글자색 변환
        
        self.qc_label.setFont(QtGui.QFont("고딕",20)) #폰트,크기 조절
        self.qc_label.setStyleSheet("Color : black") #글자색 변환

        layout_2.addWidget(self.serial_label)
        layout_2.addWidget(self.model_label)
        layout_2.addWidget(self.qc_label)
        
        # Frame 3: USB camera feed
        self.camera_view = QLabel()
        layout_3.addWidget(self.camera_view)

        # Frame 4: Production statistics and graph
        self.stats_label = QLabel("Total Production: 0\nNormal: 0\nDefective: 0")
        self.stats_label.setFont(QtGui.QFont("고딕",15)) #폰트,크기 조절
        self.stats_label.setStyleSheet("Color : black") #글자색 변환
        
        self.plot_widget = pg.PlotWidget()
        self.update_bar_graph(0, 0, 0)
        layout_4.addWidget(self.stats_label)
        layout_4.addWidget(self.plot_widget)
        
        # Set layouts to frames
        frame_1.setLayout(layout_1)
        frame_2.setLayout(layout_2)
        frame_3.setLayout(layout_3)
        frame_4.setLayout(layout_4)

        # Splitters
        spliter_1 = QSplitter(Qt.Orientation.Vertical)
        spliter_1.addWidget(frame_1)
        spliter_1.addWidget(frame_2)
        
        spliter_2 = QSplitter(Qt.Orientation.Horizontal)
        spliter_2.addWidget(spliter_1)
        spliter_2.addWidget(frame_3)
        
        spliter_3 = QSplitter(Qt.Orientation.Vertical)
        spliter_3.addWidget(spliter_2)
        spliter_3.addWidget(frame_4)

        main_layout.addWidget(spliter_3)

        self.setLayout(main_layout)
        self.resize(1920, 1000)
        self.show()

        # Camera Thread
        self.thread = CameraThread()
        self.thread.update_frame.connect(self.set_image)
        self.thread.update_product_info.connect(self.update_product_info)
        self.thread.update_bar_graph.connect(self.update_bar_graph)
        self.thread.start()
        
    def set_image(self, image):
        self.camera_view.setPixmap(QPixmap.fromImage(image))
        
    def update_time(self):
        self.time_label.setText("Time: " + datetime.datetime.now().strftime("%H:%M:%S"))
    
    def update_product_info(self, serial_number, qc_status, txt_color):
        self.serial_label.setText(f"Serial Number: {serial_number}")
        self.qc_label.setText(f"QC Status: {qc_status}")
        self.qc_label.setStyleSheet(txt_color) #글자색 변환

    def update_bar_graph(self, total, normal, defective):
        self.stats_label.setText(f"Total Production: {total}\nNormal: {normal}\nDefective: {defective}")
        bg1 = pg.BarGraphItem(x=[1, 2], height=[normal, defective], width=0.6, brushes=['g','r'])
        self.plot_widget.clear()
        self.plot_widget.addItem(bg1)
        self.plot_widget.getAxis('bottom').setTicks([[(1, 'Normal'), (2, 'Defective')]])

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
