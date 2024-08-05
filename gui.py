import sys
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QComboBox, \
    QHBoxLayout, QFrame, QStackedWidget, QGroupBox
import webbrowser
import gui_util


class CheckableButton(QPushButton):
    def __init__(self, text, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.setCheckable(True)
        self.setStyleSheet("background-color: #f0f0f0; color: black;")  # Default color
        self.toggled.connect(self.update_color)

    def update_color(self, checked):
        if checked:
            self.setStyleSheet("background-color: #FF734A; color: white;")  # Checked color
        else:
            self.setStyleSheet("background-color: #f0f0f0; color: black;")  # Default color


class NewsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('News Application')
        self.resize(660, 700)
        layout = QVBoxLayout()

        # Categories Section
        categories_layout = QVBoxLayout()
        categories_heading = QLabel('Select Categories:')
        categories_layout.addWidget(categories_heading)

        self.category_buttons = {}
        categories = ['Business', 'Technology', 'Entertainment', 'Sports', 'Science', 'Health', 'World', 'Politics']
        for category in categories:
            button = CheckableButton(category)
            self.category_buttons[category] = button
            categories_layout.addWidget(button)

        # Country Section
        country_layout = QVBoxLayout()
        country_heading = QLabel('Select Country:')
        country_layout.addWidget(country_heading)

        # Create a container layout for country selection to align items
        country_selection_layout = QHBoxLayout()

        self.country_combobox = QComboBox(self)
        self.country_combobox.setFixedWidth(200)  # Set fixed width smaller than the window
        self.country_combobox.addItems(['South Sudan', 'Zambia', 'Other'])
        self.country_combobox.currentTextChanged.connect(self.update_country_input_visibility)
        country_selection_layout.addWidget(self.country_combobox)

        self.country_input = QLineEdit(self)
        self.country_input.setPlaceholderText('Enter country')
        self.country_input.setFixedWidth(200)  # Set fixed width smaller than the window
        self.country_input.setVisible(False)
        country_selection_layout.addWidget(self.country_input)

        country_layout.addLayout(country_selection_layout)

        # Fetch Button
        self.fetch_button = QPushButton('Fetch News', self)
        self.fetch_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 12px;")
        self.fetch_button.setFixedWidth(100)
        self.fetch_button.setFixedHeight(30)
        self.fetch_button.clicked.connect(self.fetch_news)

        # Navigation Buttons
        button_layout = QHBoxLayout()
        self.articles_button = QPushButton('Articles', self)
        self.articles_button.setFixedWidth(100)
        self.articles_button.setFixedHeight(30)
        self.articles_button.clicked.connect(self.show_articles)

        button_layout.addWidget(self.articles_button)

        # Create a QWidget to hold the scrollable content
        self.results_container = QStackedWidget(self)
        self.news_frame = QFrame()
        self.news_frame.setFrameShape(QFrame.Shape.Box)
        self.news_layout = QVBoxLayout()
        self.news_frame.setLayout(self.news_layout)

        # Add frames to the stacked widget
        self.results_container.addWidget(self.news_frame)

        # Create a QScrollArea and set the results_container as its widget
        scroll_area = QScrollArea(self)
        scroll_area.setWidget(self.results_container)
        scroll_area.setWidgetResizable(True)

        # Add widgets to the main layout
        layout.addLayout(categories_layout)
        layout.addLayout(country_layout)
        layout.addWidget(self.fetch_button)
        layout.addLayout(button_layout)  # Add the button layout here
        layout.addWidget(scroll_area)

        self.setLayout(layout)

        # Initialize with articles view
        self.show_articles()

    def update_country_input_visibility(self, text):
        if text == 'Other':
            self.country_input.setVisible(True)
        else:
            self.country_input.setVisible(False)
            self.country_input.clear()

    def fetch_news(self):
        try:
            categories = [cat for cat, button in self.category_buttons.items() if button.isChecked()]
            country = self.country_combobox.currentText()

            if country == 'Other':
                country = self.country_input.text().strip()

            # Ensure country input is not empty if 'Other' is selected
            if country == '':
                self.country_input.setFocus()
                return

            # Fetch news data
            df = gui_util.scrape_news(country, categories)
            if 'title' not in df.columns:
                print("Error: 'title' column not found in DataFrame.")
                return

            df['Sentiment'] = df['title'].apply(gui_util.analyze_sentiment)
            df['Sector Impact'] = df['title'].apply(gui_util.analyze_sector_impact)

            # Limit to a maximum of 10 articles
            displayed_articles = df.head(10)
            df = df[~df['title'].isin(displayed_articles['title'])]  # Exclude displayed articles

            # Clear previous results
            for i in reversed(range(self.news_layout.count())):
                widget = self.news_layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

            for _, row in displayed_articles.iterrows():
                article_group = QGroupBox()
                article_layout = QVBoxLayout()

                title_label = QLabel(f"Title: {row['title']}")
                title_label.setWordWrap(True)  # Enable text wrapping
                article_layout.addWidget(title_label)

                published_label = QLabel(f"Published at: {row['publishedAt']}")
                article_layout.addWidget(published_label)

                sentiment_label = QLabel(f"Sentiment: {row['Sentiment']}")
                article_layout.addWidget(sentiment_label)

                # Display sector impact analysis
                sector_impact = row['Sector Impact']
                impact_labels = [QLabel(f"{sector}: {impact:.2f}") for sector, impact in sector_impact.items()]
                for label in impact_labels:
                    article_layout.addWidget(label)

                if row.get('image'):
                    image_label = QLabel()
                    try:
                        image_label.setPixmap(QPixmap(row['image']))  # Handle image downloading here
                    except Exception as e:
                        print(f"Error loading image: {e}")
                    article_layout.addWidget(image_label)

                link_button = QPushButton('Read more')
                link_button.clicked.connect(lambda checked, url=row['link']: webbrowser.open(url))
                link_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 12px;")
                link_button.setFixedWidth(100)
                link_button.setFixedHeight(30)
                article_layout.addWidget(link_button)

                article_group.setLayout(article_layout)
                self.news_layout.addWidget(article_group)

            self.results_container.setCurrentWidget(self.news_frame)

        except Exception as e:
            print(f"An error occurred: {e}")

    def show_articles(self):
        self.results_container.setCurrentWidget(self.news_frame)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NewsApp()
    window.show()
    sys.exit(app.exec())
