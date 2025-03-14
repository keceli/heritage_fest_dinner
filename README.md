# Heritage Fest Dinner Menu Generator

A Python script to generate PDF dish cards and a menu for Heritage Fest 2025 dinner event.

## Features

- Generates individual dish cards with:
  - Dish name
  - Provider information
  - Cuisine type
  - Ingredients
  - Dietary information
  - Table assignment
  - Heritage Fest logo
- Creates a comprehensive menu organized by dish types
- Automatically assigns table numbers based on dish type and requirements
- Supports emoji removal and text formatting

## Requirements

- Python 3.7+
- reportlab
- pandas
- Pillow

## Usage

1. Place your CSV file with dish information in the project directory
2. Add the Heritage Fest logo (heritage_fest.png) to the project directory
3. Run the script:
   ```bash
   python dish_card.py
   ```

The script will generate:
- Individual dish cards in the `dish_cards` directory
- A complete menu as `menu.pdf`
- An empty dish card template as `dish_card.pdf` 