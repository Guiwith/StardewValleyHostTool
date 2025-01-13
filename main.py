import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from main_window import MainWindow

def main():
    # Windows 特定的应用程序 ID
    if sys.platform == 'win32':
        myappid = 'nutt.stardewvalley.hostswap.1.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    
    app = QApplication(sys.argv)
    
    # 获取图标文件的绝对路径
    icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icons', 'icon.png')
    
    # 设置应用程序图标
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

