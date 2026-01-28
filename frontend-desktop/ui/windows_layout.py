from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        # 1. Main Window Settings
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        
        # 2. Central Widget & Layout
        self.central_widget = QWidget(MainWindow)
        self.layout = QVBoxLayout(self.central_widget)
        
        # 3. Header Label
        self.label = QLabel("Upload a CSV file to begin analysis")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #333;
                margin-top: 10px;
                font-weight: bold;
            }
        """)
        self.layout.addWidget(self.label)

        # 4. Upload Button
        self.btn_upload = QPushButton("Upload CSV")
        self.btn_upload.setCursor(Qt.PointingHandCursor)
        self.btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #2E86C1;
                color: white;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2874A6;
            }
            QPushButton:disabled {
                background-color: #AAB7B8;
            }
        """)
        self.layout.addWidget(self.btn_upload)

        # 5. Matplotlib Canvas
        self.figure = plt.figure()
        # Set a tight layout to make better use of space
        self.figure.set_tight_layout(True) 
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

        # Finalize
        MainWindow.setCentralWidget(self.central_widget)