import os
import sys
import boto3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog,
                             QListWidget, QVBoxLayout, QWidget, QComboBox, QLabel, QSpacerItem, QSizePolicy)
import qtmodern.styles
import qtmodern.windows
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QGridLayout

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
        self.uploadFolderBtn = None
        self.deleteBucketBtn = None
        self.showBucketPolicyBtn = None
        self.deleteBtn = None
        self.createBucketBtn = None
        self.showVersioningBtn = None
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
        # 主布局
        layout = QVBoxLayout()

        # 添加切换主题的按钮
        self.themeToggleBtn = QPushButton('Switch to Dark Mode', self)
        self.themeToggleBtn.clicked.connect(self.toggle_theme)
        layout.addWidget(self.themeToggleBtn)

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

        # 使用QGridLayout来布局按钮
        btnGrid = QGridLayout()

        # 上传按钮
        self.uploadBtn = QPushButton('Upload File', self)
        self.uploadBtn.clicked.connect(self.upload_file)
        # btnGrid.addWidget(self.uploadBtn, 0, 0)  # 第一行第一列

        # 下载按钮
        self.downloadBtn = QPushButton('Download File', self)
        self.downloadBtn.clicked.connect(self.download_file)
        # btnGrid.addWidget(self.downloadBtn, 0, 1)  # 第一行第二列

        # 删除文件按钮
        self.deleteBtn = QPushButton('Delete File', self)
        self.deleteBtn.clicked.connect(self.delete_file)
        # btnGrid.addWidget(self.deleteBtn, 0, 2)  # 第一行第三列

        # 预签名URL按钮
        self.generateLinkBtn = QPushButton('Generate Pre-Signed URL', self)
        self.generateLinkBtn.clicked.connect(self.generate_presigned_url)
        # btnGrid.addWidget(self.generateLinkBtn, 0, 3)  # 第一行第四列

        # Show Bucket Policy Button
        self.showBucketPolicyBtn = QPushButton('Show Bucket Policy', self)
        self.showBucketPolicyBtn.clicked.connect(self.show_bucket_policy)
        # btnGrid.addWidget(self.showBucketPolicyBtn, 1, 0)  # 第二行第一列

        # Show Versioning Button
        self.showVersioningBtn = QPushButton('Show Versioning', self)
        self.showVersioningBtn.clicked.connect(self.show_versioning)
        # btnGrid.addWidget(self.showVersioningBtn, 1, 1)  # 第二行第二列

        # Create Bucket Button
        self.createBucketBtn = QPushButton('Create New Bucket', self)
        self.createBucketBtn.clicked.connect(self.create_bucket)
        # btnGrid.addWidget(self.createBucketBtn, 1, 2)  # 第二行第三列

        # Delete Bucket Button
        self.deleteBucketBtn = QPushButton('Delete Selected Bucket', self)
        self.deleteBucketBtn.clicked.connect(self.delete_bucket)
        # btnGrid.addWidget(self.deleteBucketBtn, 1, 3)  # 第二行第四列

        # 上传文件夹按钮
        self.uploadFolderBtn = QPushButton('Upload Folder', self)
        self.uploadFolderBtn.clicked.connect(self.upload_folder)
        # btnGrid.addWidget(self.uploadFolderBtn, 2, 0)  # 第三行第一列

        # 下载文件夹按钮
        self.downloadFolderBtn = QPushButton('Download Folder', self)
        self.downloadFolderBtn.clicked.connect(self.download_folder)
        # btnGrid.addWidget(self.downloadFolderBtn, 2, 1)  # 第三行第二列

        # 编辑桶策略按钮
        self.editBucketPolicyBtn = QPushButton('Edit Bucket Policy', self)
        self.editBucketPolicyBtn.clicked.connect(self.edit_bucket_policy)
        # btnGrid.addWidget(self.editBucketPolicyBtn, 2, 2)  # 第三行第三列

        # 开启静态网站按钮
        self.enableStaticWebsiteBtn = QPushButton('Enable Static Website', self)
        self.enableStaticWebsiteBtn.clicked.connect(self.enable_static_website)
        # btnGrid.addWidget(self.enableStaticWebsiteBtn, 2, 3)  # 第三行第四列

        self.emptyBucketBtn = QPushButton('Empty Bucket', self)
        self.emptyBucketBtn.clicked.connect(self.empty_bucket)
        # btnGrid.addWidget(self.emptyBucketBtn, 3, 0)  # 第三行第一列
        buttons = [
            [self.uploadBtn, self.downloadBtn, self.deleteBtn, self.generateLinkBtn],
            [self.showBucketPolicyBtn, self.showVersioningBtn, self.createBucketBtn, self.deleteBucketBtn],
            [self.uploadFolderBtn, self.downloadFolderBtn, self.editBucketPolicyBtn, self.enableStaticWebsiteBtn],
            [self.emptyBucketBtn, None, None, None]  # 您的emptyBucketBtn是第四行第一列，其余位置没有按钮
        ]

        for x, row in enumerate(buttons):
            for y, button in enumerate(row):
                if button:  # 检查是否真的有按钮要添加
                    btnGrid.addWidget(button, x, y)
        # 将网格布局添加到主布局
        layout.addLayout(btnGrid)

        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        # 应用QSS样式
        self.apply_modern_style()

    def apply_modern_style(self):
        style_sheet = """
            /* 基本设置 */
            QWidget {
                font: 14px 'Segoe UI';
                color: #333;
            }

            QMainWindow, QDialog {
                background: #fafafa;
                padding: 10px;
                border-radius: 5px;
            }

            /* 设定按钮的样式 */
            QPushButton {
                background: #4CAF50;  /* 绿色 */
                border: none;
                padding: 10px 20px;
                text-align: center;
                border-radius: 4px;
                transition: 0.3s;
                box-shadow: 2px 2px 15px rgba(0, 0, 0, 0.1);
            }

            QPushButton:hover {
                background: #45a049;  /* 深绿色 */
                transform: scale(1.05);  /* 稍微放大 */
            }

            QPushButton:pressed {
                background: #388e3c;  /* 更深的绿色 */
                box-shadow: 1px 1px 5px rgba(0, 0, 0, 0.2);
                transform: scale(1.0);  /* 返回原始大小 */
            }

            /* 设定组合框样式 */
            QComboBox {
                padding: 5px;
                border: 2px solid #4CAF50;
                border-radius: 4px;
                background-color: #ffffff;
                selection-background-color: #4CAF50;
                box-shadow: 2px 2px 15px rgba(0, 0, 0, 0.1);
            }

            QComboBox::drop-down {
                border: none;
            }

            /* 设定列表部件样式 */
            QListWidget {
                border: 2px solid #4CAF50;
                border-radius: 4px;
                background-color: #ffffff;
                alternate-background-color: #f0f0f0;
                box-shadow: 2px 2px 15px rgba(0, 0, 0, 0.1);
            }

            /* 设置标签样式 */
            QLabel {
                color: #333;
                background-color: #ffffff;
                padding: 3px;
                border-radius: 4px;
                box-shadow: 2px 2px 15px rgba(0, 0, 0, 0.1);
            }
        """

        self.setStyleSheet(style_sheet)

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

    def show_bucket_policy(self):
        try:
            bucket_name = self.bucketComboBox.currentText()
            policy = s3.get_bucket_policy(Bucket=bucket_name)
            self.listWidget.addItem(f"Policy for {bucket_name}: {policy['Policy']}")
        except Exception as e:
            self.listWidget.addItem(f"Error fetching policy: {str(e)}")

    def show_versioning(self):
        try:
            bucket_name = self.bucketComboBox.currentText()
            versioning = s3.get_bucket_versioning(Bucket=bucket_name)
            status = versioning.get('Status', 'Not enabled')
            self.listWidget.addItem(f"Versioning for {bucket_name}: {status}")
        except Exception as e:
            self.listWidget.addItem(f"Error fetching versioning: {str(e)}")

    def create_bucket(self):
        bucket_name, ok = QInputDialog.getText(self, 'Create Bucket', 'Enter new bucket name:')
        if ok and bucket_name:
            try:
                s3.create_bucket(Bucket=bucket_name)
                self.update_bucket_list()
                self.listWidget.addItem(f"Bucket {bucket_name} created successfully!")
            except Exception as e:
                self.listWidget.addItem(f"Error creating bucket: {str(e)}")

    def delete_bucket(self):
        bucket_name = self.bucketComboBox.currentText()
        msgbox = QMessageBox()
        msgbox.setWindowTitle("Delete Bucket Confirmation")
        msgbox.setIcon(QMessageBox.Warning)
        msgbox.setText(f"Are you sure you want to delete the bucket: {bucket_name}?")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        reply = msgbox.exec_()
        if reply == QMessageBox.Yes:
            try:
                s3.delete_bucket(Bucket=bucket_name)
                self.update_bucket_list()
                self.listWidget.addItem(f"Bucket {bucket_name} deleted successfully!")
            except Exception as e:
                self.listWidget.addItem(f"Error deleting bucket: {str(e)}")

    def upload_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder to Upload')
        if folder_path:
            folder_name = os.path.basename(folder_path)  # 获取文件夹的名字
            try:
                for dirpath, _, filenames in os.walk(folder_path):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        relative_path = os.path.relpath(filepath, folder_path)
                        s3_key = os.path.join(folder_name, relative_path)
                        with open(filepath, 'rb') as file:
                            s3.upload_fileobj(file, self.bucketComboBox.currentText(), s3_key)
                self.list_files_in_bucket()
            except Exception as e:
                self.listWidget.addItem(f"Error: {str(e)}")

    def download_folder_contents(self, bucket_name, prefix, local_folder):
        try:
            results = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if 'Contents' in results:
                for item in results['Contents']:
                    key = item['Key']
                    if not key.endswith('/'):  # skip directories
                        local_file_path = os.path.join(local_folder, os.path.relpath(key, prefix))
                        local_file_dir = os.path.dirname(local_file_path)
                        os.makedirs(local_file_dir, exist_ok=True)
                        s3.download_file(bucket_name, key, local_file_path)
        except Exception as e:
            self.listWidget.addItem(f"Error: {str(e)}")

    def download_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Select where to save the folder contents')
        selected_item = self.listWidget.currentItem()
        if folder_path and selected_item:
            self.download_folder_contents(self.bucketComboBox.currentText(), selected_item.text(), folder_path)

    def edit_bucket_policy(self):
        bucket_name = self.bucketComboBox.currentText()
        try:
            current_policy = s3.get_bucket_policy(Bucket=bucket_name)['Policy']
        except:
            current_policy = "{}"

        new_policy, ok = QInputDialog.getMultiLineText(self, 'Edit Bucket Policy', 'Policy:', current_policy)
        if ok:
            s3.put_bucket_policy(Bucket=bucket_name, Policy=new_policy)

    def enable_static_website(self):
        bucket_name = self.bucketComboBox.currentText()
        index_doc = 'index.html'
        error_doc = 'error.html'

        s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration={
                'ErrorDocument': {'Key': error_doc},
                'IndexDocument': {'Suffix': index_doc},
            }
        )

    def empty_bucket(self):
        bucket_name = self.bucketComboBox.currentText()
        msgbox = QMessageBox()
        msgbox.setWindowTitle("Empty Bucket Confirmation")
        msgbox.setIcon(QMessageBox.Warning)
        msgbox.setText(
            f"Are you sure you want to empty the bucket: {bucket_name}? All files and folders will be deleted!")
        msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msgbox.setDefaultButton(QMessageBox.No)
        reply = msgbox.exec_()

        if reply == QMessageBox.Yes:
            try:
                # Keep deleting until all objects are gone
                while True:
                    objects_to_delete = s3.list_objects_v2(Bucket=bucket_name)
                    if 'Contents' in objects_to_delete:
                        objects = [{'Key': obj['Key']} for obj in objects_to_delete['Contents']]
                        s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects})
                    else:
                        break  # No more objects to delete

                self.listWidget.addItem(f"Bucket {bucket_name} emptied successfully!")
                self.list_files_in_bucket()
            except Exception as e:
                self.listWidget.addItem(f"Error emptying bucket: {str(e)}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = S3Client()
    modern_window = qtmodern.windows.ModernWindow(window)
    modern_window.show()
    sys.exit(app.exec_())
