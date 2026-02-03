import os
import sys
import json
import requests
from datetime import datetime

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QProgressBar,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QMessageBox,
    QStackedWidget,
    QScrollArea,
    QCheckBox,
    QAbstractItemView,
    QSizePolicy,
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt

API_URL = "http://localhost:8000"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HERO_PATH = os.path.abspath(
    os.path.join(BASE_DIR, "..", "frontend-web", "public", "hero-banner.png")
)
ICON_PATH = os.path.join(BASE_DIR, "assets", "app-icon.png")
ICON_FALLBACK = os.path.join(BASE_DIR, "assets", "equipzense.png")


def build_eye_icon(opened, color="#94A3B8"):
    pix = QPixmap(18, 18)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(color))
    pen.setWidth(1)
    painter.setPen(pen)
    painter.drawEllipse(2, 6, 14, 6)
    painter.drawEllipse(8, 8, 2, 2)
    if not opened:
        painter.drawLine(3, 15, 15, 3)
    painter.end()
    return QIcon(pix)


class ApiClient:
    def __init__(self):
        self.token = None

    def set_token(self, token):
        self.token = token

    def _headers(self):
        headers = {}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        return headers

    def post_json(self, path, payload):
        return requests.post(f"{API_URL}{path}", json=payload, headers=self._headers(), timeout=15)

    def get(self, path, stream=False):
        return requests.get(f"{API_URL}{path}", headers=self._headers(), timeout=20, stream=stream)

    def post_files(self, path, files):
        return requests.post(
            f"{API_URL}{path}",
            files=files,
            headers=self._headers(),
            timeout=30,
        )


class Theme:
    def __init__(self):
        self.mode = "dark"

    def toggle(self):
        self.mode = "light" if self.mode == "dark" else "dark"

    @property
    def colors(self):
        if self.mode == "dark":
            return {
                "bg": "#141026",
                "surface": "#221A3A",
                "text": "#EDE9FE",
                "subtext": "#BEB6E4",
                "border": "#2F2552",
                "primary": "#A48BFF",
                "secondary": "#7FD7E3",
            }
        return {
            "bg": "#F6F4FA",
            "surface": "#FFFFFF",
            "text": "#1F2430",
            "subtext": "#6C7280",
            "border": "#E6E1F2",
            "primary": "#7F8BFF",
            "secondary": "#5BC5D9",
        }


