import scrapy

class PlayerStatsItem(scrapy.Item):
    team_name = scrapy.Field()
    player_name = scrapy.Field()
    maps_played = scrapy.Field()
    rounds_played = scrapy.Field()
    kd_diff = scrapy.Field()
    kd_ratio = scrapy.Field()
    rating = scrapy.Field()
    side = scrapy.Field() # To distinguish between 'Overall', 'Terrorist', 'CT'

class MatchResultItem(scrapy.Item): # NOVO ITEM PARA RESULTADOS DE PARTIDAS
    team_name = scrapy.Field() # O time que estamos analisando
    date = scrapy.Field()
    event = scrapy.Field()
    opponent = scrapy.Field()
    map_name = scrapy.Field()
    result_score = scrapy.Field()
    win_lose = scrapy.Field()