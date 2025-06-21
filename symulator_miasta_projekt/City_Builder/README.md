# 🏙️ City Builder - Zaawansowany Symulator Miasta

## 📋 Opis Gry

City Builder to kompleksowy symulator zarządzania miastem, w którym wcielasz się w rolę burmistrza odpowiedzialnego za rozwój prosperującego miasta. Zarządzaj zasobami, populacją, ekonomią i odpowiadaj na wyzwania, które niesie ze sobą kierowanie rozwijającym się miastem.

## 🎮 Zasady Gry

### 🎯 Cel Gry
Twoim zadaniem jest zbudowanie i utrzymanie prosperującego miasta, które zadowoli wszystkich mieszkańców. Musisz balansować różne aspekty zarządzania: finanse, populację, zasoby i infrastrukturę, reagując na wydarzenia losowe i podejmując strategiczne decyzje.

### 🕒 Mechanika Rozgrywki
Gra działa w systemie turowym - każda tura reprezentuje okres czasu, w którym:
- Aktualizują się zasoby miasta
- Populacja rozwija się demograficznie
- Wpływają podatki i ponoszane są koszty
- Mogą wystąpić wydarzenia losowe
- Budynki generują efekty dla miasta

## 🏗️ System Budynków

### 📚 Kategorie Budynków

#### 🏠 **Budynki Mieszkalne**
- **Dom** - podstawowe mieszkanie dla 35 osób
- **Blok** - mieszkanie dla 70 osób średniej klasy
- **Wieżowiec** - luksusowe mieszkanie dla 150 osób klasy wyższej

*Wpływ na miasto:* zwiększają populację i generują podatki mieszkaniowe

#### 🏢 **Budynki Komercyjne**
- **Sklep** - podstawowy handel, zatrudnia 12 osób
- **Targowisko** - rozwinięty handel, zatrudnia 20 osób  
- **Centrum Handlowe** - nowoczesny handel, zatrudnia 40 osób

*Wpływ na miasto:* generują miejsca pracy, podatki komercyjne i zwiększają zadowolenie mieszkańców

#### 🏭 **Budynki Przemysłowe**
- **Fabryka** - produkuje towary, zatrudnia 35 osób, generuje zanieczyszczenia
- **Magazyn** - przechowuje zasoby, zatrudnia 15 osób
- **Elektrownia** - dostarcza energię, zatrudnia 20 osób

*Wpływ na miasto:* produkują zasoby, zatrudniają mieszkańców, mogą generować zanieczyszczenia

#### 🏛️ **Usługi Publiczne**
- **Ratusz** - centrum administracyjne, zwiększa efektywność zarządzania
- **Szkoła** - edukacja podstawowa, zatrudnia 20 nauczycieli
- **Uniwersytet** - wyższa edukacja, zatrudnia 40 wykładowców
- **Szpital** - opieka zdrowotna, zatrudnia 25 lekarzy
- **Komisariat Policji** - bezpieczeństwo, zatrudnia 15 policjantów
- **Straż Pożarna** - ochrona przeciwpożarowa, zatrudnia 12 strażaków
- **Oczyszczalnia Wody** - dostarcza czystą wodę

*Wpływ na miasto:* zwiększają zadowolenie mieszkańców i jakość życia

#### 🎪 **Budynki Rekreacyjne**
- **Park** - zwiększa zadowolenie i poprawia środowisko
- **Stadion** - rozrywka i turystyka, zatrudnia 35 osób

*Wpływ na miasto:* znacznie zwiększają zadowolenie mieszkańców

#### 🛣️ **Infrastruktura**
- **Droga** - umożliwia transport i dostęp do budynków
- **Chodnik** - poprawia komunikację pieszą
- **Zakręt drogi** - pozwala na tworzenie skrzyżowań

*Wpływ na miasto:* niezbędne dla funkcjonowania innych budynków

## 💰 System Ekonomiczny

### 🏦 Zasoby Miejskie

