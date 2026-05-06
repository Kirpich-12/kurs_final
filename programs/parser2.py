from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep

from models import (
    BankBranch,
    Coords,
    ExchangeRate,
    BankOrg,
    Currency
)


LINK = "https://myfin.by/banki/otdelenija-spiskom?city_id=1"


class Parser:
    def __init__(
            self,
            debug_flag: bool = False):
        try:
            options = webdriver.ChromeOptions()
            self.debug_flag = debug_flag

            if not self.debug_flag:
                options.add_argument('--headless')

            self.driver = webdriver.Chrome(
                options=options
            )
        except ValueError:
            print(f'Ошибка доступа к сайту \n Ошибка:{self.status_code}')
        except Exception as e:
            print(f'Ошибка при создании драйвера: {e}')
    
    def _get_page(self, url) -> webdriver.Chrome:
        '''Запрос страницы'''
        self.driver.get(url)
        return self.driver
    
    def _press_button(self, button_xPath:str):
        '''Нажите кпонки по переданому XPath, debug_flag - выводит что нажали'''
        try:
            button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, button_xPath))
            )
            button.click()
            if self.debug_flag:
                print('=====================================')
                print(f'Нажата кнопка со следующим путем {button_xPath}')
                print('=====================================')
        except Exception as e:
            print('=====================================')
            print(f'Кнопка {button_xPath} не была нажата')
            print(e)
            print('=====================================')

        def _get_max_pages(self, num_elz:int) -> int:
            '''возвращает максимальное количество страниц на ссылке'''
            driver = self._get_page(LINK)
            self._press_button('/html/body/div[4]/div/div[3]/button[1]')#жмакает на куки

            el_str = driver.find_element(By.ID, "productsCount")
            el_num = int("".join(filter(str.isdigit, el_str)))
            if el_num % 20 == 0:
                return el_num // 20
            else:
                return (el_num // 20) + 1
        
        def get_branch_links(self):
            