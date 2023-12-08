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

    # Find the element with the count
    count_element = soup.find("span", {"data-cy": "product-type-2-count"})
    if count_element:
        count_text = count_element.text
        count = int(re.search(r'\((\d+)\)', count_text).group(1))
    else:
        count = 0

    # Extracting prices
    prices = []
    for price in soup.find_all("p", class_="item-price"):
        prices.append(price.text.strip())

    return {
        "number_of_prices": count,
        "prices": prices
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
    collection = read_json_file('collection.json')

    # Load additional books if the file exists
    try:
        additional_books = read_json_file('additional-books.json')
        # Check for duplicate titles
        existing_titles = {book['title'] for book in collection}
        for book in additional_books:
            if book['title'] in existing_titles:
                print(f"Duplicate title found: {book['title']}")
                break
            collection.append(book)
    except FileNotFoundError:
        print("additional-books.json not found. Continuing with existing collection.")

    update_prices = '--update-prices' in sys.argv
    today = datetime.now().strftime("%Y-%m-%d")

    for book in collection:
        if update_prices:
            # print(type(book), book)  # Add this line to check the type and value of book
            scrape_results = scrape_abebooks(book['abe-search-url'])
            # Standardizing key names and updating values
            book['Number of Copies Found'] = scrape_results['number_of_prices']
            book['Highest Price'] = max([float(p[3:]) for p in scrape_results['prices'] if p.startswith('US$')], default=None)
            book['Lowest Price'] = min([float(p[3:]) for p in scrape_results['prices'] if p.startswith('US$')], default=None)
            book['Median Price'] = sorted([float(p[3:]) for p in scrape_results['prices'] if p.startswith('US$')])[len(scrape_results['prices']) // 2] if scrape_results['prices'] else None
            book['Date of Search'] = today


    # Sort collection by 'Number of Copies Found' in ascending order
    sorted_collection = sorted(collection, key=lambda x: int(x['Number of Copies Found']))

    write_json_file('collection-sorted.json', sorted_collection)
    write_to_csv(sorted_collection, 'collection-sorted.csv')


if __name__ == "__main__":
    main()
