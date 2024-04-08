import sys
import os
import re
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QScrollArea, QShortcut, QMessageBox, QHBoxLayout
from PyQt5.QtGui import QIcon, QKeySequence
import PyQt5.QtCore as QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
import subprocess
from googletrans import Translator
translator = Translator()
import pypinyin

PinyinToneMark = {
    0: "aoeiuv\u00fc",
    1: "\u0101\u014d\u0113\u012b\u016b\u01d6\u01d6",
    2: "\u00e1\u00f3\u00e9\u00ed\u00fa\u01d8\u01d8",
    3: "\u01ce\u01d2\u011b\u01d0\u01d4\u01da\u01da",
    4: "\u00e0\u00f2\u00e8\u00ec\u00f9\u01dc\u01dc",
}

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cedict_ts.u8'), "r", encoding="utf-8") as file:
    cedict = file.readlines()

def decode_pinyin(total):
    final = []
    for pinyin in total.split(" "):
        s = pinyin.lower()
        r = ""
        t = ""
        for c in s:
            if c >= 'a' and c <= 'z':
                t += c
            elif c == ':':
                assert t[-1] == 'u'
                t = t[:-1] + "\u00fc"
            else:
                if c >= '0' and c <= '5':
                    tone = int(c) % 5
                    if tone != 0:
                        m = re.search("[aoeiuv\u00fc]+", t)
                        if m is None:
                            t += c
                        elif len(m.group(0)) == 1:
                            t = t[:m.start(0)] + PinyinToneMark[tone][PinyinToneMark[0].index(m.group(0))] + t[m.end(0):]
                        else:
                            if 'a' in t:
                                t = t.replace("a", PinyinToneMark[tone][0])
                            elif 'o' in t:
                                t = t.replace("o", PinyinToneMark[tone][1])
                            elif 'e' in t:
                                t = t.replace("e", PinyinToneMark[tone][2])
                            elif t.endswith("ui"):
                                t = t.replace("i", PinyinToneMark[tone][3])
                            elif t.endswith("iu"):
                                t = t.replace("u", PinyinToneMark[tone][4])
                            else:
                                t += "!"
                r += t
                t = ""
        r += t
        final.append(r)
    return ' '.join(final)


def modify(total):
    new = []
    for result in total.split("\n"):
        first_space_index = result.find(' ')
        if first_space_index != -1:
            result = result[first_space_index + 1:]        
        start_index = result.find('[')
        end_index = result.find(']')
        
        first_part = result[:start_index].strip()
        middle_part = result[start_index+1:end_index].strip()
        last_part = result[end_index+1:].strip()

        middle_part = decode_pinyin(middle_part)

        result_list = [first_part, middle_part, last_part]
        new.append(' '.join(result_list))

    return '\n'.join(new)


class ChineseTextSearch(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("CEDICT Search")

        font = self.font()
        font.setPointSize(20)
        self.setFont(font)

        self.label = QLabel("Enter Chinese or English text:")
        self.entry = QLineEdit()
        self.label.setFont(font)
        self.entry.setFont(font)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_chinese)
        self.search_button.setFont(font)
        
        self.copy_button = QPushButton("Copy Result")
        self.copy_button.clicked.connect(self.copy_result)
        self.copy_button.setFont(font)

        self.buttons = QHBoxLayout()
        self.buttons.addWidget(self.search_button)
        self.buttons.addWidget(self.copy_button)
        
        self.result_label = QLabel()
        self.result_label.setWordWrap(True)
        self.result_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.result_label.setFont(font)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.result_label)

        self.shortcuts_button = QPushButton("Shortcuts")
        self.shortcuts_button.clicked.connect(self.shortcuts)
        self.shortcuts_button.setFont(font)
        
        # Create QWebEngineView instance
        self.web_view = QWebEngineView()
        self.web_view.setUrl(QtCore.QUrl("https://www.writeinput.com/?lang=en"))

        # Wrap QWebEngineView in a QWidget
        web_view_widget = QWidget()
        web_view_layout = QVBoxLayout(web_view_widget)
        web_view_layout.addWidget(self.web_view)
        
        # Adjust layout to include QWebEngineView
        main_layout = QHBoxLayout()
        
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.label)
        left_layout.addWidget(self.entry)
        left_layout.addLayout(self.buttons)
        left_layout.addWidget(scroll_area)
        left_layout.addWidget(self.shortcuts_button)
        
        main_layout.addLayout(left_layout)
        main_layout.addWidget(web_view_widget)  # Add the QWidget containing QWebEngineView to the right
        main_layout.setStretchFactor(left_layout,   65)
        main_layout.setStretchFactor(web_view_widget,   35)
        
        self.setLayout(main_layout)

        self.resize(1200, 500)  # Adjust window size to accommodate QWebEngineView

        try:
            self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stardict.svg')))
        except Exception as e:
            raise e

        self.entry.returnPressed.connect(self.search_chinese)

        shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        shortcut.activated.connect(self.close)
        
    
    
    def search_chinese(self):
        chinese_text = self.entry.text()
        if not chinese_text:
            self.result_label.setText("Please enter text to search.")
            return
        
        try:
            matching_lines = []
            pattern = re.compile(chinese_text, re.IGNORECASE)
            
            for line in cedict:
                if pattern.search(line):
                    matching_lines.append(line.strip())
            
            if matching_lines:
                answer = modify("\n".join(matching_lines))
            else:
                answer = chinese_text + " " + ' '.join([word[0] for word in pypinyin.pinyin(chinese_text)]) +  " /" + translator.translate(chinese_text).text + "/(GT)"
            self.result_label.setText(answer)
        except Exception as e:
            self.result_label.setText(f"An error occurred: {e}")
    
    def copy_result(self):
        result_text = self.result_label.text()
        if result_text:
            QApplication.clipboard().setText(result_text)
        else:
            QMessageBox.warning(self, "Empty Result", "No result to copy.")

    def shortcuts(self):
        QMessageBox.information(self, "Shortcuts", "Ctrl-W - Close\nEnter - Search")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChineseTextSearch()
    window.show()
    sys.exit(app.exec_())
