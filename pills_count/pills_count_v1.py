from PyQt5 import QtCore, QtGui
from PyQt5 import uic
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import *

import sys
import cv2
import numpy as np
from time import sleep, strftime, gmtime
# 비디오 재생을 위해 스레드 생성, 사진 저장
import threading

form_class = uic.loadUiType('pills_count_v1.ui')[0]
class MyMain(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.show()

    def initUI(self):
        self.btn_load.clicked.connect(self.btn_load_clicked)
        self.btn_text_load.clicked.connect(self.btn_text_load_clicked)
        self.initial_value()


    def initial_value(self):
        self.run_flag = False   #flag, video_thread 시작
        self.needs_large = 0
        self.needs_small = 0
        self.count = 0
        self.label_4.setHidden(True)

    def btn_load_clicked(self):
        self.path = self.line_load.text()
        self.video_thread()


    def btn_text_load_clicked(self):
        needs_large = self.text_box.toPlainText()
        needs_small = self.text_box_2.toPlainText()
        if needs_large.isdigit() and needs_small.isdigit() :
            self.needs_large = int(needs_large)
            self.needs_small = int(needs_small)
            self.lcdNumber.display(self.needs_large)
            self.lcdNumber_2.display(self.needs_small)
        else:
            QMessageBox.about(self, "error", "숫자만 입력 가능합니다.")
            print("숫자가 아닙니다")


#동영상 실행
########################################################################################################################

    def video_thread(self):
        self.thread = threading.Thread(target=self.video_to_frame, args=(self,))
        self.thread.daemon = True  # 프로그램 종료시 프로세스도 함께 종료 (백그라운드 재생 X)
        self.thread.start()
        self.run_flag = True

    def video_to_frame(self, MainWindow):
        ###cap으로 영상의 프레임을 가지고와서 전처리 후 화면에 띄움###
        capture = cv2.VideoCapture(self.path)
        while self.run_flag:
            self.ret, frame = capture.read()  # 영상의 정보 저장
            if self.ret:
                frame = frame[20:, :460, :]
                # self.frame = frame.copy()  # line_134 오류 방지위해 .copy()
                self.frame = cv2.flip(frame, -1)
                self.process_result()
                self.display_output_image(self.frame, 0)
                self.display_output_image(self.frame2, 1)
            else:
                break

        if self.capture.isOpened():
            self.capture.release()

    def process_result(self):
            self.frame2 = self.frame.copy()
            frame2 = cv2.GaussianBlur(self.frame2, (5, 5), 3)
            self.frame_out1 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            self.apply_binary()


    def display_output_image(self, img_dst, mode):
        h, w = img_dst.shape[:2]  # 그레이영상의 경우 ndim이 2이므로 h,w,ch 형태로 값을 얻어올수 없다

        if img_dst.ndim == 2:
            qImg = QImage(img_dst, w, h, w * 1, QImage.Format_Grayscale8)
        else:
            bytes_per_line = img_dst.shape[2] * w
            qImg = QImage(img_dst, w, h, bytes_per_line, QImage.Format_BGR888)

        self.pixmap = QtGui.QPixmap(qImg)
        p = self.pixmap.scaled(640, 640, QtCore.Qt.KeepAspectRatio)  # 프레임 크기 조정
        # p = self.pixmap.scaled(600, 450, QtCore.Qt.IgnoreAspectRatio)  # 프레임 크기 조정

        if mode == 0:
            self.lbl_src.setPixmap(p)
            self.lbl_src.update()  # 프레임 띄우기
        else:
            self.lbl_dst.setPixmap(p)
            self.lbl_dst.update()  # 프레임 띄우기

        sleep(0.01)  # 영상 1프레임당 0.01초로 이걸로 영상 재생속도 조절하면됨 0.02로하면 0.5배속인거임

########################################################################################################################


#편집
########################################################################################################################
        
    def apply_binary(self):
        frame_out = cv2.Canny(self.frame_out1, 100, 200)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        img_dial = cv2.dilate(frame_out, kernel)
        self.frame_out = cv2.morphologyEx(img_dial, cv2.MORPH_CLOSE, kernel)
        self.contour(self.frame_out)

    def contour(self,img_proc):
        contours, hierarchy = cv2.findContours(img_proc, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        self.count = 0
        large_pill = 0
        small_pill = 0
        large_flag = 0
        small_flag = 0
        # print(type(contours))
        for i, contour in enumerate(contours[::-1]):
            area = cv2.contourArea(contour)
            if area >= 100:
                self.count += 1
                cv2.drawContours(self.frame2, [contour], 0, (0, 255, 0), 2)
                #### moment
                mu = cv2.moments(contour)
                cX = int(mu['m10'] / (mu['m00']) + 1e-5)
                cY = int(mu['m01'] / (mu['m00']) + 1e-5)
                cv2.putText(self.frame2, f'{i+1}:{area}', (cX - 60, cY + 25),
                            cv2.FONT_HERSHEY_COMPLEX, 0.7, (0, 0, 255), 1)
                if 830 < area < 1100: # 큰거
                    large_pill += 1
                    if self.needs_large < large_pill:
                        large_flag = 1
                        cv2.circle(self.frame, (cX, cY), 2, (0, 130, 255), -1)
                    else:
                        large_flag = 0
                elif 550 < area < 750: #작은거
                    small_pill += 1
                    if self.needs_small < small_pill:
                        small_flag = 1
                        cv2.circle(self.frame, (cX, cY), 2, (0, 0, 255), -1)
                    else:                       
                        small_flag = 0

        self.lcdNumber_5.display(large_pill)
        self.lcdNumber_6.display(small_pill)
        if large_pill == self.needs_large and small_pill == self.needs_small:
            self.label_4.setVisible(True)
            self.label_4.setStyleSheet("background-color: green; border: 1px solid black;")
            # self.take_medicine(False)
        else:
            self.label_4.setVisible(False)
            # self.take_medicine(True)

        if large_flag == 1:
            self.label_6.setText("큰 알약 빼세요")
            self.lcdNumber_3.display(large_pill - self.needs_large)
        elif large_flag == 0:
            if self.needs_large == large_pill:
                # self.label_6.setVisible(False)
                # self.lcdNumber_3.setVisible(False)
                self.label_6.setText("")
                self.lcdNumber_3.display(0)
                pass
            else:
                self.label_6.setText("큰 알약 더가져오세요")
                self.lcdNumber_3.display(self.needs_large - large_pill)
        if small_flag == 1:
            self.label_5.setText("작은 알약 빼세요")
            self.lcdNumber_4.display(small_pill - self.needs_small)
        elif small_flag == 0:
            if self.needs_small == small_pill:
                # self.label_5.setVisible(False)
                # self.lcdNumber_4.setVisible(False)
                self.lcdNumber_4.display(0)
                self.label_5.setText("")
                pass
            else:
                self.lcdNumber_4.display(self.needs_small - small_pill)
                self.label_5.setText("작은 알약 더가져오세요")

        # if large_pill < self.needs_large:
        #     self.label_4.setHidden(False)
        #     self.sethidden(True)
        # else:
        #     self.label_4.setHidden(True)
        #     self.sethidden(False)

    # def take_medicine(self, state):
    #     self.lcdNumber_3.setVisible(state)
    #     self.lcdNumber_4.setVisible(state)
    #     self.lcdNumber_5.setVisible(state)
    #     self.lcdNumber_6.setVisible(state)
    #     self.label_6.setVisible(state)
    #     self.label_5.setVisible(state)
    #     self.label_8.setVisible(state)
    #     self.label_9.setVisible(state)


########################################################################################################################

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                               "종료 하시겠습니까?",
                                               QMessageBox.Yes | QMessageBox.No,
                                               QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.run_flag = False  # Video_to_frame에 while문에 사용(강제종료시 에러문제)
            event.accept()
        else:
            event.ignore()



    # def processing_image(self, img_gray, img_src):
    #     # 여기에 이미지 프로세싱을 진행하고 output으로 리턴하면 오른쪽에 결과 영상 출력됨
    #     # output = img_src.copy() #원본영상 그대로 리턴
    #     output = img_gray.copy()  # 그래이 영상 리턴
    #     return output


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyMain()
    sys.exit(app.exec_())