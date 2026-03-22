import sys, random, os, json, hashlib
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, 
    QHBoxLayout, QPushButton, QLineEdit, QDialog, QLabel, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QSlider, QFrame, QGridLayout, QMessageBox, QToolBar, QMenu, QInputDialog, QFileDialog, QScrollArea, QCheckBox, QTextEdit
)
from PyQt6.QtCore import QSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl, Qt, QTimer, QSettings, QEvent, pyqtSignal, QPoint, QMimeData
from PyQt6.QtGui import QDrag
from PyQt6.QtGui import QPainter, QColor, QPen, QAction, QKeySequence, QPixmap, QIcon, QFont

# ================= LEGACY NT GRAPH ENGINE =================
class NTGraph(QWidget):
    def __init__(self, primary_color="#00ff00", secondary_color=None, history=60):
        super().__init__()
        self.points = [random.randint(5, 12) for _ in range(history)]
        self.points2 = [max(0, min(100, v + random.randint(-6, 6))) for v in self.points] if secondary_color else None
        self.primary = QColor(primary_color)
        self.secondary = QColor(secondary_color) if secondary_color else None
        self.grid = QColor(0, 80, 0)
        self.setMinimumSize(300, 120)
        self.timer = QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(1000)
    def tick(self):
        def next_val(v): return max(2, min(98, v + random.randint(-6, 6)))
        self.points.pop(0); self.points.append(next_val(self.points[-1]))
        if self.points2 is not None:
            kern = max(0, min(self.points[-1] - random.randint(0, 10), 98))
            self.points2.pop(0); self.points2.append(kern)
        self.update()
    def paintEvent(self, event):
        p = QPainter(self); p.fillRect(self.rect(), Qt.GlobalColor.black)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setPen(QPen(self.grid, 1))
        for i in range(0, self.width(), 16): p.drawLine(i, 0, i, self.height())
        for i in range(0, self.height(), 16): p.drawLine(0, i, self.width(), i)
        n = len(self.points) - 1
        if n <= 0: return
        step = self.width() / float(n)
        def y(v): return self.height() - (v * self.height() / 100.0)
        p.setPen(QPen(self.primary, 1))
        for i in range(n):
            p.drawLine(int(i*step), int(y(self.points[i])), int((i+1)*step), int(y(self.points[i+1])))
        if self.points2 is not None:
            p.setPen(QPen(QColor('#ff0000'), 1))
            for i in range(n):
                p.drawLine(int(i*step), int(y(self.points2[i])), int((i+1)*step), int(y(self.points2[i+1])))

class SmallMeter(QWidget):
    def __init__(self, label_text="CPU Usage", mode="percent", limit_mb=1159):
        super().__init__()
        self.value = 0
        self.label_text = label_text
        self.mode = mode
        self.limit_mb = limit_mb
        self.setMinimumSize(160, 120)
    def set_value(self, v):
        self.value = max(0, min(100, int(v)))
        self.update()
    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#d4d0c8'))
        p.setPen(Qt.GlobalColor.black)
        p.drawText(10, 16, self.label_text)
        frame = self.rect().adjusted(8, 22, -8, -8)
        p.fillRect(frame, Qt.GlobalColor.black)
        p.setPen(QPen(QColor(0,80,0), 1))
        for i in range(frame.left(), frame.right(), 8):
            p.drawLine(i, frame.top(), i, frame.bottom())
        for j in range(frame.top(), frame.bottom(), 8):
            p.drawLine(frame.left(), j, frame.right(), j)
        bar_w = int((frame.width()-10) * self.value/100.0)
        bar_rect = frame.adjusted(5, 5, -(frame.width()-5-bar_w), -5)
        p.fillRect(bar_rect, QColor('#00ff00'))
        p.setPen(QColor('#00ff00'))
        if self.mode == 'mb':
            used = int(self.limit_mb * self.value / 100)
            txt = f"{used} / {self.limit_mb} MB"
        else:
            txt = f"{self.value}% / 100%"
        p.drawText(frame, Qt.AlignmentFlag.AlignCenter, txt)

