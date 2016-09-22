import re
from pogo.trainer import *
from pogo.inventory import items

class Champion(Trainer):
    def manage_items(self, potion_quota, revive_quota, berry_quota, ball_quota, verbose=False):
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

        logging.info("Done.")

    def measure_pokemon(self, bot, chat_id, recent = False, verbose = False):
        logging.info("Measuring strengths...")
        party = self.session.inventory.party
        pattern = re.compile('^A([0-9]+)-D([0-9]+)-S([0-9]+)')
        for pokemon in party:
            if recent and pattern.match(pokemon.nickname): continue
            logging.info("Measuring " + pokedex[pokemon.pokemon_id] + "'s IV:")
            if verbose: bot.sendMessage(chat_id, "Measuring " + pokedex[pokemon.pokemon_id] + "'s IV:")
            atk_iv = pokemon.individual_attack
            def_iv = pokemon.individual_defense
            sta_iv = pokemon.individual_stamina
            new_nickname = 'A' + str(atk_iv) + '-D' + str(def_iv) + '-S' + str(sta_iv)
            logging.info("Renaming " + pokedex[pokemon.pokemon_id] + " into " + new_nickname)
            if verbose: bot.sendMessage(chat_id, "Renaming " + pokedex[pokemon.pokemon_id] + " into " + new_nickname)
            self.session.nicknamePokemon(pokemon, new_nickname)
            time.sleep(1)
        logging.info("Done.")

    def manage_pokemon(self, bot, chat_id, verbose = False):
        logging.info("Optimising party...")
        party = self.session.inventory.party
        food_count = dict()
        common_count = dict()

        released_log = []

        for pokemon in party:
            if pokemon.pokemon_id in pokedex.trash:
                logging.info("Releasing " + pokedex[pokemon.pokemon_id] + " " + pokemon.nickname)
                released_log.append("Releasing " + pokedex[pokemon.pokemon_id] + " " + pokemon.nickname)
                if verbose: bot.sendMessage(chat_id, "Releasing " + pokedex[pokemon.pokemon_id] + " " + pokemon.nickname)
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
            no_transfer = len(food_count[f]) - min(len(food_count[f]), self.session.inventory.candies[f] / (pokedex.evolves[f] - 2))
            for i in range(int(min(no_transfer, len(food_count[f])-1))):
                logging.info("Releasing " + pokedex[f] + " " + food_count[f][i].nickname)
                released_log.append("Releasing " + pokedex[f] + " " + food_count[f][i].nickname)
                if verbose: bot.sendMessage(chat_id, "Releasing " + pokedex[f] + " " + food_count[f][i].nickname)
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
                if i.cp >= 1000: continue
                if (iv[0] < 10 and iv[1] < 10 and iv[2] < 10) or (sum(iv) < 20):
                    no_poke -= 1
                    logging.info("Releasing " + pokedex[f] + " " + i.nickname)
                    released_log.append("Releasing " + pokedex[f] + " " + i.nickname)
                    if verbose: bot.sendMessage(chat_id, "Releasing " + pokedex[f] + " " + i.nickname)
                    self.session.releasePokemon(i)
                    time.sleep(1)

        logging.info("Done.")

        return released_log

    def WalkAndSpin(self, bot, chat_id, fort, verbose = False):
        if fort:
            details = self.session.getFortDetails(fort)
            logging.info("Spinning the Fort \"%s\":", details.name)
            if verbose: bot.sendMessage(chat_id, "Spinning the Fort \"%s\" " % details.name)
            # Walk over
            self.walkTo(fort.latitude, fort.longitude, step = 3.2)
            # Give it a spin
            fortResponse = self.session.getFortSearch(fort)
            awarded_items = dict()
            for item in fortResponse.items_awarded:
                if item.item_id not in awarded_items: awarded_items[item.item_id] = item.item_count
                else: awarded_items[item.item_id] += item.item_count

            logging.info(fortResponse)
            print(fortResponse.result)
            if verbose:
                if fortResponse.result == 1:
                    response = 'Awarded Items:'
                    for item in awarded_items:
                        response += '\n' + items[item] + 'x' + str(awarded_items[item])
                else: response = 'PokeStop on cooldown!'
                bot.sendMessage(chat_id, response)

    def FindAllPokemons(self, bot, chat_id, verbose = False):
        logging.info("Finding Nearby Pokemon:")
        cells = self.session.getMapObjects(bothDirections=False)

        latitude, longitude, _ = self.session.getCoordinates()
        logging.info("Current pos: %f, %f", latitude, longitude)

        listed = set()
        pokemons = []

        for cell in cells.map_cells:
            # Heap in pokemon protos where we have long + lat
            pokes = [p for p in cell.wild_pokemons]
            pokes += [p for p in cell.catchable_pokemons]
            for poke in pokes:
                # Normalize the ID from different protos
                pokemonId = getattr(poke, "pokemon_id", None)
                if not pokemonId: pokemonId = poke.pokemon_data.pokemon_id

                encounterId = getattr(poke, "encounter_id", None)

                # Find distance to pokemon
                dist = Location.getDistance(latitude, longitude, poke.latitude, poke.longitude)

                if (dist <= 500) and (encounterId not in listed):
                    # Log the pokemon found
                    logging.info("%s, %f meters away", pokedex[pokemonId], dist)
                    pokemons.append(poke)
                    listed.add(encounterId)
                    if verbose: bot.sendMessage(chat_id, "There is a %s %f meters away from your location." % pokedex[pokemonId], dist)

        return pokemons

    def FindBestPokemon(self, bot, chat_id, wanted, verbose = False):
        logging.info("Finding Nearby Pokemon:")
        cells = self.session.getMapObjects(radius = 100, bothDirections = True)

        latitude, longitude, _ = self.session.getCoordinates()
        logging.info("Current pos: %f, %f", latitude, longitude)

        listed = set()

        best_pokemon = None
        best_id = None
        best_dist = float("Inf")

        for cell in cells.map_cells:
            # Heap in pokemon protos where we have long + lat
            pokes = [p for p in cell.wild_pokemons]
            pokes += [p for p in cell.catchable_pokemons]
            for poke in pokes:
                # Normalize the ID from different protos
                pokemonId = getattr(poke, "pokemon_id", None)
                if not pokemonId: pokemonId = poke.pokemon_data.pokemon_id

                encounterId = getattr(poke, "encounter_id", None)

                # Find distance to pokemon
                dist = Location.getDistance(latitude, longitude, poke.latitude, poke.longitude)

                if (dist <= 500) and (encounterId not in listed):
                    # Log the pokemon found
                    logging.info("There is a %s %f meters away", pokedex[pokemonId], dist)
                    listed.add(encounterId)
                    if verbose: bot.sendMessage(chat_id, "There is a %s %f meters away from your location." % pokedex[pokemonId], dist)
                    if best_pokemon == None:
                       best_pokemon = poke
                       best_id = pokemonId
                       best_dist = dist
                    elif pokedex.getRarityById(pokemonId) > pokedex.getRarityById(best_id):
                         best_pokemon = poke
                         best_id = pokemonId
                         best_dist = dist
                    elif pokedex.getRarityById(pokemonId) == pokedex.getRarityById(best_id):
                         if pokedex[pokemonId] in wanted and pokedex[best_id] not in wanted:
                            best_pokemon = poke
                            best_id = pokemonId
                            best_dist = dist
                         elif pokedex[pokemonId] in wanted and pokedex[best_id] in wanted and best_dist > dist:
                              best_pokemon = poke
                              best_id = pokemonId
                              best_dist = dist

        return best_pokemon

    def catchPokemon(self, poke, bot, chat_id, verbose = False, thresholdP = 0.5, limit = 5, delay = 5):
        pokemonId = getattr(poke, "pokemon_id", None)
        if not pokemonId: pokemonId = poke.pokemon_data.pokemon_id
        logging.info('Attempting to catch ' + pokedex[pokemonId])

        f = open('./icons/' + str(pokemonId) + '.jpg')

        bot.sendMessage(chat_id, 'Attempting to catch ' + pokedex[pokemonId])

        if verbose:
            bot.sendPhoto(chat_id, f)
            bot.sendLocation(chat_id, poke.latitude, poke.longitude)
        self.walkTo(poke.latitude, poke.longitude, step = 3.2)

        # Start encounter
        encounter = self.session.encounterPokemon(poke)

        # If party full
        if encounter.status == encounter.POKEMON_INVENTORY_FULL:
            logging.error("Can't catch! Party is full!")
            bot.sendMessage(chat_id, "Your pokemon storage is full. Please use \do_poke to transfer weak pokemons")
        # Grab needed data from proto
        chances = encounter.capture_probability.capture_probability
        balls = encounter.capture_probability.pokeball_type
        balls = balls or [items.POKE_BALL, items.GREAT_BALL, items.ULTRA_BALL]
        bag = self.session.inventory.bag

        # Have we used a razz berry yet?
        berried = False

        # Make sure we aren't oer limit
        count = 0

        if pokemonId in pokedex.precious:
           limit = 20
        if pokemonId not in pokedex.precious:
           balls = [items.POKE_BALL, items.GREAT_BALL]
        if pokemonId in pokedex.trash or pokemonId in pokedex.food:
           balls = [items.POKE_BALL]
           limit = 3

        # Attempt catch
        while True:
            bestBall = items.UNKNOWN
            altBall = items.UNKNOWN

            # Check for balls and see if we pass
            # wanted threshold
            for i, ball in enumerate(balls):
                if bag.get(ball, 0) > 0:
                    altBall = ball
                    if i < len(chances) and chances[i] >= thresholdP:
                        bestBall = ball
                        break

            # If we can't determine a ball, try a berry
            # or use a lower class ball
            if bestBall == items.UNKNOWN:
                if not berried and bag.get(items.RAZZ_BERRY, 0) > 0:
                    logging.info("Using a RAZZ_BERRY")
                    if verbose: bot.sendMessage(chat_id, 'Using a RAZZ_BERRY')
                    self.session.useItemCapture(items.RAZZ_BERRY, poke)
                    berried = True
                    time.sleep(delay)
                    continue

                # if no alt ball, there are no balls
                elif altBall == items.UNKNOWN:
                    if verbose: bot.sendMessage(chat_id, 'You are out of ball. Please visit Pokemon Stops to get more balls.')
                    raise GeneralPogoException("Out of usable balls")
                else: bestBall = altBall

            # Try to catch it!!
            logging.info("Using a %s", items[bestBall])
            if verbose: bot.sendMessage(chat_id, 'Using a ' + items[bestBall])
            attempt = self.session.catchPokemon(poke, bestBall)
            time.sleep(delay)

            # Success or run away
            if attempt.status == 1:
                if verbose: bot.sendMessage(chat_id, pokedex[pokemonId] + ' has been caught.')
                return attempt

            # CATCH_FLEE is bad news
            if attempt.status == 3:
                if verbose: bot.sendMessage(chat_id, 'The pokemon has fleed ...')
                if count == 0:
                   logging.info("Possible soft ban.")
                   bot.sendMessage(chat_id, 'I suspect that we have been soft-banned by Niantic.')
                else: logging.info("Pokemon fleed at %dth attempt", count + 1)
                return attempt

            # Only try up to x attempts
            count += 1
            if count >= limit:
                logging.info("Over catch limit")
                if verbose: bot.sendMessage(chat_id, 'This pokemon resists too ferociously. I am letting it go.')
                return None

    def advance_bot(self, bot, chat_id, session, wanted, verbose = False):

        # Only perform n training episode
        n = 1000
        cooldown = 7
        # Run the bot
        while (n > 0):
            n -=1

            bot.sendMessage(chat_id, 'Managing inventory ...')

            self.manage_items(100, 50, 50, 200, verbose)
            self.measure_pokemon(bot, chat_id, recent = True, verbose = verbose)
            self.manage_pokemon(bot, chat_id, verbose)

            time.sleep(cooldown)

            forts = self.sortCloseForts()


            self.setEggs()
            time.sleep(cooldown)

            try:
                for fort in forts:
                    pokemon = self.FindBestPokemon(bot, chat_id, wanted, verbose = verbose)
                    self.catchPokemon(pokemon, bot, chat_id, verbose = verbose)
                    self.WalkAndSpin(bot, chat_id, fort, verbose = verbose)
                    time.sleep(cooldown)

            # Catch problems and reauthenticate
            except GeneralPogoException as e:
                logging.critical('GeneralPogoException raised: %s', e)
                self._session = self.auth.reauthenticate(self.session)
                time.sleep(cooldown)
                cooldown *= 2

            except Exception as e:
                logging.critical('Exception raised: %s', e)
                self._session = self.auth.reauthenticate(self.session)
                time.sleep(cooldown)
                cooldown *= 2