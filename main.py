from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button


class PlayMenu(Screen):
    pass


class Lobby(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        anchor1 = AnchorLayout()

        box1 = BoxLayout(orientation="vertical",
                         size_hint=(0.4, 0.7))

        # Lobby list
        title = Label(text="Players",
                      font_size=30,
                      halign="center",
                      valign="center",
                      size_hint=(1, None),
                      size=(dp(100), dp(80)))
        title.text_size = title.size
        box1.add_widget(title)

        self.players_list = []
        for i in range(6):
            self.players_list.append(
                Label(text="{}: ***********".format("H" if i==0 else str(i+1)),
                      font_size=20,
                    #   halign="left",
                    #   valign="center",
                      size_hint=(1, None),
                      size=("200dp", dp(50))))
            # self.players_list[-1].text_size = self.players_list[-1].size
            box1.add_widget(self.players_list[-1])

        anchor1.add_widget(box1)
        self.add_widget(anchor1)


class WindowManager(ScreenManager):
    pass


class UpAndDownApp(App):
    pass


UpAndDownApp().run()