# ================= V57 TASK MANAGER RESTORATION =================
class NTTaskManager(QDialog):
    def __init__(self, tab_names, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Task Manager")
        self.resize(800, 600)
        self.setStyleSheet("background-color: #d4d0c8; color: black; font-family: 'Segoe UI'; font-size: 9pt;")
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(); layout.addWidget(self.tabs)
        self.tabs.addTab(self._create_applications_tab(), "Applications")
        self.tabs.addTab(self._create_processes_tab(), "Processes")
        perf = QWidget(); self.tabs.addTab(perf, "Performance")
        perf_lay = QVBoxLayout(perf)
        grid = QGridLayout(); perf_lay.addLayout(grid)
        self.cpu_meter = SmallMeter("CPU Usage", mode='percent')
        self.ram_total_mb = 2048
        self.ram_meter = SmallMeter("RAM Usage", mode='mb', limit_mb=self.ram_total_mb)
        def make_group(title, inner):
            w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(0,0,0,0)
            v.addWidget(QLabel(title))
            f = QFrame(); f.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
            fl = QVBoxLayout(f); fl.setContentsMargins(4,4,4,4)
            fl.addWidget(inner)
            v.addWidget(f)
            return w
        left_box = QVBoxLayout()
        left_box.addWidget(make_group("CPU Usage", self.cpu_meter))
        left_box.addWidget(make_group("RAM Usage", self.ram_meter))
        left_box.addStretch(1)
        grid.addLayout(left_box, 0, 0, 2, 1)
        self.cpu_graph = NTGraph("#00ff00", secondary_color="#ff0000")
        self.ram_graph = NTGraph("#00ff00")
        grid.addWidget(make_group("CPU Usage History", self.cpu_graph), 0, 1)
        grid.addWidget(make_group("RAM Usage History", self.ram_graph), 1, 1)
        stats = QGridLayout(); perf_lay.addLayout(stats)
        f_tot = QFrame(); f_tot.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        ft_l = QVBoxLayout(f_tot); ft_l.addWidget(QLabel("<b>Totals</b>"))
        ft_l.addWidget(QLabel("Handles: 9279"))
        ft_l.addWidget(QLabel("Threads: 462"))
        ft_l.addWidget(QLabel(f"Processes: {len(tab_names)}"))
        stats.addWidget(f_tot, 0, 0)
        f_cc = QFrame(); f_cc.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        fc_l = QVBoxLayout(f_cc); fc_l.addWidget(QLabel("<b>RAM (K)</b>"))
        self.ram_used_lbl = QLabel("Used: 0")
        self.ram_total_lbl = QLabel(f"Total: {self.ram_total_mb*1024}k")
        self.ram_free_lbl = QLabel("Free: 0")
        for w in (self.ram_used_lbl, self.ram_total_lbl, self.ram_free_lbl): fc_l.addWidget(w)
        stats.addWidget(f_cc, 0, 1)
        f_pm = QFrame(); f_pm.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        fp_l = QVBoxLayout(f_pm); fp_l.addWidget(QLabel("<b>Physical Memory (K)</b>"))
        fp_l.addWidget(QLabel("Total: 1048160"))
        fp_l.addWidget(QLabel("Available: 228104"))
        fp_l.addWidget(QLabel("System Cache: 315036"))
        stats.addWidget(f_pm, 1, 0)
        f_km = QFrame(); f_km.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        fk_l = QVBoxLayout(f_km); fk_l.addWidget(QLabel("<b>Kernel Memory (K)</b>"))
        fk_l.addWidget(QLabel("Total: 43488"))
        fk_l.addWidget(QLabel("Paged: 35756"))
        fk_l.addWidget(QLabel("Nonpaged: 7732"))
        stats.addWidget(f_km, 1, 1)
        sb_frame = QFrame(); sb_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        sb = QHBoxLayout(sb_frame); sb.setContentsMargins(8,4,8,4)
        self.status_proc = QLabel(f"Processes: {len(tab_names)}")
        self.status_cpu = QLabel("CPU: 0% / 100%")
        self.status_ram = QLabel(f"RAM: 0M / {self.ram_total_mb}M")
        for w in (self.status_proc, self.status_cpu, self.status_ram):
            sb.addWidget(w); sb.addStretch(1)
        perf_lay.addWidget(sb_frame)
        self.up_t = QTimer(self); self.up_t.timeout.connect(self._update_perf); self.up_t.start(1000)
        self.proc_t = QTimer(self); self.proc_t.timeout.connect(self._update_processes); self.proc_t.start(2000)
        self.tabs.addTab(self._create_networking_tab(), "Networking")
        # Users tab
        users_tab = QWidget()
        u_l = QVBoxLayout(users_tab)
        # Removed interactive controls - making tab read-only
        self.users_table = QTableWidget(0, 5)
        self.users_table.setHorizontalHeaderLabels(["User", "Status", "CPU", "Mem Usage", "Session"])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        # Make table read-only and non-editable
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        u_l.addWidget(self.users_table)
        self.tabs.addTab(users_tab, "Users")
        self._seed_users(); self._refresh_users_table()
    
    def _create_applications_tab(self):
        """Create the Applications tab with running applications and controls"""
        applications_tab = QWidget()
        a_l = QVBoxLayout(applications_tab)
        
        # Control buttons
        ctrl = QHBoxLayout()
        switch_to_btn = QPushButton("Switch To")
        minimize_btn = QPushButton("Minimize")
        maximize_btn = QPushButton("Maximize")
        close_btn = QPushButton("Close Window")
        ctrl.addWidget(switch_to_btn)
        ctrl.addWidget(minimize_btn)
        ctrl.addWidget(maximize_btn)
        ctrl.addWidget(close_btn)
        ctrl.addStretch(1)
        a_l.addLayout(ctrl)
        
        # Applications table
        self.applications_table = QTableWidget(0, 4)
        self.applications_table.setHorizontalHeaderLabels(["Name", "Status", "User", "CPU"])
        self.applications_table.horizontalHeader().setStretchLastSection(True)
        self.applications_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.applications_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        a_l.addWidget(self.applications_table)
        
        # Status bar
        sb_frame = QFrame(); sb_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        sb = QHBoxLayout(sb_frame); sb.setContentsMargins(8,4,8,4)
        self.status_applications = QLabel("Running applications: 0")
        self.status_windows = QLabel("Windows: 0")
        for w in (self.status_applications, self.status_windows):
            sb.addWidget(w); sb.addStretch(1)
        a_l.addWidget(sb_frame)
        
        # Connect buttons
        switch_to_btn.clicked.connect(self._switch_to_application)
        minimize_btn.clicked.connect(self._minimize_application)
        maximize_btn.clicked.connect(self._maximize_application)
        close_btn.clicked.connect(self._close_application)
        
        # Initialize applications
        self._seed_applications()
        self._refresh_applications_table()
        
        return applications_tab
    
    def _seed_applications(self):
        """Initialize with some sample applications"""
        self.applications_data = [
            ["Pro_Browser", "Running", "Administrator", "15%"],
            ["Notepad", "Running", "Administrator", "2%"],
            ["Calculator", "Running", "Administrator", "1%"],
            ["Paint", "Running", "Administrator", "5%"],
            ["Word", "Running", "Administrator", "8%"],
            ["Excel", "Running", "Administrator", "6%"],
            ["Chrome", "Running", "Administrator", "12%"],
            ["Spotify", "Running", "Administrator", "3%"],
            ["Discord", "Running", "Administrator", "4%"],
            ["Steam", "Running", "Administrator", "7%"]
        ]
    
    def _refresh_applications_table(self):
        """Update the applications table with current data"""
        self.applications_table.setRowCount(len(self.applications_data))
        for row, app in enumerate(self.applications_data):
            for col, value in enumerate(app):
                item = QTableWidgetItem(value)
                self.applications_table.setItem(row, col, item)
        
        # Update status
        self.status_applications.setText(f"Running applications: {len(self.applications_data)}")
        self.status_windows.setText(f"Windows: {len(self.applications_data)}")
    
    def _switch_to_application(self):
        """Switch to the selected application"""
        selected_items = self.applications_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select an application to switch to.")
            return
        
        row = selected_items[0].row()
        app_name = self.applications_data[row][0]
        
        # Simulate switching to application
        QMessageBox.information(self, "Switch To", f"Switching to {app_name}...")
    
    def _minimize_application(self):
        """Minimize the selected application"""
        selected_items = self.applications_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select an application to minimize.")
            return
        
        row = selected_items[0].row()
        app_name = self.applications_data[row][0]
        
        # Mark application as minimized
        self.applications_data[row][1] = "Minimized"
        self._refresh_applications_table()
    
    def _maximize_application(self):
        """Maximize the selected application"""
        selected_items = self.applications_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select an application to maximize.")
            return
        
        row = selected_items[0].row()
        app_name = self.applications_data[row][0]
        
        # Mark application as maximized
        self.applications_data[row][1] = "Maximized"
        self._refresh_applications_table()
    
    def _close_application(self):
        """Close the selected application"""
        selected_items = self.applications_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select an application to close.")
            return
        
        row = selected_items[0].row()
        app_name = self.applications_data[row][0]
        
        reply = QMessageBox.question(self, "Close Application", 
                                   f"Are you sure you want to close {app_name}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove application from list
            del self.applications_data[row]
            self._refresh_applications_table()
    
    def _create_processes_tab(self):
        """Create the Processes tab with process list and controls"""
        processes_tab = QWidget()
        p_l = QVBoxLayout(processes_tab)
        
        # Control buttons
        ctrl = QHBoxLayout()
        end_task_btn = QPushButton("End Task")
        end_process_btn = QPushButton("End Process")
        details_btn = QPushButton("Go to details")
        ctrl.addWidget(end_task_btn)
        ctrl.addWidget(end_process_btn)
        ctrl.addWidget(details_btn)
        ctrl.addStretch(1)
        p_l.addLayout(ctrl)
        
        # Process table
        self.processes_table = QTableWidget(0, 5)
        self.processes_table.setHorizontalHeaderLabels(["Name", "PID", "Status", "CPU", "Memory"])
        self.processes_table.horizontalHeader().setStretchLastSection(True)
        self.processes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.processes_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        p_l.addWidget(self.processes_table)
        
        # Status bar
        sb_frame = QFrame(); sb_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        sb = QHBoxLayout(sb_frame); sb.setContentsMargins(8,4,8,4)
        self.status_processes = QLabel("Processes: 0")
        self.status_cpu_proc = QLabel("CPU: 0%")
        self.status_mem_proc = QLabel("Memory: 0 MB")
        for w in (self.status_processes, self.status_cpu_proc, self.status_mem_proc):
            sb.addWidget(w); sb.addStretch(1)
        p_l.addWidget(sb_frame)
        
        # Connect buttons
        end_task_btn.clicked.connect(self._end_task)
        end_process_btn.clicked.connect(self._end_process)
        details_btn.clicked.connect(self._go_to_details)
        
        # Initialize processes
        self._seed_processes()
        self._refresh_processes_table()
        
        return processes_tab
    
    def _seed_processes(self):
        """Initialize with some sample processes"""
        self.processes_data = [
            ["chrome.exe", "1234", "Running", "12%", "256 MB"],
            ["python.exe", "5678", "Running", "8%", "128 MB"],
            ["explorer.exe", "9012", "Running", "2%", "64 MB"],
            ["svchost.exe", "3456", "Running", "5%", "96 MB"],
            ["ntoskrnl.exe", "7890", "Running", "1%", "48 MB"],
            ["Pro_Browser.exe", "1111", "Running", "15%", "320 MB"],
            ["System Idle Process", "0", "Running", "0%", "0 MB"],
            ["winlogon.exe", "2222", "Running", "1%", "32 MB"],
            ["lsass.exe", "3333", "Running", "2%", "40 MB"],
            ["csrss.exe", "4444", "Running", "1%", "28 MB"]
        ]
    
    def _refresh_processes_table(self):
        """Update the processes table with current data"""
        self.processes_table.setRowCount(len(self.processes_data))
        for row, process in enumerate(self.processes_data):
            for col, value in enumerate(process):
                item = QTableWidgetItem(value)
                self.processes_table.setItem(row, col, item)
        
        # Update status
        total_cpu = sum(int(p[3].rstrip('%')) for p in self.processes_data)
        total_mem = sum(int(p[4].split()[0]) for p in self.processes_data)
        
        self.status_processes.setText(f"Processes: {len(self.processes_data)}")
        self.status_cpu_proc.setText(f"CPU: {total_cpu}%")
        self.status_mem_proc.setText(f"Memory: {total_mem} MB")
    
    def _end_task(self):
        """End the selected task"""
        selected_items = self.processes_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a process to end.")
            return
        
        row = selected_items[0].row()
        process_name = self.processes_data[row][0]
        
        reply = QMessageBox.question(self, "End Task", 
                                   f"Are you sure you want to end {process_name}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Mark process as ended
            self.processes_data[row][2] = "Not Responding"
            self.processes_data[row][3] = "0%"
            self._refresh_processes_table()
    
    def _end_process(self):
        """End the selected process"""
        selected_items = self.processes_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a process to end.")
            return
        
        row = selected_items[0].row()
        process_name = self.processes_data[row][0]
        
        reply = QMessageBox.question(self, "End Process", 
                                   f"Are you sure you want to end {process_name}?\nThis may cause data loss.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Remove process from list
            del self.processes_data[row]
            self._refresh_processes_table()
    
    def _go_to_details(self):
        """Show details for the selected process"""
        selected_items = self.processes_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a process to view details.")
            return
        
        row = selected_items[0].row()
        process = self.processes_data[row]
        
        details = f"""
        <h3>Process Details</h3>
        <b>Name:</b> {process[0]}<br>
        <b>PID:</b> {process[1]}<br>
        <b>Status:</b> {process[2]}<br>
        <b>CPU Usage:</b> {process[3]}<br>
        <b>Memory Usage:</b> {process[4]}<br>
        <b>Architecture:</b> x64<br>
        <b>Path:</b> C:\\Program Files\\{process[0]}<br>
        <b>Command Line:</b> {process[0]} --process
        """
        
        QMessageBox.information(self, "Process Details", details)
    
    def _seed_users(self):
        """Initialize with some sample users"""
        self.users_data = [
            ["Administrator", "Active", "12%", "128 MB", "Console"],
            ["Guest", "Disconnected", "0%", "64 MB", "RDP-Tcp#0"],
            ["User1", "Active", "5%", "96 MB", "Console"]
        ]
    
    def _refresh_users_table(self):
        """Update the users table with current data"""
        self.users_table.setRowCount(len(self.users_data))
        for row, user in enumerate(self.users_data):
            for col, value in enumerate(user):
                item = QTableWidgetItem(value)
                self.users_table.setItem(row, col, item)
    
    def _add_user(self):
        """Add a new user to the table"""
        user_name, ok = QInputDialog.getText(self, "Add User", "Enter username:")
        if ok and user_name.strip():
            # Generate random stats for the new user
            cpu = f"{random.randint(0, 100)}%"
            mem = f"{random.randint(50, 500)} MB"
            status = random.choice(["Active", "Disconnected", "Idle"])
            session = random.choice(["Console", "RDP-Tcp#0", "RDP-Tcp#1"])
            
            new_user = [user_name.strip(), status, cpu, mem, session]
            self.users_data.append(new_user)
            self._refresh_users_table()
    
    def _remove_selected_user(self):
        """Remove the selected user from the table"""
        selected_rows = set()
        for item in self.users_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a user to remove.")
            return
        
        # Remove rows in reverse order to avoid index issues
        for row in sorted(selected_rows, reverse=True):
            del self.users_data[row]
        
        self._refresh_users_table()
    
    def _update_perf(self):
        cpu = int(self.cpu_graph.points[-1]) if self.cpu_graph.points else 0
        ram_p = int(self.ram_graph.points[-1]) if hasattr(self, 'ram_graph') and self.ram_graph.points else 0
        self.cpu_meter.set_value(cpu)
        self.ram_meter.set_value(ram_p)
        self.status_cpu.setText(f"CPU: {cpu}% / 100%")
        used_mb = int(self.ram_total_mb * ram_p / 100)
        self.status_ram.setText(f"RAM: {used_mb}M / {self.ram_total_mb}M")
        self.ram_used_lbl.setText(f"Used: {used_mb*1024}k")
        self.ram_total_lbl.setText(f"Total: {self.ram_total_mb*1024}k")
        self.ram_free_lbl.setText(f"Free: {(self.ram_total_mb - used_mb)*1024}k")
    
    def _create_networking_tab(self):
        """Create the Networking tab with network adapter information and graphs"""
        networking_tab = QWidget()
        n_l = QVBoxLayout(networking_tab)
        
        # Network adapter selection
        adapter_layout = QHBoxLayout()
        self.adapter_combo = QComboBox()
        self.adapter_combo.addItems(["Ethernet", "Wi-Fi", "Bluetooth Network Connection"])
        self.adapter_combo.currentTextChanged.connect(self._update_network_adapter)
        adapter_layout.addWidget(QLabel("Adapter:"))
        adapter_layout.addWidget(self.adapter_combo)
        adapter_layout.addStretch(1)
        n_l.addLayout(adapter_layout)
        
        # Network graphs
        grid = QGridLayout()
        
        # Download speed graph
        self.download_graph = NTGraph("#00ff00")
        self.download_meter = SmallMeter("Download Speed", mode='mb', limit_mb=1000)
        grid.addWidget(self._make_group("Download Speed", self.download_graph), 0, 0)
        grid.addWidget(self._make_group("Download Rate", self.download_meter), 0, 1)
        
        # Upload speed graph
        self.upload_graph = NTGraph("#0000ff")
        self.upload_meter = SmallMeter("Upload Speed", mode='mb', limit_mb=500)
        grid.addWidget(self._make_group("Upload Speed", self.upload_graph), 1, 0)
        grid.addWidget(self._make_group("Upload Rate", self.upload_meter), 1, 1)
        
        n_l.addLayout(grid)
        
        # Network statistics table
        self.network_table = QTableWidget(0, 4)
        self.network_table.setHorizontalHeaderLabels(["Connection", "Status", "Speed", "Usage"])
        self.network_table.horizontalHeader().setStretchLastSection(True)
        self.network_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.network_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        n_l.addWidget(QLabel("<b>Network Connections:</b>"))
        n_l.addWidget(self.network_table)
        
        # Status bar
        sb_frame = QFrame(); sb_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        sb = QHBoxLayout(sb_frame); sb.setContentsMargins(8,4,8,4)
        self.status_network = QLabel("Active connections: 0")
        self.status_speed = QLabel("Speed: 0 MB/s")
        self.status_usage = QLabel("Total usage: 0 MB")
        for w in (self.status_network, self.status_speed, self.status_usage):
            sb.addWidget(w); sb.addStretch(1)
        n_l.addWidget(sb_frame)
        
        # Initialize networking
        self._seed_networking()
        self._refresh_network_table()
        
        # Start network update timer
        self.net_t = QTimer(self); self.net_t.timeout.connect(self._update_networking); self.net_t.start(1000)
        
        return networking_tab
    
    def _make_group(self, title, inner):
        w = QWidget(); v = QVBoxLayout(w); v.setContentsMargins(0,0,0,0)
        v.addWidget(QLabel(title))
        f = QFrame(); f.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        fl = QVBoxLayout(f); fl.setContentsMargins(4,4,4,4)
        fl.addWidget(inner)
        v.addWidget(f)
        return w
    
    def _seed_networking(self):
        """Initialize with some sample network connections"""
        self.network_data = [
            ["Ethernet", "Connected", "1.0 Gbps", "1.2 GB"],
            ["Wi-Fi", "Connected", "150 Mbps", "856 MB"],
            ["Bluetooth", "Disconnected", "3 Mbps", "12 MB"]
        ]
    
    def _refresh_network_table(self):
        """Update the network table with current data"""
        self.network_table.setRowCount(len(self.network_data))
        for row, conn in enumerate(self.network_data):
            for col, value in enumerate(conn):
                item = QTableWidgetItem(value)
                self.network_table.setItem(row, col, item)
        
        # Update status
        active_conns = sum(1 for conn in self.network_data if conn[1] == "Connected")
        self.status_network.setText(f"Active connections: {active_conns}")
    
    def _update_network_adapter(self, adapter_name):
        """Update display when adapter selection changes"""
        # Simulate different adapter characteristics
        if adapter_name == "Ethernet":
            self.download_meter.limit_mb = 1000
            self.upload_meter.limit_mb = 500
        elif adapter_name == "Wi-Fi":
            self.download_meter.limit_mb = 500
            self.upload_meter.limit_mb = 250
        else:
            self.download_meter.limit_mb = 50
            self.upload_meter.limit_mb = 25
    
    def _update_networking(self):
        """Update network information in real-time"""
        # Update download and upload speeds
        download_speed = random.randint(10, 500)
        upload_speed = random.randint(5, 200)
        
        self.download_meter.set_value(download_speed)
        self.upload_meter.set_value(upload_speed)
        
        # Update status
        self.status_speed.setText(f"Speed: {download_speed + upload_speed} MB/s")
        
        # Update usage for connected adapters
        for i, conn in enumerate(self.network_data):
            if conn[1] == "Connected":
                # Parse current usage properly
                usage_str = conn[3]
                if " GB" in usage_str:
                    # Convert GB to MB for calculation
                    current_usage = float(usage_str.replace(" GB", "")) * 1000
                else:
                    # Already in MB
                    current_usage = float(usage_str.replace(" MB", ""))
                
                # Add random usage increase
                new_usage = current_usage + random.randint(1, 10)
                
                # Convert back to appropriate format
                if new_usage >= 1000:
                    conn[3] = f"{new_usage/1000:.1f} GB"
                else:
                    conn[3] = f"{int(new_usage)} MB"
        
        self._refresh_network_table()
    
    def _update_processes(self):
        """Update process information in real-time"""
        # Update CPU and Memory usage for running processes
        for i, process in enumerate(self.processes_data):
            if process[2] == "Running":
                # Randomly update CPU usage (0-25%)
                new_cpu = random.randint(0, 25)
                process[3] = f"{new_cpu}%"
                
                # Randomly update Memory usage (50-500 MB)
                new_mem = random.randint(50, 500)
                process[4] = f"{new_mem} MB"
        
        # Add new processes occasionally
        if random.random() < 0.1:  # 10% chance every 2 seconds
            new_process = [
                random.choice(["notepad.exe", "calc.exe", "mspaint.exe", "winword.exe", "excel.exe"]),
                str(random.randint(10000, 99999)),
                "Running",
                f"{random.randint(0, 15)}%",
                f"{random.randint(30, 200)} MB"
            ]
            self.processes_data.append(new_process)
        
        # Remove ended processes occasionally
        if len(self.processes_data) > 5 and random.random() < 0.05:  # 5% chance
            # Remove a random process
            idx = random.randint(0, len(self.processes_data) - 1)
            del self.processes_data[idx]
        
        self._refresh_processes_table()

# ================= USER ACCOUNT SYSTEM =================
class UserAccount:
    def __init__(self, email, password, name, avatar_color="#007bff", avatar_path="", is_admin=False):
        self.email = email
        self.password_hash = self._hash_password(password)
        self.name = name
        self.avatar_color = avatar_color
        self.avatar_path = avatar_path  # Path to custom avatar image
        self.is_admin = is_admin  # Admin privilege flag
        self.bookmarks = []
        self.history = []
        self.saved_passwords = []  # List of saved website credentials
        self.settings = {
            "theme": "Dark Mode",
            "font": "Consolas",
            "size": 12,
            "custom_shortcuts": {
                "New Tab": "Ctrl+T", "Reload": "Ctrl+R", "Close Tab": "Ctrl+W", 
                "Focus URL": "Ctrl+L", "Go Back": "Alt+Left", "Go Forward": "Alt+Right",
                "Custom URL": "Ctrl+G"
            },
            "custom_url": "https://www.google.com",
            "auto_save_passwords": True,
            "auto_fill_passwords": True
        }
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password):
        return self._hash_password(password) == self.password_hash
    
    def to_dict(self):
        return {
            "email": self.email,
            "password_hash": self.password_hash,
            "name": self.name,
            "avatar_color": self.avatar_color,
            "avatar_path": self.avatar_path,
            "is_admin": self.is_admin,
            "bookmarks": self.bookmarks,
            "history": self.history,
            "settings": self.settings
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls.__new__(cls)
        user.email = data["email"]
        user.password_hash = data["password_hash"]
        user.name = data["name"]
        user.avatar_color = data.get("avatar_color", "#007bff")
        user.avatar_path = data.get("avatar_path", "")
        user.is_admin = data.get("is_admin", False)  # Handle backward compatibility
        user.bookmarks = data.get("bookmarks", [])
        user.history = data.get("history", [])
        user.settings = data.get("settings", {
            "theme": "Dark Mode",
            "font": "Consolas",
            "size": 12,
            "custom_shortcuts": {
                "New Tab": "Ctrl+T", "Reload": "Ctrl+R", "Close Tab": "Ctrl+W", 
                "Focus URL": "Ctrl+L", "Go Back": "Alt+Left", "Go Forward": "Alt+Right",
                "Custom URL": "Ctrl+G"
            },
            "custom_url": "https://www.google.com"
        })
        return user

class CloudSyncServer:
    """Simple local cloud sync server for multi-device support"""
    def __init__(self, port=8765):
        self.port = port
        self.server_socket = None
        self.running = False
        self.users_data = {}
        self.sync_thread = None
        
    def start_server(self):
        """Start the local sync server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', self.port))
            self.server_socket.listen(5)
            self.running = True
            self.sync_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.sync_thread.start()
            print(f"Cloud sync server started on port {self.port}")
            return True
        except Exception as e:
            print(f"Failed to start sync server: {e}")
            return False
    
    def stop_server(self):
        """Stop the sync server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("Cloud sync server stopped")
    
    def _server_loop(self):
        """Main server loop"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True).start()
            except:
                break
    
    def _handle_client(self, client_socket):
        """Handle client requests"""
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            request = json.loads(data)
            response = self._process_request(request)
            client_socket.send(json.dumps(response).encode('utf-8'))
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
    
    def _process_request(self, request):
        """Process sync requests"""
        action = request.get('action', '')
        email = request.get('email', '')
        
        if action == 'sync_request':
            # Return current user data
            user_data = self.users_data.get(email, {})
            return {'status': 'success', 'data': user_data, 'timestamp': time.time()}
        
        elif action == 'sync_update':
            # Update user data
            user_data = request.get('data', {})
            self.users_data[email] = user_data
            return {'status': 'success', 'message': 'Data synced successfully'}
        
        elif action == 'get_devices':
            # Return list of devices for this user
            devices = list(self.users_data.get(email, {}).get('devices', {}).keys())
            return {'status': 'success', 'devices': devices}
        
        return {'status': 'error', 'message': 'Unknown action'}

class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.users = {}
        self.current_user = None
        self.load_users()
        self.create_default_admin()
        # Initialize cloud sync
        self.cloud_server = CloudSyncServer()
    
    def load_users(self):
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    data = json.load(f)
                    for email, user_data in data.items():
                        self.users[email] = UserAccount.from_dict(user_data)
            except:
                pass
    
    def create_default_admin(self):
        """Create a default admin account if none exists"""
        if not any(user.is_admin for user in self.users.values()):
            admin_email = "admin@probrowser.com"
            admin_password = "admin123"
            admin_name = "Administrator"
            
            # Create admin account
            admin_user = UserAccount(admin_email, admin_password, admin_name, is_admin=True)
            self.users[admin_email] = admin_user
            self.save_users()
            print(f"Created default admin account: {admin_email}")
    
    def save_users(self):
        data = {email: user.to_dict() for email, user in self.users.items()}
        with open(self.users_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_user(self, email, password, name):
        if email in self.users:
            return False, "Email already exists"
        
        user = UserAccount(email, password, name)
        self.users[email] = user
        self.save_users()
        return True, "User created successfully"
    
    def create_admin_user(self, email, password, name):
        """Create an admin user account"""
        if email in self.users:
            return False, "Email already exists"
        
        user = UserAccount(email, password, name, is_admin=True)
        self.users[email] = user
        self.save_users()
        return True, "Admin account created successfully"
    
    def create_admin_user(self, email, password, name):
        """Create an admin user account"""
        if email in self.users:
            return False, "Email already exists"
        
        user = UserAccount(email, password, name, is_admin=True)
        self.users[email] = user
        self.save_users()
        return True, "Admin account created successfully"
    
    def authenticate(self, email, password):
        user = self.users.get(email)
        if user and user.verify_password(password):
            self.current_user = user
            return True, user
        return False, None
    
    def switch_user(self, email):
        if email in self.users:
            self.current_user = self.users[email]
            return True
        return False
    
    def logout(self):
        self.current_user = None

class LoginDialog(QDialog):
    def __init__(self, user_manager, parent=None):
        super().__init__(parent)
        self.user_manager = user_manager
        self.setWindowTitle("Pro_Browser - Sign In")
        self.resize(400, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("Welcome to Pro_Browser")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(header, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # User List Section
        user_list_label = QLabel("Select User:")
        user_list_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(user_list_label)
        
        # User list widget
        self.user_list_widget = QWidget()
        self.user_list_layout = QVBoxLayout(self.user_list_widget)
        self.user_list_layout.setSpacing(10)
        self.user_list_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add scroll area for user list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.user_list_widget)
        scroll_area.setMaximumHeight(200)
        layout.addWidget(scroll_area)
        
        # Load existing users
        self.load_user_list()
        
        # Manual input section
        manual_label = QLabel("Or sign in manually:")
        manual_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(manual_label)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.signin_btn = QPushButton("Sign In")
        self.signup_btn = QPushButton("Sign Up")
        self.guest_btn = QPushButton("Continue as Guest")
        
        self.signin_btn.clicked.connect(self.sign_in)
        self.signup_btn.clicked.connect(self.sign_up)
        self.guest_btn.clicked.connect(self.guest_mode)
        
        btn_layout.addWidget(self.signin_btn)
        btn_layout.addWidget(self.signup_btn)
        btn_layout.addWidget(self.guest_btn)
        layout.addLayout(btn_layout)
        
        # Status message
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_user_list(self):
        """Load and display existing users with their avatars"""
        # Clear existing user buttons
        for i in reversed(range(self.user_list_layout.count())):
            item = self.user_list_layout.itemAt(i)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.setParent(None)
        
        # Add existing users
        users = list(self.user_manager.users.keys())
        if users:
            for email in users:
                user = self.user_manager.users[email]
                user_btn = self.create_user_button(user)
                self.user_list_layout.addWidget(user_btn)
        else:
            no_users_label = QLabel("No users found. Create an account to get started.")
            no_users_label.setStyleSheet("color: #666; font-style: italic;")
            self.user_list_layout.addWidget(no_users_label)
    
    def create_user_button(self, user):
        """Create a user button with avatar and name"""
        user_btn = QPushButton()
        user_btn.setFixedHeight(50)
        user_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 8px;
                padding: 8px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        
        # Create layout for user button
        btn_layout = QHBoxLayout(user_btn)
        btn_layout.setContentsMargins(5, 5, 5, 5)
        
        # Avatar
        avatar_btn = QPushButton()
        avatar_btn.setFixedSize(35, 35)
        avatar_btn.setStyleSheet("border-radius: 17px; border: 1px solid #ccc; background-color: white;")
        
        # Set avatar image or default
        if user.avatar_path and os.path.exists(user.avatar_path):
            # Load custom avatar
            pixmap = QPixmap(user.avatar_path)
            if not pixmap.isNull():
                # Resize to fit the button (35x35) while maintaining quality
                scaled_pixmap = pixmap.scaled(35, 35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                avatar_btn.setIcon(QIcon(scaled_pixmap))
                avatar_btn.setIconSize(avatar_btn.size())
                avatar_btn.setText("")  # Clear text when showing image
            else:
                # Fallback to default
                avatar_btn.setText("👤")
        else:
            # Default avatar
            avatar_btn.setText("👤")
        
        btn_layout.addWidget(avatar_btn)
        
        # User info
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(10, 0, 0, 0)
        
        # Add golden dot for admin accounts
        if user.is_admin:
            name_label = QLabel(f"● {user.name}")
            name_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #FFD700;")
        else:
            name_label = QLabel(f"{user.name}")
            name_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        
        email_label = QLabel(f"{user.email}")
        email_label.setStyleSheet("color: #666; font-size: 10px;")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(email_label)
        info_layout.addStretch()
        
        btn_layout.addLayout(info_layout)
        btn_layout.addStretch()
        
        # Connect button click
        user_btn.clicked.connect(lambda: self.select_user(user))
        
        return user_btn
    
    def select_user(self, user):
        """Handle user selection from the list"""
        self.email_input.setText(user.email)
        self.password_input.setFocus()
        self.status_label.setText(f"Selected: {user.name}")
    
    def sign_in(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not email or not password:
            self.status_label.setText("Please enter both email and password")
            return
        
        success, result = self.user_manager.authenticate(email, password)
        if success:
            self.accept()
        else:
            self.status_label.setText("Invalid email or password")
    
    def sign_up(self):
        email = self.email_input.text().strip()
        password = self.password_input.text().strip()
        
        if not email or not password:
            self.status_label.setText("Please enter both email and password")
            return
        
        # Check if this is an admin account creation
        is_admin = False
        admin_password = None
        
        # Check if the email suggests admin account
        if email.lower() in ["admin@probrowser.com", "administrator@probrowser.com"]:
            # Ask for admin password
            admin_password, ok = QInputDialog.getText(self, "Admin Account Creation", "Enter admin password:", QLineEdit.EchoMode.Password)
            if not ok or not admin_password:
                self.status_label.setText("Admin account creation cancelled.")
                return
            
            # Verify admin password (default admin password is "admin123")
            if admin_password != "admin123":
                self.status_label.setText("Incorrect admin password.")
                return
            
            is_admin = True
        
        name, ok = QInputDialog.getText(self, "Create Account", "Enter your name:")
        if ok and name.strip():
            if is_admin:
                success, message = self.user_manager.create_admin_user(email, password, name.strip())
            else:
                success, message = self.user_manager.create_user(email, password, name.strip())
            
            if success:
                self.status_label.setText("Account created! Please sign in.")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText(message)
    
    def guest_mode(self):
        self.user_manager.current_user = None
        self.accept()

# ================= MAIN BROWSER =================
class ProBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro_Browser")
        self.resize(1300, 850)
        
        # Set the application icon
        icon_path = os.path.join(os.path.dirname(__file__), "Pro_Browsericon.pngnonereziezd-ezgif.com-resize.png")
        print(f"Looking for icon at: {icon_path}")
        print(f"Icon file exists: {os.path.exists(icon_path)}")
        
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            print(f"Icon loaded successfully: {not icon.isNull()}")
            self.setWindowIcon(icon)
        else:
            print("Icon file not found, using default icon")
        
        # Initialize user management
        self.user_manager = UserManager()
        self.current_user = None
        
        # Initialize browser components
        self.settings = QSettings("ProBrowserCorp", "ProBrowser")
        self.load_settings()
        self.actions_dict = {}
        self.setup_ui()
        
        # Show login dialog after UI is set up
        self.show_login()
        
        self.setup_shortcuts()
        self.apply_theme(self.current_theme)

    def load_settings(self):
        self.current_theme = self.settings.value("theme", "Dark Mode")
        self.current_font = self.settings.value("font", "Consolas")
        self.current_size = int(self.settings.value("size", 12))
        self.bookmarks = self.settings.value("bookmarks", ["https://www.google.com"])
        # Ensure bookmarks is always a list
        if self.bookmarks is None:
            self.bookmarks = ["https://www.google.com"]
        elif isinstance(self.bookmarks, str):
            # Handle case where bookmarks might be stored as a string
            self.bookmarks = [self.bookmarks] if self.bookmarks else ["https://www.google.com"]
        self.custom_shorts = self.settings.value("shortcuts", {
            "New Tab": "Ctrl+T", "Reload": "Ctrl+R", "Close Tab": "Ctrl+W", 
            "Focus URL": "Ctrl+L", "Go Back": "Alt+Left", "Go Forward": "Alt+Right",
            "Custom URL": "Ctrl+G"
        })
        self.custom_url_target = self.settings.value("custom_url", "https://www.google.com")

    def setup_ui(self):
        central = QWidget(); self.setCentralWidget(central); layout = QVBoxLayout(central)
        
        # User Profile Row
        user_layout = QHBoxLayout()
        self.user_label = QLabel("Guest Mode")
        self.user_label.setStyleSheet("font-weight: bold; color: #007bff;")
        self.user_avatar = QPushButton("👤")
        self.user_avatar.setFixedSize(35, 35)
        self.user_avatar.clicked.connect(self.show_user_menu)
        
        user_layout.addWidget(self.user_label)
        user_layout.addWidget(self.user_avatar)
        user_layout.addStretch()
        layout.addLayout(user_layout)
        
        # Navigation Row
        nav = QHBoxLayout()
        for txt, func in [("◀", self.go_back), ("▶", self.go_fwd), ("⟳", self.reload)]:
            b = QPushButton(txt); b.setFixedSize(35,35); b.clicked.connect(func); nav.addWidget(b)
        self.url_bar = QLineEdit(); self.url_bar.returnPressed.connect(self.load_url); nav.addWidget(self.url_bar)
        for icon, func in [("⭐", self.save_bookmark), ("📊", self.open_tm), ("⚙", self.open_settings), ("💻", self.open_programming_tab), ("+", self.new_tab)]:
            b = QPushButton(icon); b.setFixedSize(35,35); b.clicked.connect(func); nav.addWidget(b)
        layout.addLayout(nav)

        # Bookmark Bar
        self.bm_bar = QHBoxLayout()
        # Add instruction label
        self.bm_instructions = QLabel("Bookmarks: Click ⭐ to add current page, click bookmark to open, right-click to delete")
        self.bm_instructions.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        layout.addWidget(self.bm_instructions)
        layout.addLayout(self.bm_bar)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.tabs.removeTab)
        self.tabs.setMovable(True)  # Allow tab reordering
        self.tabs.setAcceptDrops(True)  # Allow dropping tabs
        self.tabs.tabBar().setMouseTracking(True)
        self.tabs.tabBar().installEventFilter(self)
        layout.addWidget(self.tabs)
        self.new_tab()

    def update_bookmark_bar(self):
        # Clear existing
        for i in reversed(range(self.bm_bar.count())):
            item = self.bm_bar.itemAt(i)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.setParent(None)
                else:
                    self.bm_bar.removeItem(item)
        
        # Re-add with context menu for removal
        bookmarks = self.bookmarks if isinstance(self.bookmarks, list) else []
        for url in bookmarks:
            # Extract a clean label from URL
            if url.startswith("http"):
                # Remove protocol and get domain
                clean_url = url.replace("https://", "").replace("http://", "")
                label = clean_url.split("/")[0][:15]
            else:
                label = url[:15]
            
            btn = QPushButton(label)
            btn.setToolTip(url)  # Show full URL on hover
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.clicked.connect(lambda ch, u=url: self._open_bookmark(u))
            btn.customContextMenuRequested.connect(lambda pos, u=url, b=btn: self._bookmark_context_menu(u, b, pos))
            self.bm_bar.addWidget(btn)
        self.bm_bar.addStretch()

    def open_tm(self): NTTaskManager([self.tabs.tabText(i) for i in range(self.tabs.count())], self).exec()
    
    def open_programming_tab(self):
        """Open a programming tab with a VSCode-like code editor"""
        # Create a VSCode-like programming environment
        programming_widget = QWidget()
        programming_layout = QVBoxLayout(programming_widget)
        
        # Title
        title_label = QLabel("💻 Programming Environment")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #007bff;")
        programming_layout.addWidget(title_label)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Language selector - search bar with common languages
        language_combo = QComboBox()
        language_combo.setEditable(True)  # Make it searchable
        language_combo.addItems(["Python", "HTML", "JavaScript", "CSS", "Text", "C", "C++", "C#", "Rust", "Go", "Java", "PHP", "Ruby", "Swift", "Kotlin", "TypeScript", "R", "MATLAB", "Shell", "SQL"])
        language_combo.setFixedWidth(200)
        language_combo.setPlaceholderText("Search or type language name...")
        controls_layout.addWidget(QLabel("Language:"))
        controls_layout.addWidget(language_combo)
        
        # Auto-fill button
        autofill_btn = QPushButton("💡 IntelliSense")
        autofill_btn.setStyleSheet("background-color: #ffc107; color: #212529; font-weight: bold;")
        autofill_btn.clicked.connect(lambda: self.auto_fill_code(code_editor, language_combo.currentText()))
        controls_layout.addWidget(autofill_btn)
        
        # Run button
        run_btn = QPushButton("▶ Run Code")
        run_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        run_btn.clicked.connect(lambda: self.run_code(code_editor, language_combo.currentText()))
        controls_layout.addWidget(run_btn)
        
        # Clear button
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        clear_btn.clicked.connect(lambda: code_editor.clear())
        controls_layout.addWidget(clear_btn)
        
        # Save button
        save_btn = QPushButton("💾 Save")
        save_btn.setStyleSheet("background-color: #007bff; color: white; font-weight: bold;")
        save_btn.clicked.connect(lambda: self.save_code(code_editor, language_combo.currentText()))
        controls_layout.addWidget(save_btn)
        
        controls_layout.addStretch()
        programming_layout.addLayout(controls_layout)
        
        # Code editor area with VSCode-like styling
        code_editor = QTextEdit()
        code_editor.setPlaceholderText("Write your code here...\n\nExample:\nprint('Hello, World!')\n\n# Python code will be executed in the browser\n# You can also write HTML, CSS, and JavaScript")
        code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', 'Fira Code', monospace;
                font-size: 14px;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 10px;
            }
            QTextEdit:focus {
                border-color: #007acc;
                outline: none;
            }
        """)
        
        # Add VSCode-like features to the code editor
        self.setup_vscode_features(code_editor, language_combo, autofill_btn)
        
        programming_layout.addWidget(code_editor)
        
        # Output area
        output_label = QLabel("Output:")
        output_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        programming_layout.addWidget(output_label)
        
        output_area = QTextEdit()
        output_area.setReadOnly(True)
        output_area.setStyleSheet("""
            QTextEdit {
                background-color: #252526;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        programming_layout.addWidget(output_area)
        
        # Add the programming tab
        self.tabs.addTab(programming_widget, "💻 Programming")
        self.tabs.setCurrentWidget(programming_widget)
    
    def run_code(self, code_editor, language):
        """Execute the code based on the selected language"""
        code = code_editor.toPlainText()
        output_area = self.tabs.currentWidget().findChild(QTextEdit, "output_area")
        
        if not code.strip():
            self.show_output("Please write some code first!", "error")
            return
        
        try:
            if language == "Python":
                self.run_python_code(code)
            elif language == "HTML":
                self.run_html_code(code)
            elif language == "JavaScript":
                self.run_js_code(code)
            elif language == "CSS":
                self.run_css_code(code)
            else:
                self.show_output(f"Text mode: {code}", "info")
        except Exception as e:
            self.show_output(f"Error: {str(e)}", "error")
    
    def run_python_code(self, code):
        """Execute Python code and show output"""
        try:
            # Create a safe execution environment
            import subprocess
            import tempfile
            import os
            
            # Create temporary Python file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute the Python code
            result = subprocess.run([sys.executable, temp_file], 
                                  capture_output=True, text=True, timeout=10)
            
            # Clean up
            os.unlink(temp_file)
            
            # Show output
            if result.stdout:
                self.show_output(result.stdout, "success")
            if result.stderr:
                self.show_output(result.stderr, "error")
                
        except subprocess.TimeoutExpired:
            self.show_output("Code execution timed out (10 seconds)", "error")
        except Exception as e:
            self.show_output(f"Execution error: {str(e)}", "error")
    
    def run_html_code(self, code):
        """Display HTML code in a web view"""
        # Create a simple HTML wrapper
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Programming Output</title>
            <meta charset="utf-8">
        </head>
        <body>
            {code}
        </body>
        </html>
        """
        
        # Create a web view to display the HTML
        web_view = QWebEngineView()
        web_view.setHtml(html_content)
        
        # Create a dialog to show the HTML output
        dialog = QDialog(self)
        dialog.setWindowTitle("HTML Output")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(web_view)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def run_js_code(self, code):
        """Execute JavaScript code"""
        # Create a simple HTML page with the JavaScript
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>JavaScript Output</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h3>JavaScript Execution</h3>
            <div id="output"></div>
            <script>
                try {{
                    // Capture console.log output
                    const originalLog = console.log;
                    const output = [];
                    console.log = function(...args) {{
                        output.push(args.join(' '));
                        document.getElementById('output').innerHTML = output.join('<br>');
                        originalLog.apply(console, args);
                    }};
                    
                    // Execute the code
                    {code}
                }} catch (e) {{
                    document.getElementById('output').innerHTML = 'Error: ' + e.message;
                }}
            </script>
        </body>
        </html>
        """
        
        # Create a web view to display the JavaScript output
        web_view = QWebEngineView()
        web_view.setHtml(html_content)
        
        # Create a dialog to show the JavaScript output
        dialog = QDialog(self)
        dialog.setWindowTitle("JavaScript Output")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(web_view)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def run_css_code(self, code):
        """Display CSS code effects"""
        # Create a simple HTML page with the CSS
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSS Output</title>
            <meta charset="utf-8">
            <style>
                {code}
                body {{
                    font-family: Arial, sans-serif;
                    padding: 20px;
                }}
                .demo-box {{
                    width: 200px;
                    height: 100px;
                    border: 1px solid #ccc;
                    margin: 10px;
                    display: inline-block;
                }}
            </style>
        </head>
        <body>
            <h3>CSS Effects Demo</h3>
            <p>Here's how your CSS looks:</p>
            <div class="demo-box">Sample Box</div>
            <div class="demo-box" style="background: linear-gradient(45deg, #ff6b6b, #4ecdc4);">Gradient Box</div>
            <div class="demo-box" style="box-shadow: 5px 5px 15px rgba(0,0,0,0.3);">Shadow Box</div>
        </body>
        </html>
        """
        
        # Create a web view to display the CSS output
        web_view = QWebEngineView()
        web_view.setHtml(html_content)
        
        # Create a dialog to show the CSS output
        dialog = QDialog(self)
        dialog.setWindowTitle("CSS Output")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(web_view)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def show_output(self, text, output_type="info"):
        """Display output in the programming tab"""
        # Find the output area in the current programming tab
        current_widget = self.tabs.currentWidget()
        if hasattr(current_widget, 'findChildren'):
            output_widgets = current_widget.findChildren(QTextEdit)
            for widget in output_widgets:
                if widget.isReadOnly():  # This should be our output area
                    # Add timestamp and type indicator
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                    
                    if output_type == "error":
                        formatted_text = f"[{timestamp}] ERROR: {text}"
                        widget.setTextColor(QColor("#ff6b6b"))
                    elif output_type == "success":
                        formatted_text = f"[{timestamp}] SUCCESS: {text}"
                        widget.setTextColor(QColor("#51cf66"))
                    else:
                        formatted_text = f"[{timestamp}] INFO: {text}"
                        widget.setTextColor(QColor("#d4d4d4"))
                    
                    widget.append(formatted_text)
                    return
        
        # Fallback: just append to the last text edit
        if output_widgets:
            output_widgets[-1].append(text)
    
    def save_code(self, code_editor, language):
        """Save the current code to a file"""
        code = code_editor.toPlainText()
        if not code.strip():
            self.show_output("No code to save!", "error")
            return
        
        # Generate filename
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"code_{timestamp}.{self.get_file_extension(language)}"
        
        # Save file
        try:
            with open(filename, 'w') as f:
                f.write(code)
            self.show_output(f"Code saved as: {filename}", "success")
        except Exception as e:
            self.show_output(f"Save failed: {str(e)}", "error")
    
    def get_file_extension(self, language):
        """Get file extension for the language"""
        extensions = {
            "Python": "py",
            "HTML": "html", 
            "JavaScript": "js",
            "CSS": "css",
            "Text": "txt"
        }
        return extensions.get(language, "txt")
    def save_bookmark(self): 
        url = self.url_bar.text().strip()
        # Ensure bookmarks is a list
        if not isinstance(self.bookmarks, list):
            self.bookmarks = []
        
        if url and url not in self.bookmarks:
            self.bookmarks.append(url)
            self.settings.setValue("bookmarks", self.bookmarks)
            self.update_bookmark_bar()
            # Also save to current user if logged in
            if self.current_user:
                self.current_user.bookmarks = self.bookmarks
                self.user_manager.save_users()

    def open_settings(self):
        d = QDialog(self); d.setWindowTitle("Master Archive Settings"); d.resize(600, 750)
        l = QVBoxLayout(d)
        
        th = QComboBox(); th.addItems(["Dark Mode", "Light Mode", "Ocean Blue", "Hot Sun", "Fire Red", "YouTube"]); th.setCurrentText(self.current_theme)
        l.addWidget(QLabel("<b>Theme:</b>")); l.addWidget(th)
        
        # Shortcut Mapper Table
        table = QTableWidget(len(self.custom_shorts), 2); table.setHorizontalHeaderLabels(["Action", "Key Mapping"])
        for i, (k, v) in enumerate(self.custom_shorts.items()):
            table.setItem(i, 0, QTableWidgetItem(k)); table.setItem(i, 1, QTableWidgetItem(v))
        l.addWidget(QLabel("<b>Shortcut Mapper:</b>")); l.addWidget(table)
        
        # Custom Shortcut Target
        target_url = QLineEdit(self.custom_url_target)
        l.addWidget(QLabel("<b>Custom URL Shortcut Target (Ctrl+G):</b>")); l.addWidget(target_url)
        
        # Password Manager Section
        if self.current_user:
            l.addWidget(QLabel("<b>Password Manager:</b>"))
            
            # Password Manager Controls
            pm_layout = QHBoxLayout()
            save_passwords_cb = QCheckBox("Auto-save passwords")
            save_passwords_cb.setChecked(self.current_user.settings.get("auto_save_passwords", True))
            auto_fill_cb = QCheckBox("Auto-fill passwords")
            auto_fill_cb.setChecked(self.current_user.settings.get("auto_fill_passwords", True))
            pm_layout.addWidget(save_passwords_cb)
            pm_layout.addWidget(auto_fill_cb)
            l.addLayout(pm_layout)
            
            # Saved Passwords Table
            self.passwords_table = QTableWidget(0, 4)
            self.passwords_table.setHorizontalHeaderLabels(["Website", "Username", "Password", "Actions"])
            self.passwords_table.horizontalHeader().setStretchLastSection(True)
            self.passwords_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.passwords_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            l.addWidget(QLabel("<b>Saved Passwords:</b>"))
            l.addWidget(self.passwords_table)
            
            # Password Manager Buttons
            pm_btn_layout = QHBoxLayout()
            add_password_btn = QPushButton("Add Password")
            add_password_btn.clicked.connect(self.add_password)
            view_passwords_btn = QPushButton("View All Passwords")
            view_passwords_btn.clicked.connect(self.view_all_passwords)
            pm_btn_layout.addWidget(add_password_btn)
            pm_btn_layout.addWidget(view_passwords_btn)
            l.addLayout(pm_btn_layout)
            
            # Load saved passwords
            self.load_passwords_table()
        
        btn = QPushButton("SAVE & APPLY"); btn.clicked.connect(lambda: self.save_all(th.currentText(), table, target_url.text(), save_passwords_cb.isChecked(), auto_fill_cb.isChecked(), d))
        l.addWidget(btn); d.exec()

    def save_all(self, t, table, custom_url, save_passwords, auto_fill, d):
        self.current_theme = t; self.settings.setValue("theme", t)
        self.custom_url_target = custom_url; self.settings.setValue("custom_url", custom_url)
        for i in range(table.rowCount()): self.custom_shorts[table.item(i,0).text()] = table.item(i,1).text()
        self.settings.setValue("shortcuts", self.custom_shorts)
        
        # Save password manager settings if user is logged in
        if self.current_user:
            self.current_user.settings["auto_save_passwords"] = save_passwords
            self.current_user.settings["auto_fill_passwords"] = auto_fill
            self.user_manager.save_users()
        
        self.apply_theme(t); self.setup_shortcuts(); d.close()

    def setup_shortcuts(self):
        for a in self.actions_dict.values(): self.removeAction(a)
        m = [("New Tab", self.new_tab), ("Reload", self.reload), ("Close Tab", lambda: self.tabs.removeTab(self.tabs.currentIndex())), ("Focus URL", lambda: self.url_bar.setFocus())]
        for name, func in m:
            act = QAction(self); act.setShortcut(QKeySequence(self.custom_shorts.get(name, "")))
            act.triggered.connect(func); self.addAction(act); self.actions_dict[name] = act
        # Custom URL Shortcut
        custom_act = QAction(self); custom_act.setShortcut(QKeySequence(self.custom_shorts.get("Custom URL", "Ctrl+G")))
        custom_act.triggered.connect(lambda: self.tabs.currentWidget().setUrl(QUrl(self.custom_url_target)))
        self.addAction(custom_act); self.actions_dict["Custom URL"] = custom_act

    def apply_theme(self, name):
        font_style = f"font-family: '{self.current_font}'; font-size: {self.current_size}px;"
        img = os.path.join(os.path.dirname(__file__), "youtube pro_browser background theme.png").replace("\\", "/")
        bg = f"background-image: url('{img}'); background-position: center;" if os.path.exists(img) else "background: #181818;"
        themes = {
            "Dark Mode": "QMainWindow { background: #1a1a1a; color: white; }",
            "Light Mode": "QMainWindow { background: #fdfdfd; color: black; }",
            "Ocean Blue": "QMainWindow { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #005f73, stop:1 #0a9396); color: white; }",
            "Hot Sun": "QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffcc33, stop:1 #ff6600); }",
            "Fire Red": "QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ff0000, stop:1 #8b0000); color: white; } QPushButton { background-color: #ff4444; color: white; border: 1px solid #cc0000; }",
            "YouTube": f"QMainWindow {{ {bg} }} QPushButton {{ color: red; background: white; }}"
        }
        self.setStyleSheet(f"* {{ {font_style} }} " + themes.get(name, themes["Dark Mode"]))

    def new_tab(self):
        w = QWebEngineView()
        w.setUrl(QUrl("https://www.google.com"))
        w.titleChanged.connect(lambda: self.tabs.setTabText(self.tabs.indexOf(w), w.title()[:15]))
        w.urlChanged.connect(self.update_url_bar)
        self.tabs.addTab(w, "New Tab")
        self.tabs.setCurrentWidget(w)
    
    def eventFilter(self, source, event):
        """Handle tab drag and drop events"""
        if source == self.tabs.tabBar() and event.type() == QEvent.Type.MouseButtonPress:
            if event.button() == Qt.MouseButton.LeftButton:
                self.drag_start_pos = event.pos()
                return False
        elif source == self.tabs.tabBar() and event.type() == QEvent.Type.MouseMove:
            if not hasattr(self, 'drag_start_pos'):
                return False
            if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
                return False
            
            index = self.tabs.tabBar().tabAt(event.pos())
            if index != -1:
                self.start_tab_drag(index)
                return True
        elif source == self.tabs.tabBar() and event.type() == QEvent.Type.MouseButtonRelease:
            # Clear drag state on release
            if hasattr(self, 'drag_start_pos'):
                delattr(self, 'drag_start_pos')
        return super().eventFilter(source, event)
    
    def start_tab_drag(self, index):
        """Start dragging a tab to create a new window"""
        # Create a pixmap of the tab
        tab_rect = self.tabs.tabBar().tabRect(index)
        pixmap = QPixmap(tab_rect.size())
        self.tabs.tabBar().render(pixmap, tab_rect.topLeft())
        
        # Create drag object
        drag = QDrag(self)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(tab_rect.width() // 2, tab_rect.height() // 2))
        
        # Set mime data with tab index
        mime_data = QMimeData()
        mime_data.setText(str(index))
        drag.setMimeData(mime_data)
        
        # Execute drag
        if drag.exec(Qt.DropAction.MoveAction) == Qt.DropAction.MoveAction:
            # Tab was moved, create new window if dropped outside
            self.create_detached_tab(index)
    
    def create_detached_tab(self, index):
        """Create a new window with the detached tab"""
        # Get the widget and title from the current tab
        widget = self.tabs.widget(index)
        title = self.tabs.tabText(index)
        url = widget.url().toString() if hasattr(widget, 'url') else "https://www.google.com"
        
        # Remove tab from current window
        self.tabs.removeTab(index)
        
        # Create new browser window
        new_window = ProBrowser()
        new_window.setWindowTitle(title)
        
        # Create new tab with the same content
        new_widget = QWebEngineView()
        new_widget.setUrl(QUrl(url))
        new_widget.titleChanged.connect(lambda: new_window.tabs.setTabText(new_window.tabs.indexOf(new_widget), new_widget.title()[:15]))
        new_widget.urlChanged.connect(new_window.update_url_bar)
        new_window.tabs.addTab(new_widget, title)
        new_window.tabs.setCurrentWidget(new_widget)
        
        # Show the new window
        new_window.show()

    def load_url(self):
        url = self.url_bar.text().strip()
        if url:
            # Add http:// if no protocol specified
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self.tabs.currentWidget().setUrl(QUrl(url))
    
    def update_url_bar(self, url):
        """Update the URL bar when the page URL changes"""
        self.url_bar.setText(url.toString())
    
    def go_back(self): self.tabs.currentWidget().back()
    def go_fwd(self): self.tabs.currentWidget().forward()
    def reload(self): self.tabs.currentWidget().reload()

    def _bookmark_context_menu(self, url, button, pos):
        menu = QMenu(self)
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self._open_bookmark(url))
        menu.addAction(open_action)
        
        menu.addSeparator()
        
        remove_action = QAction("Delete", self)
        remove_action.triggered.connect(lambda: self.remove_bookmark(url))
        menu.addAction(remove_action)
        
        menu.exec(button.mapToGlobal(pos))
    
    def _open_bookmark(self, url):
        """Open a bookmark in the current tab"""
        if url:
            # Add http:// if no protocol specified
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self.tabs.currentWidget().setUrl(QUrl(url))

    def remove_bookmark(self, url):
        # Remove the bookmark if exists and persist
        if url in self.bookmarks:
            self.bookmarks.remove(url)
            self.settings.setValue("bookmarks", self.bookmarks)
            self.update_bookmark_bar()
            # Also update current user if logged in
            if self.current_user:
                self.current_user.bookmarks = self.bookmarks
                self.user_manager.save_users()
    
    def show_login(self):
        dialog = LoginDialog(self.user_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_user = self.user_manager.current_user
            self.update_user_display()
        else:
            # If login failed or cancelled, exit the application
            sys.exit(0)
    
    def update_user_display(self):
        """Update the user interface to reflect current user state"""
        if self.current_user:
            # Add golden point for admin accounts
            if self.current_user.is_admin:
                display_name = f"👑 {self.current_user.name} ({self.current_user.email})"
            else:
                display_name = f"{self.current_user.name} ({self.current_user.email})"
            
            self.user_label.setText(display_name)
            # Update avatar display
            self.update_avatar_display()
            # Load user-specific settings
            self.load_user_settings()
        else:
            self.user_label.setText("Guest Mode")
            self.user_avatar.setText("👤")
            # Load default settings
            self.load_settings()
    
    def load_user_settings(self):
        """Load settings specific to the current user"""
        if self.current_user:
            user_settings = self.current_user.settings
            self.current_theme = user_settings.get("theme", "Dark Mode")
            self.current_font = user_settings.get("font", "Consolas")
            self.current_size = user_settings.get("size", 12)
            self.bookmarks = self.current_user.bookmarks
            self.custom_shorts = user_settings.get("custom_shortcuts", {
                "New Tab": "Ctrl+T", "Reload": "Ctrl+R", "Close Tab": "Ctrl+W", 
                "Focus URL": "Ctrl+L", "Go Back": "Alt+Left", "Go Forward": "Alt+Right",
                "Custom URL": "Ctrl+G"
            })
            self.custom_url_target = user_settings.get("custom_url", "https://www.google.com")
            self.update_bookmark_bar()
    
    def save_user_settings(self):
        """Save current settings to the current user"""
        if self.current_user:
            self.current_user.settings = {
                "theme": self.current_theme,
                "font": self.current_font,
                "size": self.current_size,
                "custom_shortcuts": self.custom_shorts,
                "custom_url": self.custom_url_target
            }
            self.current_user.bookmarks = self.bookmarks
            self.user_manager.save_users()
    
    def show_user_menu(self):
        """Show the user account menu"""
        menu = QMenu(self)
        
        if self.current_user:
            # User is logged in
            profile_action = menu.addAction(f"Profile: {self.current_user.name}")
            profile_action.setEnabled(False)
            
            menu.addSeparator()
            
            # Profile management actions
            upload_avatar_action = menu.addAction("Upload Profile Picture")
            upload_avatar_action.triggered.connect(self.upload_profile_picture)
            
            remove_avatar_action = menu.addAction("Remove Profile Picture")
            remove_avatar_action.triggered.connect(self.remove_profile_picture)
            
            # Account management actions
            change_password_action = menu.addAction("Change Password")
            change_password_action.triggered.connect(self.change_password)
            
            change_email_action = menu.addAction("Change Email")
            change_email_action.triggered.connect(self.change_email)
            
            change_username_action = menu.addAction("Change Username")
            change_username_action.triggered.connect(self.change_username)
            
            # Delete account action
            delete_account_action = menu.addAction("Delete Account")
            delete_account_action.triggered.connect(self.delete_account)
            
            # Help action
            help_action = menu.addAction("How to Upload Profile Picture")
            help_action.triggered.connect(self.show_upload_instructions)
            
            # Admin-only actions
            if self.current_user.is_admin:
                menu.addSeparator()
                admin_label = menu.addAction("🔧 Administrator")
                admin_label.setEnabled(False)
                
                manage_users_action = menu.addAction("Manage Users")
                manage_users_action.triggered.connect(self.manage_users)
                
                system_info_action = menu.addAction("System Information")
                system_info_action.triggered.connect(self.show_system_info)
                
                backup_data_action = menu.addAction("Backup User Data")
                backup_data_action.triggered.connect(self.backup_user_data)
                
                restore_data_action = menu.addAction("Restore User Data")
                restore_data_action.triggered.connect(self.restore_user_data)
            
            menu.addSeparator()
            
            switch_action = menu.addAction("Switch Account")
            switch_action.triggered.connect(self.switch_account)
            
            logout_action = menu.addAction("Sign Out")
            logout_action.triggered.connect(self.logout)
        else:
            # Guest mode
            signin_action = menu.addAction("Sign In")
            signin_action.triggered.connect(self.sign_in)
            
            signup_action = menu.addAction("Create Account")
            signup_action.triggered.connect(self.create_account)
        
        menu.exec(self.user_avatar.mapToGlobal(self.user_avatar.rect().bottomLeft()))
    
    def show_upload_instructions(self):
        """Show instructions on how to upload a profile picture"""
        instructions = """
        <h3>How to Upload a Profile Picture</h3>
        <ol>
        <li><b>Click your avatar</b> (the 👤 icon) in the top-right corner</li>
        <li><b>Select "Upload Profile Picture"</b> from the menu</li>
        <li><b>Choose an image file</b> from your computer</li>
        <li><b>Supported formats:</b> PNG, JPG, JPEG, BMP, GIF</li>
        <li><b>Recommended size:</b> 100x100 pixels or larger (minimum 50x50 pixels)</li>
        <li><b>Image will be processed</b> and resized to fit the 35x35 avatar button</li>
        </ol>
        <p><b>Note:</b> Your profile picture will be saved to your account and will appear every time you log in.</p>
        <p><b>Tip:</b> Square images work best and will be automatically resized to fit perfectly.</p>
        """
        QMessageBox.information(self, "Profile Picture Upload", instructions)
    
    def upload_profile_picture(self):
        """Allow user to upload a profile picture"""
        if not self.current_user:
            return
        
        # Open file dialog to select image
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Profile Picture", 
            "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        
        if file_path:
            # Create avatars directory if it doesn't exist
            avatars_dir = os.path.join(os.path.dirname(__file__), "avatars")
            os.makedirs(avatars_dir, exist_ok=True)
            
            # Generate unique filename
            file_ext = os.path.splitext(file_path)[1]
            avatar_filename = f"{self.current_user.email.replace('@', '_').replace('.', '_')}_avatar{file_ext}"
            avatar_path = os.path.join(avatars_dir, avatar_filename)
            
            try:
                # Copy the image to our avatars directory
                import shutil
                shutil.copy2(file_path, avatar_path)
                
                # Update user's avatar path
                self.current_user.avatar_path = avatar_path
                self.user_manager.save_users()
                
                # Update the avatar display
                self.update_avatar_display()
                
                QMessageBox.information(self, "Success", "Profile picture updated successfully!")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to upload profile picture: {str(e)}")
    
    def remove_profile_picture(self):
        """Remove the user's profile picture"""
        if not self.current_user:
            return
        
        if self.current_user.avatar_path and os.path.exists(self.current_user.avatar_path):
            try:
                os.remove(self.current_user.avatar_path)
                self.current_user.avatar_path = ""
                self.user_manager.save_users()
                self.update_avatar_display()
                QMessageBox.information(self, "Success", "Profile picture removed successfully!")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to remove profile picture: {str(e)}")
        else:
            QMessageBox.information(self, "No Profile Picture", "You don't have a profile picture to remove.")
    
    def update_avatar_display(self):
        """Update the avatar button to show the user's profile picture"""
        # Complete reset of avatar state with multiple clearing steps
        self.user_avatar.setIcon(QIcon())
        self.user_avatar.setText("")
        self.user_avatar.setIconSize(QSize(0, 0))
        self.user_avatar.setStyleSheet("")  # Reset any custom styling
        
        if self.current_user and self.current_user.avatar_path and os.path.exists(self.current_user.avatar_path):
            # Load and resize the image
            pixmap = QPixmap(self.current_user.avatar_path)
            if not pixmap.isNull():
                # Resize to fit the button (35x35) while maintaining quality
                scaled_pixmap = pixmap.scaled(35, 35, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.user_avatar.setIcon(QIcon(scaled_pixmap))
                self.user_avatar.setIconSize(QSize(35, 35))
                self.user_avatar.setText("")  # Ensure text is empty when showing image
            else:
                # Fallback to default avatar
                self.user_avatar.setText("👤")
        else:
            # Use default avatar for guest mode or no user
            # Force clear any remaining icon data and set text
            self.user_avatar.setIcon(QIcon())
            self.user_avatar.setIconSize(QSize(0, 0))
            self.user_avatar.setText("👤")
    def switch_account(self):
        """Switch to a different user account"""
        users = list(self.user_manager.users.keys())
        if not users:
            QMessageBox.information(self, "No Users", "No user accounts found. Please create an account first.")
            return
        email, ok = QInputDialog.getItem(self, "Switch Account", "Select account:", users, 0, False)
        if ok and email:
            if self.user_manager.switch_user(email):
                self.current_user = self.user_manager.current_user
                self.update_user_display()
                self.apply_theme(self.current_theme)
                self.setup_shortcuts()
    def logout(self):
        """Log out the current user"""
        self.user_manager.logout()
        self.current_user = None
        self.update_user_display()
        self.load_settings()
        self.apply_theme(self.current_theme)
        self.setup_shortcuts()
    def sign_in(self):
        """Show login dialog"""
        dialog = LoginDialog(self.user_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_user = self.user_manager.current_user
            self.update_user_display()
    def delete_account(self):
        """Delete the current user account with password confirmation"""
        if not self.current_user:
            return
        
        # Ask for password confirmation
        password, ok = QInputDialog.getText(self, "Delete Account", "Enter your password to confirm deletion:", QLineEdit.EchoMode.Password)
        if not ok or not password:
            return
        
        # Verify password
        if not self.current_user.verify_password(password):
            QMessageBox.warning(self, "Incorrect Password", "The password you entered is incorrect. Account deletion cancelled.")
            return
        
        # Confirm deletion with a warning
        reply = QMessageBox.warning(self, "Delete Account", 
                                  f"Are you sure you want to delete your account?\n\n"
                                  f"Account: {self.current_user.name} ({self.current_user.email})\n"
                                  f"This action cannot be undone and will permanently delete all your data including:\n"
                                  f"- Bookmarks\n"
                                  f"- Settings\n"
                                  f"- Profile picture\n"
                                  f"- All account information\n\n"
                                  f"Type 'DELETE' to confirm:",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Get confirmation text
            confirmation, ok2 = QInputDialog.getText(self, "Confirm Deletion", "Type 'DELETE' to confirm:")
            if ok2 and confirmation == "DELETE":
                # Store email before clearing current user
                email_to_delete = self.current_user.email
                
                # Delete profile picture if exists
                if self.current_user.avatar_path and os.path.exists(self.current_user.avatar_path):
                    try:
                        os.remove(self.current_user.avatar_path)
                        print(f"Deleted profile picture: {self.current_user.avatar_path}")
                    except Exception as e:
                        print(f"Error deleting profile picture: {e}")
                
                # Remove user from user manager
                if email_to_delete in self.user_manager.users:
                    del self.user_manager.users[email_to_delete]
                    self.user_manager.save_users()
                    print(f"Deleted user from user manager: {email_to_delete}")
                
                # Clear current user
                self.current_user = None
                
                # Show success message
                QMessageBox.information(self, "Account Deleted", "Your account has been permanently deleted.")
                
                # Return to guest mode
                self.update_user_display()
                self.load_settings()
                self.apply_theme(self.current_theme)
                self.setup_shortcuts()
            else:
                QMessageBox.information(self, "Deletion Cancelled", "Account deletion has been cancelled.")
    
    def change_password(self):
        """Change the current user's password"""
        if not self.current_user:
            return
        
        # Ask for current password
        current_password, ok = QInputDialog.getText(self, "Change Password", "Enter current password:", QLineEdit.EchoMode.Password)
        if not ok or not current_password:
            return
        
        # Verify current password
        if not self.current_user.verify_password(current_password):
            QMessageBox.warning(self, "Incorrect Password", "The current password you entered is incorrect.")
            return
        
        # Ask for new password
        new_password, ok2 = QInputDialog.getText(self, "Change Password", "Enter new password:", QLineEdit.EchoMode.Password)
        if not ok2 or not new_password:
            return
        
        # Confirm new password
        confirm_password, ok3 = QInputDialog.getText(self, "Change Password", "Confirm new password:", QLineEdit.EchoMode.Password)
        if not ok3 or not confirm_password:
            return
        
        # Check if passwords match
        if new_password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "The new passwords do not match.")
            return
        
        # Update password
        self.current_user.password_hash = self.current_user._hash_password(new_password)
        self.user_manager.save_users()
        
        QMessageBox.information(self, "Success", "Password changed successfully!")
    
    def change_email(self):
        """Change the current user's email"""
        if not self.current_user:
            return
        
        # Ask for current password for security
        password, ok = QInputDialog.getText(self, "Change Email", "Enter your password for security:", QLineEdit.EchoMode.Password)
        if not ok or not password:
            return
        
        # Verify password
        if not self.current_user.verify_password(password):
            QMessageBox.warning(self, "Incorrect Password", "The password you entered is incorrect.")
            return
        
        # Ask for new email
        new_email, ok2 = QInputDialog.getText(self, "Change Email", "Enter new email:")
        if not ok2 or not new_email:
            return
        
        # Validate email format (basic check)
        if "@" not in new_email or "." not in new_email:
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
        
        # Check if email is already taken
        if new_email in self.user_manager.users and new_email != self.current_user.email:
            QMessageBox.warning(self, "Email Taken", "This email is already in use by another account.")
            return
        
        # Update email
        old_email = self.current_user.email
        self.current_user.email = new_email
        
        # Update user manager dictionary
        self.user_manager.users[new_email] = self.user_manager.users.pop(old_email)
        
        self.user_manager.save_users()
        
        QMessageBox.information(self, "Success", "Email changed successfully!")
    
    def change_username(self):
        """Change the current user's username"""
        if not self.current_user:
            return
        
        # Ask for current password for security
        password, ok = QInputDialog.getText(self, "Change Username", "Enter your password for security:", QLineEdit.EchoMode.Password)
        if not ok or not password:
            return
        
        # Verify password
        if not self.current_user.verify_password(password):
            QMessageBox.warning(self, "Incorrect Password", "The password you entered is incorrect.")
            return
        
        # Ask for new username
        new_name, ok2 = QInputDialog.getText(self, "Change Username", "Enter new username:", text=self.current_user.name)
        if not ok2 or not new_name:
            return
        
        # Update username
        self.current_user.name = new_name.strip()
        self.user_manager.save_users()
        
        # Update display
        self.update_user_display()
        
        QMessageBox.information(self, "Success", "Username changed successfully!")
    
    def create_account(self):
        """Create a new user account"""
        email, ok = QInputDialog.getText(self, "Create Account", "Enter email:")
        if ok and email:
            password, ok2 = QInputDialog.getText(self, "Create Account", "Enter password:", QLineEdit.EchoMode.Password)
            if ok2 and password:
                name, ok3 = QInputDialog.getText(self, "Create Account", "Enter your name:")
                if ok3 and name:
                    success, message = self.user_manager.create_user(email, password, name)
                    if success:
                        QMessageBox.information(self, "Success", "Account created successfully!")
                        self.sign_in()
                    else:
                        QMessageBox.warning(self, "Error", message)
    
    def load_passwords_table(self):
        """Load saved passwords into the table"""
        if not self.current_user:
            return
        
        # Ensure saved_passwords attribute exists (for backward compatibility)
        if not hasattr(self.current_user, 'saved_passwords'):
            self.current_user.saved_passwords = []
        
        self.passwords_table.setRowCount(len(self.current_user.saved_passwords))
        for row, password_entry in enumerate(self.current_user.saved_passwords):
            website_item = QTableWidgetItem(password_entry.get("website", ""))
            username_item = QTableWidgetItem(password_entry.get("username", ""))
            password_item = QTableWidgetItem("••••••••")  # Hide password
            password_item.setFlags(password_item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make non-editable
            
            # Create action buttons
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(2)
            
            view_btn = QPushButton("👁️")
            view_btn.setFixedSize(25, 25)
            view_btn.setToolTip("View Password")
            view_btn.clicked.connect(lambda ch, entry=password_entry: self.view_password(entry))
            
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(25, 25)
            edit_btn.setToolTip("Edit")
            edit_btn.clicked.connect(lambda ch, entry=password_entry: self.edit_password(entry))
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(25, 25)
            delete_btn.setToolTip("Delete")
            delete_btn.clicked.connect(lambda ch, entry=password_entry: self.delete_password(entry))
            
            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            # Create container widget for buttons
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            
            self.passwords_table.setItem(row, 0, website_item)
            self.passwords_table.setItem(row, 1, username_item)
            self.passwords_table.setItem(row, 2, password_item)
            self.passwords_table.setCellWidget(row, 3, actions_widget)
    
    def add_password(self):
        """Add a new password entry"""
        if not self.current_user:
            return
        
        # Get website URL from current tab
        current_url = self.tabs.currentWidget().url().toString()
        if current_url and current_url.startswith("http"):
            # Extract domain from URL
            domain = current_url.replace("https://", "").replace("http://", "").split("/")[0]
            website, ok = QInputDialog.getText(self, "Add Password", "Website:", text=domain)
        else:
            website, ok = QInputDialog.getText(self, "Add Password", "Website:")
        
        if not ok or not website:
            return
        
        username, ok2 = QInputDialog.getText(self, "Add Password", "Username:")
        if not ok2 or not username:
            return
        
        password, ok3 = QInputDialog.getText(self, "Add Password", "Password:", QLineEdit.EchoMode.Password)
        if not ok3 or not password:
            return
        
        # Add to user's saved passwords
        self.current_user.saved_passwords.append({
            "website": website,
            "username": username,
            "password": password
        })
        
        self.user_manager.save_users()
        self.load_passwords_table()
        
        QMessageBox.information(self, "Success", "Password saved successfully!")
    
    def view_password(self, entry):
        """View the password for a specific entry"""
        if not self.current_user:
            return
        
        password = entry.get("password", "")
        website = entry.get("website", "")
        username = entry.get("username", "")
        
        # Show password in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("View Password")
        dialog.resize(300, 150)
        
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel(f"<b>Website:</b> {website}"))
        layout.addWidget(QLabel(f"<b>Username:</b> {username}"))
        
        password_layout = QHBoxLayout()
        password_label = QLabel(password)
        password_label.setStyleSheet("font-family: monospace; font-size: 14px;")
        password_layout.addWidget(QLabel("Password:"))
        password_layout.addWidget(password_label)
        password_layout.addStretch()
        layout.addLayout(password_layout)
        
        copy_btn = QPushButton("Copy to Clipboard")
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(password))
        layout.addWidget(copy_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def edit_password(self, entry):
        """Edit an existing password entry"""
        if not self.current_user:
            return
        
        website = entry.get("website", "")
        username = entry.get("username", "")
        password = entry.get("password", "")
        
        new_website, ok = QInputDialog.getText(self, "Edit Password", "Website:", text=website)
        if not ok:
            return
        
        new_username, ok2 = QInputDialog.getText(self, "Edit Password", "Username:", text=username)
        if not ok2:
            return
        
        new_password, ok3 = QInputDialog.getText(self, "Edit Password", "Password:", QLineEdit.EchoMode.Password, text=password)
        if not ok3:
            return
        
        # Update the entry
        entry["website"] = new_website
        entry["username"] = new_username
        entry["password"] = new_password
        
        self.user_manager.save_users()
        self.load_passwords_table()
        
        QMessageBox.information(self, "Success", "Password updated successfully!")
    
    def delete_password(self, entry):
        """Delete a password entry"""
        if not self.current_user:
            return
        
        reply = QMessageBox.question(self, "Delete Password", 
                                   f"Are you sure you want to delete the password for {entry.get('website', '')}?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.current_user.saved_passwords.remove(entry)
            self.user_manager.save_users()
            self.load_passwords_table()
            
            QMessageBox.information(self, "Success", "Password deleted successfully!")
    
    def view_all_passwords(self):
        """View all saved passwords in a detailed dialog"""
        if not self.current_user or not self.current_user.saved_passwords:
            QMessageBox.information(self, "No Passwords", "You don't have any saved passwords.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("All Saved Passwords")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Create table for all passwords
        table = QTableWidget(len(self.current_user.saved_passwords), 3)
        table.setHorizontalHeaderLabels(["Website", "Username", "Password"])
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        
        for row, entry in enumerate(self.current_user.saved_passwords):
            website_item = QTableWidgetItem(entry.get("website", ""))
            username_item = QTableWidgetItem(entry.get("username", ""))
            password_item = QTableWidgetItem(entry.get("password", ""))
            
            # Make password visible in this view
            website_item.setFlags(website_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            username_item.setFlags(username_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            password_item.setFlags(password_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            table.setItem(row, 0, website_item)
            table.setItem(row, 1, username_item)
            table.setItem(row, 2, password_item)
        
        layout.addWidget(table)
        
        # Copy all button
        copy_all_btn = QPushButton("Copy All Passwords to Clipboard")
        copy_all_btn.clicked.connect(self.copy_all_passwords)
        layout.addWidget(copy_all_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def copy_all_passwords(self):
        """Copy all passwords to clipboard in a formatted way"""
        if not self.current_user or not self.current_user.saved_passwords:
            return
        
        clipboard_text = "Saved Passwords:\n" + "="*50 + "\n\n"
        
        for entry in self.current_user.saved_passwords:
            website = entry.get("website", "")
            username = entry.get("username", "")
            password = entry.get("password", "")
            
            clipboard_text += f"Website: {website}\n"
            clipboard_text += f"Username: {username}\n"
            clipboard_text += f"Password: {password}\n"
            clipboard_text += "-"*30 + "\n"
        
        QApplication.clipboard().setText(clipboard_text)
        QMessageBox.information(self, "Copied", "All passwords copied to clipboard!")
    
    # Admin functionality methods
    def manage_users(self):
        """Open the user management interface for admins"""
        if not self.current_user or not self.current_user.is_admin:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Users")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # User list table
        user_table = QTableWidget(0, 4)
        user_table.setHorizontalHeaderLabels(["Name", "Email", "Admin", "Actions"])
        user_table.horizontalHeader().setStretchLastSection(True)
        user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        user_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        layout.addWidget(user_table)
        
        # Load users into table
        users = list(self.user_manager.users.values())
        user_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            name_item = QTableWidgetItem(user.name)
            email_item = QTableWidgetItem(user.email)
            admin_item = QTableWidgetItem("Yes" if user.is_admin else "No")
            
            # Make items non-editable
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            email_item.setFlags(email_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            admin_item.setFlags(admin_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            
            user_table.setItem(row, 0, name_item)
            user_table.setItem(row, 1, email_item)
            user_table.setItem(row, 2, admin_item)
            
            # Action buttons
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(2)
            
            promote_btn = QPushButton("Promote")
            promote_btn.setFixedSize(60, 25)
            promote_btn.setEnabled(not user.is_admin)
            promote_btn.clicked.connect(lambda ch, u=user: self.promote_user(u))
            
            demote_btn = QPushButton("Demote")
            demote_btn.setFixedSize(60, 25)
            demote_btn.setEnabled(user.is_admin and user.email != self.current_user.email)  # Can't demote self
            demote_btn.clicked.connect(lambda ch, u=user: self.demote_user(u))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setFixedSize(60, 25)
            delete_btn.setEnabled(not user.is_admin)  # Can't delete admins
            delete_btn.clicked.connect(lambda ch, u=user: self.delete_user(u))
            
            actions_layout.addWidget(promote_btn)
            actions_layout.addWidget(demote_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            actions_widget = QWidget()
            actions_widget.setLayout(actions_layout)
            user_table.setCellWidget(row, 3, actions_widget)
        
        # Add new user button
        add_user_btn = QPushButton("Add New User")
        add_user_btn.clicked.connect(self.add_new_user)
        layout.addWidget(add_user_btn)
        
        dialog.exec()
    
    def promote_user(self, user):
        """Promote a user to admin"""
        if not self.current_user.is_admin:
            return
        
        user.is_admin = True
        self.user_manager.save_users()
        QMessageBox.information(self, "Success", f"{user.name} has been promoted to administrator.")
    
    def demote_user(self, user):
        """Demote an admin user to regular user"""
        if not self.current_user.is_admin:
            return
        
        if user.email == self.current_user.email:
            QMessageBox.warning(self, "Cannot Demote", "You cannot demote yourself.")
            return
        
        user.is_admin = False
        self.user_manager.save_users()
        QMessageBox.information(self, "Success", f"{user.name} has been demoted to regular user.")
    
    def delete_user(self, user):
        """Delete a user account"""
        if not self.current_user.is_admin:
            return
        
        if user.is_admin:
            QMessageBox.warning(self, "Cannot Delete", "You cannot delete administrator accounts.")
            return
        
        reply = QMessageBox.question(self, "Delete User", 
                                   f"Are you sure you want to delete {user.name} ({user.email})?\nThis action cannot be undone.",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # Delete profile picture if exists
            if user.avatar_path and os.path.exists(user.avatar_path):
                try:
                    os.remove(user.avatar_path)
                except:
                    pass
            
            # Remove user from user manager
            del self.user_manager.users[user.email]
            self.user_manager.save_users()
            
            QMessageBox.information(self, "Success", f"User {user.name} has been deleted.")
    
    def add_new_user(self):
        """Add a new user account"""
        if not self.current_user.is_admin:
            return
        
        email, ok = QInputDialog.getText(self, "Add User", "Enter email:")
        if ok and email:
            password, ok2 = QInputDialog.getText(self, "Add User", "Enter password:", QLineEdit.EchoMode.Password)
            if ok2 and password:
                name, ok3 = QInputDialog.getText(self, "Add User", "Enter name:")
                if ok3 and name:
                    success, message = self.user_manager.create_user(email, password, name)
                    if success:
                        QMessageBox.information(self, "Success", "User created successfully!")
                    else:
                        QMessageBox.warning(self, "Error", message)
    
    def show_system_info(self):
        """Show system information"""
        if not self.current_user or not self.current_user.is_admin:
            return
        
        import platform
        
        # Try to import psutil, but handle the case where it's not available
        try:
            import psutil
            cpu_info = f"{psutil.cpu_count()} cores"
            memory_info = f"{psutil.virtual_memory().total // (1024**3)} GB"
        except ImportError:
            cpu_info = "Unknown (psutil not available)"
            memory_info = "Unknown (psutil not available)"
        
        info = f"""
        <h3>System Information</h3>
        <b>Operating System:</b> {platform.system()} {platform.release()}<br>
        <b>Architecture:</b> {platform.architecture()[0]}<br>
        <b>Processor:</b> {platform.processor()}<br>
        <b>CPU Cores:</b> {cpu_info}<br>
        <b>Memory:</b> {memory_info}<br>
        <b>Python Version:</b> {platform.python_version()}<br>
        <b>PyQt6 Version:</b> {QApplication.version()}<br>
        <b>Pro_Browser Version:</b> ProBrowser<br>
        <b>Current User:</b> {self.current_user.name} ({self.current_user.email})<br>
        <b>User Type:</b> {'Administrator' if self.current_user.is_admin else 'Regular User'}<br>
        <b>Total Users:</b> {len(self.user_manager.users)}<br>
        <b>Admin Users:</b> {sum(1 for u in self.user_manager.users.values() if u.is_admin)}
        """
        
        QMessageBox.information(self, "System Information", info)
    
    def backup_user_data(self):
        """Backup all user data"""
        if not self.current_user or not self.current_user.is_admin:
            return
        
        backup_dir = QFileDialog.getExistingDirectory(self, "Select Backup Directory")
        if not backup_dir:
            return
        
        try:
            import shutil
            import datetime
            
            # Create backup filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"probrowser_backup_{timestamp}.json")
            
            # Copy users.json to backup location
            if os.path.exists("users.json"):
                shutil.copy2("users.json", backup_file)
                QMessageBox.information(self, "Backup Complete", f"User data backed up to:\n{backup_file}")
            else:
                QMessageBox.warning(self, "Backup Failed", "No user data found to backup.")
                
        except Exception as e:
            QMessageBox.warning(self, "Backup Failed", f"Failed to create backup: {str(e)}")
    
    def restore_user_data(self):
        """Restore user data from backup"""
        if not self.current_user or not self.current_user.is_admin:
            return
        
        backup_file, _ = QFileDialog.getOpenFileName(self, "Select Backup File", "", "JSON Files (*.json)")
        if not backup_file:
            return
        
        try:
            reply = QMessageBox.question(self, "Restore Data", 
                                       "This will replace all current user data. Continue?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                import shutil
                shutil.copy2(backup_file, "users.json")
                self.user_manager.load_users()
                QMessageBox.information(self, "Restore Complete", "User data has been restored.")
                
        except Exception as e:
            QMessageBox.warning(self, "Restore Failed", f"Failed to restore data: {str(e)}")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application icon for the entire application with enhanced Linux compatibility
    icon_path = os.path.join(os.path.dirname(__file__), "Pro_Browsericon.pngnonereziezd-ezgif.com-resize.png")
    print(f"Looking for icon at: {icon_path}")
    print(f"Icon file exists: {os.path.exists(icon_path)}")
    
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        print(f"Icon loaded successfully: {not app_icon.isNull()}")
        
        if not app_icon.isNull():
            # Method 1: Set at application level (most important)
            app.setWindowIcon(app_icon)
            print("Application icon set successfully")
            
            # Method 2: Set application properties for Linux desktop environments
            app.setApplicationName("Pro_Browser")
            app.setApplicationDisplayName("Pro_Browser")
            app.setOrganizationName("ProBrowserCorp")
            app.setOrganizationDomain("probrowser.corp")
            
            # Method 3: Set desktop file name hint for Linux (helps with taskbar integration)
            app.setDesktopFileName("Pro_Browser")
            
            # Method 4: Force icon update for Linux desktop environments
            # This helps ensure the icon is properly recognized by the window manager
            app.processEvents()
        else:
            print("Icon file exists but failed to load properly")
    else:
        print("Icon file not found")
    win = ProBrowser()
    win.show()
    sys.exit(app.exec())