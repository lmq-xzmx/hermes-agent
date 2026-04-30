"""
PyQt6 File Manager GUI — Thin shell with embedded WebView
Connects to FastAPI at http://localhost:8080

Phase 1: QWebEngineView replaces all PyQt file browser widgets.
Phase 2: Native menu bar, drag-and-drop upload, proper polish.
Phase 3: Auto-launch server, offline file:// mode.
"""

import sys
import os
import requests
import subprocess
import time
import socket
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QDialog, QLineEdit, QLabel, QPushButton, QMessageBox,
    QMenuBar, QMenu, QStatusBar, QFileDialog, QInputDialog,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QVBoxLayout,
    QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer, QUrl, QObject, pyqtSignal, QProcess
from PyQt6.QtGui import QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile


BASE_URL = "http://localhost:8080"
WEB_URL = f"{BASE_URL}/static/"

# Path to this file's directory
_GUI_DIR = Path(__file__).parent.resolve()
_FILE_MANAGER_ROOT = _GUI_DIR.parent.resolve()
_WEB_DIR = _FILE_MANAGER_ROOT / "web"
_SERVER_SCRIPT = _FILE_MANAGER_ROOT / "server.py"


# ============== Dark Theme Stylesheet ==============
DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #1e1e1e;
    color: #e0e0e0;
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
QStatusBar {
    background-color: #2d2d2d;
    color: #e0e0e0;
}
"""


# ============== Server Utilities ==============

def is_server_running(host="localhost", port=8080, timeout=1):
    """Check if the API server is reachable."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefused, OSError):
        return False


def wait_for_server(timeout=15):
    """Wait for the server to become ready, returning True if it does."""
    start = time.time()
    while time.time() - start < timeout:
        if is_server_running():
            return True
        time.sleep(0.5)
    return False


def start_server_process(log_file=None):
    """Launch server.py as a background process. Returns the process."""
    import site
    venv_python = sys.executable
    process = QProcess()
    if log_file:
        process.setStandardOutputFile(str(log_file))
        process.setStandardErrorFile(str(log_file))
    process.start(venv_python, [str(_SERVER_SCRIPT)])
    return process


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

        self.toggle_label = QLabel(
            '<a href="#" style="color: #58a6ff; text-decoration: none;">没有账户？立即注册</a>'
        )
        self.toggle_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.toggle_label.setOpenExternalLinks(False)
        self.toggle_label.linkActivated.connect(self.toggle_mode)
        layout.addWidget(self.toggle_label)

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
                self.do_login(username, password)
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


