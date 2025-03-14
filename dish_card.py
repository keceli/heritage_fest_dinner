from __future__ import unicode_literals
import pandas as pd
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, Color
from reportlab.lib.units import inch
from PIL import Image
import sys
import re

# Colors
NAVY_BLUE = Color(0.0, 0.12, 0.36)  # Dark blue color
ORANGE = Color(1.0, 0.5, 0.0)  # Orange color

# Path to your CSV file
csv_file = "hf25_responses3.csv"
logo_path = "heritage_fest.png"

# Column names from the actual CSV
dish_column = "Name of the dish:"
desc_columns = [
    "Represented cuisine:",
    "Type of the dish:",
    "Ingredients:",
    "Protein/Category:",
    "Allergens:",  # Simplified allergen title
]
provider_column = "Provided by:"
outlet_column = "Do you need an electrical outlet?"

# Try reading the CSV file with different encodings
encodings = ["utf-8", "utf-8-sig", "utf-16"]
df = None
for encoding in encodings:
    try:
        df = pd.read_csv(csv_file, encoding=encoding)
        print(f"Successfully read CSV with {encoding} encoding")
        break
    except UnicodeDecodeError:
        continue

if df is None:
    print("Error: Could not read CSV file with any of the attempted encodings")
    sys.exit(1)

# Rename the allergen column in the dataframe
df = df.rename(
    columns={"Allergen (Nuts are not allowed, see ACS allergy policy):": "Allergens:"}
)

# Create an output folder for the dish cards if it doesn't exist
output_dir = "dish_cards"
os.makedirs(output_dir, exist_ok=True)

# No need to register fonts - using built-in ReportLab fonts


def remove_emojis(text):
    """Remove specific food and dietary emojis from text"""
    # Create a mapping of emojis to their text representations
    emoji_map = {
        " 🌙": "(Halal)",
        " ✡️": "(Kosher)",
        " 🥦": "(Vegetarian)",
        " 🐖": "(Pork)",
        " 🐔": "(Poultry)",
        " 🐄": "(Beef)",
        " 🌱": "(Vegan)",
    }

    # Replace each emoji with its text representation or remove it
    result = str(text)
    for emoji, replacement in emoji_map.items():
        result = result.replace(emoji, "")  # Just remove the emoji without replacement

    return result.strip()


def draw_text(canvas_obj, text, x, y, font_name, font_size, max_width=None):
    """Draw text with clean formatting"""
    canvas_obj.setFont(font_name, font_size)
    clean_text = remove_emojis(text).strip()
    if max_width is None:
        canvas_obj.drawString(x, y, clean_text)
        return canvas_obj.stringWidth(clean_text, font_name, font_size)
    return 0


def wrap_text(text, font_name, font_size, max_width, canvas_obj):
    """Helper function to wrap text"""
    clean_text = remove_emojis(text).strip()
    words = clean_text.split()
    lines = []
    current_line = []
    current_width = 0

    for word in words:
        word_width = canvas_obj.stringWidth(word + " ", font_name, font_size)
        if current_width + word_width <= max_width:
            current_line.append(word)
            current_width += word_width
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def get_table_number(dish_type, needs_outlet):
    """Assign table number based on dish type and outlet requirement"""
    # Convert to string and lowercase for consistent comparison
    dish_type = str(dish_type).lower().strip()
    needs_outlet = str(needs_outlet).lower().strip()

    # Table 3 for dishes requiring outlet or desserts/drinks
    if needs_outlet == "yes" or dish_type in ["dessert", "drink"]:
        return 3
    # Table 1 for appetizers
    elif dish_type == "appetizer":
        return 1
    # Table 2 for salads and main courses
    elif dish_type in ["salad", "main course"]:
        return 2
    # Default to table 3 if type is unknown
    else:
        return 3


