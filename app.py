import aiohttp
import asyncio
import logging
import yaml
from bs4 import BeautifulSoup
import yagmail
import aiofiles

async def load_settings(path):
    with open(path, 'r') as file:
        settings = yaml.safe_load(file)
    logging.info("Settings file loaded")
    return settings

async def load_last_value(path):
    try:
        async with aiofiles.open(path, 'r') as file:
            last_value = await file.read()
    except Exception as e:
        logging.warning("Loading last value from file failed")
        logging.warning(e)
        last_value = None
    else:
        logging.info('Last value: "%s" loaded from file', last_value)
    return last_value

async def fetch_with_retry(url, retries=3):
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()  # Raise an error for bad responses
                    return await response.text()
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt == retries - 1:
                raise
            await asyncio.sleep(2)  # Wait before retrying

async def fetch_site_content(url):
    response_text = await fetch_with_retry(url)
    return response_text

async def extract_new_value(response):
    try:
        soup = BeautifulSoup(response, "html.parser")
        search_result = soup.find_all(string="Informatyka I rok")
        extracted_value = search_result[0].parent.parent.next_sibling.next_sibling.string
    except Exception as e:
        logging.exception("Error occurred when parsing response")
        extracted_value = None
    else:
        logging.info("Extracted value: %s", extracted_value)
    return extracted_value

async def notify_gmail(subject, message, recipients_email_addresses, sender_email_address, password):
    try:
        yag = yagmail.SMTP(sender_email_address, password)
        yag.send(recipients_email_addresses, subject, message)
    except Exception as e:
        logging.error("Error occurred when sending email")
        logging.error(e)
        return False
    else:
        logging.info("Email notification sent")
        return True

async def main_loop(settings, last_value):
    check_period = settings.get("check period", 15) * 60  # Convert minutes to seconds
    while True:
        response = await fetch_site_content(settings['url'])
        while response is None:
            access_retry_period = settings["access retry period"]
            logging.info("waiting %s minutes before retrying to reach the site", access_retry_period)
            await asyncio.sleep(60 * access_retry_period)
            response = await fetch_site_content(settings['url'])
        new_value = await extract_new_value(response)
        if new_value != last_value:
            subject = "New value detected"
            message = f"New value: {new_value}"
            recipients_email_addresses = settings["email recipients"]
            sender_email_address = settings["sender email"]
            password = settings["sender password"]
            await notify_gmail(subject, message, recipients_email_addresses, sender_email_address, password)
            if new_value is not None:
                with open('data/last_value.txt', 'w') as file:
                    file.write(new_value)
                last_value = new_value
            else:
                logging.warning("new_value is None, skipping write operation. This may indicate an issue with the site or the extraction process.")
        await asyncio.sleep(check_period)  # Wait for the specified check period

async def main():
    logging.basicConfig(level=logging.INFO)
    settings = await load_settings('data/settings.yaml')
    last_value = await load_last_value('data/last_value.txt')
    await main_loop(settings, last_value)

if __name__ == '__main__':
    asyncio.run(main())