# ============== Main Window with WebView + Drag-and-Drop ==============
class FileManagerWindow(QMainWindow):
    # Signal emitted when a file drop completes
    upload_requested = pyqtSignal(list, str)  # file_paths, dest_path

    def __init__(self, token, username, server_process=None):
        super().__init__()
        self.token = token
        self.username = username
        self.server_process = server_process  # Keep alive while window is open
        self.web_view = None
        self._upload_progress = None
        self.setup_ui()
        self.inject_auth_token()

    def setup_ui(self):
        self.setWindowTitle("文件管理器")
        self.setMinimumSize(1100, 700)

        self.setup_menu_bar()
        self.setup_central_widget()
        self.setup_status_bar()

        self.setStyleSheet(DARK_STYLESHEET)
        self.setAcceptDrops(True)

    def setup_menu_bar(self):
        menubar = self.menuBar()

        # --- File menu ---
        file_menu = menubar.addMenu("文件")

        upload_action = QAction("上传文件...", self)
        upload_action.setShortcut("Ctrl+U")
        upload_action.triggered.connect(self.native_upload_file)
        file_menu.addAction(upload_action)

        new_folder_action = QAction("新建文件夹...", self)
        new_folder_action.setShortcut("Ctrl+N")
        new_folder_action.triggered.connect(self.create_folder)
        file_menu.addAction(new_folder_action)

        file_menu.addSeparator()

        refresh_action = QAction("刷新", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.reload_webview)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        logout_action = QAction("退出登录", self)
        logout_action.triggered.connect(self.logout)
        file_menu.addAction(logout_action)

        # --- View menu ---
        view_menu = menubar.addMenu("视图")

        reload_action = QAction("重新加载", self)
        reload_action.setShortcut("Ctrl+R")
        reload_action.triggered.connect(self.reload_webview)
        view_menu.addAction(reload_action)

        devtools_action = QAction("开发者工具", self)
        devtools_action.setShortcut("F12")
        devtools_action.triggered.connect(self.toggle_devtools)
        view_menu.addAction(devtools_action)

        view_menu.addSeparator()

        # Toggle between online (localhost) and offline (file://) mode
        self.offline_action = QAction("离线模式", self)
        self.offline_action.setCheckable(True)
        self.offline_action.setChecked(False)
        self.offline_action.triggered.connect(self.toggle_offline_mode)
        view_menu.addAction(self.offline_action)

        # --- Help menu ---
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def setup_central_widget(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = QWebEngineView()
        self.web_view.setUrl(QUrl(WEB_URL))
        self.web_view.loadFinished.connect(self.on_load_finished)

        layout.addWidget(self.web_view)
        central.setLayout(layout)

    def setup_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("正在连接...")

    def inject_auth_token(self):
        js = f"""
        (function() {{
            localStorage.setItem('hfm_token', '{self.token}');
            localStorage.setItem('hfm_username', '{self.username}');
        }})();
        """
        self._pending_inject = js

    def on_load_finished(self, ok):
        if ok:
            self.status_bar.showMessage("就绪")
            if hasattr(self, '_pending_inject') and self._pending_inject:
                js = self._pending_inject
                self._pending_inject = None
                self.web_view.page().runJavaScript(js)
                # Reload so the app picks up the injected token
                self.web_view.setUrl(QUrl(WEB_URL))
        else:
            self.status_bar.showMessage("加载失败 — 请确认 API 服务是否运行中")

    def reload_webview(self):
        self.web_view.setUrl(QUrl(WEB_URL))

    def toggle_devtools(self):
        if hasattr(self.web_view, 'setDevToolsVisible'):
            self.web_view.setDevToolsVisible(not self.web_view.isDevToolsVisible())
        else:
            self.web_view.page().triggerAction(
                self.web_view.page().Action.DebugShowWebInspector
            )

    # ============== Drag-and-Drop Upload ==============
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            # Check that at least one URL is a file path
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    event.acceptProposedAction()
                    return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        """Handle file drops — upload each dropped file to current directory."""
        files = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                files.append(url.toLocalFile())

        if not files:
            return

        # Get current path from webview JS
        self.web_view.page().runJavaScript(
            "window.currentPath || '/';",
            lambda path: self._do_drop_upload(files, path or "/")
        )

    def _do_drop_upload(self, file_paths, dest_path):
        """Perform the actual upload via the API."""
        self.status_bar.showMessage(f"正在上传 {len(file_paths)} 个文件...")
        total = len(file_paths)

        progress = QProgressDialog(
            f"正在上传 0/{total} 个文件...",
            "取消",
            0,
            total,
            self
        )
        progress.setWindowTitle("上传文件")
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        success_count = 0
        for i, file_path in enumerate(file_paths):
            if progress.wasCanceled():
                break

            filename = os.path.basename(file_path)
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()

                files = {"file": (filename, file_data)}
                data = {"path": dest_path}
                response = requests.post(
                    f"{BASE_URL}/api/v1/files/upload",
                    files=files,
                    data=data,
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=120
                )
                if response.status_code == 200:
                    success_count += 1
            except Exception as e:
                print(f"Upload error for {filename}: {e}")

            progress.setLabelText(f"正在上传 {i+1}/{total} 个文件...")
            progress.setValue(i + 1)
            QApplication.processEvents()

        progress.close()
        self.status_bar.showMessage(f"上传完成：{success_count}/{total} 个文件成功")

        if success_count > 0:
            self.reload_webview()

    # ============== Native File Operations ==============
    def native_upload_file(self):
        """Open file picker and upload selected file(s)."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "选择要上传的文件", "",
            "所有文件 (*.*)"
        )
        if not file_paths:
            return

        # Get current path from webview
        self.web_view.page().runJavaScript(
            "window.currentPath || '/';",
            lambda path: self._do_drop_upload(file_paths, path or "/")
        )

    def create_folder(self):
        name, ok = QInputDialog.getText(self, "新建文件夹", "请输入文件夹名称：")
        if ok and name:
            # Full path = currentPath + '/' + name
            js = f"""
            (function() {{
                var currentPath = window.currentPath || '/';
                var fullPath = currentPath === '/' ? '/' + '{name}' : currentPath + '/' + '{name}';
                fetch('/api/v1/files/mkdir', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer {self.token}'
                    }},
                    body: JSON.stringify({{ path: fullPath }})
                }}).then(r => r.json()).then(d => {{
                    if (d.error) {{
                        alert('创建失败: ' + d.error);
                    }} else {{
                        window.location.reload();
                    }}
                }}).catch(err => alert('错误: ' + err.message));
            }})();
            """
            self.web_view.page().runJavaScript(js)

    def toggle_offline_mode(self, checked):
        """Switch between localhost:8080 and local file:// mode."""
        if checked:
            # Switch to offline file:// mode
            local_file = _WEB_DIR / "app.html"
            if local_file.exists():
                self.web_view.setUrl(QUrl.fromLocalFile(str(local_file)))
                self.status_bar.showMessage("离线模式")
            else:
                QMessageBox.warning(
                    self, "离线模式",
                    f"找不到本地文件：\n{local_file}\n\n请确保已构建 web 应用。"
                )
                self.offline_action.setChecked(False)
        else:
            # Back to online mode
            self.web_view.setUrl(QUrl(WEB_URL))
            self.status_bar.showMessage("在线模式")

    def logout(self):
        js = """
        (function() {
            localStorage.removeItem('hfm_token');
            localStorage.removeItem('hfm_username');
            window.location.reload();
        })();
        """
        self.web_view.page().runJavaScript(js)
        QTimer.singleShot(500, self.close)

    def show_about(self):
        QMessageBox.about(
            self, "关于",
            "<b>文件管理器</b><br>"
            "基于 PyQt6 + QWebEngineView<br>"
            "后端：FastAPI"
        )

    def closeEvent(self, event):
        """Stop the server process when the window is closed (if we own it)."""
        if self.server_process and self.server_process.state() != QProcess.ProcessState.NotRunning:
            self.server_process.terminate()
            self.server_process.waitForFinished(3000)
        event.accept()


