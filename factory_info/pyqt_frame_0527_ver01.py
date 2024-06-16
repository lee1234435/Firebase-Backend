import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
import datetime
import random
import pyqtgraph as pg

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
        self.camera_view = QCameraViewfinder()
        self.camera = QCamera(QCamera.availableDevices()[0])  # Assumes the first available camera
        self.camera.setViewfinder(self.camera_view)
        self.camera.start()
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
        
    def update_time(self):
        self.time_label.setText("Time: " + datetime.datetime.now().strftime("%H:%M:%S"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
