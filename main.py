import os
import sys

from PyQt5 import QtWidgets

from s3_pyclient import S3Client as s3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog,
                             QListWidget, QVBoxLayout, QWidget, QComboBox, QLabel)
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QGridLayout
from qt_material import apply_stylesheet, QtStyleTools
from qt_ui import AutoCloseMessageBox


class S3ClientUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.editBucketPolicyBtn = None
        self.enableStaticWebsiteBtn = None
        self.emptyBucketBtn = None
        self.downloadFolderBtn = None
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

        # 下载按钮
        self.downloadBtn = QPushButton('Download File', self)
        self.downloadBtn.clicked.connect(self.download_file)

        # 删除文件按钮
        self.deleteBtn = QPushButton('Delete File', self)
        self.deleteBtn.clicked.connect(self.delete_file)

        # 预签名URL按钮
        self.generateLinkBtn = QPushButton('Generate Pre-Signed URL', self)
        self.generateLinkBtn.clicked.connect(self.generate_presigned_url)

        # Show Bucket Policy Button
        self.showBucketPolicyBtn = QPushButton('Show Bucket Policy', self)
        self.showBucketPolicyBtn.clicked.connect(self.show_bucket_policy)

        # Show Versioning Button
        self.showVersioningBtn = QPushButton('Show Versioning', self)
        self.showVersioningBtn.clicked.connect(self.show_versioning)

        # Create Bucket Button
        self.createBucketBtn = QPushButton('Create New Bucket', self)
        self.createBucketBtn.clicked.connect(self.create_bucket)

        # Delete Bucket Button
        self.deleteBucketBtn = QPushButton('Delete Selected Bucket', self)
        self.deleteBucketBtn.clicked.connect(self.delete_bucket)

        # 上传文件夹按钮
        self.uploadFolderBtn = QPushButton('Upload Folder', self)
        self.uploadFolderBtn.clicked.connect(self.upload_folder)

        # 下载文件夹按钮
        self.downloadFolderBtn = QPushButton('Download Folder', self)
        self.downloadFolderBtn.clicked.connect(self.download_folder)

        # 编辑桶策略按钮
        self.editBucketPolicyBtn = QPushButton('Edit Bucket Policy', self)
        self.editBucketPolicyBtn.clicked.connect(self.edit_bucket_policy)

        # 开启静态网站按钮
        self.enableStaticWebsiteBtn = QPushButton('Enable Static Website', self)
        self.enableStaticWebsiteBtn.clicked.connect(self.enable_static_website)

        self.emptyBucketBtn = QPushButton('Empty Bucket', self)
        self.emptyBucketBtn.clicked.connect(self.empty_bucket)

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

        # 启用拖放
        self.listWidget.setAcceptDrops(True)
        self.listWidget.viewport().setAcceptDrops(True)
        self.listWidget.setDragDropMode(QtWidgets.QAbstractItemView.DropOnly)
        self.listWidget.dragEnterEvent = self.dragEnterEvent
        self.listWidget.dropEvent = self.dropEvent

        # 定义拖放事件

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if len(urls) == 1:
            filepath = urls[0].toLocalFile()

            # 如果是文件则上传，如果是目录则询问用户是否要上传整个目录
            if os.path.isfile(filepath):
                self.upload_file(filepath)
            elif os.path.isdir(filepath):
                msgbox = QMessageBox()
                msgbox.setWindowTitle("Upload Folder")
                msgbox.setIcon(QMessageBox.Question)
                msgbox.setText(f"Do you want to upload the entire folder: {filepath}?")
                msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msgbox.setDefaultButton(QMessageBox.Yes)
                reply = msgbox.exec_()
                if reply == QMessageBox.Yes:
                    self.upload_folder(filepath)
        else:
            # 如果拖入多个文件/目录，目前不处理，但您可以扩展此功能以支持批量上传。
            pass

    def update_bucket_list(self):
        self.buckets = [bucket['Name'] for bucket in s3.list_buckets()['Buckets']]
        self.bucketComboBox.addItems(self.buckets)

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

    def upload_file(self, filepath=None):
        if not filepath:
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

    def upload_folder(self, folder_path=None):
        if not folder_path:
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
        s3.put_bucket_website(Bucket=self.bucketComboBox.currentText())

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
    app = QtWidgets.QApplication(sys.argv)
    window = S3ClientUI()
    apply_stylesheet(app, theme='light_amber.xml', invert_secondary=True)
    window.show()
    app.exec_()
