from tqdm import tqdm
import numpy as np

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
import os


def fetch_schedule(course):
    options = Options()
    options.headless = True
    options.binary_location = r'Chromium.app/Contents/MacOS/Chromium'

    chrome_driver_path = '/Users/adithya/Workspace/auto-star-planner/chromedriver'
    driver = webdriver.Chrome(chrome_driver_path, options=options)
    driver.get("https://wish.wis.ntu.edu.sg/webexe/owa/aus_schedule.main")

    select = Select(driver.find_element_by_name('r_course_yr'))
    options_text = np.array([o.get_attribute('text') for o in select.options])
    indices = []

    for i, text in enumerate(options_text):
        if course + ' Y' in text:
            indices.append(i)

    for text in tqdm(options_text[indices]):
        try:
            select.select_by_visible_text(text)
            driver.find_element_by_xpath('/html/body/form/div[3]/table/tbody/tr/td[2]/input').click()

            with open('classSchedule/' + text + '.html', 'wb') as f:
                f.write(driver.page_source.encode('utf-8'))
        except:
            continue

    driver.quit()


if __name__ == '__main__':
    fetch_schedule('Computer Science')