def create_dish_card(row, idx):
    # Create PDF with letter size
    output_path = os.path.join(output_dir, f"dish_card_{idx+1}.pdf")
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Set margins and initial position
    margin = 72  # 1 inch in points
    content_width = width - 2 * margin
    header_height = 100  # Increased header height for longer titles

    # Draw colored header background
    c.setFillColor(NAVY_BLUE)
    c.rect(
        margin, height - margin - header_height, content_width, header_height, fill=1
    )

    # Draw border with orange color
    c.setStrokeColor(ORANGE)
    c.setLineWidth(3)
    c.rect(margin, margin, content_width, height - 2 * margin)

    current_y = height - margin - 40  # Start 20 points from top of header

    # Draw dish name (title) in white
    c.setFillColor("white")
    dish_name = str(row[dish_column])
    title_font = "Helvetica-Bold"
    title_size = 28

    # Wrap title text
    title_lines = wrap_text(dish_name, title_font, title_size, content_width - 40, c)

    # Center title vertically in header
    title_total_height = len(title_lines) * 30  # 30 points per line
    title_y = current_y - (header_height - title_total_height) / 2 + 20

    # Draw title lines
    for line in title_lines:
        line_width = c.stringWidth(line, title_font, title_size)
        x = (width - line_width) / 2
        draw_text(c, line, x, title_y, title_font, title_size)
        title_y -= 30

    current_y = height - margin - header_height - 40

    # Draw provider
    c.setFillColor(NAVY_BLUE)
    provider = f"Provided by: {str(row[provider_column])}"
    provider_lines = wrap_text(provider, "Helvetica-Bold", 18, content_width - 40, c)

    for line in provider_lines:
        line_width = c.stringWidth(line, "Helvetica-Bold", 18)
        x = (width - line_width) / 2
        draw_text(c, line, x, current_y, "Helvetica-Bold", 18)
        current_y -= 25

    current_y -= 20  # Extra space after provider

    # Calculate space needed for logo
    logo_height = 100
    logo_margin = 20
    min_y = margin + logo_height + logo_margin

    # Initialize left and right columns
    left_margin = margin + 20
    right_margin = margin + content_width / 2 + 10
    current_x = left_margin
    original_y = current_y

    # Draw other information in two columns
    for i, column in enumerate(desc_columns):
        if pd.notna(row[column]):
            # Switch to right column if we're running out of space
            if current_y < min_y and current_x == left_margin:
                current_x = right_margin
                current_y = original_y
            elif current_y < min_y:
                break  # Stop if we run out of space in both columns

            # Draw label
            c.setFillColor(NAVY_BLUE)
            label = f"{column.replace(':', '')}: "
            draw_text(c, label, current_x, current_y, "Helvetica-Bold", 14)
            label_width = c.stringWidth(label, "Helvetica-Bold", 14)

            # Calculate available width for value
            # Increase the available width by reducing the margins
            if column == "Ingredients:":
                # Give more space for ingredients
                available_width = (
                    (content_width / 2 - 10)
                    if current_x == left_margin
                    else (content_width / 2 - 10)
                )
            else:
                # Standard width for other fields
                available_width = (
                    (content_width / 2 - 25)
                    if current_x == left_margin
                    else (content_width / 2 - 15)
                )

            # Draw value
            value = str(row[column])
            value_lines = wrap_text(value, "Helvetica", 14, available_width, c)

            for line in value_lines:
                draw_text(c, line, current_x + label_width, current_y, "Helvetica", 14)
                current_y -= 20

            current_y -= 10  # Extra space between fields

    # Add electrical outlet requirement
    current_y -= 10  # Extra space before outlet info
    outlet_needed = str(row[outlet_column]).strip()
    outlet_text = f"Electrical Outlet Required: {outlet_needed}"
    c.setFillColor(NAVY_BLUE)
    # Left align the outlet text with the same margin as other content
    draw_text(c, outlet_text, left_margin, current_y, "Helvetica", 12)
    current_y -= 30  # Space after outlet info

    # Add the Heritage Fest logo at the bottom
    if os.path.exists(logo_path):
        img = Image.open(logo_path)
        aspect = img.width / img.height
        logo_width = logo_height * aspect

        # Calculate centered position for logo
        logo_x = (width - logo_width) / 2
        logo_y = margin + 10

        # Draw the logo
        c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)

    # Save the page
    c.save()


