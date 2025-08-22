import scrapy
from hltv_scraper.items import PlayerStatsItem, MatchResultItem # Importar ambos os Itens
import time
import random
import re
from scrapy.utils.project import get_project_settings # Necessário para pegar o caminho do chromedriver

class HltvSpider(scrapy.Spider):
    name = 'hltv_spider'
    allowed_domains = ['hltv.org']
    start_urls = ['https://www.hltv.org/'] # Inicia na homepage para lidar com cookies/Cloudflare

    def parse(self, response):
        # Navega para a página dos Top 50 times
        # Usando as datas que você especificou na inspeção mais recente
        top_teams_url = 'https://www.hltv.org/stats/teams?startDate=2025-04-21&endDate=2025-07-21&rankingFilter=Top50'
        yield response.follow(top_teams_url, callback=self.parse_team_list)

    def parse_team_list(self, response):
        # Extrai links para as páginas individuais dos times
        # Seletor baseado em: <td class="teamCol-teams-overview"><a href="...">...</a></td>
        team_links = response.css('td.teamCol-teams-overview a::attr(href)').getall()

        if not team_links:
            self.logger.error(f"Nenhum link de time encontrado em {response.url}. Verifique o seletor CSS 'td.teamCol-teams-overview a::attr(href)'.")
        else:
            self.logger.info(f"Encontrados {len(team_links)} links de times em {response.url}.")

        for link in team_links:
            team_page_url = response.urljoin(link)
            self.logger.info(f"Enfileirando requisição para a página do time: {team_page_url}")
            time.sleep(random.uniform(1, 3)) # Atraso aleatório para diminuir suspeita
            yield scrapy.Request(team_page_url, callback=self.parse_team_page)

    def parse_team_page(self, response):
        team_name = response.css('span.context-item-name::text').get()

        if not team_name:
            self.logger.warning(f"Não foi possível extrair o nome do time de {response.url}. Verifique o seletor 'span.context-item-name::text'.")
            return

        self.logger.info(f"Nome do time extraído com sucesso: {team_name.strip()} da URL {response.url}")

        # --- NAVEGAÇÃO PARA PÁGINA DE PARTIDAS ---
        # Exemplo da URL de partidas: https://www.hltv.org/stats/teams/matches/9565/vitality?startDate=...&rankingFilter=Top50
        match_url_suffix = "/matches/" + response.url.split("/teams/")[-1] # Pega "9565/vitality?startDate=..."
        team_matches_url = response.urljoin("/stats/teams" + match_url_suffix)

        self.logger.info(f"Enfileirando requisição para resultados de partidas do time: {team_matches_url}")
        time.sleep(random.uniform(1, 3))
        yield scrapy.Request(team_matches_url, callback=self.parse_match_results, meta={'team_name': team_name.strip(), 'driver': response.request.meta['driver']})
        # Note: 'driver': response.request.meta['driver'] é passado para que o driver do middleware seja reutilizado


        # --- Geração de URLs para as estatísticas de JOGADORES (Overall, Terrorist e CT) ---
        match_players_url_base = re.search(r'/stats/teams/(\d+)/([^?]+)', response.url)
        if match_players_url_base:
            team_id = match_players_url_base.group(1)
            team_slug = match_players_url_base.group(2)
            
            # Base URL para estatísticas de jogadores (sem side, que é o 'Overall')
            base_players_url = f'https://www.hltv.org/stats/teams/players/{team_id}/{team_slug}'
            query_params = response.url.split('?', 1)[1] if '?' in response.url else '' # Reusa parâmetros de data/ranking

            # Enfileira requisição para estatísticas GERAIS de jogadores
            overall_players_stats_url = f"{base_players_url}?{query_params}"
            self.logger.info(f"Enfileirando requisição para stats gerais de jogadores: {overall_players_stats_url}")
            time.sleep(random.uniform(1, 3))
            yield scrapy.Request(overall_players_stats_url, callback=self.parse_overall_player_stats, meta={'team_name': team_name.strip(), 'driver': response.request.meta['driver']})

            # Enfileira requisição para estatísticas do lado Terrorista
            terrorist_stats_url = f"{base_players_url}?{query_params}&side=TERRORIST"
            self.logger.info(f"Enfileirando requisição para stats T: {terrorist_stats_url}")
            time.sleep(random.uniform(1, 3))
            yield scrapy.Request(terrorist_stats_url, callback=self.parse_terrorist_stats, meta={'team_name': team_name.strip(), 'driver': response.request.meta['driver']})

            # Enfileira requisição para estatísticas do lado CT
            ct_stats_url = f"{base_players_url}?{query_params}&side=COUNTER_TERRORIST"
            self.logger.info(f"Enfileirando requisição para stats CT: {ct_stats_url}")
            time.sleep(random.uniform(1, 3))
            yield scrapy.Request(ct_stats_url, callback=self.parse_ct_stats, meta={'team_name': team_name.strip(), 'driver': response.request.meta['driver']})
        else:
            self.logger.warning(f"Não foi possível analisar ID/slug do time da URL: {response.url}. Não é possível gerar URLs de estatísticas de jogadores (geral/T/CT).")

    # --- CALLBACK PARA ESTATÍSTICAS GERAIS DE JOGADORES ---
    def parse_overall_player_stats(self, response):
        team_name = response.meta['team_name']
        yield from self.parse_player_stats(response, team_name, 'Overall')

    # --- FUNÇÃO PARA PARSEAR OS RESULTADOS DAS PARTIDAS ---
    def parse_match_results(self, response):
        team_name = response.meta['team_name']
        self.logger.info(f"Parsing resultados de partidas para o time: {team_name} em {response.url}")

        # Acessa o driver diretamente via response.request.meta['driver']
        driver = response.request.meta.get('driver')
        if not driver:
            self.logger.error(f"Driver não encontrado no meta da requisição para {response.url}. Não é possível rolar a página.")
            return

        # Lógica de rolagem da página para garantir que todo o conteúdo visível seja carregado
        # (mesmo que não seja rolagem infinita, rolar uma vez ajuda a renderizar o que está "abaixo da dobra")
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 5 # Um limite razoável para páginas que carregam tudo
        while scroll_attempts < max_scroll_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1, 3)) # Espera um pouco para o conteúdo renderizar
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height: # Se não rolou mais, todo o conteúdo já está lá
                break
            last_height = new_height
            scroll_attempts += 1
        self.logger.info(f"Página de partidas rolada {scroll_attempts} vezes até o fim para {response.url}.")

        # Re-parse o HTML da página após a rolagem para ter o conteúdo completo
        response = scrapy.http.HtmlResponse(url=response.url, body=driver.page_source, encoding='utf-8')


        # Seletor para as linhas de dados da tabela de partidas
        # <table class="stats-table"> (a imagem mostra 'stats-table' sem 'player-ratings-table' para partidas)
        match_rows = response.css('table.stats-table tbody tr')

        if not match_rows:
            self.logger.warning(f"Nenhuma linha de partida encontrada para {team_name} em {response.url}. Verifique o seletor 'table.stats-table tbody tr'.")
            self.logger.debug(f"HTML da tabela de partidas em {response.url}:\n{response.css('table.stats-table').get()[:10000]}") # Log da tabela inteira
            return

        self.logger.info(f"Encontradas {len(match_rows)} linhas de partidas para {team_name} em {response.url}.")

        for i, row in enumerate(match_rows):
            self.logger.debug(f"Linha de partida {i+1} HTML: {row.get()}")

            # 1. Date: <td class="time"><a href="...">22/06/25</a></td>
            date = row.css('td.time a::text').get()

            # 2. Event: <td class="gtSmartphone-only"><a href="..."><img...><span>BLAST.tv Austin Major 2025</span></a></td>
            # O texto do evento está dentro de um <span> dentro da <a>
            event = row.css('td.gtSmartphone-only a span::text').get()
            if not event: # Fallback para a versão smartphone-only se a gtSmartphone-only falhar
                event = row.css('td.smartphone-only a span::text').get()

            # 3. Opponent: <td><a href="..."><img ...>The MongolZ</a></td>
            # É a 4ª TD na linha (Date, Evento gtSmartphone-only, Evento smartphone-only, Oponente)
            # Usei nth-child(4) porque é a quarta coluna de td em geral
            opponent = row.css('td:nth-child(4) a::text').get()

            # 4. Map: <td class="statsMapPlayed"><span>Inferno</span></td>
            map_name = row.css('td.statsMapPlayed span::text').get()

            # 5. Result: <td class="gtSmartphone-only text-center "><span class="statsDetail">13 - 6</span></td>
            result_score = row.css('td.gtSmartphone-only span.statsDetail::text').get()

            # 6. W/L: <td class="text-center match-won won">W</td>
            win_lose = row.css('td.match-won::text, td.match-lost::text').get()


            if date and opponent: # Garante que os dados essenciais foram extraídos
                self.logger.info(f"Extraindo resultado de partida: Data: {date}, Evento: {event}, Oponente: {opponent}, Mapa: {map_name}, Resultado: {result_score}, W/L: {win_lose} para o time {team_name}.")
                item = MatchResultItem(
                    team_name=team_name,
                    date=date.strip() if date else 'N/A',
                    event=event.strip() if event else 'N/A',
                    opponent=opponent.strip() if opponent else 'N/A',
                    map_name=map_name.strip() if map_name else 'N/A',
                    result_score=result_score.strip() if result_score else 'N/A',
                    win_lose=win_lose.strip() if win_lose else 'N/A'
                )
                yield item
            else:
                self.logger.warning(f"Não foi possível extrair dados completos da linha de partida {i+1} em {response.url}. HTML da linha: {row.get()}")

    # --- FUNÇÃO PARA PARSEAR ESTATÍSTICAS DE JOGADORES (Overall, Terrorist, CT) ---
    def parse_player_stats(self, response, team_name, side):
        # O seletor para as linhas da tabela agora é mais específico para a tabela de jogadores
        player_rows = response.css('table.stats-table.player-ratings-table tbody tr')

        table_html_debug = response.css('table.stats-table.player-ratings-table').get()
        if table_html_debug:
            self.logger.debug(f"HTML da tabela para {team_name} (lado {side}) em {response.url}:\n{table_html_debug[:15000]}")
        else:
            self.logger.warning(f"Não encontrei a tabela 'table.stats-table.player-ratings-table' em {response.url}. Seletor 'table.stats-table.player-ratings-table' pode estar errado.")

        if not player_rows:
            self.logger.warning(f"Nenhuma linha de jogador encontrada para {team_name} (lado {side}) em {response.url}. Verifique o seletor 'table.stats-table.player-ratings-table tbody tr'.")
            return

        self.logger.info(f"Encontradas {len(player_rows)} linhas de jogadores para {team_name} ({side} side) em {response.url}.")

        for i, row in enumerate(player_rows):
            self.logger.debug(f"Row {i+1} HTML: {row.get()}")

            # 1. Nome do Jogador: <td class="playerCol bold"><a href="...">Name</a></td>
            player_name = row.css('td.playerCol a::text').get()

            # 2. Maps: <td class="statsDetail">51</td> - É a primeira statsDetail sem gtSmartphone-only
            maps_played = row.css('td.statsDetail:not(.gtSmartphone-only)::text').get()
            if not maps_played: # Fallback mais genérico (2ª TD geral)
                maps_played = row.css('td:nth-child(2)::text').get()

            # 3. Rounds: <td class="statsDetail gtSmartphone-only">555</td>
            rounds_played = row.css('td.statsDetail.gtSmartphone-only::text').get()
            if not rounds_played: # Fallback mais genérico (3ª TD geral)
                rounds_played = row.css('td:nth-child(3)::text').get()

            # 4. K-D Diff: <td class="kdDiffCol won"> +215 </td>
            kd_diff = row.css('td.kdDiffCol::text').get()

            # 5. K/D: <td class="statsDetail">1.75</td>
            # Pega todas as 'statsDetail' sem 'gtSmartphone-only', K/D seria o segundo item [1]
            all_stats_details_without_gt = row.css('td.statsDetail:not(.gtSmartphone-only)::text').getall()
            kd_ratio = all_stats_details_without_gt[1] if len(all_stats_details_without_gt) > 1 else 'N/A'
            if kd_ratio == 'N/A': # Fallback mais genérico (5ª TD geral)
                kd_ratio = row.css('td:nth-child(5)::text').get()

            # 6. Rating: <td class="ratingCol ratingPositive">1.31</td>
            rating = row.css('td.ratingCol::text').get()

            if player_name:
                self.logger.info(f"Extraindo dados do jogador: {player_name} (Maps: {maps_played}, Rounds: {rounds_played}, K-D Diff: {kd_diff}, K/D: {kd_ratio}, Rating: {rating}) para {team_name} ({side}).")
                item = PlayerStatsItem(
                    team_name=team_name,
                    player_name=player_name.strip(),
                    maps_played=maps_played.strip() if maps_played else 'N/A',
                    rounds_played=rounds_played.strip() if rounds_played else 'N/A',
                    kd_diff=kd_diff.strip() if kd_diff else 'N/A',
                    kd_ratio=kd_ratio.strip() if kd_ratio else 'N/A',
                    rating=rating.strip() if rating else 'N/A',
                    side=side
                )
                yield item
            else:
                self.logger.warning(f"Não foi possível extrair o nome do jogador da linha {i+1} em {response.url}. HTML da linha: {row.get()}")

    def parse_terrorist_stats(self, response):
        team_name = response.meta['team_name']
        # Reutiliza parse_player_stats, apenas com 'side' diferente
        yield from self.parse_player_stats(response, team_name, 'Terrorist')

    def parse_ct_stats(self, response):
        team_name = response.meta['team_name']
        # Reutiliza parse_player_stats, apenas com 'side' diferente
        yield from self.parse_player_stats(response, team_name, 'CT')