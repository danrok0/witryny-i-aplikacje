# Instrukcje Testowania Nowych Funkcji

## 🎯 System Celów/Misji

### Jak testować:
1. Uruchom grę i kliknij **"Cele"** w menu
2. Sprawdź zakładkę **"Aktywne"** - powinny być widoczne 3 początkowe cele
3. Zbuduj kilka domów i sprawdź postęp celu "Podstawowe Usługi"
4. Osiągnij 250 mieszkańców, aby ukończyć pierwszy cel
5. Po ukończeniu celu sprawdź zakładkę **"Ukończone"**
6. Nowe cele powinny się odblokować automatycznie

### Cele do przetestowania:
- **Łatwe**: Pierwsi Mieszkańcy (250 pop), Podstawowe Usługi (17 budynków), Pierwsza Infrastruktura (20 dróg)
- **Średnie**: Rozwijające się Miasto (1000 pop), Stabilna Ekonomia (75000$), Zadowoleni Mieszkańcy (75% przez 15 tur)
- **Trudne**: Megamiasto (5000 pop), Potęga Ekonomiczna (150000$), Gigant Ekonomiczny (300000$)

## 💾 System Save/Load

### Jak testować:
1. Zbuduj kilka budynków i rozwijaj miasto
2. Kliknij **"Gra" → "Zapisz Grę"**
3. Podaj nazwę zapisu (np. "test1")
4. Plik zostanie zapisany w folderze `saves/`
5. Kliknij **"Gra" → "Wczytaj Grę"**
6. Wybierz plik zapisu z listy
7. Sprawdź czy wszystko zostało wczytane poprawnie

### Co sprawdzić po wczytaniu:
- Budynki na mapie
- Stan ekonomii (pieniądze)
- Populacja
- Poziom miasta
- Cele zostały zresetowane (to normalne)

## 📊 System Raportów

### Jak testować:
1. Graj przez kilka tur (minimum 10)
2. Kliknij **"Raporty"** w menu
3. Sprawdź wszystkie 6 wykresów:
   - Populacja w czasie
   - Budżet miasta
   - Zadowolenie mieszkańców
   - Stopa bezrobocia
   - Przychody vs wydatki
   - Bilans budżetu
4. Zmień zakres czasowy (10/25/50 tur)
5. Kliknij **"Eksportuj CSV"** i sprawdź plik w folderze `exports/`

## 🎲 System Wydarzeń

### Jak testować:
1. Graj normalnie - wydarzenia pojawiają się co 8 tur
2. Gdy pojawi się okno wydarzenia, przeczytaj opis
3. Wybierz jedną z 3 opcji
4. Sprawdź wpływ na miasto (pieniądze, populacja, zadowolenie)
5. Wydarzenia są kontekstowe - różne w zależności od stanu miasta

### Typy wydarzeń do sprawdzenia:
- **Katastrofy**: Pożar, Trzęsienie ziemi, Epidemia
- **Ekonomiczne**: Recesja, Strajki, Dotacje
- **Społeczne**: Protesty, Festiwale
- **Technologiczne**: Innowacje

## 🔬 System Technologii

### Jak testować:
1. Kliknij **"Technologie"** w menu
2. Sprawdź wymagania każdej technologii
3. Osiągnij wymaganą populację i pieniądze
4. Kup technologię
5. Sprawdź wpływ na zadowolenie mieszkańców

### Technologie do odblokowania:
- **Edukacja**: 500 pop, 2000$
- **Zdrowie**: 1000 pop, 3000$
- **Transport**: 2000 pop, 5000$
- **Energia**: 3000 pop, 8000$
- **Ekologia**: 4000 pop, 12000$

## 🚨 Znane Problemy

1. **Cele mogą być trudne** - to zamierzone, aby gra była wyzwaniem
2. **Wydarzenia co 8 tur** - można zmienić częstotliwość w kodzie
3. **Resetowanie celów po load** - to normalne zachowanie
4. **Wykresy mogą być puste** na początku - potrzeba kilku tur danych
5. **Cele nie sprawdzają się w pierwszych 2 turach** - to zamierzone, żeby gracz miał czas na start

