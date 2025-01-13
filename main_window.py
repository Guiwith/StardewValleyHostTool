from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                            QListWidget, QListWidgetItem, QMessageBox, QFileDialog)
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtCore import Qt
from file_handler import SaveFileHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.save_handler = SaveFileHandler()
        
        # 显示欢迎提示
        self.show_welcome_message()
        
        # 初始化UI
        self.init_ui()

    def init_ui(self):
        """初始化UI"""
        # 设置窗口标题和大小
        self.setWindowTitle('星露谷物语房主切换工具')
        self.setGeometry(300, 300, 500, 400)

        # 创建中心部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建玩家列表
        self.player_list = QListWidget()
        layout.addWidget(self.player_list)

        # 创建按钮
        load_button = QPushButton('选择存档')
        load_button.clicked.connect(self.load_save)
        layout.addWidget(load_button)

        swap_button = QPushButton('设为房主')
        swap_button.clicked.connect(self.swap_host)
        layout.addWidget(swap_button)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QListWidget {
                border: 1px solid #dcdde1;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
                font-family: 'Microsoft YaHei';
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)

    def show_welcome_message(self):
        """显示欢迎提示窗口"""
        msg = QMessageBox(self)
        msg.setWindowTitle('欢迎使用')
        msg.setText('换房主工具由nutt开源，感谢使用，禁止售卖。')
        msg.setIcon(QMessageBox.Information)
        
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
                font-size: 14px;
                font-family: 'Microsoft YaHei';
                padding: 10px;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                min-width: 80px;
                font-family: 'Microsoft YaHei';
            }
            QPushButton:hover {
                background-color: #357abd;
            }
        """)
        
        msg.exec_()

    def update_player_list(self):
        """更新玩家列表显示"""
        self.player_list.clear()
        
        if not self.save_handler.save_game_data:
            return
            
        # 添加房主
        if self.save_handler.save_game_data.host:
            host_item = QListWidgetItem()
            host_item.setText(f'房主: {self.save_handler.save_game_data.host.name}')
            host_item.setData(Qt.UserRole, self.save_handler.save_game_data.host)
            # 设置房主项的样式
            host_item.setForeground(QColor('#4a90e2'))
            font = host_item.font()
            font.setBold(True)
            host_item.setFont(font)
            self.player_list.addItem(host_item)
        
        # 添加其他玩家
        for player in self.save_handler.save_game_data.farmhands:
            player_item = QListWidgetItem()
            player_item.setText(f'玩家: {player.name}')
            player_item.setData(Qt.UserRole, player)
            self.player_list.addItem(player_item)

    def load_save(self):
        """加载存档"""
        try:
            folder = QFileDialog.getExistingDirectory(self, '选择存档文件夹')
            if folder:
                self.save_handler.read_save_files(folder)
                self.update_player_list()
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'加载存档失败：{str(e)}')

    def swap_host(self):
        """交换房主"""
        try:
            # 获取选中的新房主
            selected_items = self.player_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, '错误', '请先选择一个玩家')
                return
                
            selected_player = selected_items[0].data(Qt.UserRole)
            if not selected_player:
                return
                
            # 执行房主交换
            if self.save_handler.swap_host(selected_player.unique_id):
                QMessageBox.information(self, '成功', '房主已成功更换')
                
                # 重新加载存档数据
                self.save_handler.read_save_files(self.save_handler.save_game_data.save_path)
                
                # 更新界面显示
                self.update_player_list()
                
            else:
                QMessageBox.warning(self, '错误', '房主更换失败')
                
        except Exception as e:
            QMessageBox.critical(self, '错误', f'发生错误：{str(e)}') 