# ============== Application Entry Point ==============
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("文件管理器")

    server_process = None
    auto_started = False

    # Phase 3: Auto-launch server if not already running
    if not is_server_running():
        reply = QMessageBox.question(
            None,  # No parent yet
            "启动文件管理器",
            "API 服务未运行。是否自动启动服务器？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Create a log file for server output
            log_path = _GUI_DIR / "server.log"
            server_process = start_server_process(log_file=log_path)
            if not wait_for_server():
                QMessageBox.critical(
                    None, "启动失败",
                    f"无法在 {_SERVER_SCRIPT} 启动 API 服务。\n"
                    "请查看 server.log 了解详情。"
                )
                server_process.terminate()
                sys.exit(1)
            auto_started = True
        else:
            QMessageBox.information(
                None, "提示",
                "GUI 将无法加载内容，除非手动启动：\n"
                f"  python {_SERVER_SCRIPT}"
            )

    # Show login dialog (native — better IME/input support)
    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        if server_process:
            server_process.terminate()
        sys.exit(0)

    # Show main window — web content inside native shell
    window = FileManagerWindow(login.token, login.username, server_process=server_process)
    window.show()

    if auto_started:
        QTimer.singleShot(2000, lambda: window.status_bar.showMessage(
            "API 服务已自动启动"
        ))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
