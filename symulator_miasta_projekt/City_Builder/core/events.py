import random
from typing import Dict, List, Optional

class Event:
    """
    Klasa reprezentująca pojedyncze wydarzenie w grze.
    
    Wydarzenia to losowe zdarzenia, które wpływają na miasto i wymagają decyzji gracza.
    Każde wydarzenie ma tytuł, opis, podstawowe efekty oraz opcjonalne wybory decyzji.
    """
    def __init__(self, title, description, effects, options=None, decision_effects=None):
        """
        Konstruktor wydarzenia.
        
        Args:
            title (str): tytuł wydarzenia wyświetlany graczowi
            description (str): szczegółowy opis sytuacji
            effects (dict): podstawowe efekty wydarzenia (np. {'money': -100, 'satisfaction': -10})
            options (list): lista opcji do wyboru przez gracza
            decision_effects (dict): efekty różnych decyzji gracza
        """
        self.title = title                              # tytuł wydarzenia
        self.description = description                  # opis wydarzenia
        self.effects = effects                          # podstawowe efekty wydarzenia
        self.options = options or []                    # opcje wyboru (domyślnie pusta lista)
        self.decision_effects = decision_effects or {}  # efekty różnych decyzji

class EventManager:
    """
    Klasa zarządzająca wszystkimi wydarzeniami w grze.
    
    Odpowiada za:
    - Przechowywanie definicji wszystkich wydarzeń
    - Losowe wybieranie wydarzeń
    - Kontekstowy wybór wydarzeń na podstawie stanu gry
    - Śledzenie historii wydarzeń
    - Zastosowanie efektów decyzji gracza
    """
    def __init__(self):
        """
        Konstruktor - inicjalizuje wszystkie dostępne wydarzenia w grze.
        """
        # Lista wszystkich możliwych wydarzeń w grze
        self.events = [
            # KATASTROFY - wydarzenia negatywne wymagające szybkiej reakcji
            Event(
                "Pożar w Dzielnicy",
                "Wybuchł pożar w dzielnicy mieszkalnej! Straż pożarna prosi o instrukcje.",
                {"population": -30, "satisfaction": -15},  # podstawowe efekty
                ["Wysłać wszystkie jednostki straży", "Ewakuować mieszkańców", "Zignorować"],
                {  # efekty różnych decyzji
                    "Wysłać wszystkie jednostki straży": {"money": -500, "population": -10, "satisfaction": 5},
                    "Ewakuować mieszkańców": {"population": -5, "satisfaction": -5, "money": -200},
                    "Zignorować": {"population": -50, "satisfaction": -25}
                }
            ),
            Event(
                "Epidemia Grypy",
                "W mieście wybuchła epidemia grypy. Szpitale są przepełnione.",
                {"population": -80, "satisfaction": -20},
                ["Wprowadzić kwarantannę", "Zwiększyć budżet szpitali", "Zignorować"],
                {
                    "Wprowadzić kwarantannę": {"money": -1000, "population": -20, "satisfaction": -10},
                    "Zwiększyć budżet szpitali": {"money": -1500, "population": -40, "satisfaction": 5},
                    "Zignorować": {"population": -120, "satisfaction": -35}
                }
            ),
            Event(
                "Trzęsienie Ziemi",
                "Słabe trzęsienie ziemi uszkodziło część infrastruktury miasta.",
                {"money": -2000, "satisfaction": -10},
                ["Natychmiastowe naprawy", "Stopniowa odbudowa", "Minimalne naprawy"],
                {
                    "Natychmiastowe naprawy": {"money": -3000, "satisfaction": 10},
                    "Stopniowa odbudowa": {"money": -1500, "satisfaction": 0},
                    "Minimalne naprawy": {"money": -500, "satisfaction": -15}
                }
            ),
            
            # KRYZYSY EKONOMICZNE - wydarzenia wpływające na finanse miasta
            Event(
                "Kryzys Ekonomiczny",
                "Globalny kryzys ekonomiczny dotarł do miasta. Bezrobocie rośnie.",
                {"money": -800, "satisfaction": -15},
                ["Program pomocy społecznej", "Obniżyć podatki", "Nic nie robić"],
                {
                    "Program pomocy społecznej": {"money": -1200, "satisfaction": 15},
                    "Obniżyć podatki": {"money": -600, "satisfaction": 10},
                    "Nic nie robić": {"satisfaction": -20}
                }
            ),
            Event(
                "Strajk Pracowników",
                "Pracownicy miejskich służb rozpoczęli strajk domagając się podwyżek.",
                {"satisfaction": -20},
                ["Spełnić żądania", "Negocjować kompromis", "Odrzucić żądania"],
                {
                    "Spełnić żądania": {"money": -1500, "satisfaction": 20},
                    "Negocjować kompromis": {"money": -700, "satisfaction": 5},
                    "Odrzucić żądania": {"satisfaction": -30}
                }
            ),
            
            # WYDARZENIA POZYTYWNE - korzystne dla miasta
            Event(
                "Dotacja Rządowa",
                "Rząd przyznał miastu dotację na rozwój infrastruktury!",
                {"money": 3000, "satisfaction": 10},
                ["Zainwestować w transport", "Zbudować parki", "Odłożyć na później"],
                {
                    "Zainwestować w transport": {"money": 1000, "satisfaction": 15},
                    "Zbudować parki": {"money": 1500, "satisfaction": 20},
                    "Odłożyć na później": {"money": 3000, "satisfaction": 5}
                }
            ),
            Event(
                "Festiwal Miejski",
                "Organizatorzy proponują zorganizowanie wielkiego festiwalu w mieście.",
                {"satisfaction": 5},
                ["Sfinansować festiwal", "Częściowe wsparcie", "Odmówić"],
                {
                    "Sfinansować festiwal": {"money": -1500, "satisfaction": 25, "population": 10},  # Zmniejszone z 20 na 10
                    "Częściowe wsparcie": {"money": -500, "satisfaction": 15},
                    "Odmówić": {"satisfaction": -10}
                }
            ),
            Event(
                "Nowa Firma w Mieście",
                "Duża firma chce otworzyć oddział w waszym mieście.",
                {"population": 25, "satisfaction": 10},  # Zmniejszone z 50 na 25
                ["Dać ulgi podatkowe", "Standardowe warunki", "Odrzucić ofertę"],
                {
                    "Dać ulgi podatkowe": {"money": -500, "population": 40, "satisfaction": 15},  # Zmniejszone z 100 na 40
                    "Standardowe warunki": {"money": 500, "population": 25, "satisfaction": 10},  # Zmniejszone z 50 na 25
                    "Odrzucić ofertę": {"satisfaction": -5}
                }
            ),
            
            # WYDARZENIA SPOŁECZNE - dotyczące relacji z mieszkańcami
            Event(
                "Protest Mieszkańców",
                "Mieszkańcy protestują przeciwko wysokim podatkom i niskiej jakości usług.",
                {"satisfaction": -30},
                ["Obniżyć podatki", "Poprawić usługi", "Zignorować protesty"],
                {
                    "Obniżyć podatki": {"money": -1000, "satisfaction": 20},
                    "Poprawić usługi": {"money": -2000, "satisfaction": 25},
                    "Zignorować protesty": {"satisfaction": -45, "population": -30}
                }
            ),
            Event(
                "Dzień Ziemi",
                "Mieszkańcy organizują obchody Dnia Ziemi i proszą o wsparcie ekologicznych inicjatyw.",
                {"satisfaction": 5},
                ["Sfinansować inicjatywy", "Symboliczne wsparcie", "Nie wspierać"],
                {
                    "Sfinansować inicjatywy": {"money": -1000, "satisfaction": 20},
                    "Symboliczne wsparcie": {"money": -200, "satisfaction": 10},
                    "Nie wspierać": {"satisfaction": -10}
                }
            ),
            
            # WYDARZENIA TECHNOLOGICZNE - związane z innowacjami i nauką
            Event(
                "Innowacja Technologiczna",
                "Lokalni naukowcy opracowali innowacyjną technologię. Chcą wsparcia na dalsze badania.",
                {"satisfaction": 5},
                ["Sfinansować badania", "Częściowe wsparcie", "Odmówić"],
                {
                    "Sfinansować badania": {"money": -2000, "satisfaction": 15},
                    "Częściowe wsparcie": {"money": -800, "satisfaction": 8},
                    "Odmówić": {"satisfaction": -5}
                }
            ),
            
            # WYDARZENIA SEZONOWE - związane z porami roku i pogodą
            Event(
                "Surowa Zima",
                "Nadeszła wyjątkowo surowa zima. Koszty ogrzewania i utrzymania wzrosły.",
                {"money": -1200, "satisfaction": -15},
                ["Zwiększyć pomoc społeczną", "Standardowe działania", "Oszczędzać na wszystkim"],
                {
                    "Zwiększyć pomoc społeczną": {"money": -2000, "satisfaction": 10},
                    "Standardowe działania": {"money": -1200, "satisfaction": -15},
                    "Oszczędzać na wszystkim": {"money": -500, "satisfaction": -30}
                }
            ),
            Event(
                "Fala Upałów",
                "Rekordowe temperatury powodują problemy z dostawami energii i wody.",
                {"money": -800, "satisfaction": -10},
                ["Uruchomić systemy awaryjne", "Racjonować zasoby", "Nic nie robić"],
                {
                    "Uruchomić systemy awaryjne": {"money": -1500, "satisfaction": 5},
                    "Racjonować zasoby": {"money": -400, "satisfaction": -20},
                    "Nic nie robić": {"satisfaction": -25, "population": -20}
                }
            )
        ]
        
        # Statystyki i historia wydarzeń
        self.event_history = []        # lista przeszłych wydarzeń
        self.last_event_turn = 0       # numer ostatniej tury z wydarzeniem
        
    def trigger_random_event(self, game_state=None):
        """
        Wybiera losowe wydarzenie, opcjonalnie uwzględniając stan gry.
        
        Args:
            game_state (dict, optional): aktualny stan gry z informacjami o mieście
            
        Returns:
            Event: wybrane wydarzenie do przeprowadzenia
        """
        # Podstawowa implementacja - wybiera całkowicie losowe wydarzenie
        event = random.choice(self.events)  # random.choice() wybiera losowy element z listy
        
        # Można dodać logikę wyboru wydarzenia na podstawie stanu gry
        if game_state:
            event = self._select_contextual_event(game_state)
        
        # Zapisz w historii wydarzeń dla statystyk
        self.event_history.append({
            'event': event,  # samo wydarzenie
            'turn': game_state.get('turn', 0) if game_state else 0  # numer tury
        })
        
        return event
    
    def _select_contextual_event(self, game_state):
        """
        Wybiera wydarzenie na podstawie kontekstu gry (prywatna metoda).
        
        Args:
            game_state (dict): aktualny stan gry
            
        Returns:
            Event: wydarzenie dopasowane do sytuacji w grze
            
        Ta metoda analizuje stan miasta i wybiera odpowiednie wydarzenia.
        Np. jeśli miasto ma mało pieniędzy, może wybrać wydarzenia ekonomiczne.
        """
        # Pobierz kluczowe parametry stanu gry (domyślne wartości jeśli brak)
        money = game_state.get('money', 0)              # ilość pieniędzy
        population = game_state.get('population', 0)    # liczba mieszkańców
        satisfaction = game_state.get('satisfaction', 50)  # zadowolenie mieszkańców
        
        # Lista wydarzeń odpowiednich dla aktualnej sytuacji
        suitable_events = []
        
        # Przejrzyj wszystkie dostępne wydarzenia
        for event in self.events:
            # Logika wyboru wydarzeń na podstawie stanu miasta
            # Używa operatora "in" do sprawdzania czy tekst występuje w tytule
            if "Kryzys" in event.title and money < 2000:      # gdy mało pieniędzy
                suitable_events.append(event)
            elif "Dotacja" in event.title and satisfaction > 60:  # gdy mieszkańcy zadowoleni
                suitable_events.append(event)
            elif "Protest" in event.title and satisfaction < 40:  # gdy mieszkańcy niezadowoleni
                suitable_events.append(event)
            elif "Festiwal" in event.title and money > 5000:     # gdy dużo pieniędzy
                suitable_events.append(event)
            else:
                # Dodaj wszystkie inne wydarzenia z mniejszym prawdopodobieństwem
                # random.random() zwraca liczbę między 0.0 a 1.0
                if random.random() < 0.3:  # 30% szansy na dodanie
                    suitable_events.append(event)
        
        # Jeśli nie ma odpowiednich wydarzeń, wybierz z wszystkich dostępnych
        if not suitable_events:  # jeśli lista jest pusta
            suitable_events = self.events
        
        # Zwróć losowe wydarzenie z odpowiednich
        return random.choice(suitable_events)
    
    def apply_decision_effects(self, event, decision):
        """
        Zwraca efekty wybranej decyzji gracza.
        
        Args:
            event (Event): wydarzenie, na które gracz reaguje
            decision (str): decyzja wybrana przez gracza
            
        Returns:
            dict: słownik z efektami decyzji (np. {'money': -500, 'satisfaction': 10})
        """
        # Sprawdź czy dla tej decyzji są specjalnie zdefiniowane efekty
        if decision in event.decision_effects:
            return event.decision_effects[decision]  # zwróć specjalne efekty
        else:
            # Jeśli nie ma specjalnych efektów decyzji, zwróć podstawowe efekty wydarzenia
            return event.effects
    
    def get_event_statistics(self):
        """
        Zwraca statystyki wszystkich wydarzeń, które miały miejsce w grze.
        
        Returns:
            dict: statystyki wydarzeń zawierające:
                - total_events: całkowitą liczbę wydarzeń
                - recent_events: listę ostatnich 5 wydarzeń
                - event_types: podział na typy wydarzeń
        """
        # Sprawdź czy w ogóle były jakieś wydarzenia
        if not self.event_history:  # jeśli lista jest pusta
            return {"total_events": 0, "recent_events": []}
        
        return {
            "total_events": len(self.event_history),           # liczba wszystkich wydarzeń
            "recent_events": self.event_history[-5:],          # ostatnie 5 wydarzeń (slice [-5:])
            "event_types": self._count_event_types()          # podział na kategorie
        }
    
    def _count_event_types(self):
        """
        Liczy i kategoryzuje typy wydarzeń w historii (prywatna metoda).
        
        Returns:
            dict: słownik z liczbą wydarzeń każdego typu
        """
        types = {}  # pusty słownik do zliczania
        
        # Przejdź przez wszystkie wydarzenia w historii
        for entry in self.event_history:
            event_title = entry['event'].title  # pobierz tytuł wydarzenia
            
            # Kategoryzuj wydarzenia na podstawie słów kluczowych w tytule
            if "Pożar" in event_title or "Trzęsienie" in event_title or "Epidemia" in event_title:
                # dict.get(klucz, domyślna) zwraca wartość lub domyślną jeśli klucz nie istnieje
                types["Katastrofy"] = types.get("Katastrofy", 0) + 1
            elif "Kryzys" in event_title or "Strajk" in event_title:
                types["Kryzysy"] = types.get("Kryzysy", 0) + 1
            elif "Dotacja" in event_title or "Festiwal" in event_title or "Firma" in event_title:
                types["Pozytywne"] = types.get("Pozytywne", 0) + 1
            elif "Protest" in event_title:
                types["Społeczne"] = types.get("Społeczne", 0) + 1
            else:
                types["Inne"] = types.get("Inne", 0) + 1  # wszystkie inne wydarzenia
        
        return types
