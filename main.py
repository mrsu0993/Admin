import json
import os
import sys
import requests
from pathlib import Path
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineListItem
from kivymd.uix.textfield import MDTextField
from kivy.core.audio import SoundLoader
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivymd.uix.button import MDFlatButton
from kivymd.icon_definitions import md_icons
from kivymd.uix.slider import MDSlider
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard

#Window.size = [1200, 700]
#Window.fullscreen = "auto"


def create_directory_if_not_exists(path):
    directory_path = Path(path)
    if not directory_path.exists():
        directory_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory '{path}' already exists")

def load_kv_file():
    kv_file_url = "https://raw.githubusercontent.com/mrsu0993/Admin/master/main.kv"
    try:
        response = requests.get(kv_file_url)
        if response.status_code == 200:
            try:
                Builder.load_string(response.text)
                print("Loaded main.kv from GitHub")
                return  # Load thành công, không cần tiếp tục
            except Exception as e:
                print("Failed to load main.kv:", e)
                # Nếu không thể tải main.kv từ GitHub, tiếp tục thử tải các tệp cục bộ
        else:
            kv_files = ["main.kv", "_internal/dist/main/main.kv"]
            for kv_file in kv_files:
                if os.path.exists(kv_file):
                    try:
                        Builder.load_file(kv_file)
                        print("Loaded", kv_file)
                        return  # Load thành công, không cần tiếp tục
                    except Exception as e:
                        print("Failed to load", kv_file, ":", e)
            print("Both main2.kv and main.kv failed to load. Exiting...")
            sys.exit(1)
    except requests.exceptions.RequestException as e:
        # Nếu không có kết nối mạng, sử dụng các giá trị mặc định từ tệp kv cục bộ
        kv_files = ["main.kv", "_internal/dist/main/main.kv"]
        for kv_file in kv_files:
            if os.path.exists(kv_file):
                try:
                    Builder.load_file(kv_file)
                    print("Loaded", kv_file)
                    return  # Load thành công, không cần tiếp tục
                except Exception as e:
                    print("Failed to load", kv_file, ":", e)

        print("No local KV files found. Exiting...")
        sys.exit(1)

class DropdownPopup(Popup):
    pass