#### **Pieniądze** 💰
- **Źródła przychodów:** podatki od mieszkańców, firm i przemysłu
- **Wydatki:** budowa budynków, koszty utrzymania, programy społeczne
- **Zarządzanie:** ustalanie stawek podatkowych dla różnych sektorów

#### **Energia** ⚡
- **Źródła:** elektrownie, alternatywne źródła energii
- **Zużycie:** wszystkie budynki wymagają energii do funkcjonowania
- **Brak energii:** budynki działają mniej efektywnie

#### **Woda** 💧
- **Źródła:** oczyszczalnie wody, naturalne źródła
- **Zużycie:** mieszkańcy i przemysł
- **Brak wody:** spadek zadowolenia i zdrowia populacji

#### **Materiały Budowlane** 🔨
- **Źródła:** import, lokalna produkcja
- **Zużycie:** budowa nowych budynków
- **Ograniczenia:** brak materiałów blokuje ekspansję

#### **Żywność** 🍞
- **Źródła:** import, lokalne gospodarstwa
- **Zużycie:** populacja miasta
- **Brak żywności:** spadek zdrowia i zadowolenia

#### **Towary Luksusowe** 💎
- **Źródła:** import, lokalna produkcja
- **Zużycie:** klasa średnia i wyższa
- **Wpływ:** zwiększają zadowolenie zamożniejszych mieszkańców

### 📈 System Podatkowy
Możesz ustalać różne stawki podatkowe (0-20%) dla:
- **Budynków mieszkalnych** - wpływa na migrację
- **Firm komercyjnych** - wpływa na rozwój handlu
- **Przemysłu** - wpływa na produkcję

**Zasada:** Wyższe podatki = więcej przychodów, ale może to zniechęcić mieszkańców i inwestorów

## 👥 System Populacji

### 🎭 Grupy Społeczne

#### **Robotnicy** 🔧
- **Potrzeby:** podstawowe mieszkania, praca w przemyśle/handlu
- **Wrażliwość:** na bezrobocie i koszty utrzymania
- **Podatki:** niskie, ale stanowią dużą część populacji

#### **Klasa Średnia** 🏢
- **Potrzeby:** lepsze mieszkania, edukacja, opieka zdrowotna
- **Wrażliwość:** na jakość usług publicznych
- **Podatki:** średnie, stabilne dochody

#### **Klasa Wyższa** 💼
- **Potrzeby:** luksusowe mieszkania, wysokiej jakości usługi
- **Wrażliwość:** na bezpieczeństwo i prestiż miasta
- **Podatki:** wysokie, ale wymagają najlepszych warunków

#### **Studenci** 🎓
- **Potrzeby:** edukacja, przystępne mieszkania
- **Wrażliwość:** na dostępność uniwersytetów
- **Przyszłość:** mogą zostać i zwiększyć klasę średnią

#### **Bezrobotni** 😔
- **Sytuacja:** brak pracy, obciążenie dla miasta
- **Potrzeby:** miejsca pracy, programy społeczne
- **Ryzyko:** wysokie bezrobocie prowadzi do problemów społecznych

### 📊 Czynniki Wpływające na Populację

#### **Zadowolenie Mieszkańców**
- **Pozytywne:** parki, szpitale, szkoły, bezpieczeństwo, niska przestępczość
- **Negatywne:** zanieczyszczenia, wysokie podatki, brak usług, bezrobocie
- **Skutki:** wysokie zadowolenie przyciąga nowych mieszkańców

#### **Migracje**
- **Imigracja:** zadowolone miasto przyciąga nowych mieszkańców
- **Emigracja:** problemy w mieście powodują odpływ ludności
- **Równowaga:** cel to stabilny wzrost populacji

#### **Demografia**
- **Urodziny:** naturalne zwiększenie populacji
- **Zgony:** naturalne zmniejszenie populacji
- **Czynniki:** poziom opieki zdrowotnej wpływa na wskaźniki demograficzne

## 🎲 System Wydarzeń Losowych

### 🌪️ Typy Wydarzeń

