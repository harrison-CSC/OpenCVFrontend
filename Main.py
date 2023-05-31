import sys
import cv2
import signal
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QImage, QPixmap, QTransform
from PyQt5.QtWidgets import QApplication, QButtonGroup, QCheckBox, QDesktopWidget, QLabel, QLineEdit, QPushButton, QSlider, QWidget, QMainWindow

VERBOSE = True

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCV Frontend")
        width = 1280
        height = 720

        self.sr = cv2.dnn_superres.DnnSuperResImpl_create()
        self.imagePath = ""
        self.image = None

        # Y-value of the element that is going to be added next
        self.currY = 0
        
        self.setGeometry(int((QDesktopWidget().availableGeometry().width() / 2) - (width / 2)),
            int((QDesktopWidget().availableGeometry().height() / 2) - (height / 2)),
            width,
            height)
        
        self.setFixedSize(self.size())


        self.imageDrop = ImageDrop(self)
        self.imageDrop.setGeometry(200, 25, 1050, 650)


        label = sectionLabel("Upscale Level", self)
        self.addToLeftPanel(label)

        self.x2Scale = QCheckBox("2x", self)
        self.addToLeftPanel(self.x2Scale)
        self.x2Scale.setToolTip("Scale width and height by 2x (4x total pixels)")
        self.x2Scale.setChecked(True)

        self.x3Scale = QCheckBox("3x", self)
        self.x3Scale.setToolTip("Scale width and height by 3x (9x total pixels)")
        self.addToLeftPanel(self.x3Scale)

        self.x4Scale = QCheckBox("4x", self)
        self.x3Scale.setToolTip("Scale width and height by 4x (16x total pixels)")
        self.addToLeftPanel(self.x4Scale)

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.x2Scale)
        self.button_group.addButton(self.x3Scale)
        self.button_group.addButton(self.x4Scale)


        label = sectionLabel("Upscale Model", self)
        self.addToLeftPanel(label)

        self.epscn_cb = QCheckBox("ESPCN", self)
        self.epscn_cb.setToolTip("This model is faster but has worse quality. Name stands for 'Efficient Sub-Pixel CNN'")
        self.addToLeftPanel(self.epscn_cb)
        self.epscn_cb.setChecked(True)

        self.edsr_cb = QCheckBox("EDSR", self)
        self.edsr_cb.setToolTip("This model has better quality but is slower. Name stands for 'Enhanced Deep Residual Networks for Single Image Super-Resolution'")
        self.addToLeftPanel(self.edsr_cb)

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.epscn_cb)
        self.button_group.addButton(self.edsr_cb)


        label = sectionLabel("Image Rotation", self)
        self.addToLeftPanel(label)

        self.rot_0 = QCheckBox("0°", self)
        self.addToLeftPanel(self.rot_0)
        self.rot_0.setChecked(True)

        self.rot_90 = QCheckBox("90°", self)
        self.addToLeftPanel(self.rot_90)

        self.rot_180 = QCheckBox("180°", self)
        self.addToLeftPanel(self.rot_180)

        self.rot_270 = QCheckBox("270°", self)
        self.addToLeftPanel(self.rot_270)

        self.rot_0.stateChanged.connect(lambda:self.updateImage())
        self.rot_90.stateChanged.connect(lambda:self.updateImage())
        self.rot_180.stateChanged.connect(lambda:self.updateImage())
        self.rot_270.stateChanged.connect(lambda:self.updateImage())


        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.rot_0)
        self.button_group.addButton(self.rot_90)
        self.button_group.addButton(self.rot_180)
        self.button_group.addButton(self.rot_270)


        label = sectionLabel("Color Options", self)
        self.addToLeftPanel(label)

        label = QLabel("Brightness", self)
        self.addToLeftPanel(label)

        self.slider_bright = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_bright.setRange(-2, 5)
        self.slider_bright.setTickPosition(QSlider.TicksAbove)
        self.slider_bright.setTickInterval(1)
        self.slider_bright.valueChanged.connect(lambda:self.updateImage())
        self.addToLeftPanel(self.slider_bright)
        self.slider_bright.setFixedWidth(150)

        label = QLabel("Contrast", self)
        self.addToLeftPanel(label)

        self.slider_cont = QSlider(Qt.Orientation.Horizontal, self)
        self.slider_cont.setRange(1, 7)
        self.slider_cont.setTickPosition(QSlider.TicksAbove)
        self.slider_cont.setTickInterval(1)
        self.slider_cont.valueChanged.connect(lambda:self.updateImage())
        self.addToLeftPanel(self.slider_cont)
        self.slider_cont.setFixedWidth(150)


        label = sectionLabel("Current Image", self)
        self.addToLeftPanel(label)

        self.wLabel = QLabel("Width: N/A", self)
        self.addToLeftPanel(self.wLabel)

        self.hLabel = QLabel("Height: N/A", self)
        self.addToLeftPanel(self.hLabel)


        self.applyButton = QPushButton("Upscale", self)
        self.applyButton.setEnabled(False)
        self.applyButton.move(20, 675)
        self.applyButton.clicked.connect(self.exec_changes)


        self.show()


    def getCurrRotation(self, cv2mode=False):
        if self.rot_0.isChecked():
            return 0
        elif self.rot_90.isChecked():
            return cv2.ROTATE_90_CLOCKWISE if cv2mode else 90
        elif self.rot_180.isChecked():
            return cv2.ROTATE_180 if cv2mode else 180
        else:
            return cv2.ROTATE_90_COUNTERCLOCKWISE if cv2mode else 270


    # This function adds an element to the left panel. This manages both the x and y values automatically
    # Most element will increase currY by 25, while labels will increase it by 50
    def addToLeftPanel(self, element):
        if element.__class__.__name__ == "sectionLabel":
            self.currY += 25
        element.move(20, self.currY)
        self.currY += 25


    # Handle the user adding an image
    def updateImage(self):
        self.image = cv2.imread(self.imagePath)

        self.applyButton.setEnabled(True)
        self.wLabel.setText("Width: " + str(self.image.shape[1]))
        self.hLabel.setText("Height: " + str(self.image.shape[0]))

        if self.getCurrRotation() != 0:
            self.image = cv2.rotate(self.image, self.getCurrRotation(cv2mode=True))

        # Brightness and contrast
        self.image = cv2.convertScaleAbs(
            self.image,
            alpha=(1 + ((self.slider_cont.value() - 1) / 5)), # Contrast
            beta=(1 + (10 * (self.slider_bright.value() - 1))) # Brightness
        )

        self.imageDrop.setImage(self.image)


    @pyqtSlot()
    def exec_changes(self):
        if self.x2Scale.isChecked():
            up_lvl = 2
        elif self.x3Scale.isChecked():
            up_lvl = 3
        else:
            up_lvl = 4

        up_mdl = "ESPCN" if self.epscn_cb.isChecked() else "EDSR"

        if VERBOSE:
            print("Executing changes:")
            print("Upscale Level: " + str(up_lvl) + "x")
            print("Upscale Model:", up_mdl)
            

        path = "Models/" + up_mdl + "_x" + str(up_lvl) + ".pb"
        self.sr.readModel(path)
        self.sr.setModel(up_mdl.lower(), up_lvl)

        upscaledImage = self.sr.upsample(self.image)

        # Example rename: 'in.jpg' -> 'in_UPSCALED.jpg'
        newFilename = self.imagePath[:self.imagePath.rfind(".")] + "_UPSCALED" +  self.imagePath[self.imagePath.rfind("."):]
        cv2.imwrite(newFilename, upscaledImage)


class ImageDrop(QLabel):
    def __init__(self, parent):
        super().__init__("Drop Image Here", parent)
        self.setAlignment(Qt.AlignCenter)
        self.myParent = parent
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasImage:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasImage:
            event.setDropAction(Qt.CopyAction)
            file_path = event.mimeData().urls()[0].toLocalFile()
            self.myParent.imagePath = file_path
            self.myParent.updateImage()

            event.accept()
        else:
            event.ignore()


    def setImage(self, cv2_image):
        pixmap = QPixmap(QImage(cv2_image,
            cv2_image.shape[1],
            cv2_image.shape[0],
            cv2_image.shape[1] * 3,
            QImage.Format_BGR888)
        )
        super().setPixmap(pixmap.scaled(1050, 650, Qt.KeepAspectRatio))



# A sectionLabel is almost the same as a QLabel, but with 2 differences. First, the text is bold,
# second, the y-spacing will be different
class sectionLabel(QLabel):
    def __init__(self, label, parent):
        super().__init__(label, parent)
        self.setStyleSheet("font-weight: bold")


signal.signal(signal.SIGINT, signal.SIG_DFL)
app = QApplication(sys.argv)
ex = App()
sys.exit(app.exec_())