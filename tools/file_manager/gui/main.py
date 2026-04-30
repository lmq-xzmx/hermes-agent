"""
PyQt6 File Manager GUI
Connects to FastAPI at http://localhost:8080
"""

import sys
import os
import requests
from io import BytesIO

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QDialog, QLineEdit, QPushButton, QLabel, QMessageBox, QTreeWidget,
    QTreeWidgetItem, QListWidget, QListWidgetItem, QFileDialog,
    QToolBar, QStatusBar, QMenuBar, QMenu, QTextEdit, QInputDialog,
    QSplitter, QDialogButtonBox, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon, QPalette, QColor, QCursor


BASE_URL = "http://localhost:8080"


# ============== Dark Theme Stylesheet ==============
DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #1e1e1e;
    color: #e0e0e0;
}
QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}
QMenuBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
}
QMenuBar::item:selected {
    background-color: #3d3d3d;
}
QMenu {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
}
QMenu::item:selected {
    background-color: #3d3d3d;
}
QToolBar {
    background-color: #2d2d2d;
    border: none;
    spacing: 4px;
    padding: 4px;
}
QToolButton {
    background-color: transparent;
    border: none;
    padding: 6px;
    border-radius: 4px;
}
QToolButton:hover {
    background-color: #3d3d3d;
}
QLineEdit, QTextEdit {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    padding: 4px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #0078d4;
}
QPushButton {
    background-color: #0e639c;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 70px;
}
QPushButton:hover {
    background-color: #1177bb;
}
QPushButton:pressed {
    background-color: #0d5a8c;
}
QPushButton:disabled {
    background-color: #3d3d3d;
    color: #808080;
}
QTreeWidget, QListWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    outline: none;
}
QTreeWidget::item:hover, QListWidget::item:hover {
    background-color: #2d2d2d;
}
QTreeWidget::item:selected, QListWidget::item:selected {
    background-color: #094771;
}
QTreeWidget::branch:has-children:!has-siblings:closed,
QTreeWidget::branch:closed:has-children:has-siblings {
    border-image: none;
    image: url(dark/branch-closed.png);
}
QTreeWidget::branch:open:has-children:!has-siblings,
QTreeWidget::branch:open:has-children:has-siblings {
    border-image: none;
    image: url(dark/branch-open.png);
}
QHeaderView::section {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: none;
    border-right: 1px solid #3d3d3d;
    border-bottom: 1px solid #3d3d3d;
    padding: 4px;
}
QStatusBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
}
QDialogButtonBox QPushButton {
    min-width: 80px;
}
QSplitter::handle {
    background-color: #3d3d3d;
}
"""


# ============== Login / Register Dialog ==============
class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.token = None
        self.username = None
        self.is_register_mode = False
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("登录 — 文件管理器")
        self.setMinimumWidth(380)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.title_label = QLabel("<h2>欢迎回来</h2>")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel("登录以访问您的文件")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.subtitle_label.setStyleSheet("color: #808080;")
        layout.addWidget(self.subtitle_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名（3–32个字符）")
        self.username_input.setMinimumHeight(32)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码（至少6个字符）")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Extra field for register mode (confirm password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("确认密码")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setVisible(False)

        form_layout.addRow("用户名：", self.username_input)
        form_layout.addRow("密码：", self.password_input)
        form_layout.addRow("确认：", self.confirm_password_input)

        layout.addLayout(form_layout)

        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #ff6b6b;")
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Toggle link
        self.toggle_label = QLabel(
            '<a href="#" style="color: #58a6ff; text-decoration: none;">没有账户？立即注册</a>'
        )
        self.toggle_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.toggle_label.setOpenExternalLinks(False)
        self.toggle_label.linkActivated.connect(self.toggle_mode)
        layout.addWidget(self.toggle_label)

        # Buttons
        self.btn_box = QDialogButtonBox()
        self.submit_btn = QPushButton("登录")
        self.submit_btn.setDefault(True)
        self.submit_btn.setMinimumHeight(36)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumHeight(36)
        self.btn_box.addButton(self.submit_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_box.addButton(self.cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

        self.submit_btn.clicked.connect(self.handle_submit)
        self.cancel_btn.clicked.connect(self.reject)

        layout.addWidget(self.btn_box)
        self.setLayout(layout)

    def toggle_mode(self):
        self.is_register_mode = not self.is_register_mode
        self.status_label.setVisible(False)

        if self.is_register_mode:
            self.title_label.setText("<h2>创建账户</h2>")
            self.subtitle_label.setText("注册后即可开始管理文件")
            self.submit_btn.setText("注册")
            self.toggle_label.setText(
                '<a href="#" style="color: #58a6ff; text-decoration: none;">已有账户？立即登录</a>'
            )
            self.confirm_password_input.setVisible(True)
            self.setWindowTitle("注册 — 文件管理器")
        else:
            self.title_label.setText("<h2>欢迎回来</h2>")
            self.subtitle_label.setText("登录以访问您的文件")
            self.submit_btn.setText("登录")
            self.toggle_label.setText(
                '<a href="#" style="color: #58a6ff; text-decoration: none;">没有账户？立即注册</a>'
            )
            self.confirm_password_input.setVisible(False)
            self.setWindowTitle("登录 — 文件管理器")

    def handle_submit(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_password_input.text() if self.is_register_mode else ""

        if not username or not password:
            self.show_error("请填写所有字段")
            return

        if self.is_register_mode:
            self.do_register(username, password, confirm)
        else:
            self.do_login(username, password)

    def show_error(self, msg):
        self.status_label.setText(msg)
        self.status_label.setVisible(True)

    def clear_error(self):
        self.status_label.setVisible(False)

    def do_login(self, username, password):
        self.clear_error()
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/login",
                json={"username": username, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.username = username
                self.accept()
            elif response.status_code == 401:
                self.show_error("用户名或密码错误")
            else:
                try:
                    detail = response.json().get("detail", f"HTTP {response.status_code}")
                except Exception:
                    detail = f"HTTP {response.status_code}"
                self.show_error(detail)
        except requests.exceptions.ConnectionError:
            self.show_error("无法连接服务器。\n请确认 API 服务是否正在运行？")
        except Exception as e:
            self.show_error(f"错误：{str(e)}")

    def do_register(self, username, password, confirm):
        self.clear_error()

        if len(username) < 3:
            self.show_error("用户名至少需要3个字符")
            return
        if len(password) < 6:
            self.show_error("密码至少需要6个字符")
            return
        if password != confirm:
            self.show_error("两次密码输入不一致")
            return

        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/auth/register",
                json={"username": username, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                # Auto-login after register
                self.do_login(username, password)
            else:
                try:
                    detail = response.json().get("detail", f"HTTP {response.status_code}")
                except Exception:
                    detail = f"HTTP {response.status_code}"
                self.show_error(detail)
        except requests.exceptions.ConnectionError:
            self.show_error("Cannot connect to server.\nIs the API server running?")
        except Exception as e:
            self.show_error(f"Error: {str(e)}")


# ============== Text Editor Dialog ==============
class TextEditorDialog(QDialog):
    def __init__(self, filename, content, readonly=False, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.original_content = content
        self.readonly = readonly
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"编辑：{self.filename}" if not self.readonly else self.filename)
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout()

        self.toolbar = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_file)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.close)
        self.toolbar.addWidget(self.save_btn)
        self.toolbar.addStretch()
        self.toolbar.addWidget(self.cancel_btn)
        layout.addLayout(self.toolbar)

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.original_content)
        if self.readonly:
            self.text_edit.setReadOnly(True)
            self.save_btn.setVisible(False)
        layout.addWidget(self.text_edit)

        self.setLayout(layout)

    def save_file(self):
        self.original_content = self.text_edit.toPlainText()
        self.accept()


# ============== File Item Widget ==============
class FileItem(QWidget):
    def __init__(self, name, is_dir, size=0, path="", parent=None):
        super().__init__(parent)
        self.name = name
        self.is_dir = is_dir
        self.size = size
        self.path = path
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        icon_label = QLabel("📁" if self.is_dir else "📄")
        icon_label.setStyleSheet("font-size: 16pt;")
        layout.addWidget(icon_label)

        name_label = QLabel(self.name)
        name_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(name_label, 1)

        if not self.is_dir:
            size_label = QLabel(self.format_size(self.size))
            size_label.setStyleSheet("color: #808080;")
            layout.addWidget(size_label)

        self.setLayout(layout)

    def format_size(self, size):
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"


# ============== Share Dialog ==============
class ShareDialog(QDialog):
    def __init__(self, share_url, parent=None):
        super().__init__(parent)
        self.share_url = share_url
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("分享文件")
        self.setMinimumWidth(450)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h3>文件分享成功</h3>"))

        layout.addWidget(QLabel("分享链接："))
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setText(self.share_url)
        self.url_input.setReadOnly(True)
        copy_btn = QPushButton("复制")
        copy_btn.clicked.connect(self.copy_url)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(copy_btn)
        layout.addLayout(url_layout)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4caf50;")
        layout.addWidget(self.status_label)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def copy_url(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.share_url)
        self.status_label.setText("已复制到剪贴板！")


# ============== Main Window ==============
class FileManagerWindow(QMainWindow):
    def __init__(self, token):
        super().__init__()
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.current_path = "/"
        self.clipboard = None
        self.clipboard_action = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("文件管理器")
        self.setMinimumSize(900, 600)

        self.setup_menu_bar()
        self.setup_tool_bar()
        self.setup_central_widget()
        self.setup_status_bar()

        self.apply_dark_theme()
        self.load_root()

    def apply_dark_theme(self):
        self.setStyleSheet(DARK_STYLESHEET)

    def setup_menu_bar(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")

        upload_action = QAction("上传文件", self)
        upload_action.setShortcut("Ctrl+U")
        upload_action.triggered.connect(self.upload_file)
        file_menu.addAction(upload_action)

        new_folder_action = QAction("新建文件夹", self)
        new_folder_action.setShortcut("Ctrl+N")
        new_folder_action.triggered.connect(self.create_folder)
        file_menu.addAction(new_folder_action)

        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_current)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()
        logout_action = QAction("退出登录", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)

        edit_menu = menubar.addMenu("编辑")

        cut_action = QAction("剪切", self)
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(lambda: self.cut_copy("cut"))
        edit_menu.addAction(cut_action)

        copy_action = QAction("复制", self)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(lambda: self.cut_copy("copy"))
        edit_menu.addAction(copy_action)

        paste_action = QAction("粘贴", self)
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
        edit_menu.addAction(paste_action)

        delete_action = QAction("删除", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_selected)
        edit_menu.addAction(delete_action)

        view_menu = menubar.addMenu("视图")

        list_view_action = QAction("列表视图", self)
        list_view_action.setCheckable(True)
        list_view_action.setChecked(True)
        list_view_action.triggered.connect(self.set_list_view)
        view_menu.addAction(list_view_action)

        tree_view_action = QAction("树状视图", self)
        tree_view_action.setCheckable(True)
        tree_view_action.triggered.connect(self.set_tree_view)
        view_menu.addAction(tree_view_action)

    def setup_tool_bar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        back_btn = QPushButton("←")
        back_btn.clicked.connect(self.go_back)
        back_btn.setFixedSize(35, 35)
        toolbar.addWidget(back_btn)

        forward_btn = QPushButton("→")
        forward_btn.clicked.connect(self.go_forward)
        forward_btn.setFixedSize(35, 35)
        toolbar.addWidget(forward_btn)

        up_btn = QPushButton("↑")
        up_btn.clicked.connect(self.go_up)
        up_btn.setFixedSize(35, 35)
        toolbar.addWidget(up_btn)

        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("导航至路径...")
        self.path_input.setMinimumWidth(300)
        self.path_input.returnPressed.connect(self.navigate_to_path)
        toolbar.addWidget(self.path_input)

        home_btn = QPushButton("🏠")
        home_btn.clicked.connect(self.go_home)
        home_btn.setFixedSize(35, 35)
        toolbar.addWidget(home_btn)

        toolbar.addSeparator()

        upload_btn = QPushButton("⬆ 上传")
        upload_btn.clicked.connect(self.upload_file)
        toolbar.addWidget(upload_btn)

        new_folder_btn = QPushButton("📁 新建文件夹")
        new_folder_btn.clicked.connect(self.create_folder)
        toolbar.addWidget(new_folder_btn)

        refresh_btn = QPushButton("🔄")
        refresh_btn.clicked.connect(self.refresh_current)
        refresh_btn.setFixedSize(35, 35)
        toolbar.addWidget(refresh_btn)

    def setup_central_widget(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - file tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("文件夹")
        self.tree_widget.setMinimumWidth(200)
        self.tree_widget.itemDoubleClicked.connect(self.tree_item_double_clicked)
        self.tree_widget.itemClicked.connect(self.tree_item_clicked)
        self.splitter.addWidget(self.tree_widget)

        # Right panel - file list
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(400)
        self.list_widget.itemDoubleClicked.connect(self.list_item_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.splitter.addWidget(self.list_widget)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 3)

        main_layout.addWidget(self.splitter)
        central_widget.setLayout(main_layout)

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    # Navigation history
    def add_to_history(self, path):
        self.history_pos = 0
        self.history = [path]

    # ============== API Methods ==============
    def api_list_directory(self, path):
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/files/list",
                params={"path": path},
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                self.show_error(f"Failed to list directory: {response.status_code}")
                return None
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return None

    def api_create_folder(self, path, name):
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/files/folder",
                json={"path": path, "name": name},
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return False

    def api_delete(self, path):
        try:
            response = requests.delete(
                f"{BASE_URL}/api/v1/files/delete",
                params={"path": path},
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return False

    def api_upload(self, file_data, filename, dest_path):
        try:
            files = {"file": (filename, file_data)}
            data = {"path": dest_path}
            response = requests.post(
                f"{BASE_URL}/api/v1/files/upload",
                files=files,
                data=data,
                headers=self.headers,
                timeout=60
            )
            return response.status_code == 200
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return False

    def api_download(self, path):
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/files/download",
                params={"path": path},
                headers=self.headers,
                timeout=60
            )
            if response.status_code == 200:
                return response.content
            else:
                return None
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return None

    def api_share(self, path):
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/files/share",
                params={"path": path},
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("url")
            else:
                return None
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return None

    def api_get_content(self, path):
        try:
            response = requests.get(
                f"{BASE_URL}/api/v1/files/content",
                params={"path": path},
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return None

    def api_save_content(self, path, content):
        try:
            response = requests.put(
                f"{BASE_URL}/api/v1/files/content",
                json={"path": path, "content": content},
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return False

    def api_move(self, source, dest):
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/files/move",
                json={"source": source, "destination": dest},
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return False

    def api_copy(self, source, dest):
        try:
            response = requests.post(
                f"{BASE_URL}/api/v1/files/copy",
                json={"source": source, "destination": dest},
                headers=self.headers,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.show_error(f"Connection error: {str(e)}")
            return False

    # ============== UI Methods ==============
    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_success(self, message):
        QMessageBox.information(self, "Success", message)

    def load_root(self):
        self.current_path = "/"
        self.path_input.setText(self.current_path)
        self.load_directory(self.current_path)
        self.populate_tree()

    def load_directory(self, path):
        self.status_bar.showMessage(f"正在加载 {path}...")
        data = self.api_list_directory(path)

        if data is not None:
            self.current_path = path
            self.path_input.setText(path)
            self.populate_list(data.get("items", []) if isinstance(data, dict) else data)

        self.status_bar.showMessage("就绪")

    def populate_tree(self):
        self.tree_widget.clear()
        root_item = QTreeWidgetItem(self.tree_widget, ["/"])
        root_item.setData(0, Qt.ItemDataRole.UserRole, "/")
        root_item.setExpanded(True)
        self.add_tree_children(root_item)

    def add_tree_children(self, parent_item):
        parent_path = parent_item.data(0, Qt.ItemDataRole.UserRole)
        data = self.api_list_directory(parent_path)
        if data:
            items = data.get("items", []) if isinstance(data, dict) else data
            for item in items:
                if item.get("is_dir", False) or item.get("is_directory", False):
                    child = QTreeWidgetItem(parent_item, [item.get("name", "Unknown")])
                    child.setData(0, Qt.ItemDataRole.UserRole, item.get("path", ""))
                    self.add_tree_children(child)

    def populate_list(self, data):
        self.list_widget.clear()

        # Sort: directories first, then files
        dirs = sorted([d for d in data if d.get("is_dir", False) or d.get("is_directory", False)], key=lambda x: x.get("name", "").lower())
        files = sorted([f for f in data if not f.get("is_dir", False) and not f.get("is_directory", False)], key=lambda x: x.get("name", "").lower())

        for item in dirs + files:
            list_item = QListWidgetItem(self.list_widget)
            widget = FileItem(
                name=item.get("name", "Unknown"),
                is_dir=item.get("is_dir", False) or item.get("is_directory", False),
                size=item.get("size", 0),
                path=item.get("path", "")
            )
            list_item.setSizeHint(widget.sizeHint())
            self.list_widget.setItemWidget(list_item, widget)

    # ============== Navigation ==============
    def navigate_to_path(self):
        path = self.path_input.text().strip()
        if path:
            self.load_directory(path)

    def go_back(self):
        pass  # Simplified

    def go_forward(self):
        pass  # Simplified

    def go_up(self):
        if self.current_path != "/":
            parts = self.current_path.strip("/").split("/")
            parent = "/" + "/".join(parts[:-1])
            self.load_directory(parent if parent else "/")

    def go_home(self):
        self.load_directory("/")

    def refresh_current(self):
        self.load_directory(self.current_path)

    # ============== Tree Interactions ==============
    def tree_item_clicked(self, item, column):
        pass

    def tree_item_double_clicked(self, item, column):
        path = item.data(0, Qt.ItemDataRole.UserRole)
        data = self.api_list_directory(path)
        if data is None:
            return
        self.load_directory(path)

    # ============== List Interactions ==============
    def list_item_double_clicked(self, item):
        widget = self.list_widget.itemWidget(item)
        if widget.is_dir:
            self.load_directory(widget.path)
        else:
            self.open_file(widget.path)

    def open_file(self, path):
        content = self.api_get_content(path)
        if content is not None:
            filename = path.split("/")[-1]
            editor = TextEditorDialog(filename, content, readonly=True, parent=self)
            editor.exec()

    def edit_file(self, path):
        content = self.api_get_content(path)
        if content is not None:
            filename = path.split("/")[-1]
            editor = TextEditorDialog(filename, content, parent=self)
            if editor.exec() == QDialog.DialogCode.Accepted:
                if self.api_save_content(path, editor.original_content):
                    self.show_success("文件保存成功")
                    self.refresh_current()
                else:
                    self.show_error("文件保存失败")

    # ============== Context Menu ==============
    def show_context_menu(self, position):
        item = self.list_widget.itemAt(position)
        if not item:
            return

        widget = self.list_widget.itemWidget(item)
        menu = QMenu()

        if widget.is_dir:
            open_action = menu.addAction("打开")
            open_action.triggered.connect(lambda: self.load_directory(widget.path))
        else:
            view_action = menu.addAction("查看")
            view_action.triggered.connect(lambda: self.open_file(widget.path))

            edit_action = menu.addAction("编辑")
            edit_action.triggered.connect(lambda: self.edit_file(widget.path))

            download_action = menu.addAction("下载")
            download_action.triggered.connect(lambda: self.download_file(widget.path))

        menu.addSeparator()

        share_action = menu.addAction("分享")
        share_action.triggered.connect(lambda: self.share_file(widget.path))

        cut_action = menu.addAction("剪切")
        cut_action.triggered.connect(lambda: self.cut_copy("cut", widget.path))

        copy_action = menu.addAction("复制")
        copy_action.triggered.connect(lambda: self.cut_copy("copy", widget.path))

        delete_action = menu.addAction("删除")
        delete_action.triggered.connect(lambda: self.delete_file(widget.path))

        menu.exec(QCursor.pos())

    # ============== Actions ==============
    def upload_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择要上传的文件")
        if file_path:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                file_data = f.read()

            if self.api_upload(file_data, filename, self.current_path):
                self.show_success(f"文件 '{filename}' 上传成功")
                self.refresh_current()
            else:
                self.show_error("文件上传失败")

    def download_file(self, path):
        filename = path.split("/")[-1]
        save_path, _ = QFileDialog.getSaveFileName(self, "保存文件", filename)
        if save_path:
            content = self.api_download(path)
            if content:
                with open(save_path, "wb") as f:
                    f.write(content)
                self.show_success("文件下载成功")
            else:
                self.show_error("文件下载失败")

    def create_folder(self):
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称：")
        if ok and name:
            if self.api_create_folder(self.current_path, name):
                self.show_success(f"文件夹 '{name}' 已创建")
                self.refresh_current()
            else:
                self.show_error("文件夹创建失败")

    def delete_file(self, path):
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除此项目吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.api_delete(path):
                self.show_success("已删除")
                self.refresh_current()
            else:
                self.show_error("删除失败")

    def delete_selected(self):
        item = self.list_widget.currentItem()
        if item:
            widget = self.list_widget.itemWidget(item)
            self.delete_file(widget.path)

    def share_file(self, path):
        url = self.api_share(path)
        if url:
            dialog = ShareDialog(url, self)
            dialog.exec()
        else:
            self.show_error("Failed to share file")

    def cut_copy(self, action, path=None):
        if path:
            self.clipboard = path
            self.clipboard_action = action
        else:
            item = self.list_widget.currentItem()
            if item:
                widget = self.list_widget.itemWidget(item)
                self.clipboard = widget.path
                self.clipboard_action = action

    def paste(self):
        if not self.clipboard:
            return

        name = self.clipboard.split("/")[-1]
        dest = self.current_path + "/" + name

        if self.clipboard_action == "cut":
            if self.api_move(self.clipboard, dest):
                self.show_success("文件已移动")
                self.refresh_current()
            else:
                self.show_error("文件移动失败")
        elif self.clipboard_action == "copy":
            if self.api_copy(self.clipboard, dest):
                self.show_success("文件已复制")
                self.refresh_current()
            else:
                self.show_error("文件复制失败")

    def set_list_view(self):
        pass

    def set_tree_view(self):
        pass

    def logout(self):
        self.close()


# ============== Application Entry Point ==============
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("文件管理器")

    # Show login dialog
    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)

    # Show main window
    window = FileManagerWindow(login.token)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