def create_menu():
    """Create a menu PDF organized by dish types with enhanced styling"""
    # Create PDF with letter size
    output_path = "menu.pdf"
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Set margins and initial position
    margin = 72  # 1 inch in points
    content_width = width - 2 * margin

    def draw_page_header(is_first_page=False):
        # Add the Heritage Fest logo at the top left only on the first page
        if is_first_page and os.path.exists(logo_path):
            img = Image.open(logo_path)
            aspect = img.width / img.height
            logo_height = 90  # Reduced logo height
            logo_width = logo_height * aspect

            # Position logo on the left
            logo_x = margin
            logo_y = height - margin - logo_height

            # Draw the logo
            c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)

            # Draw centered title
            title = "Dinner Menu"
            c.setFont("Helvetica-Bold", 24)  # Reduced title size
            c.setFillColor(NAVY_BLUE)
            title_width = c.stringWidth(title, "Helvetica-Bold", 24)
            # Center the title on the page
            title_x = (width - title_width) / 2
            title_y = height - margin - (logo_height / 2) + 10
            c.drawString(title_x, title_y, title)

            return height - margin - logo_height - 20  # Reduced spacing after header
        return height - margin - 20  # Reduced top margin for subsequent pages

    def draw_decorative_line(y_position):
        # Draw decorative line
        c.setStrokeColor(ORANGE)
        c.setLineWidth(2)
        c.line(margin + 30, y_position, width - margin - 30, y_position)

    # Start with the header
    current_y = draw_page_header(True)

    # # Draw decorative line
    # draw_decorative_line(current_y)
    # current_y -= 30  # Reduced space after decorative line

    # Group dishes by type
    dish_types = df["Type of the dish:"].unique()

    # Define the desired order
    type_order = ["Appetizer", "Salad", "Main course", "Dessert", "Drink"]

    # Filter and sort dish types according to the defined order
    ordered_types = []
    for dish_type in type_order:
        if dish_type in dish_types:
            ordered_types.append(dish_type)

    # Add any remaining types that weren't in our predefined order
    for dish_type in sorted(dish_types):
        if dish_type not in ordered_types:
            ordered_types.append(dish_type)

    def draw_dish_entry(
        dish_name, provider, dish_type, needs_outlet, x, y, available_width
    ):
        """Helper function to draw dish name and provider with proper wrapping"""
        bullet = "◆ "
        c.setFont("Helvetica", 12)  # Reduced font size for dish items
        bullet_width = c.stringWidth(bullet, "Helvetica", 12)

        # Get table number
        table_num = get_table_number(dish_type, needs_outlet)

        # Format provider text with table number
        provider_text = f" ~ by {provider} at Table {table_num}"

        # Combine dish name and provider
        full_text = f"{dish_name}{provider_text}"

        # Calculate wrapping
        words = full_text.split()
        lines = []
        current_line = []
        current_width = bullet_width

        for word in words:
            # Check if this is the provider part
            if word == "~" and "by" in words[words.index(word) + 1 :]:
                # Add provider part in Times-Italic font
                provider_part = " ".join(words[words.index(word) :])
                if current_line:
                    lines.append(
                        (" ".join(current_line), "Helvetica")
                    )  # Regular font for dish name
                lines.append((provider_part, "Times-Italic"))  # Italic for provider
                break

            # Calculate word width in regular font (for dish name)
            word_width = c.stringWidth(word + " ", "Helvetica", 12)  # Reduced font size

            if current_width + word_width <= available_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append((" ".join(current_line), "Helvetica"))
                current_line = [word]
                current_width = bullet_width + word_width

        if current_line and not any("by" in line[0] for line in lines):
            lines.append((" ".join(current_line), "Helvetica"))

        # Draw lines
        current_y = y
        for i, (line, font_name) in enumerate(lines):
            if i == 0:
                # First line includes bullet
                c.setFont("Helvetica", 12)  # Reduced font size
                c.drawString(x, current_y, bullet)
                x_offset = x + bullet_width
            else:
                # Subsequent lines are indented
                x_offset = x + bullet_width

            # Set appropriate font with reduced size
            c.setFont(font_name, 12)  # Reduced font size
            c.drawString(x_offset, current_y, line)
            current_y -= 16  # Reduced line spacing to match smaller font

        return current_y + 16  # Return the last y position with reduced spacing

    for dish_type in ordered_types:
        # Skip if we're running out of space
        if current_y < margin + 80:  # Reduced minimum space requirement
            c.showPage()
            current_y = draw_page_header(False)

        # Draw section header with decorative elements
        c.setFillColor(NAVY_BLUE)
        c.setFont("Helvetica-Bold", 14)  # Reduced section header size
        section_text = dish_type.title()
        text_width = c.stringWidth(section_text, "Helvetica-Bold", 14)

        # Draw centered section header
        c.drawString((width - text_width) / 2, current_y, section_text)
        current_y -= 10  # Reduced space before line

        # Draw short decorative line under section header
        c.setStrokeColor(ORANGE)
        line_width = min(text_width + 40, 200)
        c.line((width - line_width) / 2, current_y, (width + line_width) / 2, current_y)
        current_y -= 15  # Reduced space after line

        # Get dishes of this type
        type_dishes = df[df["Type of the dish:"] == dish_type]
        # Sort dishes alphabetically
        type_dishes = type_dishes.sort_values(by=dish_column)

        for _, row in type_dishes.iterrows():
            # Check if we need a new page
            if current_y < margin + 80:  # Reduced minimum space requirement
                c.showPage()
                current_y = draw_page_header(False)

                # Redraw section header on new page
                c.setFillColor(NAVY_BLUE)
                c.setFont("Helvetica-Bold", 14)
                c.drawString((width - text_width) / 2, current_y, section_text)
                current_y -= 25

            # Draw dish name and provider with table number
            dish_name = str(row[dish_column]).strip()
            provider = str(row[provider_column]).strip()
            dish_type = str(row["Type of the dish:"]).strip()
            needs_outlet = str(row[outlet_column]).strip()

            # Calculate available width for the entire entry
            available_width = content_width - 60

            # Draw the dish entry and update current_y
            current_y = draw_dish_entry(
                dish_name,
                provider,
                dish_type,
                needs_outlet,
                margin + 30,
                current_y,
                available_width,
            )
            current_y -= 15  # Reduced space between dishes

        current_y -= 20  # Reduced space between sections

    # Draw final decorative line at the bottom of the last page
    draw_decorative_line(margin + 50)

    # Save the menu
    c.save()


