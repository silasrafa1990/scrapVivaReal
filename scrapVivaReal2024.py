import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, ElementClickInterceptedException, NoSuchElementException, \
    TimeoutException


class ScraperVivaReal:
    wait_time = 5

    def __init__(self, url):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-notifications")
        # options.add_argument("--headless=new")
        self.driver = webdriver.Chrome(options=options)
        self.driver.maximize_window()
        self.driver.get(url)
        time.sleep(self.wait_time)

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)

        WebDriverWait(self.driver, self.wait_time).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="adopt-accept-all-button"]'))).click()
        time.sleep(self.wait_time)

    def wait_for_page_to_load(self):

        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(self.wait_time)
        print("Aguardei o carregamento completo da página.")

    def __scroll_to_bottom(self):

        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                new_height = self.driver.execute_script("return document.body.scrollHeight")

                if new_height == last_height:
                    break
                last_height = new_height
        except Exception as e:
            print(f"Erro ao rolar a página: {e}")

    def scrap(self):

        self.__scroll_to_bottom()

        result = []

        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        except WebDriverException:
            print('Webdriver foi fechado manualmente!')
            return result

        itens = soup.find_all('div', class_='property-card__content')
        print(f"Itens encontrados nesta página: {len(itens)}")

        for item in itens:
            try:
                preço = item.find('section', class_='property-card__values').text.strip()
            except AttributeError:
                preço = "Não informado"

            try:
                localização = item.find('span', class_='property-card__address').text.strip()
            except AttributeError:
                localização = "Não informado"

            try:
                area = item.find('li', class_='property-card__detail-item property-card__detail-area').text.strip()
            except AttributeError:
                area = "Não informado"

            try:
                dorms = item.find('li', class_='property-card__detail-item property-card__detail-room js-property-detail-rooms').text.strip()
            except AttributeError:
                dorms = "Não informado"

            try:
                bath = item.find('li', class_='property-card__detail-item property-card__detail-bathroom js-property-detail-bathroom').text.strip()
            except AttributeError:
                bath = "Não informado"

            try:
                garage = item.find('li', class_='property-card__detail-item property-card__detail-garage js-property-detail-garages').text.strip()
            except AttributeError:
                garage = "Não informado"

            try:
                title = item.find('span', class_='property-card__title js-cardLink js-card-title').text.strip()
            except AttributeError:
                title = "Não informado"

            add_list = re.split(',|-', localização)
            add_list = [item.strip() for item in add_list]
            if len(add_list) == 1:
                st = add_list
                cidade = 'N/I'
                bairro = 'N/I'
                endereço = 'N/I'
                numero = 'N/I'

            if len(add_list) == 2:
                cidade, st = add_list
                bairro = 'N/I'
                endereço = 'N/I'
                numero = 'N/I'
            if len(add_list) == 3:
                bairro, cidade, st = add_list
                endereço = 'N/I'
                numero = 'N/I'
            if len(add_list) == 4:
                endereço, bairro, cidade, st = add_list
                numero = 'N/I'
            elif len(add_list) == 5:
                endereço, numero, bairro, cidade, st = add_list


            row = {'Preço': preço, 'Cidade': cidade, 'Bairro': bairro, 'Endereço': endereço,
                   'Numero': numero, 'Dorms': dorms,
                   'Banheiros': bath, 'Area': area, 'Vagas': garage, 'Titulo': title}
            result.append(row)
        df = pd.DataFrame(result)
        print(df)
        return result

    def __next_page__(self):

        try:
            next_button = WebDriverWait(self.driver, self.wait_time).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@class="js-change-page" and @title="Próxima página"]'))
            )
            next_button.click()

            WebDriverWait(self.driver, self.wait_time).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'property-card__content'))
            )

            print("Página seguinte carregada com sucesso.")
            return True
        except (ElementClickInterceptedException, NoSuchElementException) as e:
            print(f"Erro ao tentar clicar na próxima página: {e}")
            return False
        except TimeoutException as e:
            print("Tempo limite atingido ao tentar encontrar o botão da próxima página.")
            return False

    def run(self, output):

        tem_proximo = True
        armazenados = []

        while tem_proximo:
            results = self.scrap()
            armazenados.extend(results)
            print(f'Coletamos nessa página {len(results)} itens! Total: {len(armazenados)}')

            if len(results) == 0:
                break

            tem_proximo = self.__next_page__()

            time.sleep(self.wait_time)

        pd.DataFrame(armazenados).to_csv(output, index=False)
        self.driver.quit()

S = ScraperVivaReal('https://www.vivareal.com.br/venda/sp/caraguatatuba/?pagina=#onde=Brasil,S%C3%A3o%20Paulo,Caraguatatuba,,,,,,BR%3ESao%20Paulo%3ENULL%3ECaraguatatuba,,,')
S.run('output.csv')