class MediaPlayer(MDBoxLayout):
    def __init__(self, **kwargs):
        super(MediaPlayer, self).__init__(**kwargs)
        self.index = 0
        self.name_git = "mrsu0993"
        self.name_audio = "Business"
        self.num = 1
        self.total_english_words = 0
        self.current_english_word_index = 0
        self.sound = None
        self.playing = False
        self.words = []
        self.word_counts = {}
        self.interacting_with_slider = False  # Thêm cờ này để theo dõi việc tương tác với thanh tiến trình
        self.load_audio_filenames()
        self.dropdown_data = {}
        self.load_dropdown_data()

    def load_dropdown_data(self):
        json_url = "https://raw.githubusercontent.com/mrsu0993/Admin/master/name.json"
        
        try:
            response = requests.get(json_url)
            if response.status_code == 200:
                self.dropdown_data = json.loads(response.text)
            else:
                popup = Popup(title='Lỗi kết nối mạng', content=MDLabel(text='Hãy kết nối mạng để tiếp tục'), size_hint=(None, None), size=(400, 200))
                popup.open()
        except requests.exceptions.RequestException as e:
            popup = Popup(title='Lỗi kết nối mạng', content=MDLabel(text='Hãy kết nối mạng để tiếp tục'), size_hint=(None, None), size=(400, 200))
            popup.open()

        self.dropdown = DropdownPopup()
        for key, value in self.dropdown_data.items():
            item = MDFlatButton(text=value)
            item.bind(on_release=lambda btn, text=key: self.select_audio(text))
            self.dropdown.ids.dropdown_list.add_widget(item)
        self.dropdown_button = MDFlatButton(text='Chọn File Nói Audio', on_release=self.dropdown.open)
        self.ids.label.add_widget(self.dropdown_button)

    def calculate_num(self):
        return "" if self.total_english_words < 500 else (self.current_english_word_index // 1000) + 1

    def select_audio(self, name_audio):
        self.name_audio = name_audio
        self.num = self.calculate_num()
        self.stop_audio()  # Dừng âm thanh hiện tại (nếu có)
        self.index = 0  # Reset lại chỉ số từ
        self.current_english_word_index = 0  # Reset lại chỉ số từ hiện tại
        self.word_counts.clear()  # Xóa bộ đếm từ
        self.total_english_words = 0
        self.load_audio_filenames()
        self.dropdown.dismiss()
        self.play_audio()

    def play_audio(self):
        if self.current_english_word_index < self.total_english_words * 2:
            filename = f"{self.words[self.index]}"

            self.num = self.calculate_num()

            if self.index % 2 == 0:
                url = f"https://raw.githubusercontent.com/{self.name_git}/{self.name_audio}{self.num}/master/en/{filename}"
                filename_display = self.extract_filename(filename)
                self.ids.current_file_label.text = filename_display
                self.update_word_count(filename_display.lower())
            else:
                url = f"https://raw.githubusercontent.com/{self.name_git}/{self.name_audio}{self.num}/master/vi/{filename}"

            try:
                response = requests.get(url)
                if response.status_code == 200:
                    temp_filename = Path.home() / "Documents" / "Suspeak" / 'temp.mp3'
                    with open(temp_filename, 'wb') as f:
                        f.write(response.content)
                    self.sound = SoundLoader.load(str(temp_filename))
                    os.remove(temp_filename)
                    if self.sound:
                        self.sound.bind(on_stop=self.on_sound_stop)
                        self.sound.play()
                        self.playing = True
                        self.ids.play_button.icon = 'pause'
                        self.ids.progress_slider.value = self.index
                        self.ids.index_word.text = f"{self.index}/{self.total_english_words} từ"
                    else:
                        print("Failed to load MP3 file")
                else:
                    print("Failed to fetch MP3 file from URL")
            except requests.exceptions.RequestException as e:
                # Handle no internet connection
                popup = Popup(title='Lỗi kết nối mạng', content=MDLabel(text='Hãy kết nối mạng để tiếp tục'), size_hint=(None, None), size=(400, 200))
                popup.open()
        else:
            self.index = 0
            self.current_english_word_index = 0
            self.ids.play_button.icon = 'play'
            self.stop_audio()

    def load_audio_filenames(self):
        try:
            excel_url = f"https://raw.githubusercontent.com/{self.name_git}/Json/master/{self.name_audio}_word.json"
            response = requests.get(excel_url)
            if response.status_code == 200:
                json_data = json.loads(response.text)
                self.words.clear()
                for key, value in json_data.items():
                    self.words.append(key)
                    self.words.append(value)
                    self.total_english_words += 1
                self.ids.progress_slider.max = self.total_english_words * 2
            else:
                popup = Popup(title='Lỗi kết nối mạng', content=MDLabel(text='Hãy kết nối mạng để tiếp tục'), size_hint=(None, None), size=(400, 200))
                popup.open()
        except Exception as e:
            popup = Popup(title='Lỗi kết nối mạng', content=MDLabel(text='Hãy kết nối mạng để tiếp tục'), size_hint=(None, None), size=(400, 200))
            popup.open()

        self.word_counts = self.load_word_counts()
        self.update_total_word_count_label()

    def load_word_counts(self):
        json_file = Path.home()/"Documents"/"Suspeak"/"count.json"
        if os.path.exists(json_file):
            with open(json_file, 'r') as f:
                return json.load(f)
        else:
            with open(json_file, 'w') as f:
                json.dump({}, f)
            return {}

    def play_pause(self):
        if not self.playing:
            self.play_audio()
        else:
            self.pause_audio()

    def pause_audio(self):
        if self.sound and self.playing:
            self.sound.stop()
            self.playing = False
            self.ids.play_button.icon = 'play'

    def stop_audio(self):
        if self.sound:
            self.sound.stop()
            self.playing = False
            self.ids.play_button.icon = 'play'
            self.index = 0
            self.current_english_word_index = 0

    def on_sound_stop(self, instance):
        if self.playing:
            self.index += 1
            self.current_english_word_index += 1
            if self.index % 1000 == 0:
                self.num += 1
            self.play_audio()

    def update_word_count(self, word):
        if word in self.word_counts:
            self.word_counts[word] += 1
        else:
            self.word_counts[word] = 1
        json_file = Path.home()/"Documents"/"Suspeak"/"count.json"
        with open(json_file, 'w') as f:
            json.dump(self.word_counts, f)
        self.update_word_count_label(word)
        self.update_total_word_count_label()

    def update_word_count_label(self, word):
        count = self.word_counts.get(word, 0)
        if word.isalpha() and len(word) < 4:
            self.ids.current_file_label.font_size = '150sp'
        elif 4 <= word.isalpha() and len(word) < 8:
            self.ids.current_file_label.font_size = '130sp'
        else:
            self.ids.current_file_label.font_size = '120sp'
            self.ids.current_file_label.text_color = 0, 0, 0, 1

        if count > 25:
            self.ids.current_file_label.text_color = 1, 0, 0, 1
        elif 10 < count < 25:
            self.ids.current_file_label.text_color = 0, 0, 1, 1
        else:
            self.ids.current_file_label.text_color = 0, 0, 0, 1

        self.ids.word_count_label.text = f"Bạn đã NÓI từ này: {count} lần"

    def get_total_word_count(self):
        total_count = len(self.word_counts)
        return total_count

    def update_total_word_count_label(self):
        total_count = self.get_total_word_count()
        self.ids.total_word_count_label.text = f"Bạn đã NÓI được tổng số từ là: {total_count}"

    def slider_touch_down(self, instance, touch):
        if self.sound and self.ids.progress_slider.collide_point(*touch.pos):
            self.interacting_with_slider = True  # Người dùng đang tương tác với thanh tiến trình
            self.sound.stop()

    def slider_touch_move(self, instance, touch):
        if self.sound and self.ids.progress_slider.collide_point(*touch.pos):
            self.current_english_word_index = int(self.ids.progress_slider.value)
            self.ids.current_index_text.text = str(self.current_english_word_index)

    def slider_touch_up(self, instance, touch):
        if self.sound and self.ids.progress_slider.collide_point(*touch.pos):
            self.index = self.current_english_word_index
            if not self.interacting_with_slider:  # Chỉ chạy audio nếu không có tương tác với thanh tiến trình
                self.play_audio()
            else:
                self.interacting_with_slider = False  # Reset cờ sau khi thả thanh tiến trình

    @staticmethod
    def extract_filename(filename):
        filename_without_extension = filename.split('.')[0]
        filename_parts = filename_without_extension.split('_')
        return ' '.join(filename_parts[2:]).capitalize()

class SuSpeakApp(MDApp):
    def build(self):
        icon_path = str(Path.home()/"Documents"/"Suspeak"/"icon.png")
        if os.path.exists(icon_path):
            self.icon = icon_path
        else:
            self.icon = self.resource_path('assets\\images\\icon.png')
        return MediaPlayer()

    def resource_path(self,relative_path):
        try:
            base_path = sys._MEIPASS2
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def on_start(self):
        icon_url = "https://raw.githubusercontent.com/mrsu0993/Admin/master/icon.png"
        try:
            response = requests.get(icon_url)
            if response.status_code == 200:
                with open(Path.home()/"Documents"/"Suspeak"/"icon.png", "wb") as f:
                    f.write(response.content)
            else:
                popup = Popup(title='Lỗi kết nối mạng', content=MDLabel(text='Hãy kết nối mạng để tiếp tục'), size_hint=(None, None), size=(400, 200))
                popup.open()
        except requests.exceptions.RequestException as e:
            popup = Popup(title='Lỗi kết nối mạng', content=MDLabel(text='Hãy kết nối mạng để tiếp tục'), size_hint=(None, None), size=(400, 200))
            popup.open()

if __name__ == '__main__':
    directory_path = Path.home()/"Documents"/"Suspeak"
    create_directory_if_not_exists(directory_path)
    load_kv_file()
    SuSpeakApp().run()