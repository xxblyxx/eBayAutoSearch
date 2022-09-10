import argparse
import datetime
import json
import re
import sqlite3
import time
from signal import signal, SIGINT
from sqlite3 import Error
from sys import exit
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse
from urllib.parse import parse_qs

import requests
import telebot
from lxml import html

import config_gui

global con

MAX_RETRIES = 5
RESTART_TIME = 10
numberOfHits = 15

class TooManyConnectionRetries(Exception):
    pass


def exit_handler(signal_received, frame):
    global con
    print("CTRL-C Pressed, exiting...")
    try:
        # Safely close the database connection and exit the application
        con.close()
    except Exception:
        pass
    exit(0)


def sql_connection(file_name):
    try:
        conbd = sqlite3.connect(file_name)
        return conbd
    except Error:
        print(Error)

def get_page(url):
    print('Getting search results...')
    response = requests.get(url)

    # If error in reaching Ebay via provided url, throw a custom error message
    if not response.ok:
        print('Server responded:', response.status_code)
    else:
        soup = BeautifulSoup(response.text, 'lxml')

    return soup

# Returns a dictionary containing the title, price, currency, and number of item sold given an item's url link
def get_detail_data(soup, url):
    # Get title of item
    try:
        title = soup.find('h1', {'class':'x-item-title__mainTitle'}).get_text(strip=True)
        #title = title.lstrip("Details about \xa0")
    except:
        title = 'exceptionDetected'

    # Get price of item
    try:
        p = soup.find('span', id='prcIsum').text.strip()
        currency, price = p.split(' ')
    except:
        try:
            p = soup.find('span', id='prcIsum_bidPrice').text.strip()
            currency, price = p.split(' ')
        except:
            currency = ''
            price = 'exceptionDetected'

    # Get # of items sold (note, this is inconsistent)
    try:
        sold = soup.find('span', class_='vi-qtyS').find('a').text.strip().split(' ')[0].replace('\xa0', '')
    except:
        sold = ''

    # Get ID
    try:
        id = soup.find('div', id='descItemNumber').get_text(strip=True)
    except:
        id = 0
    
    data = {
        'title': title,
        'price': price,
        'currency': currency,
        'total_sold': sold,
        'url': url,
        'id': id
    }

    return data

def get_index_data(soup):
    try:
        links = soup.find_all('a', class_='s-item__link')
    except:
        links = []

    urls = [item.get('href') for item in links]
    urls = urls[1:]

    return urls

def itemIDExistInDB(itemID):
    global con
    cursordb = con.cursor()
    try:
        cursordb.execute("SELECT * FROM identifiers where id=?",(itemID,))
        rowcount = len(cursordb.fetchall()) #gets count of list
        if rowcount != 1:
            cursordb.close()
            print(itemID + ' DOES NOT exist in database.')
            return False
        else: 
            cursordb.close()
            print(itemID + ' already exists in database.')
            return True
    except Exception as e:
        print('execption itemidexistindb')
        print(e)
        cursordb.close()
        return False
    return False

def scraper(url, apikey, chatid, sleep):
    global con
    cursordb = con.cursor()

    # Infinite loop, safe way to close the program is to send a SIGINT signal (CTRL-C)
    while True:
        # Load and parse the html from supplied ebay search page
        # If it raises an connectionerror, it will retry a few times
        for i in range(MAX_RETRIES):
            try:
                products = get_index_data(get_page(url))
            except requests.exceptions.ConnectionError:
                print("Connection Error: Please check your internet connection")
                print("Retrying in " + sleep + " seconds (" + str(i) + "/" + str(MAX_RETRIES) + ")")
                time.sleep(int(sleep))
                continue
            else:
                break
        else:
            # The scraper will raise an exception if it exceeds the max number of connection retries (MAX_RETRIES)
            raise TooManyConnectionRetries

        #BeautifulSoupImplementation
        productList =[]
        for link in products[0:numberOfHits]:
            
            #check link to see if in DB, if not get detail
            parsed_url = urlparse(link)
            itemID = parsed_url.path.split('/')[2]
            if (itemIDExistInDB(itemID) == False):
                print('Hitting Ebay for data...')
                data = get_detail_data(get_page(link), link)
                productList.append(data)

        # Insert every id into the database table
        # If the id is already present on the table, cursor.execute() will raise an sqlite3.IntegrityError exception which will skip the process of sending the link
        # as a telegram message
        for prodstr in productList:
            try:
                # Insert the id and the timestamp
                cursordb.execute("INSERT INTO identifiers(id,listingDate) VALUES(?,?)",
                                (prodstr['id'], datetime.now()))

                # Print the listing url based on the identifier  
                print('Found new item')             
                print(prodstr['title'])
                print(prodstr['id'])
                print(prodstr['price'])
                print(prodstr['url'])

                # If the user specified a telegram bot apikey + chatid, it will send the previously printed list as a text message (only if the previous line didn't produce an exception)
                if apikey != "" and chatid != "":
                    try:
                        print('telegramming')
                        telebot.TeleBot(apikey, threaded=False).send_message(chatid,
                                                             prodstr['title'] 
                                                             + "\n" + prodstr['price']
                                                             + "\n" + prodstr['url'])
                        # Telegram API limits the number of messages per second so we need to wait a little bit
                        time.sleep(0.5)
                    except telebot.apihelper.ApiTelegramException:
                        pass
            except sqlite3.IntegrityError:
                # When this exception rises, the program will just continue to the next element of the for-loop
                pass
        con.commit()
        print(str(datetime.now()) + ' - Refresh complete, sleeping...')
        # Wait before repeting the process
        time.sleep(int(sleep))


def startup(filename_path):
    global con
    # Obtain parameters from the json file
    # User must specify the file path as an argument when running this script
    with open(filename_path) as config_file:
        config = json.load(config_file)
        url = config["url"]
        apikey = config["telegramAPIKEY"]
        chatid = config["telegramCHATID"]
        dbname = config["databaseFile"]
        sleep = config["sleep"]

    config_file.close()

    # Connect to db and create the table (if not exists)
    con = sql_connection(dbname)
    cursor = con.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS identifiers(id VARCHAR(12) PRIMARY KEY, listingDate timestamp)")
    con.commit()

    # Start the exit handler
    signal(SIGINT, exit_handler)

    # Start the scraper
    scraper(url, apikey, chatid, sleep)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-nogui", "--nogui", action="store_true")
    parser.add_argument("-path", metavar="--path",
                        type=str,
                        default="config.json",
                        required=False,
                        help="the path to the config file (defaults to config.json)")

    options = parser.parse_args()
    filename = options.path
    if not options.nogui:
        config_gui.GUI(filename)

    # There must be a better way
    while True:
        try:
            startup(filename)
        except Exception as e:
            print(e)
            print("Restarting the application in " + str(RESTART_TIME) + " seconds")
            time.sleep(RESTART_TIME)
            try:
                con.close()
            except Exception:
                pass
