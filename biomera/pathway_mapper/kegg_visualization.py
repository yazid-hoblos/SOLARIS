#!/usr/bin/env python3
"""
Automate KEGG Mapper and print the colored pathway URL.
"""

import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import re
import argparse


def prepare_kegg_mapper_data(ec_results):
    color_map = {
        'FULLY_FOUND': '#00FF00',
        'PARTIALLY_FOUND': '#FFA500',
        'NOT_FOUND': '#FF0000'
    }
    
    mapper_lines = []
    for _, row in ec_results.iterrows():
        ec = row['EC_number']
        status = row['Status']
        color = color_map.get(status, '#CCCCCC')
        mapper_lines.append(f"{ec}\t{color}")
    
    return '\n'.join(mapper_lines)

def setup_driver(headless=True):
    firefox_options = FirefoxOptions()
    if headless:
        firefox_options.add_argument('--headless')
    
    driver = webdriver.Firefox(options=firefox_options)
    return driver

def get_colored_pathway_url(driver, mapper_data):
    # Navigate to KEGG Mapper
    driver.get("https://www.genome.jp/kegg/mapper/color.html")
    time.sleep(2)
    
    # Fill form
    text_area = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "unclassified"))
    )
    text_area.clear()
    text_area.send_keys(mapper_data)
    time.sleep(1)
    
    # Submit
    submit_button = driver.find_element(By.XPATH, "//input[@value='Exec']")
    submit_button.click()
    time.sleep(5)
    
    # Find first pathway link
    links = driver.find_elements(By.TAG_NAME, "a")
    
    first_pathway_link = None
    for link in links:
        text = link.text.strip()
        if re.match(r'^map\d+', text):
            if '01100' in text:  # skip "map01100"
                continue
            first_pathway_link = link
            break
    
    if not first_pathway_link:
        for link in links:
            text = link.text.strip()
            href = link.get_attribute('href') or ''
            if 'map' in text.lower() and re.search(r'\d{5}', text + href):
                first_pathway_link = link
                break
    
    if not first_pathway_link:
        return None
    
    # Click pathway link
    first_pathway_link.click()
    time.sleep(2)
    
    # Switch to new tab if opened
    window_handles = driver.window_handles
    if len(window_handles) > 1:
        driver.switch_to.window(window_handles[-1])
    
    # Wait for page to load
    time.sleep(5)
    
    # Get URL
    page_url = driver.execute_script("return window.location.href;")
    
    return page_url

def main():
    parser = argparse.ArgumentParser(description="Automate KEGG Mapper and print the colored pathway URL.")
    parser.add_argument('--ec_file', type=str, required=True, help='Path to the EC results CSV file')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    args = parser.parse_args()
    ec_file = args.ec_file
    headless = args.headless
    ec_results = pd.read_csv(ec_file)
    # add headless as argument
    
    
    mapper_data = prepare_kegg_mapper_data(ec_results)
    
    driver = setup_driver(headless)
    
    try:
        pathway_url = get_colored_pathway_url(driver, mapper_data)
        
        if pathway_url:
            print("\nColored Pathway URL:")
            print(pathway_url)
        else:
            print("\nCould not get pathway URL")
        
    finally:
        # close on prompt
        if not headless:
            input("Press Enter to close the browser...")
        driver.quit()

if __name__ == '__main__':
    main()