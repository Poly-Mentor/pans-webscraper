from urllib.request import Request, urlopen
from time import sleep
from bs4 import BeautifulSoup
import logging
import yaml


def load_settings(path):
    with open(path, 'r') as file:
        settings = yaml.load(file)
    logging.info("Settings file loaded")
    return settings

def load_last_value(path):
    try:
        with open(path, 'r') as file:
            last_value = file.read()
    except Exception as e:
        logging.warning("Loading last value from file failed")
        logging.warning(e)
        last_value = None
    return last_value

def save_last_value(path, last_value):
    try:
        with open(path, 'w') as file:
            file.write(last_value)
    except Exception as e:
        logging.warning("Writing last value to file failed")
        logging.warning(e)
    else:
        logging.info('Last value: "%s" saved to file %s', last_value, path)

def get_site_content(url):
    try:
        request = Request(url)
        response = urlopen(request)
    except Exception as e:
        logging.warning("Couldn't reach site: %s", url)
        logging.warning(e)
        response = None
    else:
        logging.info('site "%s" reached with status %s, response downloaded', response.status)
    return response

def extract_new_value(response):
    try:
        soup = BeautifulSoup(response.read(), "html.parser")
        # ---CUSTOM CODE---
        search_result = soup.find_all(string="Informatyka I rok")
        new_value = search_result[0].parent.parent.next_sibling.next_sibling.string
    except Exception as e:
        logging.error("Error occured when parsing response")
        logging.error(e)
        new_value = None
    return new_value

def notify_gmail(message, recipents_email_addressed, sender_email_address, password):
    pass

def notify_discord(message, token):
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    settings = load_settings('settings.yaml')

    # show loaded settings when "debugging logs" value was set to true in settings.yaml
    if settings["debugging logs"]:
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("--- Settings ---")
        for setting_name, setting_value in settings:
            logging.debug("%s = %s", setting_name, setting_value)
        logging.debug("--- /SETTINGS ---")
    last_value = load_last_value('last_value.txt')
    
    # synchronous approach
    # main loop
    while True:
        # try to reach site
        response = get_site_content(settings['url'])
        while response is None:
            access_retry_period = settings["access_retry_period"]
            logging.info("waiting %s seconds before retrying to reach the site", access_retry_period)
            sleep(access_retry_period)
            response = get_site_content(settings['url'])
        
        # parse new value
        new_value = extract_new_value(response)

        # check if it changed
        if new_value != last_value:
            # try to notify about a change
            notification_successful = notify_gmail( \
                    settings["message"],\
                    settings["email recipents"],\
                    settings["sender email"],\
                    settings["sender_password"])
            # keep retrying if not successful
            while not notification_successful:
                notification_retry_period = settings["notification retry period"]
                logging.info("waiting %s seconds before retrying to notify", notification_retry_period)
                sleep(notification_retry_period)
                notification_successful = notify_gmail( \
                    settings["message"],\
                    settings["email recipents"],\
                    settings["sender email"],\
                    settings["sender_password"])
            # after succesfull notification update last value and save it to a file
            last_value = new_value
            save_last_value('last_value.txt', last_value)

        # wait for the next check
        check_period = settings["check period"]
        logging.info("waiting %s seconds before next check", check_period)
        sleep(check_period)
        
    # end of main loop