#### **Katastrofy Naturalne**
- **Powódź** - zniszczenia budynków, koszty odbudowy
- **Pożar** - straty w infrastrukturze, potrzeba straży pożarnej
- **Trzęsienie ziemi** - masowe zniszczenia, duże koszty
- **Susza** - problemy z wodą, spadek produkcji rolnej

#### **Wydarzenia Ekonomiczne**
- **Kryzys ekonomiczny** - spadek przychodów z podatków
- **Boom gospodarczy** - zwiększone przychody i inwestycje
- **Inflacja** - wzrost kosztów budowy i utrzymania
- **Odkrycie złóż** - nowe źródło przychodów

#### **Wydarzenia Społeczne**
- **Epidemia** - spadek populacji, potrzeba lepszej opieki zdrowotnej
- **Strajk** - czasowe zatrzymanie produkcji
- **Festival** - zwiększenie zadowolenia i turystyki
- **Fala przestępczości** - potrzeba więcej policji

#### **Wydarzenia Technologiczne**
- **Nowa technologia** - możliwość budowy nowych typów budynków
- **Przełom w medycynie** - poprawa wskaźników zdrowia
- **Innowacja energetyczna** - tańsza energia
- **Cyfryzacja** - zwiększenie efektywności administracji

### 🤔 Podejmowanie Decyzji
Większość wydarzeń wymaga podjęcia decyzji:
- **Opcja A:** Często kosztowna, ale z długoterminowymi korzyściami
- **Opcja B:** Tańsza, ale może mieć negatywne skutki
- **Opcja C:** Brak działania - czasem najmądrzejszy wybór

**Przykład:**
*Wybuch epidemii w mieście*
- **Zamknij miasto** - kosztowne, ale zatrzyma epidemię
- **Zwiększ finansowanie szpitali** - drogie, ale ratuje życie
- **Ignoruj problem** - tanio, ale epidemia się rozprzestrzeni

## 🤝 System Dyplomacji i Handlu

### 🏛️ Miasta Sąsiednie
Wokół twojego miasta znajduje się 5 innych miast/państw:
- **Porta Marina** - miasto portowe, specjalizuje się w handlu morskim
- **Górny Przemysł** - centrum przemysłowe, ma dużo fabryk
- **Zielone Doliny** - region rolniczy, produkuje żywność
- **Technopolis** - centrum technologiczne, oferuje innowacje
- **Stara Stolica** - historyczne miasto, centrum kultury

### 💼 Handel Międzynarodowy
#### **Eksport**
- Sprzedajesz nadwyżki swoich zasobów
- Ceny zależą od popytu i relacji dyplomatycznych
- Regularne umowy handlowe zapewniają stały dochód

#### **Import**
- Kupujesz potrzebne zasoby
- Ceny zależą od dostępności i relacji
- Niektóre zasoby mogą być dostępne tylko z importu

#### **Negocjacje**
- Możliwość negocjowania lepszych cen
- Długoterminowe umowy zapewniają stabilność
- Relacje dyplomatyczne wpływają na warunki handlu

### 🕊️ Relacje Dyplomatyczne
#### **Poziomy Relacji**
- **Sojusz** - najlepsze ceny, wspólne projekty, pomoc w kryzysach
- **Przyjażń** - dobre ceny, współpraca
- **Neutralność** - standardowe warunki handlu
- **Napięcie** - gorsze ceny, możliwe sankcje
- **Konflikt** - brak handlu, możliwe sabotaże

#### **Akcje Dyplomatyczne**
- **Misje handlowe** - poprawa relacji poprzez handel
- **Pomoc humanitarna** - wsparcie w kryzysach buduje zaufanie
- **Projekty współpracy** - wspólne inwestycje
- **Sankcje** - działania wymuszające, ale pogarszające relacje

## 🎯 Poziomy Miasta i Rozwój

### 📈 System Poziomów
Twoje miasto rozwija się przez 10 poziomów (1-10), każdy odblokowany przez osiągnięcie określonej populacji:

