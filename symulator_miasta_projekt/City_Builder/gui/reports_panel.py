import matplotlib
matplotlib.use('Qt5Agg')  # Ustaw backend matplotlib na Qt5 przed importem pyplot
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel
import csv
import os
from datetime import datetime

class ReportsPanel(QWidget):
    """
    Panel raportów i statystyk miasta.
    
    Wyświetla interaktywne wykresy pokazujące rozwój miasta w czasie:
    - Wzrost populacji
    - Zmiany budżetu
    - Zadowolenie mieszkańców
    - Stopę bezrobocia
    - Dochody vs wydatki
    - Bilans budżetowy
    
    Używa matplotlib do generowania wykresów i PyQt6 do interfejsu.
    Pozwala na eksport danych do plików CSV.
    """
    
    def __init__(self, parent=None):
        """
        Konstruktor panelu raportów.
        
        Args:
            parent: widget rodzica (opcjonalny)
            
        Inicjalizuje strukturę danych historycznych i interfejs użytkownika.
        """
        super().__init__(parent)
        
        # Słownik przechowujący dane historyczne miasta
        # Każdy klucz to lista wartości dla kolejnych tur
        self.history_data = {
            'turns': [],          # numery tur
            'population': [],     # liczba mieszkańców
            'budget': [],         # stan budżetu miasta
            'satisfaction': [],   # zadowolenie mieszkańców (0-100%)
            'unemployment': [],   # stopa bezrobocia (0-100%)
            'income': [],         # dochody z podatków
            'expenses': []        # wydatki miasta
        }
        self.init_ui()  # inicjalizuj interfejs użytkownika

    def init_ui(self):
        """
        Inicjalizuje interfejs użytkownika panelu raportów.
        
        Tworzy:
        - Panel kontrolny z filtrami i przyciskami
        - Obszar wykresów matplotlib
        - 6 podwykresów w układzie 2x3
        """
        layout = QVBoxLayout()  # główny układ pionowy
        
        # Panel kontrolny - przyciski i filtry
        controls_layout = QHBoxLayout()  # układ poziomy dla kontrolek
        
        # Selektor zakresu czasu - pozwala filtrować dane
        controls_layout.addWidget(QLabel("Zakres czasu:"))
        self.time_range_combo = QComboBox()  # lista rozwijana
        self.time_range_combo.addItems(["Ostatnie 10 tur", "Ostatnie 25 tur", "Ostatnie 50 tur", "Wszystkie dane"])
        # Podłącz sygnał zmiany wyboru do metody aktualizacji wykresów
        self.time_range_combo.currentTextChanged.connect(self.update_charts)
        controls_layout.addWidget(self.time_range_combo)
        
        # Przycisk eksportu do CSV
        self.export_btn = QPushButton("Eksportuj do CSV")
        self.export_btn.clicked.connect(self.export_to_csv)  # podłącz do metody eksportu
        controls_layout.addWidget(self.export_btn)
        
        # Przycisk odświeżania
        self.refresh_btn = QPushButton("Odśwież")
        self.refresh_btn.clicked.connect(self.update_charts)  # podłącz do metody aktualizacji
        controls_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(controls_layout)  # dodaj panel kontrolny do głównego układu

        # Utwórz figurę matplotlib i canvas Qt
        # matplotlib to biblioteka do tworzenia wykresów w Pythonie
        self.figure = plt.figure(figsize=(12, 8))  # rozmiar figury w calach
        self.canvas = FigureCanvas(self.figure)  # widget Qt zawierający wykres matplotlib
        layout.addWidget(self.canvas)

        # Utwórz 6 podwykresów w układzie 2x3 (2 rzędy, 3 kolumny)
        # add_subplot(abc) gdzie a=rzędy, b=kolumny, c=pozycja (1-6)
        self.ax1 = self.figure.add_subplot(231)  # pozycja 1 (góra lewo)
        self.ax2 = self.figure.add_subplot(232)  # pozycja 2 (góra środek)
        self.ax3 = self.figure.add_subplot(233)  # pozycja 3 (góra prawo)
        self.ax4 = self.figure.add_subplot(234)  # pozycja 4 (dół lewo)
        self.ax5 = self.figure.add_subplot(235)  # pozycja 5 (dół środek)
        self.ax6 = self.figure.add_subplot(236)  # pozycja 6 (dół prawo)

        self.setLayout(layout)  # ustaw główny układ
        self.setWindowTitle("Raporty i Statystyki Miasta")
        self.resize(1000, 700)  # rozmiar okna w pikselach

    def add_data_point(self, turn, population, budget, satisfaction, unemployment, income, expenses):
        """
        Dodaje nowy punkt danych do historii miasta.
        
        Args:
            turn: numer tury
            population: liczba mieszkańców
            budget: stan budżetu
            satisfaction: zadowolenie mieszkańców (0-100)
            unemployment: stopa bezrobocia (0-100)
            income: dochody z podatków
            expenses: wydatki miasta
            
        Ta metoda jest wywoływana na końcu każdej tury przez silnik gry.
        """
        # Dodaj nowe wartości do odpowiednich list
        self.history_data['turns'].append(turn)
        self.history_data['population'].append(population)
        self.history_data['budget'].append(budget)
        self.history_data['satisfaction'].append(satisfaction)
        self.history_data['unemployment'].append(unemployment)
        self.history_data['income'].append(income)
        self.history_data['expenses'].append(expenses)
        
        # Ograniczenie do ostatnich 200 punktów dla wydajności
        # Zbyt dużo punktów może spowolnić rysowanie wykresów
        max_points = 200
        for key in self.history_data:
            if len(self.history_data[key]) > max_points:
                # Zachowaj tylko ostatnie max_points elementów
                self.history_data[key] = self.history_data[key][-max_points:]

    def get_filtered_data(self):
        """
        Zwraca dane przefiltrowane według wybranego zakresu czasowego.
        
        Returns:
            dict: słownik z przefiltrowanymi danymi historycznymi
            
        Filtruje dane na podstawie wyboru w time_range_combo.
        Pozwala na wyświetlanie tylko ostatnich N tur.
        """
        range_text = self.time_range_combo.currentText()  # pobierz aktualny wybór
        
        # Określ limit na podstawie wyboru użytkownika
        if range_text == "Ostatnie 10 tur":
            limit = 10
        elif range_text == "Ostatnie 25 tur":
            limit = 25
        elif range_text == "Ostatnie 50 tur":
            limit = 50
        else:  # "Wszystkie dane"
            limit = len(self.history_data['turns'])  # bez limitu
        
        # Utwórz nowy słownik z przefiltrowanymi danymi
        filtered_data = {}
        for key, values in self.history_data.items():
            # Weź ostatnie 'limit' elementów z każdej listy
            filtered_data[key] = values[-limit:] if len(values) > limit else values
        
        return filtered_data

    def update_charts(self):
        """
        Aktualizuje wszystkie wykresy na podstawie aktualnych danych.
        
        Główna metoda odpowiedzialna za generowanie wykresów:
        1. Pobiera przefiltrowane dane
        2. Czyści poprzednie wykresy
        3. Generuje 6 różnych wykresów
        4. Aktualizuje wyświetlanie
        """
        data = self.get_filtered_data()  # pobierz dane do wyświetlenia
        
        # Jeśli brak danych, nie rysuj niczego
        if not data['turns']:
            return
        
        # Wyczyść poprzednie wykresy - usuń wszystkie linie i punkty
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]:
            ax.clear()

        turns = data['turns']  # oś X dla wszystkich wykresów (numery tur)

        # Wykres 1: Populacja miasta w czasie
        self.ax1.plot(turns, data['population'], 'b-', linewidth=2, marker='o', markersize=4)
        # 'b-' = niebieska linia, linewidth=grubość, marker='o'=kółka na punktach
        self.ax1.set_title('Populacja', fontsize=12, fontweight='bold')
        self.ax1.set_ylabel('Mieszkańcy')  # etykieta osi Y
        self.ax1.grid(True, alpha=0.3)  # siatka z przezroczystością 30%

        # Wykres 2: Budżet miasta
        self.ax2.plot(turns, data['budget'], 'g-', linewidth=2, marker='s', markersize=4)
        # 'g-' = zielona linia, marker='s'=kwadraciki
        self.ax2.set_title('Budżet Miasta', fontsize=12, fontweight='bold')
        self.ax2.set_ylabel('Pieniądze ($)')
        self.ax2.grid(True, alpha=0.3)

        # Wykres 3: Zadowolenie mieszkańców
        self.ax3.plot(turns, data['satisfaction'], 'orange', linewidth=2, marker='^', markersize=4)
        # 'orange' = pomarańczowa linia, marker='^'=trójkąty
        self.ax3.set_title('Zadowolenie Mieszkańców', fontsize=12, fontweight='bold')
        self.ax3.set_ylabel('Zadowolenie (%)')
        self.ax3.set_ylim(0, 100)  # ustaw zakres osi Y na 0-100%
        self.ax3.grid(True, alpha=0.3)

        # Wykres 4: Stopa bezrobocia
        self.ax4.plot(turns, data['unemployment'], 'r-', linewidth=2, marker='v', markersize=4)
        # 'r-' = czerwona linia, marker='v'=trójkąty w dół
        self.ax4.set_title('Stopa Bezrobocia', fontsize=12, fontweight='bold')
        self.ax4.set_ylabel('Bezrobocie (%)')
        self.ax4.grid(True, alpha=0.3)

        # Wykres 5: Dochody vs Wydatki - dwie linie na jednym wykresie
        self.ax5.plot(turns, data['income'], 'g-', linewidth=2, label='Dochody', marker='o', markersize=3)
        self.ax5.plot(turns, data['expenses'], 'r-', linewidth=2, label='Wydatki', marker='s', markersize=3)
        # label= etykiety dla legendy
        self.ax5.set_title('Ekonomia - Dochody vs Wydatki', fontsize=12, fontweight='bold')
        self.ax5.set_ylabel('Pieniądze ($)')
        self.ax5.legend()  # pokaż legendę z etykietami
        self.ax5.grid(True, alpha=0.3)

        # Wykres 6: Bilans budżetowy (dochody - wydatki) jako wykres słupkowy
        if len(data['income']) == len(data['expenses']):  # sprawdź czy listy mają tę samą długość
            # Oblicz bilans dla każdej tury
            balance = [inc - exp for inc, exp in zip(data['income'], data['expenses'])]
            # zip łączy dwie listy w pary: [(inc1,exp1), (inc2,exp2), ...]
            
            # Ustaw kolory słupków: zielone dla zysku, czerwone dla straty
            colors = ['g' if b >= 0 else 'r' for b in balance]  # lista comprehension
            
            # Utwórz wykres słupkowy
            self.ax6.bar(turns, balance, color=colors, alpha=0.7)  # alpha=przezroczystość
            self.ax6.set_title('Bilans Budżetowy', fontsize=12, fontweight='bold')
            self.ax6.set_ylabel('Bilans ($)')
            self.ax6.axhline(y=0, color='black', linestyle='-', alpha=0.5)  # linia na poziomie 0
            self.ax6.grid(True, alpha=0.3)

        # Ustaw etykiety osi X dla wszystkich wykresów
        for ax in [self.ax1, self.ax2, self.ax3, self.ax4, self.ax5, self.ax6]:
            ax.set_xlabel('Tura')

        # Dostosuj układ wykresów i odśwież wyświetlanie
        self.figure.tight_layout()  # automatycznie dostosuj odstępy między wykresami
        self.canvas.draw()  # odśwież canvas Qt

    def export_to_csv(self):
        """
        Eksportuje dane historyczne do pliku CSV.
        
        Tworzy plik CSV z wszystkimi danymi historycznymi miasta.
        Plik jest zapisywany w folderze 'exports' z timestamp w nazwie.
        CSV (Comma-Separated Values) to format danych łatwy do otwarcia w Excelu.
        """
        try:
            # Upewnij się że folder exports istnieje
            export_dir = os.path.join(os.path.dirname(__file__), '..', 'exports')
            os.makedirs(export_dir, exist_ok=True)  # utwórz folder jeśli nie istnieje
            
            # Wygeneruj nazwę pliku z aktualną datą i czasem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # format: 20241220_143052
            filename = os.path.join(export_dir, f"city_report_{timestamp}.csv")
            
            # Zapisz dane do pliku CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)  # obiekt do zapisu CSV
                
                # Nagłówek tabeli
                writer.writerow(['Tura', 'Populacja', 'Budżet', 'Zadowolenie (%)', 
                               'Bezrobocie (%)', 'Dochody', 'Wydatki', 'Bilans'])
                
                # Wiersze z danymi - iteruj przez wszystkie tury
                for i in range(len(self.history_data['turns'])):
                    # Pobierz dane dla tury i (z zabezpieczeniem przed brakiem danych)
                    income = self.history_data['income'][i] if i < len(self.history_data['income']) else 0
                    expenses = self.history_data['expenses'][i] if i < len(self.history_data['expenses']) else 0
                    balance = income - expenses  # oblicz bilans
                    
                    # Zapisz wiersz danych
                    writer.writerow([
                        self.history_data['turns'][i],
                        self.history_data['population'][i],
                        self.history_data['budget'][i],
                        round(self.history_data['satisfaction'][i], 1),  # zaokrągl do 1 miejsca po przecinku
                        round(self.history_data['unemployment'][i], 1),
                        income,
                        expenses,
                        balance
                    ])
            
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, 'Eksport', f'Dane wyeksportowane do:\n{filename}')
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, 'Błąd eksportu', f'Nie udało się wyeksportować danych:\n{str(e)}')

    def update_reports(self, population_history, budget_history, satisfaction_history, resources_history):
        """Zachowuje kompatybilność z poprzednią wersją (deprecated)"""
        # Ta metoda jest zachowana dla kompatybilności, ale zaleca się używanie add_data_point
        if population_history and budget_history and satisfaction_history:
            # Dodaj tylko ostatni punkt jeśli to nowe dane
            if not self.history_data['turns'] or len(population_history) > len(self.history_data['population']):
                turn = len(self.history_data['turns']) + 1
                self.add_data_point(
                    turn=turn,
                    population=population_history[-1] if population_history else 0,
                    budget=budget_history[-1] if budget_history else 0,
                    satisfaction=satisfaction_history[-1] if satisfaction_history else 0,
                    unemployment=0,  # Będzie aktualizowane przez add_data_point
                    income=0,  # Będzie aktualizowane przez add_data_point
                    expenses=0  # Będzie aktualizowane przez add_data_point
                )
                self.update_charts()
