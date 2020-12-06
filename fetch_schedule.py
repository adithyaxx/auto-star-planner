import time

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
import os


class FetchSchedule(QThread):
    update = pyqtSignal(int)

    def __init__(self, sem, major):
        super().__init__()
        self.sem = sem
        self.major = major

    def run(self):
        options = Options()
        options.headless = True
        options.binary_location = r'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser'

        chrome_driver_path = os.getcwd() + '/chromedriver'
        driver = webdriver.Chrome(chrome_driver_path, options=options)
        driver.get("https://wish.wis.ntu.edu.sg/webexe/owa/aus_schedule.main")

        sem_select = Select(driver.find_element_by_name('acadsem'))
        sem_select.select_by_visible_text(self.sem)

        major_select = Select(driver.find_element_by_name('r_course_yr'))
        options_text = np.array([o.get_attribute('text') for o in major_select.options])
        indices = []

        for i, text in enumerate(options_text):
            if self.major + ' Y' in text:
                indices.append(i)

        for i, text in enumerate(options_text[indices]):
            self.update.emit(int((i + 1) * 100 / len(indices)))
            try:
                major_select.select_by_visible_text(text)
                driver.find_element_by_xpath('/html/body/form/div[3]/table/tbody/tr/td[2]/input').click()
                driver.switch_to.window(driver.window_handles[-1])
                with open('classSchedule/' + text + '.html', 'wb') as f:
                    f.write(driver.page_source.encode('utf-8'))
                driver.switch_to.window(driver.window_handles[0])
            except:
                print('error')
                continue

        driver.quit()
