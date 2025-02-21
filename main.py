from itertools import count

from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.uix.label import Label

Window.size =(400, 720)



class grid(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.count = 0
        self.layout()
        self.cols = 1


    def layout(self):
        self.lbl = Label(text=f"Clicks: {self.count}")
        self.add_widget(self.lbl)
        self.btn = Button(text="Press me", size=(self.width*4, self.height/2))
        self.btn.bind(on_release=self.upCount)
        self.add_widget(self.btn)


    def upCount(self, instance):
        self.count += 1
        self.lbl.text = f"Clicks: {self.count}"



class mainApp(App):
    def build(self):
        return grid()


app = mainApp()
app.run()
