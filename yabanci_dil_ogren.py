import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QWidget, QTabWidget, QMessageBox, QAction, QInputDialog, QListWidget, QListWidgetItem, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt

class KelimeBilgisiSekmesi(QWidget):
    def __init__(self, db_conn, parent=None):
        super(KelimeBilgisiSekmesi, self).__init__(parent)
        
        self.db_conn = db_conn
        self.initUI()
        self.load_words()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        self.word_list = QListWidget(self)
        self.word_list.itemDoubleClicked.connect(self.edit_word)
        layout.addWidget(self.word_list)
        
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Kelime Ekle", self)
        self.add_button.setFixedSize(100, 40)
        self.add_button.setStyleSheet("font-size: 18px;")
        self.add_button.clicked.connect(self.add_word)
        button_layout.addWidget(self.add_button, alignment=Qt.AlignCenter)
        
        self.delete_button = QPushButton("Kelime Sil", self)
        self.delete_button.setFixedSize(100, 40)
        self.delete_button.setStyleSheet("font-size: 18px;")
        self.delete_button.clicked.connect(self.delete_word)
        button_layout.addWidget(self.delete_button, alignment=Qt.AlignCenter)

        self.study_button = QPushButton("Çalış", self)
        self.study_button.setFixedSize(100, 40)
        self.study_button.setStyleSheet("font-size: 18px;")
        self.study_button.clicked.connect(self.study_words)
        button_layout.addWidget(self.study_button, alignment=Qt.AlignCenter)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def add_word(self):
        word, ok1 = QInputDialog.getText(self, "Yeni Kelime", "Kelime:")
        if ok1 and word:
            meaning, ok2 = QInputDialog.getText(self, "Yeni Kelime", "Anlamı:")
            if ok2 and meaning:
                word_entry = f"{word} - {meaning}"
                list_item = QListWidgetItem(word_entry)
                self.word_list.addItem(list_item)
                self.save_word_to_db(word, meaning)
    
    def edit_word(self, item):
        word_entry = item.text().split(' - ')
        word = word_entry[0]
        meaning = word_entry[1]
        
        new_word, ok1 = QInputDialog.getText(self, "Kelimeyi Düzenle", "Kelime:", text=word)
        if ok1 and new_word:
            new_meaning, ok2 = QInputDialog.getText(self, "Kelimeyi Düzenle", "Anlamı:", text=meaning)
            if ok2 and new_meaning:
                new_word_entry = f"{new_word} - {new_meaning}"
                item.setText(new_word_entry)
                self.update_word_in_db(word, meaning, new_word, new_meaning)
    
    def delete_word(self):
        selected_item = self.word_list.currentItem()
        if selected_item:
            reply = QMessageBox.question(self, 'Silme Onayı', 'Bu kelimeyi silmek istediğinize emin misiniz?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                word_entry = selected_item.text().split(' - ')
                word = word_entry[0]
                meaning = word_entry[1]
                self.remove_word_from_db(word, meaning)
                self.word_list.takeItem(self.word_list.currentRow())

    def load_words(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT word, meaning FROM words")
        rows = cursor.fetchall()
        for row in rows:
            word, meaning = row
            word_entry = f"{word} - {meaning}"
            list_item = QListWidgetItem(word_entry)
            self.word_list.addItem(list_item)
    
    def save_word_to_db(self, word, meaning):
        cursor = self.db_conn.cursor()
        cursor.execute("INSERT INTO words (word, meaning) VALUES (?, ?)", (word, meaning))
        self.db_conn.commit()
    
    def update_word_in_db(self, old_word, old_meaning, new_word, new_meaning):
        cursor = self.db_conn.cursor()
        cursor.execute("UPDATE words SET word = ?, meaning = ? WHERE word = ? AND meaning = ?", (new_word, new_meaning, old_word, old_meaning))
        self.db_conn.commit()
    
    def remove_word_from_db(self, word, meaning):
        cursor = self.db_conn.cursor()
        cursor.execute("DELETE FROM words WHERE word = ? AND meaning = ?", (word, meaning))
        self.db_conn.commit()

    def study_words(self):
        self.study_window = StudyWindow(self.db_conn)
        self.study_window.show()

class StudyWindow(QWidget):
    def __init__(self, db_conn, parent=None):
        super(StudyWindow, self).__init__(parent)
        
        self.db_conn = db_conn
        self.initUI()
        self.load_words()
    
    def initUI(self):
        self.setWindowTitle('Kelime Çalışma')
        self.setGeometry(150, 150, 400, 300)
        
        layout = QVBoxLayout()
        
        self.word_label = QLabel("", self)
        self.word_label.setAlignment(Qt.AlignCenter)
        self.word_label.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.word_label)
        
        button_layout = QHBoxLayout()
        
        self.show_meaning_button = QPushButton("Anlamı Göster", self)
        self.show_meaning_button.setFixedSize(150, 40)
        self.show_meaning_button.setStyleSheet("font-size: 18px;")
        self.show_meaning_button.clicked.connect(self.show_meaning)
        button_layout.addWidget(self.show_meaning_button, alignment=Qt.AlignCenter)
        
        self.next_word_button = QPushButton("Sonraki Kelime", self)
        self.next_word_button.setFixedSize(150, 40)
        self.next_word_button.setStyleSheet("font-size: 18px;")
        self.next_word_button.clicked.connect(self.next_word)
        button_layout.addWidget(self.next_word_button, alignment=Qt.AlignCenter)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.words = []
        self.current_word_index = -1
    
    def load_words(self):
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT word, meaning FROM words")
        self.words = cursor.fetchall()
        self.next_word()
    
    def show_meaning(self):
        if self.current_word_index >= 0:
            self.word_label.setText(self.words[self.current_word_index][1])
    
    def next_word(self):
        self.current_word_index = (self.current_word_index + 1) % len(self.words)
        self.word_label.setText(self.words[self.current_word_index][0])

class DilOgrenmeUygulamasi(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.db_conn = sqlite3.connect("dil_ogrenme.db")
        self.init_db()
        self.initUI()
    
    def init_db(self):
        cursor = self.db_conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                meaning TEXT NOT NULL
            )
        """)
        self.db_conn.commit()
    
    def initUI(self):
        self.setWindowTitle('Dil Öğrenme Uygulaması')
        self.setGeometry(100, 100, 600, 400)
        
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)
        
        self.kelime_bilgisi_sekmesi = KelimeBilgisiSekmesi(self.db_conn)
        self.tab_widget.addTab(self.kelime_bilgisi_sekmesi, "Kelime Bilgisi")
        
        menubar = self.menuBar()
        dosya_menu = menubar.addMenu('Dosya')
        
        cikis_action = QAction("Çıkış", self)
        cikis_action.setShortcut("Ctrl+Q")
        cikis_action.triggered.connect(self.close)
        dosya_menu.addAction(cikis_action)
        
        # QSS stili uygula
        self.setStyleSheet(self.qss_stili())
        
        self.show()
    
    def qss_stili(self):
        return """
        QMainWindow {
            background-color: #f0f0f0;
        }
        QTabWidget::pane {
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        QTabBar::tab {
            background: #ddd;
            border: 1px solid #ccc;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            padding: 5px;
            margin-right: 1px;
        }
        QTabBar::tab:selected {
            background: #f0f0f0;
            border-color: #999;
        }
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3e8e41;
        }
        QListWidget {
            font-size: 16px;
        }
        QLabel {
            font-size: 24px;
        }
        """
    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    dil_ogrenme_uygulamasi = DilOgrenmeUygulamasi()
    sys.exit(app.exec_())
