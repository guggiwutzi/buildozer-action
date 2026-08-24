import os
import webbrowser
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.utils import platform
from kivy.uix.button import Button

try:
    from plyer import notification
except ImportError:
    notification = None

# Start-Einstellungen ohne feste Vorgaben (wird live am Handy eingetippt)
max_preis = 20
suchbegriffe = []
bereits_gesehen = set()

class HauptScreen(Screen):
    def liste_aktualisieren(self):
        self.ids.ergebnis_liste.clear_widgets()
        app = App.get_running_app()
        for ad_id, titel, preis in app.aktuelle_treffer:
            btn_text = f"💰 {preis}€ | {titel[:40]}..."
            btn = Button(
                text=btn_text,
                size_hint_y=None,
                height=60,
                background_color=(0.2, 0.2, 0.2, 1),
                halign='left',
                valign='middle'
            )
            btn.bind(size=btn.setter('text_size'))
            # Bei Klick öffnet sich die Anzeige direkt auf willhaben
            btn.bind(on_press=lambda instance, aid=ad_id: webbrowser.open(f"https://willhaben.at{aid}"))
            self.ids.ergebnis_liste.add_widget(btn)

class EinstellungsScreen(Screen):
    def speichern(self):
        global max_preis, suchbegriffe
        app = App.get_running_app()
        try:
            max_preis = int(self.ids.preis_input.text)
        except ValueError:
            max_preis = 20
        begriffe_text = self.ids.such_input.text
        suchbegriffe = [b.strip() for b in begriffe_text.split(",") if b.strip()]
        self.manager.current = 'haupt'
        app.suche_ausfuehren(0)

class AutoBastlerApp(App):
    aktuelle_treffer = []
    def build(self):
        self.title = "Bastler Pro Finder"
        from kivy.lang import Builder
        Builder.load_string('''
<HauptScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 10
        spacing: 10
        Button:
            text: "⚙️ Einstellungen"
            size_hint_y: None
            height: 50
            background_color: (0, 0.6, 0.8, 1)
            on_press: root.manager.current = 'einstellungen'
        Label:
            id: status_label
            text: "⏳ Warte auf automatischen Scan..."
            font_size: '15sp'
            size_hint_y: None
            height: 30
            bold: True
            color: (0, 1, 0, 1)
        ScrollView:
            BoxLayout:
                id: ergebnis_liste
                orientation: 'vertical'
                spacing: 8
                size_hint_y: None
                height: self.minimum_height
<EinstellungsScreen>:
    BoxLayout:
        orientation: 'vertical'
        padding: 15
        spacing: 10
        Label:
            text: "⚙️ Einstellungen"
            font_size: '20sp'
            bold: True
            size_hint_y: None
            height: 40
        Label:
            text: "Maximaler Preis (€):"
            halign: 'left'
            size_hint_y: None
            height: 25
        TextInput:
            id: preis_input
            multiline: False
            size_hint_y: None
            height: 45
            hint_text: "20"
        Label:
            text: "Suchbegriffe (mit Komma trennen):"
            halign: 'left'
            size_hint_y: None
            height: 25
        TextInput:
            id: such_input
            multiline: True
            hint_text: "e-scooter, hoverboard, quad, motor, bastler"
        Button:
            text: "💾 Speichern & Suchen"
            size_hint_y: None
            height: 55
            background_color: (0, 0.8, 0.4, 1)
            on_press: root.speichern()
''')
        sm = ScreenManager()
        sm.add_widget(HauptScreen(name='haupt'))
        sm.add_widget(EinstellungsScreen(name='einstellungen'))
        self.haupt_screen = sm.get_screen('haupt')
        Clock.schedule_once(self.suche_ausfuehren, 2)
        Clock.schedule_interval(self.suche_ausfuehren, 300)
        return sm

    def send_android_notification(self, titel, text):
        if platform == 'android' and notification:
            try:
                notification.notify(title=titel, message=text, app_name="BastlerFinder")
            except Exception:
                pass

    def suche_ausfuehren(self, dt):
        global max_preis, suchbegriffe, bereits_gesehen
        if not suchbegriffe:
            self.haupt_screen.ids.status_label.text = "⚠️ Keine Suchbegriffe eingetragen!"
            return
            
        self.haupt_screen.ids.status_label.text = "🔄 Suche läuft vollautomatisch..."
        neue_treffer = []
        for begriff in suchbegriffe:
            url = "https://willhaben.at"
            params = {"keyword": begriff, "price_max": str(max_preis), "rows": "5", "sort": "1", "verticalId": "1"}
            headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36", "Accept": "application/json"}
            try:
                response = requests.get(url, params=params, headers=headers, timeout=5)
                if response.status_code == 200:
                    ads = response.json().get("feed", {}).get("advertisements", [])
                    for ad in ads:
                        ad_id = ad.get("id")
                        titel = ad.get("description", "Kein Titel")
                        preis = "0"
                        attributes = ad.get("attributes", {}).get("attribute", [])
                        for attr in attributes:
                            if attr.get("name") == "PRICE":
                                values = attr.get("values", [])
                                if values:
                                    preis = values
                        if ad_id:
                            if ad_id not in bereits_gesehen:
                                bereits_gesehen.add(ad_id)
                                self.send_android_notification(titel="🛠️ Neuer Bastler-Deal!", text=f"{titel[:30]}... für {preis}€!")
                            if (ad_id, titel, preis) not in neue_treffer:
                                neue_treffer.append((ad_id, titel, preis))
            except Exception:
                pass
        self.aktuelle_treffer = neue_treffer
        if self.root and self.root.current == 'haupt':
            self.haupt_screen.liste_aktualisieren()
        self.haupt_screen.ids.status_label.text = f"✅ {len(self.aktuelle_treffer)} Sachen aktiv! Auto-Scan läuft."

if __name__ == '__main__':
    AutoBastlerApp().run()