- **Poziom 1:** 0 mieszkańców - miasto startowe
- **Poziom 2:** 600 mieszkańców - odblokowuje parki, ratusz
- **Poziom 3:** 1,400 mieszkańców - odblokowuje bloki, szkoły
- **Poziom 4:** 2,800 mieszkańców - odblokowuje fabryki, policję
- **Poziom 5:** 5,000 mieszkańców - odblokowuje szpitale, centra handlowe
- **Poziom 6:** 8,000 mieszkańców - odblokowuje wieżowce
- **Poziom 7:** 12,000 mieszkańców - odblokowuje uniwersytety
- **Poziom 8:** 17,000 mieszkańców - odblokowuje stadiony
- **Poziom 9:** 23,000 mieszkańców - odblokowuje zaawansowane technologie
- **Poziom 10:** 30,000 mieszkańców - metropolia, wszystkie budynki dostępne

### 🔓 Odblokowywanie Budynków
Każdy poziom miasta odblokuje nowe możliwości:
- **Nowe typy budynków** - bardziej efektywne i zaawansowane
- **Większe limity** - możliwość budowy więcej budynków
- **Nowe technologie** - ulepszenia istniejących systemów
- **Nowe opcje dyplomatyczne** - większy wpływ na sąsiadów

## 📊 System Raportowania

### 📈 Dostępne Raporty
- **Raport Demograficzny** - analiza populacji i migracji
- **Raport Ekonomiczny** - przychody, wydatki, trendy finansowe
- **Raport Zasobów** - produkcja i zużycie wszystkich zasobów
- **Raport Zadowolenia** - analiza zadowolenia różnych grup społecznych
- **Raport Budynków** - efektywność i koszty utrzymania infrastruktury
- **Raport Środowiskowy** - zanieczyszczenia i działania ekologiczne
- **Raport Dyplomatyczny** - status relacji z sąsiednimi miastami

### 📉 Analizy i Trendy
- **Wykresy historyczne** - śledzenie zmian w czasie
- **Prognozy** - przewidywanie przyszłych trendów
- **Porównania** - analiza różnych okresów
- **Eksport danych** - możliwość zapisu raportów do plików

## 🏆 System Osiągnięć

### 🎖️ Kategorie Osiągnięć
- **Populacyjne** - osiągnięcia związane z rozwojem demograficznym
- **Ekonomiczne** - sukcesy w zarządzaniu finansami
- **Budowlane** - osiągnięcia w rozwoju infrastruktury
- **Technologiczne** - postęp w badaniach i rozwoju
- **Środowiskowe** - dbanie o ekologię miasta
- **Dyplomatyczne** - sukcesy w relacjach międzynarodowych
- **Specjalne** - unikalne wyzwania i osiągnięcia

## 🎮 Tryby Gry

### 🏖️ **Tryb Piaskownica**
- Nieograniczone zasoby początkowe
- Brak ograniczeń czasowych
- Możliwość eksperymentowania
- Idealny do nauki mechanik gry

### 📜 **Tryb Scenariuszy**
- Predefiniowane wyzwania
- Określone cele do osiągnięcia
- Unikalne warunki startowe
- Różne poziomy trudności

### ⚡ **Tryb Wyzwania**
- Ograniczony czas lub zasoby
- Intensywna rozgrywka
- Wymagania dotyczące efektywności
- Dla doświadczonych graczy

### 🎯 **Tryb Kampanii**
- Sekwencja połączonych scenariuszy
- Progresja między misjami
- Rozwijająca się fabuła
- Długoterminowe cele

## 🔧 Sterowanie i Interface

### ⌨️ Klawisze
- **Spacja** - pauza/wznowienie gry
- **R** - obrót wybranego budynku przed postawieniem
- **ESC** - anulowanie obecnego działania
- **F1** - pomoc kontekstowa
- **Ctrl+S** - szybki zapis gry
- **Ctrl+L** - wczytanie gry

