# HLTV Scraper: Extrator de Estatísticas de Counter-Strike
Um web scraper construído com Scrapy e Selenium para extrair dados detalhados de jogadores e resultados de partidas do HLTV.org, o principal portal de notícias e estatísticas de Counter-Strike.

## 📖 Sobre o Projeto
Este projeto foi desenvolvido para automatizar a coleta de dados estatísticos de times profissionais de Counter-Strike. A ferramenta navega pelo site da HLTV, contornando proteções de anti-bot como Cloudflare e pop-ups de consentimento de cookies, para extrair informações valiosas e estruturá-las em arquivos CSV para fácil análise.

O scraper é capaz de coletar:

Estatísticas Gerais dos Jogadores: K/D Ratio, Rating 2.0, Mapas Jogados, etc.

Estatísticas por Lado: Desempenho dos jogadores atuando como Terrorista (TR) e Contra-Terrorista (CT).

Resultados de Partidas: Histórico de confrontos dos times, incluindo oponentes, placares e mapas.

## ✨ Funcionalidades Principais
Scraping dos Top 50 Times: Automaticamente coleta dados dos times mais bem ranqueados em um período pré-definido.

Manipulação de Conteúdo Dinâmico: Utiliza Selenium com undetected-chromedriver para renderizar páginas baseadas em JavaScript e interagir com elementos da página (ex: aceitar cookies).

Dados Estruturados: Salva os dados coletados em quatro arquivos CSV distintos para uma análise organizada:

hltv_all_player_stats.csv (Estatísticas gerais)

hltv_terrorist_stats.csv (Estatísticas como Terrorista)

hltv_ct_stats.csv (Estatísticas como Contra-Terrorista)

hltv_match_results.csv (Resultados de partidas)

Scraping Consciente: Implementa delays e a extensão AutoThrottle do Scrapy para interagir com o site de forma respeitosa, evitando sobrecarregar seus servidores.

## 🛠️ Tecnologias Envolvidas
Este projeto utiliza uma combinação de tecnologias poderosas para web scraping e manipulação de dados:

Python: Linguagem de programação principal.

Scrapy: Framework de web crawling para a estrutura geral do scraper, gerenciamento de requisições e processamento de dados.

Selenium: Ferramenta de automação de navegador para lidar com JavaScript, interações e conteúdo dinâmico.

Undetected Chromedriver: Versão otimizada do Chromedriver para evitar detecção por sistemas anti-bot.

Pandas: Biblioteca utilizada para processar os dados coletados e exportá-los para arquivos CSV.

## 🚀 Começando
Siga estas instruções para configurar e executar o projeto em sua máquina local.

### Pré-requisitos
Antes de começar, garanta que você tenha os seguintes softwares instalados:

Python 3.8 ou superior

pip (gerenciador de pacotes do Python)

Google Chrome (instalado em sua versão mais recente)

Git

### Instalação e Uso
Clone o repositório:
```
git clone https://github.com/seu-usuario/hltv-scraper.git
cd hltv-scraper
```


### Crie e ative um ambiente virtual (recomendado):

No Windows:
```
python -m venv venv
.\venv\Scripts\activate
```
No macOS/Linux:
```
python3 -m venv venv
source venv/bin/activate
```
### Instale as dependências:
```
pip install -r requirements.txt
```

### Configure o Chromedriver:

Baixe o Chromedriver: Faça o download da versão do Chromedriver que corresponda exatamente à versão do seu Google Chrome. Você pode encontrá-lo no site oficial do Chrome for Testing.

Atualize o caminho: Extraia o arquivo chromedriver.exe (ou chromedriver em macOS/Linux) para uma pasta de sua preferência. Abra o arquivo hltv_scraper/settings.py e atualize a variável UNDETECTED_CHROMEDRIVER_PATH com o caminho completo para o executável.

Exemplo em settings.py:

## Altere este caminho para o local onde você salvou o chromedriver
UNDETECTED_CHROMEDRIVER_PATH = "C:/caminho/completo/para/drivers/chromedriver.exe"

## Execute o Scraper:
Com tudo configurado, execute o scraper a partir do diretório raiz do projeto com o seguinte comando:

scrapy crawl hltv_spider

O processo será iniciado, e você verá os logs da execução no seu terminal. Ao final, os arquivos CSV serão gerados na raiz do projeto.
```
📁 Estrutura do Projeto
hltv-scraper/
│
├── hltv_scraper/
│   ├── spiders/
│   │   ├── __init__.py
│   │   └── hltv_spider.py       # Lógica principal do spider (requests e parsing)
│   ├── __init__.py
│   ├── items.py                 # Definição dos itens de dados (data containers)
│   ├── middlewares.py           # Middleware com Selenium para processar requests
│   ├── pipelines.py             # Pipeline para processar e salvar os itens em CSV
│   └── settings.py              # Configurações do projeto (delays, paths, etc.)
│
└── scrapy.cfg                   # Arquivo de configuração de deploy do Scrapy
```
📄 Saída
Após a execução bem-sucedida, quatro arquivos CSV serão criados no diretório raiz do projeto, contendo os dados estruturados:

hltv_all_player_stats.csv: Estatísticas gerais de cada jogador.

hltv_terrorist_stats.csv: Estatísticas de cada jogador no lado Terrorista.

hltv_ct_stats.csv: Estatísticas de cada jogador no lado Contra-Terrorista.

hltv_match_results.csv: Histórico detalhado das partidas do time.

⚖️ Licença
Distribuído sob a Licença MIT. Veja LICENSE.txt para mais informações.
