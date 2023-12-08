import requests
from bs4 import BeautifulSoup
import re
import json
import sys
import csv
from datetime import datetime

def scrape_abebooks(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extracting stock image URL
    image_element = soup.find("img", {"class": "srp-item-image"})
    image_url = image_element['src'] if image_element else 'No image found'

    # Find the element with the count
    count_element = soup.find("span", {"data-cy": "product-type-2-count"})
    if count_element:
        count_text = count_element.text
        match = re.search(r'\((\d+)\)', count_text)
        count = int(match.group(1)) if match else 0
    else:
        count = 0

    # Extracting prices
    prices = []
    for price in soup.find_all("p", class_="item-price"):
        price_text = price.text.strip()
        if price_text.startswith('US$'):
            price_text = price_text[3:].replace(',', '')  # Remove comma and currency symbol
        prices.append(float(price_text))  # Convert price to float

    highest_price = max(prices, default=None)
    lowest_price = min(prices, default=None)
    median_price = sorted(prices)[len(prices) // 2] if prices else None

    return {
        "Stock Image": image_url,
        "Number of Copies Found": count,
        "Highest Price": highest_price,
        "Median Price": median_price,
        "Lowest Price": lowest_price,
        "Date of Search": datetime.now().strftime("%Y-%m-%d")
    }

def read_json_file(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def write_json_file(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file, indent=4)

def write_to_csv(data, file_name):
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(data[0].keys())
        # Write the data rows
        for book in data:
            writer.writerow(book.values())        

def main():
    # Load existing collection
    collection = read_json_file('collection-raw.json')

    # Load additional books if the file exists
    try:
        additional_books = read_json_file('additional-books.json')

        # Check for duplicate titles
        existing_titles = {book['Title'] for book in collection}
        for book in additional_books:
            if book['Title'] in existing_titles:
                print(f"Duplicate Title found: {book['Title']}")
                break
            collection.append(book)
    except FileNotFoundError:
        print("additional-books.json not found. Continuing with existing collection.")

    update_prices = '--update-prices' in sys.argv
    today = datetime.now().strftime("%Y-%m-%d")

    for book in collection:
        scrape_results = scrape_abebooks(book['ABE Search'])
        book.update(scrape_results)
        # Standardizing key names and updating values


    # Sort collection by 'Number of Copies Found' in ascending order
    sorted_collection = sorted(collection, key=lambda x: int(x.get('Number of Copies Found', 0)))

    write_json_file('collection-sorted.json', sorted_collection)
    write_to_csv(sorted_collection, 'collection-sorted.csv')


if __name__ == "__main__":
    main()
