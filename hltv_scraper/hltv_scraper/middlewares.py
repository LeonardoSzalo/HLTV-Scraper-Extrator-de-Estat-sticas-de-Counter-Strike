from scrapy.http import HtmlResponse
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from scrapy.exceptions import IgnoreRequest
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException # Importar exceções específicas
import undetected_chromedriver as uc
import time
import random
from scrapy.utils.project import get_project_settings

class UndetectedChromeMiddleware:
    def __init__(self):
        self.driver = None
        self.spider = None # Armazenado via from_crawler
        self._initialize_driver()

    def _initialize_driver(self):
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                time.sleep(random.uniform(1, 2))
            except Exception as e:
                print(f"DEBUG: Erro ao fechar driver existente: {e}")
                self.driver = None

        settings = get_project_settings()
        chromedriver_path = settings.get('UNDETECTED_CHROMEDRIVER_PATH')

        if not chromedriver_path:
            raise Exception("UNDETECTED_CHROMEDRIVER_PATH não está definido em settings.py!")

        try:
            self.driver = uc.Chrome(headless=False, driver_executable_path=chromedriver_path)
            print("INFO: WebDriver Chrome inicializado com sucesso.")
        except SessionNotCreatedException as e:
            print(f"ERROR: Falha ao criar a sessão do WebDriver. Verifique a versão do Chrome/Chromedriver e o caminho. Erro: {e}")
            raise IgnoreRequest(f"Falha fatal ao inicializar o WebDriver: {e}")
        except Exception as e:
            print(f"ERROR: Erro inesperado ao inicializar o WebDriver: {e}")
            raise IgnoreRequest(f"Falha fatal ao inicializar o WebDriver: {e}")

    @classmethod
    def from_crawler(cls, crawler):
        obj = cls()
        obj.spider = crawler.spider
        return obj

    def process_request(self, request, spider):
        # NOTA: O 'response' que causa o NameError não existe neste ponto.
        # Estamos no processo de criar a response a partir do driver.
        # A instância de 'spider' é acessível, assim como 'request'.

        if request.meta.get('dont_retry', False):
            return None

        if not self.driver:
            self.spider.logger.warning("WebDriver não está ativo, tentando reinicializá-lo.")
            self._initialize_driver()
            if not self.driver:
                self.spider.logger.error("Falha ao reinicializar o WebDriver. Ignorando requisição.")
                raise IgnoreRequest("Falha na reinicialização do WebDriver.")

        try:
            self.spider.logger.info(f"Visitando URL: {request.url}")
            self.driver.get(request.url)

            time.sleep(random.uniform(2, 4))

            try:
                accept_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll'))
                )
                self.spider.logger.info("Pop-up de consentimento de cookies detectado. Tentando clicar 'Allow all cookies'.")
                accept_button.click()
                time.sleep(random.uniform(2, 4))
                self.spider.logger.info("Clicado no botão de consentimento de cookies.")
            except Exception as e:
                self.spider.logger.debug(f"Pop-up de cookies não encontrado ou falha ao clicar: {request.url} - {e}")


            self.spider.logger.info("Corpo da página principal carregado com sucesso.")

            last_height = self.driver.execute_script("return document.body.scrollHeight")
            scroll_attempts = 0
            max_scroll_attempts = 5
            while scroll_attempts < max_scroll_attempts:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(random.uniform(1, 3))
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_attempts += 1
            self.spider.logger.info(f"Página rolada {scroll_attempts} vezes até o fim para {request.url}.")


            # CRÍTICO: Passar o driver para o meta da request para uso posterior nos parsers
            # É a request que viaja para o parser, não a response ainda.
            request.meta['driver'] = self.driver
            request.dont_filter = True

            # Cria o objeto HtmlResponse APÓS todas as interações e rolagem,
            # usando o page_source ATUALIZADO do driver.
            # Este é o objeto 'response' que será enviado para o callback do spider.
            return HtmlResponse(url=self.driver.current_url, body=self.driver.page_source, encoding='utf-8', request=request)

        except WebDriverException as e:
            self.spider.logger.error(f"Erro de WebDriver durante a requisição {request.url}: {e}. Tentando reinicializar o driver.")
            self._initialize_driver()
            raise IgnoreRequest(f"Erro de WebDriver, requisição {request.url} será ignorada após tentativa de reinicialização.")
        except Exception as e:
            self.spider.logger.error(f"Erro inesperado ao processar requisição com Chrome {request.url}: {e}. Ignorando requisição.")
            raise IgnoreRequest(f"Falha ao carregar a página com o Chrome: {request.url}")

    def spider_closed(self):
        if self.driver:
            self.driver.quit()
            self.driver = None