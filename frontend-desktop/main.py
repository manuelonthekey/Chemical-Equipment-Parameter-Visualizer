import sys
import os
import requests
import tempfile
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QFileDialog, QProgressBar, QFrame, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QGraphicsDropShadowEffect,
                             QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QMessageBox,
                             QSplitter, QListWidget, QListWidgetItem, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap, QPainter
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.lib.utils import ImageReader

# --- Login Dialog ---
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setFixedSize(300, 150)
        self.token = None
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.handle_login)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
            
        try:
            response = requests.post('http://localhost:8000/api/login/', 
                                   json={'username': username, 'password': password})
            
            if response.status_code == 200:
                self.token = response.json().get('token')
                self.accept()
            else:
                QMessageBox.critical(self, "Login Failed", "Invalid credentials")
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))

# --- Custom Drag & Drop Widget ---
class DragDropWidget(QLabel):
    fileDropped = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setText("Drag & Drop your CSV file here\nor click to browse")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("DragDropWidget")
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.setProperty("dragging", True)
            self.style().unpolish(self)
            self.style().polish(self)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def dropEvent(self, event):
        self.setProperty("dragging", False)
        self.style().unpolish(self)
        self.style().polish(self)
        
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if f.endswith('.csv'):
                self.fileDropped.emit(f)
                return

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
            if file_path:
                self.fileDropped.emit(file_path)

