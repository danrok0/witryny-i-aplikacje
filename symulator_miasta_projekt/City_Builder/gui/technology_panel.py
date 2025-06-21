from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QLabel, QPushButton

class TechnologyPanel(QWidget):
    def __init__(self, technology_tree, game_engine, parent=None):
        super().__init__(parent)
        self.technology_tree = technology_tree
        self.game_engine = game_engine
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create list widget for technologies
        self.technology_list = QListWidget()
        for tech in self.technology_tree.technologies.values():
            if not tech.is_researched:
                self.technology_list.addItem(tech.name)
        layout.addWidget(self.technology_list)

        # Create label for technology details
        self.details_label = QLabel("Wybierz technologię, aby zobaczyć szczegóły")
        layout.addWidget(self.details_label)

        # Create button to unlock technology
        self.unlock_button = QPushButton("Odblokuj technologię")
        self.unlock_button.clicked.connect(self.unlock_selected_technology)
        layout.addWidget(self.unlock_button)

        # Connect selection change to update details
        self.technology_list.itemSelectionChanged.connect(self.update_details)

        self.setLayout(layout)

    def unlock_selected_technology(self):
        selected_items = self.technology_list.selectedItems()
        if selected_items:
            technology_name = selected_items[0].text()
            for tech in self.technology_tree.technologies.values():
                if tech.name == technology_name and not tech.is_researched:
                    # Sprawdź czy można rozpocząć badanie
                    can_research, reason = self.technology_tree.can_research(tech.id)
                    
                    if can_research and self.game_engine.economy.get_resource_amount('money') >= tech.cost:
                        # Rozpocznij badanie
                        if self.technology_tree.start_research(tech.id):
                            self.game_engine.economy.spend_money(tech.cost)
                            
                            # Natychmiast ukończ badanie dla uproszczenia
                            tech.research_progress = tech.research_time
                            completed_tech = self.technology_tree.update_research()
                            
                            if completed_tech:
                                # Zastosuj efekty technologii
                                for effect, value in completed_tech.effects.items():
                                    if effect == "happiness_bonus":
                                        for group in self.game_engine.population.groups.values():
                                            group.satisfaction = min(100, group.satisfaction + value * 10)
                                
                                self.technology_list.takeItem(self.technology_list.row(selected_items[0]))
                                self.details_label.setText(f"Odblokowano technologię: {technology_name}")
                            else:
                                self.details_label.setText("Błąd podczas odblokowywania technologii!")
                        else:
                            self.details_label.setText("Nie można rozpocząć badania!")
                    else:
                        self.details_label.setText(f"Nie można badać: {reason}")

    def update_details(self):
        selected_items = self.technology_list.selectedItems()
        if selected_items:
            technology_name = selected_items[0].text()
            for tech in self.technology_tree.technologies.values():
                if tech.name == technology_name:
                    # Sprawdź prerequisity
                    prereq_text = "Brak" if not tech.prerequisites else ", ".join([
                        self.technology_tree.technologies[prereq_id].name 
                        for prereq_id in tech.prerequisites
                    ])
                    
                    eff_text = ", ".join([f"{k}: +{v}" for k, v in tech.effects.items()])
                    
                    self.details_label.setText(
                        f"Opis: {tech.description}\n"
                        f"Koszt: ${tech.cost:,}\n"
                        f"Czas badania: {tech.research_time} tur\n"
                        f"Wymagania: {prereq_text}\n"
                        f"Efekty: {eff_text}"
                    )
                    break
        else:
            self.details_label.setText("Wybierz technologię, aby zobaczyć szczegóły") 