## ✅ Naprawione Problemy

1. ✅ **Import Error** - naprawiony błąd importu building
2. ✅ **System Save/Load** - działa poprawnie, przetestowany
3. ✅ **Cele zbyt łatwe** - zwiększone wymagania ekonomiczne
4. ✅ **Cele ukańczające się od razu** - dodano opóźnienie 2 tur
5. ✅ **Nieprawidłowe informacje o budynkach** - naprawiony system poziomów
6. ✅ **Błędny próg poziomów w turze 0** - naprawiony hardkodowany tekst

## 🏗️ System Poziomów Budynków

### Jak testować naprawiony system:
1. Uruchom grę i sprawdź panel "Poziom miasta"
2. Informacje o dostępnych budynkach są teraz prawidłowe:
   - **Poziom 1**: Dom, Sklep, Droga
   - **Poziom 2**: + Zakret drogi, Chodnik, Ratusz, Park
   - **Poziom 3**: + Blok, Targowisko, Magazyn, Szkoła
   - **Poziom 4**: + Fabryka, **Elektrownia**, Policja, Straż Pożarna
   - **Poziom 5**: + Centrum handlowe, Szpital, Oczyszczalnia wody
   - **Poziom 6**: + Wieżowiec
   - **Poziom 7**: + Uniwersytet
   - **Poziom 8**: + Stadion (wszystkie budynki)

3. Panel pokazuje też podgląd budynków na następnym poziomie
4. Przyciski budynków są prawidłowo włączane/wyłączane

### Naprawione błędy:
- ❌ **Elektrownia była pokazana na poziomie 2** → ✅ **Teraz prawidłowo na poziomie 4**
- ❌ **Szkoła była pokazana na poziomie 2** → ✅ **Teraz prawidłowo na poziomie 3**
- ❌ **Szpital był pokazany na poziomie 3** → ✅ **Teraz prawidłowo na poziomie 5**
- ❌ **Uniwersytet był pokazany na poziomie 4** → ✅ **Teraz prawidłowo na poziomie 7**

## 🎯 Wyjaśnienie: Dlaczego próg poziomów się zmienia

**Problem zgłoszony**: "W 0 turze pokazuje mi inny próg ile muszę mieć mieszkańców do następnego poziomu niż w 1 nie powinno tak być"

**Status**: ✅ **NAPRAWIONE** - problem był w kodzie, nie w logice gry!

### Co było nie tak:
1. **Hardkodowana wartość**: Panel miał wpisane na stałe "0/1000 mieszkańców" zamiast prawidłowych "0/600"
2. **Brak aktualizacji**: Funkcja `update_city_level_info()` nie była wywoływana podczas rozpoczynania nowej gry
3. **Wynik**: W turze 0 pokazywało błędną wartość 1000, a dopiero w turze 1 (po pierwszej aktualizacji) pokazywało prawidłowe 600

### Co zostało naprawione:
1. ✅ Zmieniono hardkodowaną wartość z 1000 na 600 w `build_panel.py`
2. ✅ Dodano wywołanie `update_city_level_info()` w funkcji `new_game()` w `Main.py`
3. ✅ Teraz panel pokazuje prawidłowe wartości od samego początku gry

### Jak to sprawdzić:
1. Uruchom nową grę (File → New Game)
2. **Tura 0**: Powinno pokazywać "Do następnego poziomu: 290/600 mieszkańców" (lub podobną wartość ~290)
3. **Tura 1**: Wartość może się zmienić w zależności od wzrostu populacji, ale będzie prawidłowa

**Wniosek**: Problem był rzeczywiście błędem w kodzie i został naprawiony! 🎉

## 💡 Wskazówki

- **Buduj systematycznie**: domy → sklepy → usługi
- **Monitoruj zadowolenie**: buduj parki i usługi
- **Oszczędzaj pieniądze**: na większe cele ekonomiczne
- **Używaj raportów**: do analizy trendów
- **Eksperymentuj z wydarzeniami**: różne wybory = różne efekty

**Powodzenia w testowaniu! 🎮** 