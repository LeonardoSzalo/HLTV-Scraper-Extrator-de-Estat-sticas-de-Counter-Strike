import pandas as pd
from collections import defaultdict
from itemadapter import ItemAdapter
from hltv_scraper.items import PlayerStatsItem, MatchResultItem # Importar ambos os Itens

class HltvScraperPipeline:
    def __init__(self):
        self.all_player_stats = defaultdict(list) # Mantido, caso decida usar os dados Overall
        self.terrorist_stats = defaultdict(list)
        self.ct_stats = defaultdict(list)
        self.match_results = defaultdict(list) # Para os resultados das partidas

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if isinstance(item, PlayerStatsItem):
            side = adapter.pop('side')

            if side == 'Overall':
                for key, value in adapter.items():
                    self.all_player_stats[key].append(value)
            elif side == 'Terrorist':
                for key, value in adapter.items():
                    self.terrorist_stats[key].append(value)
            elif side == 'CT':
                for key, value in adapter.items():
                    self.ct_stats[key].append(value)
        elif isinstance(item, MatchResultItem):
            for key, value in adapter.items():
                self.match_results[key].append(value)
        return item

    def close_spider(self, spider):
        if self.all_player_stats:
            df_all_stats = pd.DataFrame(self.all_player_stats)
            df_all_stats.to_csv('hltv_all_player_stats.csv', index=False)
            spider.logger.info("DataFrame salvo: hltv_all_player_stats.csv")

        if self.terrorist_stats:
            df_terrorist_stats = pd.DataFrame(self.terrorist_stats)
            df_terrorist_stats.to_csv('hltv_terrorist_stats.csv', index=False)
            spider.logger.info("DataFrame salvo: hltv_terrorist_stats.csv")

        if self.ct_stats:
            df_ct_stats = pd.DataFrame(self.ct_stats)
            df_ct_stats.to_csv('hltv_ct_stats.csv', index=False)
            spider.logger.info("DataFrame salvo: hltv_ct_stats.csv")

        if self.match_results:
            df_match_results = pd.DataFrame(self.match_results)
            df_match_results.to_csv('hltv_match_results.csv', index=False)
            spider.logger.info("DataFrame salvo: hltv_match_results.csv")

        spider.logger.info("Todos os DataFrames relevantes processados e salvos.")