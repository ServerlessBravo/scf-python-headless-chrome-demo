# -*- coding: utf8

import os
import sys

parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')
sys.path.insert(1, vendor_dir)

import asyncio
import logging
from pyppeteer import launch

async def test():

    # Config for headless mode
    browser = await launch(headless=True,
                           userDataDir='/tmp/pyppeteer/',
                           logLevel=logging.ERROR,
                           executablePath='/opt/chrome-linux/chrome',
                           env={'PUPPETEER_SKIP_CHROMIUM_DOWNLOAD': 'true'},
                           args=['--no-sandbox', '--window-size=1920,1080', '--disable-infobars'])

    page = await browser.newPage()
    await page.goto('http://baidu.com')
    title = await page.title()
    print("Page title is " + title)
    await browser.close()
    return title


def main_handler(event, context):
    print("Received event: " + str(event))
    print("Received context: " + str(context))

    results = asyncio.get_event_loop().run_until_complete(test())
    print(results)

    return results
