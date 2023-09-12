import sys
import boto3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog,
                             QListWidget, QVBoxLayout, QWidget, QComboBox, QLabel, QSpacerItem, QSizePolicy)
import qtmodern.styles
import qtmodern.windows
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox

s3 = boto3.client('s3')


class AutoCloseMessageBox(QMessageBox):
    def __init__(self, timeout=3, parent=None):
        super().__init__(parent)
        self.timeout = timeout
        self.setStyleSheet("QLabel{min-width: 200px;}")

    def showEvent(self, event):
        QTimer.singleShot(self.timeout * 1000, self.accept)
        super().showEvent(event)


class S3Client(QMainWindow):
    def __init__(self):
        super().__init__()
        self.listWidget = None
        self.downloadBtn = None
        self.generateLinkBtn = None
        self.uploadBtn = None
        self.bucketComboBox = None
        self.bucketLabel = None
        self.themeToggleBtn = None
        self.buckets = None
        self.dark_mode = False  # 初始为亮色模式
        self.initUI()

    def initUI(self):
        self.setWindowTitle('S3 Client with PyQt')
        layout = QVBoxLayout()

        # 添加切换主题的按钮
        self.themeToggleBtn = QPushButton('Switch to Dark Mode', self)
        self.themeToggleBtn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.themeToggleBtn)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        # Bucket选择
        self.bucketLabel = QLabel('Select Bucket:')
        self.bucketComboBox = QComboBox()
        self.update_bucket_list()
        self.bucketComboBox.currentTextChanged.connect(self.list_files_in_bucket)
        layout.addWidget(self.bucketLabel)
        layout.addWidget(self.bucketComboBox)

        # 文件列表
        self.listWidget = QListWidget()
        layout.addWidget(self.listWidget)

        # 上传按钮
        self.uploadBtn = QPushButton('Upload File', self)
        self.uploadBtn.clicked.connect(self.upload_file)
        layout.addWidget(self.uploadBtn)

        # 下载按钮
        self.downloadBtn = QPushButton('Download File', self)
        self.downloadBtn.clicked.connect(self.download_file)
        layout.addWidget(self.downloadBtn)

        # 删除文件按钮
        self.deleteBtn = QPushButton('Delete File', self)
        self.deleteBtn.clicked.connect(self.delete_file)
        layout.addWidget(self.deleteBtn)

        # 预签名URL按钮
        self.generateLinkBtn = QPushButton('Generate Pre-Signed URL', self)
        self.generateLinkBtn.clicked.connect(self.generate_presigned_url)
        layout.addWidget(self.generateLinkBtn)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def update_bucket_list(self):
        self.buckets = [bucket['Name'] for bucket in s3.list_buckets()['Buckets']]
        self.bucketComboBox.addItems(self.buckets)
        # self.list_files_in_bucket()  # 手动列出第一个存储桶的文件

    def toggle_theme(self):
        if self.dark_mode:
            qtmodern.styles.light(app)
            self.themeToggleBtn.setText('Switch to Dark Mode')
        else:
            qtmodern.styles.dark(app)
            self.themeToggleBtn.setText('Switch to Light Mode')
        self.dark_mode = not self.dark_mode

    def list_files_in_bucket(self):
        bucket_name = self.bucketComboBox.currentText()
        self.listWidget.clear()
        try:
            response = s3.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in response:
                files = [item['Key'] for item in response['Contents']]
                self.listWidget.addItems(files)
            else:
                self.listWidget.addItem("No files in the bucket!")
        except Exception as e:
            self.listWidget.addItem(f"Error: {str(e)}")

    def upload_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, 'Select File to Upload')
        if filepath:
            try:
                file_name = filepath.split("/")[-1]
                with open(filepath, 'rb') as file:
                    s3.upload_fileobj(file, self.bucketComboBox.currentText(), file_name)
                self.list_files_in_bucket()
            except Exception as e:
                self.listWidget.addItem(f"Error: {str(e)}")

    def download_file(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Select where to save the file')
        selected_item = self.listWidget.currentItem()
        if file_name and selected_item:
            try:
                s3.download_file(self.bucketComboBox.currentText(), selected_item.text(), file_name)
            except Exception as e:
                self.listWidget.addItem(f"Error: {str(e)}")

    def generate_presigned_url(self):
        selected_item = self.listWidget.currentItem()
        print(f"1{self.bucketComboBox.currentText()}2,1{selected_item.text()}123")
        if selected_item:
            try:
                url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucketComboBox.currentText(), 'Key': selected_item.text()},
                    ExpiresIn=3600
                )
                self.listWidget.addItem(f"Generated URL: {url}")

                # Copy URL to clipboard
                clipboard = QApplication.clipboard()
                clipboard.setText(url)

                # Show auto-close message box
                msg = AutoCloseMessageBox(timeout=1)  # the number is the time in seconds after which the box will close
                msg.setIcon(QMessageBox.Information)
                msg.setText("URL copied to clipboard!")
                msg.setWindowTitle("Success")
                msg.exec_()

            except Exception as e:
                self.listWidget.addItem(f"Error: {str(e)}")

    def delete_file(self):
        selected_item = self.listWidget.currentItem()
        if selected_item:
            msgbox = QMessageBox()
            msgbox.setWindowTitle("Delete Confirmation")
            msgbox.setIcon(QMessageBox.Warning)
            msgbox.setText(f"Are you sure you want to delete {selected_item.text()}?")
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msgbox.setDefaultButton(QMessageBox.No)
            reply = msgbox.exec_()
            if reply == QMessageBox.Yes:
                try:
                    s3.delete_object(Bucket=self.bucketComboBox.currentText(), Key=selected_item.text())
                    self.listWidget.removeItemWidget(selected_item)
                    del selected_item
                    # 重新列出桶中的文件
                    self.list_files_in_bucket()
                except Exception as e:
                    self.listWidget.addItem(f"Error: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = S3Client()
    modern_window = qtmodern.windows.ModernWindow(window)
    modern_window.show()
    sys.exit(app.exec_())