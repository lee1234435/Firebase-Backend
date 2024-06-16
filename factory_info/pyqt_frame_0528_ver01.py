import sys
import cv2
import os
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import datetime
import random
import pyqtgraph as pg
from ultralytics import YOLO

step = 0
ser_num = "SN" + datetime.datetime.now().strftime("%Y%m%d") 
classNames = ['Grap', 'Pass', 'Product']
x1,x2,y1,y2 = 0,0,0,0
total_cnt = 0
nomal_cnt = 0
detc_cnt = 0

new_ = 1

images_dir = "images"
image_filename = ""
image_path = ""
object_img = ""

class CameraThread(QThread):
    update_frame = pyqtSignal(QImage)
    update_product_info = pyqtSignal(str, str)
    update_bar_graph = pyqtSignal(int, int, int)


    def __init__(self, parent=None):
        super(CameraThread, self).__init__(parent)
        self.cap = cv2.VideoCapture(0)
        self.model = YOLO('Quality Control.pt')  # Load your custom YOLOv8 model
        self.running = True

    def run(self):
        global step, x1, x2, y1, y2, images_dir, image_filename, image_path, new_, object_img, total_cnt, nomal_cnt, detc_cnt
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                results = self.model(frame,conf = 0.9)
                annotated_frame = results[0].plot()

                detected_classes = []
                boxes_dict = {}
                
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
                            self.update_product_info.emit(serial_number, qc_status)
                            
                            step = 0
                            
                        if 'Product' in detected_classes and step == 0 and new_ == 1:
                        
                            image_filename = f'{ser_num}{total_cnt:03d}.jpg'
                            image_path = os.path.join(images_dir, image_filename)
                            step = 1
                            
                        elif 'Grap' in detected_classes and step == 1 and new_ == 1:
                            
                            x1, y1, x2, y2 = boxes_dict['Product']
                            object_img = annotated_frame[y1:y2, x1:x2]
                            serial_number = f'{ser_num}{total_cnt:03d}'
                            qc_status = "FAIL"
                            self.update_product_info.emit(serial_number, qc_status)
                            
                            
                            # self.stdout.write(self.style.SUCCESS('Image saving...'))
                            cv2.imwrite(image_path, object_img)
                            # self.stdout.write(self.style.SUCCESS(f'Image saved grap successfully: {image_path}'))
                            # self.update_database(judgement_cls, image_path)                            
                            # self.run_robot()
                            # self.stdout.write(self.style.SUCCESS(f'Robot Operating......'))
                            new_ = 0
                            step = 2
                            detc_cnt += 1
                            total_cnt += 1
                        
                        elif 'Pass' in detected_classes and step == 1 and new_ == 1:                            
                            serial_number = f'{ser_num}{total_cnt:03d}'
                            x1, y1, x2, y2 = boxes_dict['Product']
                            object_img = annotated_frame[y1:y2, x1:x2]
                            qc_status = "PASS"
                            self.update_product_info.emit(serial_number, qc_status)

                            # self.stdout.write(self.style.SUCCESS('Image saving...'))
                            cv2.imwrite(image_path, object_img)
                            
                            # self.stdout.write(self.style.SUCCESS(f'Image saved pass successfully: {image_path}'))
                            # self.update_database(judgement_cls, image_path)
                            step = 2
                            nomal_cnt += 1
                            total_cnt += 1
                            new_ = 0
                        
                        if step == 2:
                            # db 추가 부분 코딩
                            # 로봇 동작 부분
                            step = 0

                    if not detected_classes:
                        new_ = 1

                        ########################################################################
                        
                        # confidence = box.conf[0]
                        # cls = box.cls[0]
                        # if confidence > 0.85:  # confidence threshold
                        #     # Dummy serial number and QC status
                        #     serial_number = "SN" + str(random.randint(1000000000, 9999999999))
                        #     qc_status = "Passed" if random.random() > 0.1 else "Failed"
                        #     self.update_product_info.emit(serial_number, qc_status)
                    detected_classes = []
                    self.update_bar_graph.emit(total_cnt, nomal_cnt, detc_cnt)
                    
                color_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = color_frame.shape
                bytes_per_line = ch * w
                converted_frame = QImage(color_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.update_frame.emit(converted_frame) # gui 캠 업데이트

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
        layout_2.addWidget(self.serial_label)
        layout_2.addWidget(self.model_label)
        layout_2.addWidget(self.qc_label)
        
        # Frame 3: USB camera feed
        self.camera_view = QLabel()
        layout_3.addWidget(self.camera_view)

        # Frame 4: Production statistics and graph
        self.stats_label = QLabel("Total Production: 0\nNormal: 0\nDefective: 0")
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
    
    def update_product_info(self, serial_number, qc_status):
        self.serial_label.setText(f"Serial Number: {serial_number}")
        self.qc_label.setText(f"QC Status: {qc_status}")

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
