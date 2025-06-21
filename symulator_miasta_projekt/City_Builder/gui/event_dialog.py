from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

class EventDialog(QDialog):
    """
    Okno dialogowe wyświetlające wydarzenia w grze.
    
    Dziedziczy po QDialog - standardowym oknie dialogowym w PyQt6.
    Wyświetla wydarzenie z opisem i opcjami wyboru dla gracza.
    Po wyborze opcji okno się zamyka i zwraca wybraną opcję.
    """
    
    def __init__(self, event, parent=None):
        """
        Konstruktor okna dialogowego wydarzenia.
        
        Args:
            event: obiekt Wydarzenia zawierający tytuł, opis i opcje
            parent: okno nadrzędne (opcjonalne, domyślnie None)
        """
        super().__init__(parent)        # wywołaj konstruktor klasy nadrzędnej (QDialog)
        self.event = event              # zapisz obiekt wydarzenia
        self.selected_option = None     # wybrana opcja (na początku żadna)
        self.init_ui()                  # zainicjalizuj interfejs użytkownika

    def init_ui(self):
        """
        Inicjalizuje interfejs użytkownika okna dialogowego.
        
        Tworzy:
        - Tytuł okna z tytułem wydarzenia
        - Etykietę z opisem wydarzenia
        - Przyciski dla każdej opcji wyboru
        - Układ elementów w oknie
        """
        # Ustaw tytuł okna na tytuł wydarzenia
        self.setWindowTitle(self.event.title)
        
        # Utwórz pionowy układ (elementy jeden pod drugim)
        layout = QVBoxLayout()

        # Utwórz etykietę z opisem wydarzenia
        description_label = QLabel(self.event.description)
        layout.addWidget(description_label)  # dodaj etykietę do układu

        # Utwórz poziomy układ dla przycisków opcji (obok siebie)
        options_layout = QHBoxLayout()
        
        # Przejdź przez wszystkie opcje wydarzenia
        for option in self.event.options:
            # Utwórz przycisk dla każdej opcji
            button = QPushButton(option)
            
            # Podłącz sygnał clicked do metody select_option
            # lambda - funkcja anonimowa, opt=option - przechwytuje wartość w pętli
            button.clicked.connect(lambda checked, opt=option: self.select_option(opt))
            
            # Dodaj przycisk do układu poziomego
            options_layout.addWidget(button)

        # Dodaj układ przycisków do głównego układu
        layout.addLayout(options_layout)
        
        # Ustaw układ jako układ tego okna
        self.setLayout(layout)

    def select_option(self, option):
        """
        Obsługuje wybór opcji przez gracza.
        
        Args:
            option (str): wybrana opcja
            
        Ta metoda jest wywoływana gdy gracz kliknie jeden z przycisków.
        Zapisuje wybraną opcję i zamyka okno z wynikiem akceptacji.
        """
        self.selected_option = option   # zapisz wybraną opcję
        self.accept()                   # zamknij okno z kodem akceptacji (OK) 