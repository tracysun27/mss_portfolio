"""
ORIGINAL SOURCE: https://github.com/thenotoriousskc/xctf-data/tree/main 
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import argparse
import time
import csv
from io import StringIO
import pandas as pd
import os

def dump_rendered_page(team_id, year=2024, sport="cross-country", 
                       save_dir=f"{os.getcwd()}", print_output=False):
    race_dict = {}
    # Format the URL with the given team ID, year, and sport
    url = f'https://www.athletic.net/CrossCountry/Results/Season.aspx?SchoolID={team_id}&S={year}'
    # Set up Selenium WebDriver (change path if needed)
    service = Service( )  # Replace with the actual path to your WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode for faster execution (no browser UI)
    driver = webdriver.Chrome(service=service, options=options)
    
    # Load the page and wait for it to render
    driver.get(url)
    time.sleep(2)  # Wait to ensure the page fully loads (adjust as necessary)
    
    # Get the rendered HTML and close the browser
    rendered_html = driver.page_source
    driver.quit()
    
    # Parse with BeautifulSoup and print the content
    soup = BeautifulSoup(rendered_html, 'html.parser')

    # for child in soup.descendants:
    #     if child.name:
  
    #         print(child.name, ":", child.get_text())

    # print(soup.prettify())  # Dump the HTML for inspection

    table = soup.find('table', class_='pull-right-sm')
    

    table_id = table.get('id', 'No ID')
    table_class = ' '.join(table.get('class', [])) if table.get('class') else 'No Class'
    
    # print(f"  ID: {table_id}")
    # print(f"  Class: {table_class}")

    # Extract and print the table rows
    rows = table.find_all('td')
    # Create a dictionary from the table data
    race_distances = {}

    for row in table.find_all("td"):
        sub = row.find("sub")
        if not sub:
            continue

        key = int(sub.text.strip())  

        value_parts = []
        for sib in sub.next_siblings:
            if isinstance(sib, str):
                value_parts.append(sib)
            else:
                value_parts.append(sib.get_text())

        value = "".join(value_parts).strip()
        race_distances[key] = value

    # print(race_distances)
    tables = soup.find_all('table', id='MeetList')
    # Iterate over each table
    for i, table in enumerate(tables, start=1):
        # Get the id and class attributes
        table_id = table.get('id', 'No ID')
        table_class = ' '.join(table.get('class', [])) if table.get('class') else 'No Class'
        
        # print(f"Table {i}:")
        # print(f"  ID: {table_id}")
        # print(f"  Class: {table_class}")
        
        # Extract and print the table rows
        rows = table.find_all('tr')
        for row in rows:
            # Extract all cell data
            cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td', 'y'])]
            if print_output:
                print(','.join(cells))  # Print tab-separated row
            if len(cells) > 1:
                race_dict[cells[0]] = cells[1]
        if print_output:
            print("-" * 40)
        # print(race_dict)


    tables = soup.find_all('table', class_='table-responsive small DataTable')

    header = (
    "race_date,"
    "grade,"
    "athlete_name,"
    "time,"
    "meet_name,"
    "distance,"
    "is_PR,"
    "is_SR,"
    "is_improvement\n"
)

    mens_str = header
    womens_str = header

    for race in race_dict: # race = 1 particular race that was ran (e.g. MHAL #1)

        # print("Race:", race)
        for idx, table in enumerate(tables):
            # Find all rows

            rows = table.find_all('tr')
            
            # Determine the column index for the "Date" header
            # Determine the column index for the header containing "Date"
            headers = [th.get_text(strip=True) for th in rows[0].find_all('th')]
            date_col_index = next((i for i, header in enumerate(headers) if race in header), None)
        
            if date_col_index is None:
                print(f'No column containing {race} found in table.')
                continue
        
            # print(f"Rows matching date {race}:")
            
            # Iterate over the remaining rows

            # print("Found header", rows[0])
            # print("Table number", idx)
            # table numbers: 0 = men, 1 = women team

            for row in rows[1:]:  # Skip the header row
                race_dist = [0] * 24
                pr_flags = [0] * 24
                sr_flags = [0] * 24
                improvement_flags = [0] * 24
                for i, td in enumerate(row.find_all('td')):
                    subscript = td.find('span', class_='subscript')
                    if subscript and subscript.text.isdigit():
                        race_dist[i] = int(subscript.text)  

                    classes = td.get("class", [])
                    # IS_PR
                    if "pR" in classes:
                        pr_flags[i] = 1
                    # IS_SR
                    if "sR" in classes:
                        sr_flags[i] = 1
                    # IS_IMPROVEMENT
                    if "imp" in classes:
                        improvement_flags[i] = 1

                cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                # print(f'race_dist: {race_dist}')
                # print(f'date_col_index: {date_col_index}') 
                # print(f'race_distances: {race_distances.items()}')  
                # Skip rows with no data in the date column or missing data
                ### PRINT ROWS
                if len(cells) > date_col_index and cells[date_col_index]:
                    if race_dict[race] == "":
                        meet_name = race_dict[race]
                    else:
                        meet_name = race_dict[race].replace(",", "")
                    # print(list(race_distances.items())[race_dist[date_col_index] - 1][1])
                    # print(race_distances.get(race_dist[date_col_index], ""))
                    if race_distances.get(race_dist[date_col_index], "") == "":
                        distance = race_distances.get(race_dist[date_col_index], "")
                    else:
                        distance = race_distances.get(race_dist[date_col_index], "").replace(",", "")
                    cell_str = f"{race} {year},{cells[0]},{cells[1]},{cells[date_col_index]},{meet_name},{distance},{pr_flags[date_col_index]},{sr_flags[date_col_index]},{improvement_flags[date_col_index]}"
                    if idx == 0:
                        mens_str += f"{cell_str}\n"
                    elif idx == 1:
                        womens_str += f"{cell_str}\n"
    if print_output:
        print(f"All men's times from {year}:")
        print(mens_str)

        print(f"All women's times from {year}:")
        print(womens_str)
    # save as csv file
    with open(f"{save_dir}/mens_{year}.csv", "w", newline='') as csvfile:
        csvfile.write(mens_str)
    
    with open(f"{save_dir}/womens_{year}.csv", "w", newline='') as csvfile:
        csvfile.write(womens_str)

if __name__ == "__main__":

    ## COMMAND: (lhs data)
    ## python scrape_season.py --team_id 1067 --year 2017

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Dump a season of race times from Athletic.net in csv format.  Currently works for XC only")
    parser.add_argument("--team_id", type=int, help="Team ID of the team on Athletic.net")
    parser.add_argument("--year", type=int, default=2024, help="Year for the team data")
    parser.add_argument("--sport", type=str, default="cross-country", help="Sport type (e.g., cross-country, track-and-field)")
    parser.add_argument("--save_dir", type=str, default=f"{os.getcwd()}", help="Save directory")
    parser.add_argument("--print_output", action='store_true', help="Print before save (for debugging)")

    # Parse the command-line arguments
    args = parser.parse_args()
    
    # Call the function to dump the rendered page content
    dump_rendered_page(args.team_id, args.year, args.sport, args.save_dir, args.print_output)

