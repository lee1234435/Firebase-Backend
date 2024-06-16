import sys
import cv2
import torch
import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import datetime
import random
import pyqtgraph as pg
from ultralytics import YOLO

class CameraThread(QThread):
    update_frame = pyqtSignal(QImage)

    def __init__(self, parent=None):
        super(CameraThread, self).__init__(parent)
        self.cap = cv2.VideoCapture(0)
        self.model = YOLO('auto_qc_model.pt')  # Load your custom YOLOv8 model
        self.running = True

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                results = self.model(frame)
                annotated_frame = results[0].plot()
                # for result in results:
                #     boxes = result.boxes
                #     for box in boxes:
                #         x1, y1, x2, y2 = map(int, box.xyxy[0])
                #         confidence = box.conf[0]
                #         cls = box.cls[0]
                #         if confidence > 0.85:  # confidence threshold
                #             frame = cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                #             label = f'{self.model.names[int(cls)]} {confidence:.2f}'
                #             frame = cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                color_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = color_frame.shape
                bytes_per_line = ch * w
                converted_frame = QImage(color_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.update_frame.emit(converted_frame)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()

class Main(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
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
        self.serial_label = QLabel("Serial Number: 1234567890")
        self.model_label = QLabel("Model Name: XYZ123")
        self.qc_label = QLabel("QC Status: Passed")
        layout_2.addWidget(self.serial_label)
        layout_2.addWidget(self.model_label)
        layout_2.addWidget(self.qc_label)
        
        # Frame 3: USB camera feed
        self.camera_view = QLabel()
        layout_3.addWidget(self.camera_view)

        # Frame 4: Production statistics and graph
        self.stats_label = QLabel("Total Production: 100\nNormal: 90\nDefective: 10")
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.plot([random.random() for _ in range(10)], [random.random() for _ in range(10)])
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
        self.resize(1920, 1080)
        self.show()

        # Camera Thread
        self.thread = CameraThread()
        self.thread.update_frame.connect(self.set_image)
        self.thread.start()
        
    def set_image(self, image):
        self.camera_view.setPixmap(QPixmap.fromImage(image))
        
    def update_time(self):
        self.time_label.setText("Time: " + datetime.datetime.now().strftime("%H:%M:%S"))
    
    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