# --- Worker Thread ---
class UploadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path, api_url, token):
        super().__init__()
        self.file_path = file_path
        self.api_url = api_url
        self.token = token

    def run(self):
        try:
            # Simulate progress for better UX
            for i in range(0, 90, 10):
                self.progress.emit(i)
                self.msleep(50) 
            
            headers = {'Authorization': f'Token {self.token}'}
            with open(self.file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(self.api_url, files=files, headers=headers)
            
            self.progress.emit(100)
            
            if response.status_code == 201:
                self.finished.emit(response.json())
            else:
                self.error.emit(f"Server Error: {response.status_code} - {response.text}")
        except Exception as e:
            self.error.emit(str(e))

# --- Main Window ---
class MainWindow(QMainWindow):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.setWindowTitle("EquipZense")
        self.resize(1200, 850)
        self.current_theme = 'light'
        self.current_data = None
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "equipzense.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Main Layout with Splitter for History
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # History Sidebar
        self.history_widget = QWidget()
        self.history_widget.setFixedWidth(250)
        self.history_widget.setObjectName("HistorySidebar")
        self.history_layout = QVBoxLayout(self.history_widget)
        
        self.history_label = QLabel("History (Last 10)")
        self.history_label.setObjectName("SectionTitle")
        self.history_layout.addWidget(self.history_label)
        
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_history_item)
        self.history_layout.addWidget(self.history_list)
        
        self.refresh_history_btn = QPushButton("Refresh History")
        self.refresh_history_btn.clicked.connect(self.load_history_list)
        self.history_layout.addWidget(self.refresh_history_btn)
        
        self.main_layout.addWidget(self.history_widget)

        # Content Area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(40, 40, 40, 40)
        self.content_layout.setSpacing(20)
        self.main_layout.addWidget(self.content_widget)

        # Header Row (Navbar)
        self.navbar = QFrame()
        self.navbar.setObjectName("Navbar")
        header_layout = QHBoxLayout(self.navbar)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(12)
        
        # App icon on the left
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "equipzense.png")
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path)
            icon_label.setPixmap(pix.scaled(QSize(28, 28), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        header_layout.addWidget(icon_label)
        
        header_text_layout = QVBoxLayout()
        self.header = QLabel("EquipZense")
        self.header.setObjectName("HeaderLabel")
        header_text_layout.addWidget(self.header)
        
        self.sub_header = QLabel("Analyze. Visualize. Optimize.")
        self.sub_header.setObjectName("SubHeaderLabel")
        header_text_layout.addWidget(self.sub_header)
        
        header_layout.addLayout(header_text_layout)
        header_layout.addStretch()
        
        self.theme_btn = QPushButton("Switch to Dark Mode")
        self.theme_btn.setCheckable(True)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)
        
        self.content_layout.addWidget(self.navbar)

        # Upload Section
        self.upload_container = QWidget()
        self.upload_layout = QVBoxLayout(self.upload_container)
        
        self.drag_drop_widget = DragDropWidget()
        self.drag_drop_widget.fileDropped.connect(self.start_upload)
        self.upload_layout.addWidget(self.drag_drop_widget)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        self.upload_layout.addWidget(self.progress_bar)

        self.error_label = QLabel()
        self.error_label.setObjectName("ErrorLabel")
        self.error_label.setVisible(False)
        self.upload_layout.addWidget(self.error_label)
        
        self.content_layout.addWidget(self.upload_container)

        # Dashboard Section
        self.dashboard_scroll = QScrollArea()
        self.dashboard_scroll.setWidgetResizable(True)
        self.dashboard_scroll.setVisible(False)
        self.dashboard_scroll.setFrameShape(QFrame.NoFrame)
        
        self.dashboard_container = QWidget()
        self.dashboard_layout = QVBoxLayout(self.dashboard_container)
        
        # Dashboard Header (Reset & PDF)
        dash_header = QHBoxLayout()
        
        self.upload_date_label = QLabel("")
        self.upload_date_label.setObjectName("DateLabel")
        dash_header.addWidget(self.upload_date_label)
        
        dash_header.addStretch()
        
        pdf_btn = QPushButton("Download PDF Report")
        pdf_btn.clicked.connect(self.generate_pdf)
        dash_header.addWidget(pdf_btn)
        
        reset_btn = QPushButton("Upload New File")
        reset_btn.setObjectName("ResetButton")
        reset_btn.setCursor(Qt.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_ui)
        dash_header.addWidget(reset_btn)
        
        self.dashboard_layout.addLayout(dash_header)

        # Stats Cards
        self.stats_layout = QHBoxLayout()
        self.card_total = self.create_stat_card("Total Records", "0")
        self.card_types = self.create_stat_card("Equipment Types", "0")
        self.stats_layout.addWidget(self.card_total)
        self.stats_layout.addWidget(self.card_types)
        self.dashboard_layout.addLayout(self.stats_layout)

        # Average Parameters
        self.avg_label = QLabel("Average Parameters")
        self.avg_label.setObjectName("SectionTitle")
        self.dashboard_layout.addWidget(self.avg_label)

        self.avg_layout = QHBoxLayout()
        self.avg_flow = self.create_colored_card("Flowrate", "0", "#4BC0C0")
        self.avg_press = self.create_colored_card("Pressure", "0", "#36A2EB")
        self.avg_temp = self.create_colored_card("Temperature", "0", "#FF6384")
        
        self.avg_layout.addWidget(self.avg_flow)
        self.avg_layout.addWidget(self.avg_press)
        self.avg_layout.addWidget(self.avg_temp)
        self.dashboard_layout.addLayout(self.avg_layout)

        # Filters
        self.filter_card = QFrame()
        self.filter_card.setObjectName("FilterCard")
        self.filter_layout = QHBoxLayout(self.filter_card)
        self.filter_layout.setContentsMargins(16, 12, 16, 12)
        self.filter_layout.setSpacing(12)
        
        # Type filter
        type_box = QHBoxLayout()
        type_lbl = QLabel("Type")
        self.filter_type = QListWidget()
        self.filter_type_input = QLineEdit()
        self.filter_type_input.setPlaceholderText("All")
        type_box.addWidget(type_lbl)
        type_box.addWidget(self.filter_type_input)
        type_container = QFrame()
        type_container.setLayout(type_box)
        self.filter_layout.addWidget(type_container)
        
        # Name search
        name_box = QHBoxLayout()
        name_lbl = QLabel("Search")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Equipment Name")
        name_box.addWidget(name_lbl)
        name_box.addWidget(self.search_input)
        name_container = QFrame()
        name_container.setLayout(name_box)
        self.filter_layout.addWidget(name_container)
        
        # Flowrate range
        flow_box = QHBoxLayout()
        flow_lbl = QLabel("Flowrate")
        self.flow_min = QLineEdit()
        self.flow_min.setPlaceholderText("min")
        self.flow_max = QLineEdit()
        self.flow_max.setPlaceholderText("max")
        flow_box.addWidget(flow_lbl)
        flow_box.addWidget(self.flow_min)
        flow_box.addWidget(self.flow_max)
        flow_container = QFrame()
        flow_container.setLayout(flow_box)
        self.filter_layout.addWidget(flow_container)
        
        # Pressure range
        press_box = QHBoxLayout()
        press_lbl = QLabel("Pressure")
        self.press_min = QLineEdit()
        self.press_min.setPlaceholderText("min")
        self.press_max = QLineEdit()
        self.press_max.setPlaceholderText("max")
        press_box.addWidget(press_lbl)
        press_box.addWidget(self.press_min)
        press_box.addWidget(self.press_max)
        press_container = QFrame()
        press_container.setLayout(press_box)
        self.filter_layout.addWidget(press_container)
        
        # Temperature range
        temp_box = QHBoxLayout()
        temp_lbl = QLabel("Temperature")
        self.temp_min = QLineEdit()
        self.temp_min.setPlaceholderText("min")
        self.temp_max = QLineEdit()
        self.temp_max.setPlaceholderText("max")
        temp_box.addWidget(temp_lbl)
        temp_box.addWidget(self.temp_min)
        temp_box.addWidget(self.temp_max)
        temp_container = QFrame()
        temp_container.setLayout(temp_box)
        self.filter_layout.addWidget(temp_container)
        
        self.dashboard_layout.addWidget(self.filter_card)
        
        # Chart
        self.figure = plt.figure(figsize=(10, 4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(350)
        self.dashboard_layout.addWidget(self.canvas)

        # Table Preview
        self.table_label = QLabel("Data Preview")
        self.table_label.setObjectName("SectionTitle")
        self.dashboard_layout.addWidget(self.table_label)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(['Equipment Name', 'Type', 'Flowrate', 'Pressure', 'Temperature'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setMinimumHeight(200)
        self.dashboard_layout.addWidget(self.table)
        
        self.dashboard_scroll.setWidget(self.dashboard_container)
        self.content_layout.addWidget(self.dashboard_scroll)

        # Initial Load
        self.apply_styles()
        self.load_history_list()
        
        # Filter signals
        self.search_input.textChanged.connect(self.update_plots_with_filters)
        self.filter_type_input.textChanged.connect(self.update_plots_with_filters)
        self.flow_min.textChanged.connect(self.update_plots_with_filters)
        self.flow_max.textChanged.connect(self.update_plots_with_filters)
        self.press_min.textChanged.connect(self.update_plots_with_filters)
        self.press_max.textChanged.connect(self.update_plots_with_filters)
        self.temp_min.textChanged.connect(self.update_plots_with_filters)
        self.temp_max.textChanged.connect(self.update_plots_with_filters)

    def create_stat_card(self, title, value):
        card = QFrame()
        card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        
        title_lbl = QLabel(title)
        title_lbl.setObjectName("StatTitle")
        
        value_lbl = QLabel(value)
        value_lbl.setObjectName("StatValue")
        
        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        return card

    def create_colored_card(self, title, value, color):
        card = QFrame()
        card.setObjectName("StatCard")
        # Add a border left or something to distinguish
        card.setStyleSheet(f"border-left: 5px solid {color};")
        layout = QVBoxLayout(card)
        
        title_lbl = QLabel(title)
        title_lbl.setObjectName("StatTitle")
        title_lbl.setStyleSheet(f"color: {color};")
        
        value_lbl = QLabel(value)
        value_lbl.setObjectName("StatValue")
        value_lbl.setStyleSheet(f"color: {color};")
        
        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)
        return card

    def toggle_theme(self):
        if self.current_theme == 'light':
            self.current_theme = 'dark'
            self.theme_btn.setText("Switch to Light Mode")
        else:
            self.current_theme = 'light'
            self.theme_btn.setText("Switch to Dark Mode")
        self.apply_styles()

    def apply_styles(self):
        is_dark = self.current_theme == 'dark'
        
        bg_color = "#1e293b" if is_dark else "#f8fafc"
        text_color = "#f8fafc" if is_dark else "#1e293b"
        card_bg = "#334155" if is_dark else "#ffffff"
        border_color = "#475569" if is_dark else "#e2e8f0"
        sub_text = "#94a3b8" if is_dark else "#64748b"
        
        style = f"""
            QMainWindow, QScrollArea {{
                background-color: {bg_color};
            }}
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
            }}
            #Navbar {{
                background-color: {'#111827' if is_dark else '#eef2ff'};
                border-bottom: 1px solid {border_color};
            }}
            #HistorySidebar {{
                background-color: {card_bg};
                border-right: 1px solid {border_color};
            }}
            QListWidget {{
                background-color: {bg_color};
                border: none;
                color: {text_color};
            }}
            QListWidget::item:hover {{
                background-color: {border_color};
            }}
            #HeaderLabel {{
                font-size: 28px;
                font-weight: bold;
                color: #3b82f6;
                margin-bottom: 5px;
            }}
            #SubHeaderLabel {{
                font-size: 16px;
                color: {sub_text};
                margin-bottom: 20px;
            }}
            #DragDropWidget {{
                border: 2px dashed {border_color};
                border-radius: 16px;
                background-color: {card_bg};
                padding: 60px;
                font-size: 18px;
                color: {sub_text};
            }}
            #DragDropWidget[dragging="true"] {{
                border-color: #3b82f6;
                background-color: #eff6ff;
            }}
            #StatCard {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 20px;
            }}
            #StatTitle {{
                color: {sub_text};
                font-size: 12px;
                text-transform: uppercase;
                font-weight: bold;
                background-color: transparent;
            }}
            #StatValue {{
                color: {text_color};
                font-size: 32px;
                font-weight: bold;
                background-color: transparent;
            }}
            #FilterCard {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 12px;
                padding: 12px;
            }}
            #ResetButton {{
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QTableWidget {{
                background-color: {card_bg};
                border: 1px solid {border_color};
                border-radius: 8px;
                color: {text_color};
                gridline-color: {border_color};
            }}
            QHeaderView::section {{
                background-color: {card_bg};
                padding: 10px;
                border: none;
                border-bottom: 2px solid {border_color};
                color: {sub_text};
                font-weight: bold;
            }}
            #SectionTitle {{
                font-size: 18px;
                font-weight: bold;
                color: {text_color};
                margin-top: 20px;
            }}
            #DateLabel {{
                font-size: 14px;
                color: {sub_text};
                font-style: italic;
            }}
        """
        self.setStyleSheet(style)
        
        if hasattr(self, 'figure'):
            self.figure.patch.set_facecolor(bg_color)
            for ax in self.figure.axes:
                ax.set_facecolor(bg_color)
                ax.title.set_color(text_color)
                ax.xaxis.label.set_color(text_color)
                ax.yaxis.label.set_color(text_color)
                ax.tick_params(axis='x', colors=text_color)
                ax.tick_params(axis='y', colors=text_color)
                for spine in ax.spines.values():
                    spine.set_color(border_color)
            self.canvas.draw()

    def start_upload(self, file_path):
        self.error_label.setVisible(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.drag_drop_widget.setText(f"Uploading {os.path.basename(file_path)}...")
        self.drag_drop_widget.setEnabled(False)

        self.worker = UploadWorker(file_path, "http://localhost:8000/api/upload/", self.token)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.handle_success)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def handle_success(self, data):
        self.progress_bar.setVisible(False)
        self.upload_container.setVisible(False)
        self.dashboard_scroll.setVisible(True)
        self.update_dashboard(data)
        self.load_history_list() # Refresh history

    def handle_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.drag_drop_widget.setEnabled(True)
        self.drag_drop_widget.setText("Drag & Drop your CSV file here\nor click to browse")
        self.error_label.setText(error_msg)
        self.error_label.setVisible(True)

    def load_history_list(self):
        try:
            headers = {'Authorization': f'Token {self.token}'}
            response = requests.get('http://localhost:8000/api/history/', headers=headers)
            if response.status_code == 200:
                self.history_list.clear()
                for item in response.json():
                    # Display filename and date
                    date_str = item.get('uploaded_at', '').split('T')[0]
                    name = os.path.basename(item.get('file', 'Unknown'))
                    list_item = QListWidgetItem(f"{name}\n{date_str}")
                    list_item.setData(Qt.UserRole, item.get('id'))
                    self.history_list.addItem(list_item)
        except Exception as e:
            print(f"Error loading history: {e}")

    def load_history_item(self, item):
        history_id = item.data(Qt.UserRole)
        try:
            headers = {'Authorization': f'Token {self.token}'}
            response = requests.get(f'http://localhost:8000/api/history/{history_id}/', headers=headers)
            if response.status_code == 200:
                self.upload_container.setVisible(False)
                self.dashboard_scroll.setVisible(True)
                self.update_dashboard(response.json())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load history item: {e}")

    def update_dashboard(self, data):
        self.current_data = data
        
        # Update Date
        date_str = data.get('uploaded_at', '')
        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                self.upload_date_label.setText(f"Uploaded on: {dt.strftime('%Y-%m-%d %H:%M')}")
            except:
                self.upload_date_label.setText(f"Uploaded on: {date_str}")

        # Update Stats
        self.card_total.findChild(QLabel, "StatValue").setText(str(data.get('total_count', 0)))
        type_count = len(data.get('type_distribution', {}))
        self.card_types.findChild(QLabel, "StatValue").setText(str(type_count))

        # Update Averages
        avgs = data.get('averages', {})
        self.avg_flow.findChild(QLabel, "StatValue").setText(str(avgs.get('flowrate', 0)))
        self.avg_press.findChild(QLabel, "StatValue").setText(str(avgs.get('pressure', 0)))
        self.avg_temp.findChild(QLabel, "StatValue").setText(str(avgs.get('temperature', 0)))

        # Records and filters
        self.records = data.get('records', data.get('preview', []))
        self.update_plots_with_filters()

        # Update Table
        table_rows = self.filtered_records[:50] if hasattr(self, 'filtered_records') else data.get('preview', [])
        self.table.setRowCount(len(table_rows))
        for i, row in enumerate(table_rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row.get('Equipment Name', ''))))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.get('Type', ''))))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.get('Flowrate', ''))))
            self.table.setItem(i, 3, QTableWidgetItem(str(row.get('Pressure', ''))))
            self.table.setItem(i, 4, QTableWidgetItem(str(row.get('Temperature', ''))))
    
    def update_plots_with_filters(self):
        records = self.records if hasattr(self, 'records') else []
        # Build filters
        term = (self.search_input.text() or "").lower()
        type_filter = (self.filter_type_input.text() or "All")
        def parse_num(s):
            try:
                return float(s)
            except:
                return None
        fmin = parse_num(self.flow_min.text())
        fmax = parse_num(self.flow_max.text())
        pmin = parse_num(self.press_min.text())
        pmax = parse_num(self.press_max.text())
        tmin = parse_num(self.temp_min.text())
        tmax = parse_num(self.temp_max.text())
        
        filtered = []
        for r in records:
            name = str(r.get("Equipment Name", "")).lower()
            typ = r.get("Type", "")
            f = float(r.get("Flowrate", 0))
            p = float(r.get("Pressure", 0))
            t = float(r.get("Temperature", 0))
            name_ok = (not term) or (term in name)
            type_ok = (not type_filter) or (type_filter == "All") or (typ == type_filter)
            flow_ok = (fmin is None or f >= fmin) and (fmax is None or f <= fmax)
            press_ok = (pmin is None or p >= pmin) and (pmax is None or p <= pmax)
            temp_ok = (tmin is None or t >= tmin) and (tmax is None or t <= tmax)
            if name_ok and type_ok and flow_ok and press_ok and temp_ok:
                filtered.append(r)
        self.filtered_records = filtered
        self.plot_line_charts(filtered)
    
    def plot_line_charts(self, records):
        self.figure.clear()
        is_dark = self.current_theme == 'dark'
        text_color = "#f8fafc" if is_dark else "#1e293b"
        bg_color = "#1e293b" if is_dark else "#f8fafc"
        self.figure.patch.set_facecolor(bg_color)
        
        names = [str(r.get("Equipment Name", "")) for r in records]
        flow = [float(r.get("Flowrate", 0)) for r in records]
        press = [float(r.get("Pressure", 0)) for r in records]
        temp = [float(r.get("Temperature", 0)) for r in records]
        
        axes = self.figure.subplots(1, 3, sharex=False)
        config = [
            ("Flowrate", flow, "#4BC0C0"),
            ("Pressure", press, "#36A2EB"),
            ("Temperature", temp, "#FF6384"),
        ]
        for ax, (title, series, color) in zip(axes, config):
            ax.set_facecolor(bg_color)
            ax.plot(names, series, color=color, marker='o')
            ax.set_title(title, color=text_color)
            ax.tick_params(axis='x', colors=text_color, rotation=45)
            ax.tick_params(axis='y', colors=text_color)
            ax.grid(True, linestyle='--', alpha=0.3)
            for spine in ax.spines.values():
                spine.set_color('#cccccc')
        self.canvas.draw()

    def reset_ui(self):
        self.dashboard_scroll.setVisible(False)
        self.upload_container.setVisible(True)
        self.drag_drop_widget.setEnabled(True)
        self.drag_drop_widget.setText("Drag & Drop your CSV file here\nor click to browse")
        self.error_label.setVisible(False)
        self.current_data = None

    def generate_pdf(self):
        if not self.current_data:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", f"Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", "PDF Files (*.pdf)")
        
        if file_path:
            try:
                c = pdf_canvas.Canvas(file_path, pagesize=letter)
                width, height = letter
                
                # Title
                c.setFont("Helvetica-Bold", 24)
                c.drawString(50, height - 50, "Analysis Report")
                
                # Date
                c.setFont("Helvetica", 12)
                c.drawString(50, height - 80, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                if self.upload_date_label.text():
                     c.drawString(50, height - 100, self.upload_date_label.text())

                # Stats
                c.setFont("Helvetica-Bold", 14)
                c.drawString(50, height - 140, "Summary Statistics")
                
                c.setFont("Helvetica", 12)
                y = height - 170
                c.drawString(50, y, f"Total Records: {self.current_data.get('total_count', 0)}")
                c.drawString(250, y, f"Equipment Types: {len(self.current_data.get('type_distribution', {}))}")
                
                y -= 30
                avgs = self.current_data.get('averages', {})
                c.drawString(50, y, f"Avg Flowrate: {avgs.get('flowrate', 0)}")
                c.drawString(200, y, f"Avg Pressure: {avgs.get('pressure', 0)}")
                c.drawString(350, y, f"Avg Temperature: {avgs.get('temperature', 0)}")

                # Chart
                # Save chart to temp file
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    self.figure.savefig(tmp.name, facecolor="white")
                    tmp_name = tmp.name
                
                # Draw chart
                c.drawImage(tmp_name, 50, height - 500, width=500, height=250)
                os.unlink(tmp_name)

                c.save()
                QMessageBox.information(self, "Success", "Report saved successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate PDF: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Segoe UI", 10)
    font.setBold(True)
    app.setFont(font)
    
    login = LoginDialog()
    if login.exec_() == QDialog.Accepted:
        window = MainWindow(login.token)
        window.show()
        sys.exit(app.exec_())