class HeroBanner(QWidget):
    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        self.image = QLabel()
        self.image.setAlignment(Qt.AlignCenter)
        self.image.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.base_pix = None
        if os.path.exists(HERO_PATH):
            pix = QPixmap(HERO_PATH)
            if not pix.isNull():
                self.base_pix = pix
                self._resize_pixmap()
            else:
                self.image.setText("EquipZense\nAnalyze. Visualize. Optimize.")
        else:
            self.image.setText("EquipZense\nAnalyze. Visualize. Optimize.")
        layout.addStretch()
        layout.addWidget(self.image, alignment=Qt.AlignCenter)
        layout.addStretch()

    def _resize_pixmap(self):
        if not self.base_pix:
            return
        target = min(720, max(320, int(self.width() * 0.85)))
        self.image.setPixmap(self.base_pix.scaledToWidth(target, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_pixmap()


class LoginPage(QWidget):
    def __init__(self, api, on_login, on_register):
        super().__init__()
        self.api = api
        self.on_login = on_login
        self.on_register = on_register
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("AuthCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        title = QLabel("Login")
        title.setObjectName("AuthTitle")
        card_layout.addWidget(title)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.add_password_toggle(self.password)
        self.username.returnPressed.connect(self.handle_login)
        self.password.returnPressed.connect(self.handle_login)
        card_layout.addWidget(self.username)
        card_layout.addWidget(self.password)

        self.error = QLabel("")
        self.error.setObjectName("ErrorLabel")
        self.error.setVisible(False)
        card_layout.addWidget(self.error)

        btn = QPushButton("Login")
        btn.clicked.connect(self.handle_login)
        btn.setObjectName("PrimaryButton")
        card_layout.addWidget(btn)

        link = QPushButton("Need an account? Register")
        link.setObjectName("LinkButton")
        link.clicked.connect(self.on_register)
        card_layout.addWidget(link)

        layout.addStretch()
        layout.addWidget(card, alignment=Qt.AlignCenter)
        layout.addStretch()

    def handle_login(self):
        self.error.setVisible(False)
        payload = {"username": self.username.text(), "password": self.password.text()}
        if not payload["username"] or not payload["password"]:
            self.error.setText("Please enter username and password.")
            self.error.setVisible(True)
            return
        try:
            res = self.api.post_json("/api/login/", payload)
            if res.status_code == 200:
                data = res.json()
                self.api.set_token(data.get("token"))
                self.on_login(data.get("user"))
            else:
                msg = res.json().get("error") if res.headers.get("content-type", "").startswith("application/json") else "Login failed."
                self.error.setText(msg or "Login failed.")
                self.error.setVisible(True)
        except Exception as exc:
            self.error.setText(str(exc))
            self.error.setVisible(True)

    def add_password_toggle(self, line_edit):
        action = line_edit.addAction(build_eye_icon(False), QLineEdit.TrailingPosition)
        action.setToolTip("Show password")
        def toggle():
            if line_edit.echoMode() == QLineEdit.Password:
                line_edit.setEchoMode(QLineEdit.Normal)
                action.setIcon(build_eye_icon(True))
                action.setToolTip("Hide password")
            else:
                line_edit.setEchoMode(QLineEdit.Password)
                action.setIcon(build_eye_icon(False))
                action.setToolTip("Show password")
        action.triggered.connect(toggle)


class RegisterPage(QWidget):
    def __init__(self, api, on_register, on_login):
        super().__init__()
        self.api = api
        self.on_register = on_register
        self.on_login = on_login
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        card = QFrame()
        card.setObjectName("AuthCard")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        title = QLabel("Register")
        title.setObjectName("AuthTitle")
        card_layout.addWidget(title)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.add_password_toggle(self.password)
        self.username.returnPressed.connect(self.handle_register)
        self.email.returnPressed.connect(self.handle_register)
        self.password.returnPressed.connect(self.handle_register)
        card_layout.addWidget(self.username)
        card_layout.addWidget(self.email)
        card_layout.addWidget(self.password)

        self.error = QLabel("")
        self.error.setObjectName("ErrorLabel")
        self.error.setVisible(False)
        card_layout.addWidget(self.error)

        btn = QPushButton("Register")
        btn.setObjectName("PrimaryButton")
        btn.clicked.connect(self.handle_register)
        card_layout.addWidget(btn)

        link = QPushButton("Already have an account? Login")
        link.setObjectName("LinkButton")
        link.clicked.connect(self.on_login)
        card_layout.addWidget(link)

        layout.addStretch()
        layout.addWidget(card, alignment=Qt.AlignCenter)
        layout.addStretch()

    def handle_register(self):
        self.error.setVisible(False)
        payload = {
            "username": self.username.text(),
            "email": self.email.text(),
            "password": self.password.text(),
        }
        if not payload["username"] or not payload["email"] or not payload["password"]:
            self.error.setText("Please fill out all fields.")
            self.error.setVisible(True)
            return
        try:
            res = self.api.post_json("/api/register/", payload)
            if res.status_code in (200, 201):
                data = res.json()
                self.api.set_token(data.get("token"))
                self.on_register(data.get("user"))
            else:
                try:
                    data = res.json()
                    msg = data.get("error") or (data.get("username") or ["Registration failed."])[0]
                except Exception:
                    msg = "Registration failed."
                self.error.setText(msg)
                self.error.setVisible(True)
        except Exception as exc:
            self.error.setText(str(exc))
            self.error.setVisible(True)

    def add_password_toggle(self, line_edit):
        action = line_edit.addAction(build_eye_icon(False), QLineEdit.TrailingPosition)
        action.setToolTip("Show password")
        def toggle():
            if line_edit.echoMode() == QLineEdit.Password:
                line_edit.setEchoMode(QLineEdit.Normal)
                action.setIcon(build_eye_icon(True))
                action.setToolTip("Hide password")
            else:
                line_edit.setEchoMode(QLineEdit.Password)
                action.setIcon(build_eye_icon(False))
                action.setToolTip("Show password")
        action.triggered.connect(toggle)


class UploadCard(QFrame):
    def __init__(self, api, on_success):
        super().__init__()
        self.api = api
        self.on_success = on_success
        self.setObjectName("UploadCard")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.drop = QPushButton("Drag & Drop your CSV file here\nor click to browse")
        self.drop.setObjectName("DropArea")
        self.drop.clicked.connect(self.pick_file)
        layout.addWidget(self.drop)

        self.file_label = QLabel("")
        self.file_label.setObjectName("FileName")
        layout.addWidget(self.file_label)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.error = QLabel("")
        self.error.setObjectName("ErrorLabel")
        self.error.setVisible(False)
        layout.addWidget(self.error)

        support = QLabel("Supported format: .csv (Equipment Name, Type, Flowrate, Pressure, Temperature)")
        support.setObjectName("SupportText")
        layout.addWidget(support)

    def pick_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.upload(file_path)

    def upload(self, file_path):
        self.error.setVisible(False)
        self.progress.setVisible(True)
        self.progress.setValue(10)
        self.file_label.setText(os.path.basename(file_path))
        try:
            with open(file_path, "rb") as f:
                res = self.api.post_files("/api/upload/", {"file": f})
            if res.status_code == 201:
                self.progress.setValue(100)
                self.on_success(res.json())
            else:
                self.error.setText("Failed to upload file.")
                self.error.setVisible(True)
        except Exception as exc:
            self.error.setText(str(exc))
            self.error.setVisible(True)
        finally:
            self.progress.setVisible(False)


class CompareCard(QFrame):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.setObjectName("CompareCard")
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        inputs = QHBoxLayout()
        self.file_a = QPushButton("Choose CSV A")
        self.file_b = QPushButton("Choose CSV B")
        self.file_a.setObjectName("SecondaryButton")
        self.file_b.setObjectName("SecondaryButton")
        self.file_a.clicked.connect(lambda: self.pick_file("a"))
        self.file_b.clicked.connect(lambda: self.pick_file("b"))
        inputs.addWidget(self.file_a)
        inputs.addWidget(self.file_b)
        layout.addLayout(inputs)

        self.compare_btn = QPushButton("Compare CSVs")
        self.compare_btn.setObjectName("PrimaryButton")
        self.compare_btn.clicked.connect(self.compare)
        layout.addWidget(self.compare_btn)

        self.error = QLabel("")
        self.error.setObjectName("ErrorLabel")
        self.error.setVisible(False)
        layout.addWidget(self.error)

        self.summary = QLabel("")
        self.summary.setObjectName("SupportText")
        layout.addWidget(self.summary)

        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "Equipment", "Type A", "Type B",
            "Flow A", "Flow B", "Δ Flow",
            "Pressure A", "Pressure B", "Δ Pressure",
            "Temp A", "Temp B", "Δ Temp",
            "Status",
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setVisible(False)
        layout.addWidget(self.table)

        self.path_a = None
        self.path_b = None

    def pick_file(self, which):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV", "", "CSV Files (*.csv)")
        if not file_path:
            return
        if which == "a":
            self.path_a = file_path
            self.file_a.setText(os.path.basename(file_path))
        else:
            self.path_b = file_path
            self.file_b.setText(os.path.basename(file_path))

    def compare(self):
        self.error.setVisible(False)
        if not self.path_a or not self.path_b:
            self.error.setText("Please select both CSV files before comparing.")
            self.error.setVisible(True)
            return
        try:
            with open(self.path_a, "rb") as fa, open(self.path_b, "rb") as fb:
                res = self.api.post_files("/api/compare/", {"file_a": fa, "file_b": fb})
            if res.status_code == 200:
                data = res.json()
                summary = data.get("diff", {}).get("summary", {})
                self.summary.setText(
                    f"Only in A: {summary.get('only_in_a')} | "
                    f"Only in B: {summary.get('only_in_b')} | "
                    f"In Both: {summary.get('in_both')}"
                )
                rows = data.get("diff", {}).get("rows", [])
                self.table.setRowCount(len(rows))
                for i, row in enumerate(rows):
                    values = [
                        row.get("equipment_name"),
                        row.get("type_a"),
                        row.get("type_b"),
                        row.get("flowrate_a"),
                        row.get("flowrate_b"),
                        row.get("flowrate_delta"),
                        row.get("pressure_a"),
                        row.get("pressure_b"),
                        row.get("pressure_delta"),
                        row.get("temperature_a"),
                        row.get("temperature_b"),
                        row.get("temperature_delta"),
                        row.get("status"),
                    ]
                    for j, value in enumerate(values):
                        self.table.setItem(i, j, QTableWidgetItem(str(value)))
                self.table.setVisible(True)
            else:
                self.error.setText("Failed to compare files.")
                self.error.setVisible(True)
        except Exception as exc:
            self.error.setText(str(exc))
            self.error.setVisible(True)


class UploadPage(QWidget):
    def __init__(self, api, on_analysis):
        super().__init__()
        self.api = api
        self.on_analysis = on_analysis
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(16)

        switch = QHBoxLayout()
        self.single_btn = QPushButton("Single Upload")
        self.compare_btn = QPushButton("Compare Two CSVs")
        self.single_btn.setObjectName("SwitchActive")
        self.compare_btn.setObjectName("SwitchInactive")
        self.single_btn.clicked.connect(lambda: self.set_mode("single"))
        self.compare_btn.clicked.connect(lambda: self.set_mode("compare"))
        switch.addWidget(self.single_btn)
        switch.addWidget(self.compare_btn)
        layout.addLayout(switch)

        self.stack = QStackedWidget()
        self.upload_card = UploadCard(api, self.on_analysis)
        self.compare_card = CompareCard(api)
        self.stack.addWidget(self.upload_card)
        self.stack.addWidget(self.compare_card)
        layout.addWidget(self.stack)

        self.set_mode("single")

    def set_mode(self, mode):
        if mode == "single":
            self.stack.setCurrentIndex(0)
            self.single_btn.setObjectName("SwitchActive")
            self.compare_btn.setObjectName("SwitchInactive")
        else:
            self.stack.setCurrentIndex(1)
            self.single_btn.setObjectName("SwitchInactive")
            self.compare_btn.setObjectName("SwitchActive")
        self.style().unpolish(self)
        self.style().polish(self)


class HistoryPage(QWidget):
    def __init__(self, api, on_view):
        super().__init__()
        self.api = api
        self.on_view = on_view
        self.favorites = self.load_favorites()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Upload History")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        controls = QHBoxLayout()
        self.toggle = QPushButton("Show Favorites")
        self.toggle.setCheckable(True)
        self.toggle.clicked.connect(self.refresh)
        controls.addWidget(self.toggle)
        self.count = QLabel("")
        self.count.setObjectName("SupportText")
        controls.addWidget(self.count)
        controls.addStretch()
        layout.addLayout(controls)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Favorite", "ID", "File Name", "Uploaded At"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self.handle_view)
        layout.addWidget(self.table)

    def load_favorites(self):
        path = os.path.join(BASE_DIR, "favorites.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def save_favorites(self):
        path = os.path.join(BASE_DIR, "favorites.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.favorites, f)

    def refresh(self):
        try:
            res = self.api.get("/api/history/")
            if res.status_code == 200:
                data = res.json()
                if self.toggle.isChecked():
                    data = [d for d in data if str(d.get("id")) in self.favorites]
                self.table.setRowCount(len(data))
                for i, item in enumerate(data):
                    fav_btn = QPushButton("★" if str(item["id"]) in self.favorites else "☆")
                    fav_btn.clicked.connect(lambda _, row=item: self.toggle_favorite(row))
                    self.table.setCellWidget(i, 0, fav_btn)
                    self.table.setItem(i, 1, QTableWidgetItem(str(item["id"])))
                    self.table.setItem(i, 2, QTableWidgetItem(os.path.basename(item["file"])))
                    self.table.setItem(i, 3, QTableWidgetItem(item["uploaded_at"]))
                self.count.setText(f"Favorites: {len(self.favorites)}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def toggle_favorite(self, item):
        key = str(item["id"])
        if key in self.favorites:
            del self.favorites[key]
        else:
            self.favorites[key] = True
        self.save_favorites()
        self.refresh()

    def handle_view(self, row, col):
        item = self.table.item(row, 1)
        if not item:
            return
        self.on_view(int(item.text()))


class AnalysisPage(QWidget):
    def __init__(self, api, on_history):
        super().__init__()
        self.api = api
        self.on_history = on_history
        self.stats = None
        self.setMinimumHeight(980)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("Analysis Report")
        title.setObjectName("SectionTitle")
        header.addWidget(title)
        header.addStretch()
        self.download_btn = QPushButton("Download PDF")
        self.download_btn.clicked.connect(self.download_pdf)
        self.download_btn.setObjectName("PrimaryButton")
        header.addWidget(self.download_btn)
        history_btn = QPushButton("History")
        history_btn.clicked.connect(self.on_history)
        history_btn.setObjectName("SecondaryButton")
        header.addWidget(history_btn)
        layout.addLayout(header)

        self.summary_row = QHBoxLayout()
        self.summary_label = QLabel("Total Equipment Count: 0")
        self.summary_label.setObjectName("SupportText")
        self.summary_row.addWidget(self.summary_label)
        self.summary_row.addStretch()
        layout.addLayout(self.summary_row)

        self.avg_row = QHBoxLayout()
        self.avg_flow = QLabel("Flowrate: 0")
        self.avg_press = QLabel("Pressure: 0")
        self.avg_temp = QLabel("Temperature: 0")
        for lbl in (self.avg_flow, self.avg_press, self.avg_temp):
            lbl.setObjectName("AvgCard")
            self.avg_row.addWidget(lbl)
        layout.addLayout(self.avg_row)

        self.figure = plt.figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(520)
        layout.addWidget(self.canvas)

        filters = QHBoxLayout()
        self.col_filters = {}
        self.type_filters = {}
        self.columns = ["Equipment Name", "Type", "Flowrate", "Pressure", "Temperature"]
        self.col_box = QFrame()
        col_layout = QVBoxLayout(self.col_box)
        col_layout.addWidget(QLabel("Columns"))
        for col in self.columns:
            cb = QCheckBox(col)
            cb.setChecked(True)
            cb.stateChanged.connect(self.apply_filters)
            self.col_filters[col] = cb
            col_layout.addWidget(cb)
        filters.addWidget(self.col_box)

        self.type_box = QFrame()
        type_layout = QVBoxLayout(self.type_box)
        type_layout.addWidget(QLabel("Equipment Types"))
        self.type_layout = type_layout
        filters.addWidget(self.type_box)
        filters.addStretch()
        layout.addLayout(filters)

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def set_stats(self, stats):
        self.stats = stats
        total = stats.get("total_count", 0)
        self.summary_label.setText(f"Total Equipment Count: {total}")
        avgs = stats.get("averages", {})
        self.avg_flow.setText(f"Flowrate: {avgs.get('flowrate', 0)}")
        self.avg_press.setText(f"Pressure: {avgs.get('pressure', 0)}")
        self.avg_temp.setText(f"Temperature: {avgs.get('temperature', 0)}")
        self.setup_type_filters()
        self.render_charts()
        self.apply_filters()

    def setup_type_filters(self):
        for i in reversed(range(self.type_layout.count())):
            item = self.type_layout.itemAt(i)
            widget = item.widget()
            if widget and isinstance(widget, QCheckBox):
                widget.setParent(None)
        self.type_filters = {}
        types = sorted({r.get("Type") for r in self.stats.get("records", []) if r.get("Type")})
        for t in types:
            cb = QCheckBox(t)
            cb.setChecked(True)
            cb.stateChanged.connect(self.apply_filters)
            self.type_filters[t] = cb
            self.type_layout.addWidget(cb)

    def render_charts(self):
        self.figure.clear()
        if not self.stats:
            self.canvas.draw()
            return
        records = self.stats.get("records", [])
        names = [r.get("Equipment Name", "") for r in records]
        flow = [r.get("Flowrate", 0) for r in records]
        press = [r.get("Pressure", 0) for r in records]
        temp = [r.get("Temperature", 0) for r in records]
        ax1 = self.figure.add_subplot(121)
        if names:
            idx = list(range(len(names)))
            width = 0.25
            ax1.bar([i - width for i in idx], flow, width=width, label="Flowrate")
            ax1.bar(idx, press, width=width, label="Pressure")
            ax1.bar([i + width for i in idx], temp, width=width, label="Temperature")
            ax1.set_xticks(idx)
            ax1.set_xticklabels(names, rotation=45, ha="right", fontsize=8)
        ax1.set_title("Equipment Metrics")
        ax1.grid(axis="y", linestyle="--", alpha=0.3)
        ax1.legend(fontsize=8)

        ax2 = self.figure.add_subplot(122)
        type_dist = self.stats.get("type_distribution", {})
        labels = list(type_dist.keys())
        values = list(type_dist.values())
        if values:
            ax2.pie(values, labels=labels, autopct="%1.0f%%")
        else:
            ax2.text(0.5, 0.5, "No data", ha="center", va="center")
        self.figure.tight_layout()
        self.canvas.draw()

    def download_pdf(self):
        if not self.stats:
            return
        report_id = self.stats.get("file_id")
        if not report_id:
            return
        res = self.api.get(f"/api/history/{report_id}/report/", stream=True)
        if res.status_code == 200:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save PDF", f"analysis_report_{report_id}.pdf", "PDF Files (*.pdf)")
            if file_path:
                with open(file_path, "wb") as f:
                    f.write(res.content)
        else:
            QMessageBox.critical(self, "Error", "Failed to download PDF.")

    def apply_filters(self):
        if not self.stats:
            return
        visible_cols = [c for c in self.columns if self.col_filters[c].isChecked()]
        active_types = [t for t, cb in self.type_filters.items() if cb.isChecked()]
        raw_rows = self.stats.get("preview", [])
        filtered = [r for r in raw_rows if (not active_types or r.get("Type") in active_types)]

        self.table.setColumnCount(len(visible_cols))
        self.table.setHorizontalHeaderLabels(visible_cols)
        self.table.setRowCount(len(filtered))
        for i, row in enumerate(filtered):
            for j, col in enumerate(visible_cols):
                self.table.setItem(i, j, QTableWidgetItem(str(row.get(col, ""))))
        self.adjust_table_height()

    def adjust_table_height(self, min_rows=10):
        header_height = self.table.horizontalHeader().height()
        row_height = self.table.verticalHeader().defaultSectionSize()
        target_rows = max(min_rows, 1)
        self.table.setMinimumHeight(header_height + row_height * target_rows + 6)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api = ApiClient()
        self.theme = Theme()
        self.setWindowTitle("EquipZense")
        self.resize(1280, 820)
        icon_path = ICON_PATH if os.path.exists(ICON_PATH) else ICON_FALLBACK
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.navbar = QFrame()
        self.navbar.setObjectName("Navbar")
        nav_layout = QHBoxLayout(self.navbar)
        nav_layout.setContentsMargins(20, 10, 20, 10)
        self.brand = QLabel("EquipZense")
        self.brand.setObjectName("BrandLabel")
        nav_layout.addWidget(self.brand)
        nav_layout.addStretch()
        self.upload_btn = QPushButton("Upload")
        self.history_btn = QPushButton("History")
        self.logout_btn = QPushButton("Logout")
        self.theme_btn = QPushButton("Toggle Theme")
        self.upload_btn.setObjectName("NavPrimary")
        self.history_btn.setObjectName("NavSecondary")
        self.logout_btn.setObjectName("NavSecondary")
        self.theme_btn.setObjectName("NavGhost")
        self.upload_btn.clicked.connect(lambda: self.show_page("upload"))
        self.history_btn.clicked.connect(lambda: self.show_page("history"))
        self.logout_btn.clicked.connect(self.logout)
        self.theme_btn.clicked.connect(self.toggle_theme)
        nav_layout.addWidget(self.upload_btn)
        nav_layout.addWidget(self.history_btn)
        nav_layout.addWidget(self.logout_btn)
        nav_layout.addWidget(self.theme_btn)
        root_layout.addWidget(self.navbar)

        self.hero = HeroBanner()
        root_layout.addWidget(self.hero)

        self.stack = QStackedWidget()
        self.content_scroll = QScrollArea()
        self.content_scroll.setWidgetResizable(True)
        self.content_scroll.setFrameShape(QFrame.NoFrame)
        self.content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.content_scroll.setWidget(self.stack)
        root_layout.addWidget(self.content_scroll)

        self.login_page = LoginPage(self.api, self.on_login, self.show_register)
        self.register_page = RegisterPage(self.api, self.on_register, self.show_login)
        self.upload_page = UploadPage(self.api, self.on_analysis)
        self.history_page = HistoryPage(self.api, self.on_history_item)
        self.analysis_page = AnalysisPage(self.api, lambda: self.show_page("history"))

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.register_page)
        self.stack.addWidget(self.upload_page)
        self.stack.addWidget(self.history_page)
        self.stack.addWidget(self.analysis_page)

        self.show_login()
        self.apply_theme()

    def show_login(self):
        self.stack.setCurrentWidget(self.login_page)
        self.set_nav_visible(False)

    def show_register(self):
        self.stack.setCurrentWidget(self.register_page)
        self.set_nav_visible(False)

    def set_nav_visible(self, visible):
        self.navbar.setVisible(visible)
        self.hero.setVisible(visible)

    def on_login(self, user):
        self.set_nav_visible(True)
        self.show_page("upload")

    def on_register(self, user):
        self.set_nav_visible(True)
        self.show_page("upload")

    def logout(self):
        self.api.set_token(None)
        self.show_login()

    def show_page(self, name):
        if name == "upload":
            self.stack.setCurrentWidget(self.upload_page)
        elif name == "history":
            self.history_page.refresh()
            self.stack.setCurrentWidget(self.history_page)
        elif name == "analysis":
            self.stack.setCurrentWidget(self.analysis_page)

    def on_analysis(self, stats):
        self.analysis_page.set_stats(stats)
        self.show_page("analysis")

    def on_history_item(self, item_id):
        res = self.api.get(f"/api/history/{item_id}/")
        if res.status_code == 200:
            self.analysis_page.set_stats(res.json())
            self.show_page("analysis")
        else:
            QMessageBox.critical(self, "Error", "Failed to load analysis.")

    def toggle_theme(self):
        self.theme.toggle()
        self.apply_theme()

    def apply_theme(self):
        c = self.theme.colors
        gradient = (
            f"qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {c['bg']}, stop:0.55 {c['bg']}, stop:1 #0a0714)"
            if self.theme.mode == "dark"
            else c["bg"]
        )
        style = f"""
            QMainWindow {{
                background-color: {c['bg']};
            }}
            QWidget {{
                background-color: {gradient};
                color: {c['text']};
                font-size: 12px;
            }}
            QScrollArea {{
                background-color: {c['bg']};
                border: none;
            }}
            QScrollArea QWidget {{
                background-color: transparent;
            }}
            #Navbar {{
                background-color: {c['bg']};
                border-bottom: 1px solid {c['border']};
            }}
            #BrandLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {c['primary']};
            }}
            #NavPrimary {{
                background-color: {c['primary']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 10px;
                font-weight: 600;
            }}
            #NavPrimary:hover {{
                border: 1px solid {c['secondary']};
                background-color: rgba(164, 139, 255, 0.85);
            }}
            #NavSecondary {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                color: {c['text']};
                padding: 8px 16px;
                border-radius: 10px;
            }}
            #NavSecondary:hover {{
                border-color: {c['primary']};
                color: {c['primary']};
                background-color: rgba(164, 139, 255, 0.12);
            }}
            #NavGhost {{
                background-color: transparent;
                border: 1px solid {c['border']};
                color: {c['subtext']};
                padding: 8px 12px;
                border-radius: 10px;
            }}
            #NavGhost:hover {{
                border-color: {c['secondary']};
                color: {c['secondary']};
                background-color: {c['surface']};
            }}
            QPushButton {{
                padding: 10px 18px;
                border-radius: 10px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                border-color: {c['primary']};
            }}
            #AuthCard {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 12px;
                padding: 20px;
                min-width: 420px;
            }}
            #AuthTitle {{
                font-size: 20px;
                font-weight: bold;
            }}
            QLineEdit {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 10px 12px;
                min-width: 260px;
            }}
            QLineEdit::indicator {{
                width: 0px;
                height: 0px;
            }}
            QCheckBox {{
                spacing: 8px;
            }}
            QProgressBar {{
                background: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                height: 12px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {c['primary']};
                border-radius: 8px;
            }}
            #PrimaryButton {{
                background-color: {c['primary']};
                color: white;
                border: none;
                padding: 10px 18px;
                border-radius: 10px;
                font-weight: 600;
            }}
            #PrimaryButton:hover {{
                border: 1px solid {c['secondary']};
                background-color: rgba(164, 139, 255, 0.9);
            }}
            #SecondaryButton {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                padding: 10px 18px;
                border-radius: 10px;
            }}
            #SecondaryButton:hover {{
                border-color: {c['primary']};
                color: {c['primary']};
                background-color: rgba(164, 139, 255, 0.12);
            }}
            #LinkButton {{
                background: transparent;
                border: none;
                color: {c['secondary']};
                text-align: left;
                min-width: 0;
            }}
            #UploadCard, #CompareCard {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 16px;
                padding: 20px;
                min-width: 560px;
            }}
            #DropArea {{
                background-color: {c['bg']};
                border: 2px dashed {c['border']};
                border-radius: 12px;
                padding: 30px;
                text-align: center;
            }}
            #DropArea:hover {{
                border-color: {c['primary']};
                color: {c['primary']};
                background-color: rgba(164, 139, 255, 0.08);
            }}
            #SupportText {{
                color: {c['subtext']};
            }}
            #SectionTitle {{
                font-size: 18px;
                font-weight: 700;
                color: {c['text']};
            }}
            #ErrorLabel {{
                color: #ef4444;
            }}
            #AvgCard {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                border-radius: 10px;
                padding: 12px 16px;
                font-weight: bold;
            }}
            #SwitchActive {{
                background-color: rgba(157, 124, 255, 0.2);
                border: 1px solid rgba(157, 124, 255, 0.35);
                padding: 8px 16px;
                border-radius: 10px;
            }}
            #SwitchActive:hover {{
                background-color: rgba(157, 124, 255, 0.32);
            }}
            #SwitchInactive {{
                background-color: transparent;
                border: 1px solid {c['border']};
                padding: 8px 16px;
                border-radius: 10px;
            }}
            #SwitchInactive:hover {{
                border-color: {c['primary']};
                color: {c['primary']};
                background-color: rgba(164, 139, 255, 0.08);
            }}
            QTableWidget {{
                background-color: {c['surface']};
                border: 1px solid {c['border']};
                gridline-color: {c['border']};
                border-radius: 10px;
            }}
            QTableWidget::item:selected {{
                background-color: rgba(157, 124, 255, 0.18);
            }}
            QHeaderView::section {{
                background-color: {c['surface']};
                border-bottom: 1px solid {c['border']};
                color: {c['subtext']};
                padding: 10px;
            }}
        """
        self.setStyleSheet(style)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    icon_path = ICON_PATH if os.path.exists(ICON_PATH) else ICON_FALLBACK
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
