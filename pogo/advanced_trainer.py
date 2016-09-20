import math
from trainer import *
from pogo.inventory import items

class Champion(Trainer):
    def manage_items(self, potion_quota, revive_quota, berry_quota, ball_quota):
        logging.info("Managing Inventory...")
        bag = self.session.inventory.bag

        potions = [
            items.MAX_POTION,
            items.HYPER_POTION,
            items.SUPER_POTION,
            items.POTION
        ]

        revives = [
            items.MAX_REVIVE,
            items.REVIVE
        ]

        berries = [
            items.RAZZ_BERRY
        ]

        balls = [
            items.ULTRA_BALL,
            items.GREAT_BALL,
            items.POKE_BALL
        ]

        # Discard redundant potions
        total_potion = 0
        for i in range(len(potions)):
            if potions[i] in bag:
                total_potion += bag[potions[i]]
                if total_potion > potion_quota:
                    self.session.recycleItem(potions[i], total_potion - potion_quota)
                    total_potion = potion_quota
                    time.sleep(1)

        total_revive = 0
        for i in range(len(revives)):
            if revives[i] in bag:
                total_revive += bag[revives[i]]
                if total_revive > revive_quota:
                    self.session.recycleItem(revives[i], total_revive - revive_quota)
                    total_revive = revive_quota
                    time.sleep(1)

        total_berry = 0
        for i in range(len(berries)):
            if berries[i] in bag:
                total_berry += bag[berries[i]]
                if total_berry > berry_quota:
                    self.session.recycleItem(berries[i], total_berry - berry_quota)
                    total_berry = berry_quota
                    time.sleep(1)

        total_ball = 0
        for i in range(len(balls)):
            if balls[i] in bag:
                total_ball += bag[balls[i]]
                if total_ball > ball_quota:
                    self.session.recycleItem(balls[i], total_ball - ball_quota)
                    total_ball = ball_quota
                    time.sleep(1)

    def measure_pokemon(self):
        logging.info("Measuring strengths...")
        party = self.session.inventory.party
        for pokemon in party:
            logging.info("Measuring " + pokedex[pokemon.pokemon_id] + "'s IV:")
            atk_iv = pokemon.individual_attack
            def_iv = pokemon.individual_defense
            sta_iv = pokemon.individual_stamina
            new_nickname = 'A' + str(atk_iv) + '-D' + str(def_iv) + '-S' + str(def_iv)
            logging.info("Renaming " + pokedex[pokemon.pokemon_id] + " into " + new_nickname)
            self.session.nicknamePokemon(pokemon, new_nickname)
            time.sleep(1)

    def manage_pokemon(self):
        logging.info("Optimising party...")
        party = self.session.inventory.party
        food_count = dict()
        common_count = dict()

        for pokemon in party:
            if pokemon.pokemon_id in pokedex.trash:
                logging.info("Releasing " + pokedex[pokemon.pokemon_id] + " " + pokemon.nickname)
                self.session.releasePokemon(pokemon)
                time.sleep(1)

        for pokemon in party:
            if pokemon.pokemon_id in pokedex.food:
                if pokemon.pokemon_id not in food_count:
                    food_count[pokemon.pokemon_id] = [pokemon]
                else:
                    food_count[pokemon.pokemon_id].append(pokemon)

        for f in food_count:
            food_count[f].sort(key = lambda x: x.cp)
            no_transfer = len(food_count[f]) - min(len(food_count[f]), self.session.inventory.candies[f] / (pokedex.evolves[f] - 1))
            for i in range(min(no_transfer, len(food_count[f])-1)):
                logging.info("Releasing " + pokedex[f] + " " + food_count[f][i].nickname)
                self.session.releasePokemon(food_count[f][i])
                time.sleep(1)

        for pokemon in party:
            if (pokemon.pokemon_id not in pokedex.food) and (pokemon.pokemon_id not in pokedex.precious):
                if pokemon.pokemon_id not in common_count:
                    common_count[pokemon.pokemon_id] = [pokemon]
                else:
                    common_count[pokemon.pokemon_id].append(pokemon)

        for f in common_count:
            no_poke = len(common_count[f])
            for i in common_count[f]:
                if no_poke == 1: break
                iv = [i.individual_attack, i.individual_defense, i.individual_stamina]
                if (iv[0] < 10 and iv[1] < 10 and iv[2] < 10) or (sum(iv) < 20):
                    no_poke -= 1
                    logging.info("Releasing " + pokedex[f] + " " + i.nickname)
                    self.session.releasePokemon(i)
                    time.sleep(1)