def create_empty_dish_card():
    """Create an empty dish card template with a white box for the title"""
    output_path = "dish_card.pdf"
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter

    # Set margins and initial position
    margin = 72  # 1 inch in points
    content_width = width - 2 * margin
    header_height = 100  # Increased header height for longer titles

    # Draw colored header background
    c.setFillColor(NAVY_BLUE)
    c.rect(
        margin, height - margin - header_height, content_width, header_height, fill=1
    )

    # Draw white box for handwritten title
    c.setFillColor("white")
    title_box_height = 60
    title_box_margin = 20
    c.rect(
        margin + title_box_margin,
        height - margin - header_height + (header_height - title_box_height) / 2,
        content_width - 2 * title_box_margin,
        title_box_height,
        fill=1,
    )

    # Draw border with orange color
    c.setStrokeColor(ORANGE)
    c.setLineWidth(3)
    c.rect(margin, margin, content_width, height - 2 * margin)

    # Start position for content
    current_y = height - margin - header_height - 60

    # Draw empty provider section
    c.setFillColor(NAVY_BLUE)
    c.setFont("Helvetica-Bold", 18)
    provider_text = "Provided by: ___________________________"
    c.drawString(margin + 30, current_y, provider_text)

    # Move down for the next sections
    current_y -= 80

    # All sections in a single column
    sections = [
        "Represented cuisine:",
        "Type of the dish:",
        "Ingredients:",
        "Protein/Category:",
        "Allergens:",
    ]

    # Draw sections with proper spacing
    left_margin = margin + 30
    for section in sections:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(left_margin, current_y, section)

        # Draw underline
        c.setFont("Helvetica", 14)
        c.drawString(left_margin + 150, current_y, "_" * 30)

        # Move down for next section
        current_y -= 50  # Increased spacing between sections

    # Add the Heritage Fest logo at the bottom
    if os.path.exists(logo_path):
        img = Image.open(logo_path)
        aspect = img.width / img.height
        logo_height = 100
        logo_width = logo_height * aspect

        # Calculate centered position for logo
        logo_x = (width - logo_width) / 2
        logo_y = margin + 10

        # Draw the logo
        c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)

    # Save the page
    c.save()
    print("Created empty dish card template: dish_card.pdf")


