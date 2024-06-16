import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QTextBrowser
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, QDateTime, QThread, pyqtSignal
from ultralytics import YOLO

model = YOLO('yolov8n.pt')  # 코랩에서 학습 후 모델 (코랩해서 학습해서 신호등 초록, 빨강색 구분 모델용)


class YOLOThread(QThread):
    frame_processed = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)
        self.running = True

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                result_yolo = model(frame)
                annotated_frame = result_yolo[0].plot()
                self.frame_processed.emit(annotated_frame)

    def stop(self):
        self.running = False
        self.cap.release()


class USBCamera(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

        # YOLO 스레드 초기화 및 시작
        self.yolo_thread = YOLOThread()
        self.yolo_thread.frame_processed.connect(self.update_frame)
        self.yolo_thread.start()

        # 현재 시간 업데이트를 위한 타이머 설정: 1초마다 업데이트
        self.time_timer = QTimer(self)
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)

    def initUI(self):
        self.setWindowTitle('Factory Info')
        
        self.setGeometry(0, 0, 1920, 1080)  # 윈도우 크기 고정

        # 전체 레이아웃 설정
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)
        
        

        # 왼쪽 레이아웃 (카메라 피드 및 상단 정보)
        self.left_layout = QVBoxLayout()
        self.main_layout.addLayout(self.left_layout)

        # 상단 정보 레이아웃 설정
        self.info_layout = QHBoxLayout()
        self.left_layout.addLayout(self.info_layout)

        # 생산 라인 라벨
        self.production_line_label = QLabel('생산라인: 1', self)
        self.info_layout.addWidget(self.production_line_label)

        # 날짜 라벨
        self.date_label = QLabel(self)
        self.info_layout.addWidget(self.date_label)

        # 시간 라벨
        self.time_label = QLabel(self)
        self.info_layout.addWidget(self.time_label)

        # 카메라 피드 QLabel 생성 및 레이아웃에 추가
        self.camera_label = QLabel(self)
        self.left_layout.addWidget(self.camera_label)

        # 오른쪽 레이아웃 (제품 정보)
        self.right_layout = QVBoxLayout()
        self.main_layout.addLayout(self.right_layout)

        # 제품명 라벨 및 텍스트 브라우저
        self.product_name_label = QLabel('제품명:', self)
        self.right_layout.addWidget(self.product_name_label)
        self.product_name_browser = QTextBrowser(self)
        self.product_name_browser.setText('제품 A')
        self.right_layout.addWidget(self.product_name_browser)

        # 시리얼 번호 라벨 및 텍스트 브라우저
        self.serial_number_label = QLabel('시리얼 번호:', self)
        self.right_layout.addWidget(self.serial_number_label)
        self.serial_number_browser = QTextBrowser(self)
        self.serial_number_browser.setText('123456789')
        self.right_layout.addWidget(self.serial_number_browser)

        # Q/C 여부 라벨 및 텍스트 브라우저
        self.qc_label = QLabel('Q/C 여부:', self)
        self.right_layout.addWidget(self.qc_label)
        self.qc_browser = QTextBrowser(self)
        self.qc_browser.setText('합격')
        self.right_layout.addWidget(self.qc_browser)

        # 초기 날짜 및 시간 설정
        self.update_time()

    def update_frame(self, frame):
        # OpenCV 이미지를 PyQt QImage로 변환
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # QImage를 QPixmap으로 변환하여 QLabel에 설정
        self.camera_label.setPixmap(QPixmap.fromImage(qimg))

    def update_time(self):
        current_datetime = QDateTime.currentDateTime()
        date_str = current_datetime.toString('yyyy-MM-dd')
        time_str = current_datetime.toString('HH:mm:ss')

        self.date_label.setText(f'날짜: {date_str}')
        self.time_label.setText(f'현재 시간: {time_str}')

    def closeEvent(self, event):
        # 창이 닫힐 때 YOLO 스레드 종료
        self.yolo_thread.stop()
        self.yolo_thread.wait()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = USBCamera()
    ex.show()
    sys.exit(app.exec_())
