from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.uix.button import MDIconButton
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty
from kivymd.app import MDApp
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.storage.jsonstore import JsonStore
from datetime import datetime
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.properties import NumericProperty, StringProperty
from kivy_garden.matplotlib import FigureCanvasKivyAgg
import matplotlib.pyplot as plt
import os
import json


SOUNDS_FOLDER = "sounds_folder"


class mainApp(MDApp):
    def build(self):
        self.store = JsonStore("daily_popup.json")
        self.show_popup()
        return Builder.load_file("main.kv")

    def show_popup(self):

        today = datetime.today().strftime("%Y-%m-%d")

        if not self.store.exists("last_shown") or self.store.get("last_shown")["date"] != today:
            layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

            label = Label(
                text="How are you feeling today!",
                font_size=20,
                color=(1, 1, 1, 1)
            )
            layout.add_widget(label)

            icon_layout = BoxLayout(orientation="horizontal", spacing=15)

            icon1 = MDIconButton(icon="crying.png", on_release=self.icon_click)
            icon2 = MDIconButton(icon="sad.png", on_release=self.icon_click)
            icon3 = MDIconButton(icon="confused.png", on_release=self.icon_click)
            icon4 = MDIconButton(icon="happy.png", on_release=self.icon_click)
            icon5 = MDIconButton(icon="happy-face.png", on_release=self.icon_click)

            icon_layout.add_widget(icon1)
            icon_layout.add_widget(icon2)
            icon_layout.add_widget(icon3)
            icon_layout.add_widget(icon4)
            icon_layout.add_widget(icon5)

            layout.add_widget(icon_layout)


            self.popup = Popup(
                title="Daily Reminder",
                content=layout,
                size_hint=(1, 0.4),
                auto_dismiss=True,
                background_color=(0, 0, 0, 1)
            )
            self.popup.open()
            # Save today's date to prevent showing the popup again today
            self.store.put("last_shown", date=today)

    def icon_click(self, instance):
        self.popup.dismiss()
        print(f"Icon {instance.icon} clicked!")

    dark_mode = BooleanProperty(False)
    notifications_enabled = BooleanProperty(False)
    theme_colors = ["Blue", "Red", "Green", "Purple", "Indigo"]  # Colours to cycle through
    current_theme_index = 0  # Index to track current theme

    def toggle_dark_mode(self, instance, value):
        # Toggles between dark mode and light mode when switch is pressed.
        self.dark_mode = value
        self.update_theme()

    def toggle_notifications(self, instance, value):
        # Enable or disable notifications.
        self.notifications_enabled = value

    def change_theme(self):
        """Cycles through themes (Blue → Red → Green → Blue ...) each time the button is pressed."""
        self.current_theme_index = (self.current_theme_index + 1) % len(self.theme_colors)
        self.theme_color = self.theme_colors[self.current_theme_index]

        # Get the running app instance and update theme
        app = MDApp.get_running_app()
        app.theme_cls.primary_palette = self.theme_color  # Apply the selected theme color
        self.update_theme()

    def update_theme(self):
        # Updates the page based on user preference (Dark/Light).
        app = MDApp.get_running_app()
        if self.dark_mode:
            app.theme_cls.theme_style = "Dark"
            Window.clearcolor = (0.1, 0.1, 0.1, 1)
        else:
            app.theme_cls.theme_style = "Light"
            Window.clearcolor = (1, 1, 1, 1)  # White background

    def on_kv_post(self, base_widget):
        self.update_theme()

    time_left = NumericProperty(0)
    timer_label_text = StringProperty("00:00")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize instance variables
        self.timer = None  # Clock event for the timer
        self.selected_sound_path = None  # Path of the selected sound
        self.current_sound = None  # Currently loaded sound object
        self.snippet_event = None  # Event to stop the sound snippet

    def start_timer(self):
        # Starts the meditation timer and sound playback.
        if self.timer:
            return  # Timer already running

        # Set the timer for 5 minutes (300 seconds)
        self.time_left = 300
        self.update_timer_label()

        # Cancel any scheduled snippet-stop event if one exists
        if self.snippet_event:
            self.snippet_event.cancel()
            self.snippet_event = None

        # Start sound playback in loop mode if a sound has been selected
        if self.selected_sound_path:
            if self.current_sound:
                self.current_sound.stop()
            self.current_sound = SoundLoader.load(self.selected_sound_path)
            if self.current_sound:
                self.current_sound.loop = True
                self.current_sound.play()

        # Schedule the timer to update every second
        self.timer = Clock.schedule_interval(self.update_time, 1)

    def stop_timer(self):
        # Stops the timer and sound playback.
        if self.timer:
            self.timer.cancel()
            self.timer = None

        if self.current_sound:
            self.current_sound.stop()
            self.current_sound = None

        self.reset_timer()

    def update_time(self, dt):
        """Updates the timer each second."""
        if self.time_left > 0:
            self.time_left -= 1
            self.update_timer_label()
        else:
            self.stop_timer()
            self.show_end_message()

    def update_timer_label(self):
        """Updates the timer label in MM:SS format."""
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        self.timer_label_text = f"{minutes:02}:{seconds:02}"
        # If you bind this property in your KV, the label will update automatically.
        if 'timer_label' in self.root.ids:
            self.root.ids.timer_label.text = self.timer_label_text

    def show_end_message(self):
        """Displays the end-of-session message."""
        self.timer_label_text = "Time's up! Meditation complete."
        if 'timer_label' in self.root.ids:
            self.root.ids.timer_label.text = self.timer_label_text

    def reset_timer(self):
        """Resets the timer display to 00:00."""
        self.time_left = 0
        self.update_timer_label()

    def select_sound(self, sound_filename):
        """
        Plays a short snippet of the selected sound and saves its path.

        :param sound_filename: Filename of the sound (e.g., "ocean_waves.mp3")
        """
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound = None

        # Construct the file path using the constant
        self.selected_sound_path = os.path.join(SOUNDS_FOLDER, sound_filename)
        self.current_sound = SoundLoader.load(self.selected_sound_path)
        if self.current_sound:
            self.current_sound.loop = False
            self.current_sound.play()
            if self.snippet_event:
                self.snippet_event.cancel()
            self.snippet_event = Clock.schedule_once(lambda dt: self.stop_snippet(), 5)

    def stop_snippet(self):
        """Stops the sound snippet playback."""
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound = None

    def plot_graph(self):
        try:
            with open("data.json", "r") as f:
                mood_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            mood_data = {}

        day_mapping = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}

        # Sort data and get lists for plotting
        days = sorted(mood_data.keys(), key=int)
        moods = [mood_data[day] for day in days]

        # Convert day numbers to labels
        day_labels = [day_mapping[int(day)] for day in days]

        # Create figure
        fig, ax = plt.subplots()
        ax.plot(day_labels, moods, marker="o", linestyle="-", color="green", linewidth=2)

        # Set labels and grid
        ax.set_xlabel("Days")
        ax.set_ylabel("Mood")
        ax.set_title("Mood Tracker")
        ax.grid(True)

        # Clear previous graph and add new one
        graph_container = self.root.ids.graph_container
        graph_container.clear_widgets()
        graph_container.add_widget(FigureCanvasKivyAgg(fig))

    # graph.add_plot(plot)

    def clearGraph(self):
        graph = self.root.ids.graph

        for x in graph.plots[:]:
            graph.remove_plot(x)

    def show_popup(self):
        today = datetime.today().strftime("%Y-%m-%d")

        # if not self.store.exists("last_shown") or self.store.get("last_shown")["date"] != today:
        layout = BoxLayout(orientation="vertical", padding=20, spacing=10)

        label = Label(
            text="How are you feeling today?",
            font_size=20,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(label)

        icon_layout = BoxLayout(orientation="horizontal", spacing=15)

        emotions = {
            "crying.png": 1,  # Very sad
            "sad.png": 2,  # Sad
            "confused.png": 3,  # Neutral
            "happy.png": 4,  # Happy
            "happy-face.png": 5  # Very happy
        }

        for icon, mood_value in emotions.items():
            button = MDIconButton(icon=icon)
            button.bind(on_release=lambda instance, value=mood_value: self.icon_click(instance, value))
            icon_layout.add_widget(button)

        layout.add_widget(icon_layout)

        self.popup = Popup(
            title="Daily Reminder",
            content=layout,
            size_hint=(1, 0.4),
            auto_dismiss=True,
            background_color=(0, 0, 0, 1)
        )
        self.popup.open()
        # Save today's date to prevent showing the popup again today
        self.store.put("last_shown", date=today)

    def icon_click(self, instance, mood_value):
        """Stores the selected mood into the JSON file based on the current day."""
        day_mapping = {
            "Monday": 1,
            "Tuesday": 2,
            "Wednesday": 3,
            "Thursday": 4,
            "Friday": 5,
            "Saturday": 6,
            "Sunday": 7
        }

        today_name = datetime.today().strftime("%A")  # Get the day name (e.g., "Monday")
        day_number = day_mapping[today_name]  # Convert to a number (1-7)

        try:
            with open("data.json", "r") as f:
                mood_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            mood_data = {}

        mood_data[str(day_number)] = mood_value  # Store mood with the day number as the key

        with open("data.json", "w") as f:
            json.dump(mood_data, f, indent=4)  # Save back to the JSON file

        print(f"Stored mood {mood_value} for {today_name} (Day {day_number})")

        self.popup.dismiss()
        self.plot_graph()  # Update the graph after saving


app = mainApp()
app.run()