def create_signs():
    """Create large signs for tables and directions in landscape orientation"""
    signs = ["TABLE 1", "TABLE 2", "TABLE 3", "ENTER", "EXIT"]

    for sign_text in signs:
        # Create PDF with letter size in landscape
        output_path = f"{sign_text.lower().replace(' ', '_')}_sign.pdf"
        width, height = letter[1], letter[0]  # Swap width and height for landscape
        c = canvas.Canvas(output_path, pagesize=(width, height))

        # Set margins
        margin = 72  # 1 inch in points
        content_width = width - 2 * margin
        content_height = height - 2 * margin

        # Draw Heritage Fest logo on the left top
        if os.path.exists(logo_path):
            img = Image.open(logo_path)
            aspect = img.width / img.height
            logo_height = 120
            logo_width = logo_height * aspect

            # Position logo in the top left
            logo_x = margin
            logo_y = height - margin - logo_height
            c.drawImage(logo_path, logo_x, logo_y, width=logo_width, height=logo_height)

        # Draw QR code on the right top if it exists
        qr_code_path = "menu_qr.png"
        if os.path.exists(qr_code_path):
            qr_img = Image.open(qr_code_path)
            qr_aspect = qr_img.width / qr_img.height
            qr_height = 100
            qr_width = qr_height * qr_aspect

            # Position QR code in the top right
            qr_x = width - margin - qr_width
            qr_y = height - margin - qr_height
            c.drawImage(qr_code_path, qr_x, qr_y, width=qr_width, height=qr_height)

            # Add caption under QR code
            c.setFont("Helvetica", 10)
            c.setFillColor(NAVY_BLUE)
            caption = "scan for the dinner menu"
            caption_width = c.stringWidth(caption, "Helvetica", 10)
            c.drawString(qr_x + (qr_width - caption_width) / 2, qr_y - 15, caption)

        # Draw the main text
        c.setFont("Helvetica-Bold", 120)  # Large font size for visibility
        c.setFillColor(NAVY_BLUE)

        # Calculate text dimensions
        text_width = c.stringWidth(sign_text, "Helvetica-Bold", 120)
        text_height = 120  # Approximate height of the text

        # Center the text on the page
        x = (width - text_width) / 2
        y = (height - text_height) / 2

        # Draw orange border
        border_margin = 40  # Space between text and border
        c.setStrokeColor(ORANGE)
        c.setLineWidth(3)
        c.rect(
            x - border_margin,
            y - border_margin,
            text_width + 2 * border_margin,
            text_height + 2 * border_margin,
        )

        # Draw the text
        c.drawString(x, y, sign_text)

        # Save the page
        c.save()
        print(f"Created sign: {output_path}")


# Create individual dish cards
for idx, row in df.iterrows():
    create_dish_card(row, idx)
    print(f"Created dish card {idx + 1}")

# Create the menu
create_menu()
print("Created menu.pdf")

# Create empty dish card template
create_empty_dish_card()

# Create signs
create_signs()