### 🖱️ Mysz
- **Lewy klik** - wybór budynku/akcji
- **Prawy klik** - anulowanie/menu kontekstowe
- **Kółko myszy** - zoom mapy
- **Przeciąganie** - przewijanie mapy

### 🎛️ Interfejs
- **Panel budowy** (prawo) - wybór budynków do postawienia  
- **Panel zasobów** (góra) - aktualne zasoby miasta
- **Panel informacyjny** (dół) - komunikaty i alerty
- **Mapa** (centrum) - główny obszar gry
- **Menu** (góra) - opcje gry i zapisywanie

## 💡 Wskazówki dla Graczy

### 🚀 **Start Gry**
1. **Zacznij od podstaw** - postaw kilka domów i sklepów
2. **Zbuduj infrastrukturę** - drogi są kluczowe
3. **Monitoruj zasoby** - nie pozwól na wyczerpanie energii/wody
4. **Obserwuj zadowolenie** - niezadowoleni mieszkańcy emigrują

### 📈 **Rozwój Miasta**  
1. **Balansuj podatki** - za wysokie zniechęcą mieszkańców
2. **Inwestuj w usługi** - szpitale i szkoły zwiększają zadowolenie
3. **Planuj długoterminowo** - niektóre budynki to długoterminowe inwestycje
4. **Dywersyfikuj ekonomię** - nie polegaj tylko na jednym sektorze

### ⚠️ **Zarządzanie Kryzysami**
1. **Utrzymuj rezerwy** - zawsze miej zapas pieniędzy na emergencje
2. **Przygotuj się na wydarzenia** - niektóre można przewidzieć
3. **Nie panikuj** - większość problemów ma rozwiązanie
4. **Ucz się na błędach** - każdy kryzys to lekcja na przyszłość

### 🌟 **Zaawansowane Strategie**
1. **Specjalizuj się** - rozwijaj mocne strony miasta
2. **Buduj sojusze** - dobre relacje dyplomatyczne są cenne
3. **Inwestuj w przyszłość** - edukacja i technologie zwracają się długoterminowo
4. **Adaptuj się** - bądź gotowy na zmianę strategii

---

## 📁 Struktura Projektu

```
City_Builder/
├── Main.py                 # Główny plik aplikacji
├── requirements.txt        # Zależności Python
├── core/                  # Logika gry
│   ├── game_engine.py     # Główny silnik gry
│   ├── city_map.py        # System mapy miasta
│   ├── resources.py       # Zarządzanie zasobami
│   ├── population.py      # System populacji
│   ├── events.py          # Wydarzenia losowe
│   ├── diplomacy.py       # System dyplomacji
│   └── tile.py            # Kafelki i budynki
├── gui/                   # Interfejs użytkownika
├── assets/                # Grafiki i zasoby
├── saves/                 # Zapisy gry
├── data/                  # Dane konfiguracyjne
└── tests/                 # Testy jednostkowe
```

## 🚀 Instalacja i Uruchomienie

### Wymagania Systemowe
- **Python 3.8+** (zalecane Python 3.11)
- **System operacyjny:** Windows 10+, macOS 10.14+, Linux Ubuntu 18.04+
- **RAM:** Minimum 4GB, zalecane 8GB
- **Miejsce na dysku:** 500MB dla aplikacji + 1GB dla danych

### Instalacja

1. **Przygotowanie środowiska:**
```bash
# Sklonuj projekt
git clone [repo_url]
cd City_Builder

# Utwórz środowisko wirtualne
python -m venv city_builder_env

# Aktywuj środowisko (Windows)
city_builder_env\Scripts\activate

# Aktywuj środowisko (macOS/Linux)  
source city_builder_env/bin/activate
```

2. **Instalacja zależności:**
```bash
# Zainstaluj wszystkie wymagane pakiety
pip install -r requirements.txt
```

3. **Uruchomienie gry:**
```bash
# Uruchom główną aplikację
python Main.py
```

---

*Miłej zabawy w zarządzaniu swoim miastem! 🏙️✨*
