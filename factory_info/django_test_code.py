from django.core.management.base import BaseCommand
from traffic_app.models import traffic_system
from django.core.files.base import ContentFile
from django.db import transaction
from ultralytics import YOLO
from datetime import datetime
from pymycobot.mycobot import MyCobot

import cv2
import time
import os
import csv
import numpy as np

class Command(BaseCommand):
    help = 'Capture images using webcam, save to CSV, and update database'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.csv_file_path = 'Q_C_line_system_Data_System_original_copy.csv'

        # Initialize MyCobot
        self.mc = MyCobot('COM3', 115200)
        self.mc.set_gripper_mode(0)
        self.mc.init_eletric_gripper()
        self.init_robot()

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Starting the script...'))

            # Ensure the images directory exists
            images_dir = 'images'
            if not os.path.exists(images_dir):
                os.makedirs(images_dir)
                self.stdout.write(self.style.SUCCESS(f'Created directory: {images_dir}'))

            # Load YOLO model
            model = YOLO('Quality_control.pt')
            classNames = ['Grap', 'Pass', 'Product']
            self.stdout.write(self.style.SUCCESS('YOLO model loaded successfully.'))

            # Start capturing from webcam
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.stdout.write(self.style.ERROR('Failed to open webcam.'))
                return

            cap.set(3, 640)
            cap.set(4, 480)
            self.stdout.write(self.style.SUCCESS('Webcam opened successfully.'))

            last_capture_time = time.time()

            while True:
                current_time = time.time()
                success, img = cap.read()

                if not success:
                    self.stdout.write(self.style.ERROR('Failed to capture image from webcam.'))
                    break

                if current_time - last_capture_time >= 10:
                    last_capture_time = current_time
                    self.stdout.write(self.style.SUCCESS('Capturing image...'))

                    results = model(img, stream=True, conf = 0.90)
                    detected_classes = []
                    boxes_dict = {}

                    for r in results:
                        boxes = r.boxes

                        for box in boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0])
                            cls = int(box.cls[0])
                            cls_name = classNames[min(cls, len(classNames) - 1)]
                            detected_classes.append(cls_name)
                            boxes_dict[cls_name] = (x1, y1, x2, y2)
                            image_path = ''
                            
                            if 'Product' not in detected_classes:
                                self.stdout.write(self.style.SUCCESS('No Product detected, skipping this capture.'))
                                break
                            
                            if 'Product' in detected_classes:
                                # image_filename = f'{int(time.time())}_{judgement_cls}.jpg'
                                # image_path = os.path.join(images_dir, image_filename)
                                # self.stdout.write(self.style.SUCCESS('Image saving...'))
                                
                                if 'Pass' in detected_classes:
                                    x1, y1, x2, y2 = boxes_dict['Product']
                                    object_img = img[y1:y2, x1:x2]
                                    judgement_cls = 'Pass'
                                    
                                    image_filename = f'{int(time.time())}_{judgement_cls}.jpg'
                                    image_path = os.path.join(images_dir, image_filename)
                                    self.stdout.write(self.style.SUCCESS('Image saving...'))
                                    cv2.imwrite(image_path, object_img)
                                    
                                    self.stdout.write(self.style.SUCCESS(f'Image saved pass successfully: {image_path}'))
                                    self.update_database(judgement_cls, image_path)
                                    
                                elif 'Grap' in detected_classes:
                                    x1, y1, x2, y2 = boxes_dict['Product']
                                    object_img = img[y1:y2, x1:x2]
                                    judgement_cls = 'Grap'
                                    
                                    image_filename = f'{int(time.time())}_{judgement_cls}.jpg'
                                    image_path = os.path.join(images_dir, image_filename)
                                    self.stdout.write(self.style.SUCCESS('Image saving...'))
                                    cv2.imwrite(image_path, object_img)
                                    
                                    
                                    self.stdout.write(self.style.SUCCESS(f'Image saved grap successfully: {image_path}'))
                                    self.update_database(judgement_cls, image_path)
                                    
                                    self.run_robot()
                                    self.stdout.write(self.style.SUCCESS(f'Robot Operating......'))
                                    break
                                    
                                else:
                                    continue
                                
                            
                        detected_classes = []

                        # try:
                        #     if cv2.imwrite(image_path, object_img):
                        #         self.stdout.write(self.style.SUCCESS(f'Image saved successfully: {image_path}'))
                        #         self.update_database(judgement_cls, image_path)
                        #     else:
                        #         self.stdout.write(self.style.ERROR(f'Failed to save image: {image_path}'))
                        #         continue
                        # except Exception as e:
                        #     self.stdout.write(self.style.ERROR(f'Error saving image: {e}'))
                        #     continue

                cv2.imshow('Webcam', img)
                if cv2.waitKey(1) == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error in handle method: {e}'))

    def update_database(self, cls_name, image_path):
        try:
            with open(self.csv_file_path, 'r', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                next(csv_reader)
                for row in csv_reader:
                    _, name, serial_number, size, line, _, _ = row[:7]
                    with open(image_path, 'rb') as f:
                        image_content = ContentFile(f.read(), name=os.path.basename(image_path))
                        traffic_system.objects.create(
                            name=name,
                            date=datetime.now().date(),
                            serial_number=serial_number,
                            size=size,
                            line=line,
                            judgement=cls_name,
                            image=image_content
                        )
            self.stdout.write(self.style.SUCCESS('Updated Database successfully.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error saving to database: {e}"))
            self.stdout.write(self.style.ERROR(f"Unexpected row format: {row}"))

    def init_robot(self):
        self.mc.send_angles([0, 0, 0, 0, 90, 0], 40)
        time.sleep(4)

    def gripper_open(self):
        print("OPEN")
        self.mc.set_eletric_gripper(0)
        self.mc.set_gripper_value(100, 30)
        time.sleep(2)

    def gripper_close(self):
        print("CLOSE")
        self.mc.set_eletric_gripper(1)
        self.mc.set_gripper_value(45, 30)
        time.sleep(2)

    def wait(self):
        self.mc.send_angles([0, -23, -40, -17, 90, 90], 40)
        time.sleep(3)

    def up_release(self):
        self.mc.send_angles([0, 0, 0, 0, 90, 90], 40)
        time.sleep(3)
        self.mc.send_angles([100, 0, 0, 0, 90, 90], 40)
        time.sleep(3)
        self.mc.send_angles([100, -40, -35, -0, 90, 90], 40)
        time.sleep(3)

    def stand(self):
        self.mc.send_angles([100, 0, 0, 0, 90, 90], 40)
        time.sleep(3)
        self.mc.send_angles([0, 0, 0, 0, 90, 90], 40)
        time.sleep(3)

    def run_robot(self):
        self.wait()
        self.gripper_open()
        self.gripper_close()
        self.up_release()
        self.gripper_open()
        self.stand()
        self.wait()