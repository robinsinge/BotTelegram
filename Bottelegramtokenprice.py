import telebot
import requests
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from coinpaprika.client import Client
from moralis import evm_api
from covalent import CovalentClient

# @GolemD3Pierrebot sur telegram
TOKEN = '6879191013:AAHQBYclNWSKKgthF5NkFl3ouiGvgoVsNs8'
bot = telebot.TeleBot(TOKEN)

#client coinpaprika
free_client = Client()

#Clefs des différents API
clefmob= '5ae75c6a-334b-4db7-90a5-50d36242a09e'
clefCMC='25a9ee12-29dd-4be5-bf84-a634b3653183'
clefmoralis= 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImE4NmFmZjUyLWQzYmQtNGQxYi1iZjdjLTExMjljNWIwMGE3MiIsIm9yZ0lkIjoiMzY3MTM2IiwidXNlcklkIjoiMzc3MzIwIiwidHlwZUlkIjoiMTVmMGNlNWQtOGYyMC00Njk1LWI0NWUtYjkxZTRhMDg3YjVkIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3MDE4NjczMjAsImV4cCI6NDg1NzYyNzMyMH0.Py9Ygh8LiJj1pMA6hEQeShLFcV0hxqWqFEzWUSq4j6Y'
clefchainbase= '2Z7ariVsNucJAWzBGqaJ7PZEgIN'
clefcovalent='cqt_rQVYgQk96tWpyKjxpY8KPXF7HgpB'
# Dictionnaire pour stocker les réponses des utilisateurs
user_responses = {}

#requete API Mobula
def prixmobula(AssetName):
    url = "https://api.app-mobula.com/api/1/market/data"
    querystring = {"asset":AssetName,"APIkey":'5ae75c6a-334b-4db7-90a5-50d36242a09e'}
    response = requests.request("GET", url, params=querystring)
    print(response.text)
    return response.text

#requete API Moralis
def prixmoralis(chain,contract):
  params = {
    "chain": chain,
    "include": "percent_change",
    "address": contract
  }

  result = evm_api.token.get_token_price(
    api_key=clefmoralis,
    params=params,
  )
  return(result)

#requete API Coinmarketcap
def prixcmc(symbole):
    url = 'https://pro-api.coinmarketcap.com/v1/tools/price-conversion'
    parameters = {
        'amount': '1',  # Montant de la crypto-monnaie à convertir
        'symbol': symbole,  # Symbole de la crypto-monnaie (par exemple, 'sol' pour Solana)
        'convert': 'USD'   # Devise de conversion (par exemple, 'USD')
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': '25a9ee12-29dd-4be5-bf84-a634b3653183',
    }

    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        return data
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return str(e)

#requete API Chainbase
def prixchainbase(chain_id,contract_adress):
    url = "https://api.chainbase.online/v1/token/price?chain_id="+chain_id+"&contract_address="+contract_adress
    headers = {
        "accept": "application/json",
        "x-api-key": '2Z7ariVsNucJAWzBGqaJ7PZEgIN'
    }

    response = requests.get(url, headers=headers)
    return(response.text)

#requete API cpaprika
def prixcpaprika(symbole):
    url = f"https://api.coinpaprika.com/v1/tickers/{symbole}"
    try:
        reponse = requests.get(url)
        reponse.raise_for_status()
        donnees = reponse.json()
        return donnees
    except requests.RequestException as e:
        return f"Erreur lors de la récupération du prix: {e}"

'''
#requete API covalent
def prixcovalent(chaine,contract_address):
    c = CovalentClient(clefcovalent)
    b = c.pricing_service.get_token_prices(chaine,"USD",contract_address)
    if not b.error:
        print(b.data)
    else:
        print(b.error_message)
'''
#convertit la reponse de la requete en str plus lisible pour un format message telegram compatible uniquement avec mobula
def convertmsgmobula(json_str):
    try:
        data_dict = json.loads(json_str)
        readable_str = []
        for key, value in data_dict["data"].items():
            readable_str.append(f"{key.replace('_', ' ').title()}: {value}")
        return '\n'.join(readable_str)
    except json.JSONDecodeError:
        return "Erreur: Le format JSON est invalide."

#convertit la reponse de la requete en str plus lisible pour un format message telegram compatible uniquement avec cpaprika
def convertmsgcpaprika(donnees):
    try:
        # Extraction des informations utiles
        nom = donnees.get('name', 'Inconnu')
        symbole = donnees.get('symbol', 'Inconnu')
        rang = donnees.get('rank', 'Inconnu')
        prix_usd = donnees.get('quotes', {}).get('USD', {}).get('price', 'Prix non disponible')

        # Création du message
        message = f"Nom: {nom} ({symbole})\nRang: {rang}\nPrix (USD): {prix_usd}"

        return message
    except KeyError as e:
        return f"Erreur de clé: {e}"

#convertit la reponse de la requete en str plus lisible pour un format message telegram compatible uniquement avec coinmarketcap
def convertmsgcmc(donnees):
    try:
        # Extraction des données utiles
        symbole = donnees['data']['symbol']
        nom = donnees['data']['name']
        montant = donnees['data']['amount']
        prix = donnees['data']['quote']['USD']['price']
        date_mise_a_jour = donnees['data']['last_updated']

        # Convertir la date en format lisible
        date_lisible = date_mise_a_jour.replace('T', ' ').replace('Z', '')

        # Création du message
        message = f"Nom: {nom} ({symbole})\nMontant: {montant}\nPrix (USD): {prix:.2f}\nDernière mise à jour: {date_lisible}"

        return message
    except KeyError as e:
        return f"Erreur de clé: {e}"

#convertit la reponse de la requete en str plus lisible pour un format message telegram compatible uniquement avec moralis
def convertmsgmoralis(token_data):
    formatted_message = [
        f"Nom du Token: {token_data.get('tokenName', 'Non disponible')}",
        f"Symbole: {token_data.get('tokenSymbol', 'Non disponible')}",
        f"Prix en USD: {token_data.get('usdPriceFormatted', 'Non disponible')}",
        f"Changement sur 24h: {token_data.get('24hrPercentChange', 'Non disponible')}%",
        f"Plateforme d'échange: {token_data.get('exchangeName', 'Non disponible')}",
        f"Adresse du Token: {token_data.get('tokenAddress', 'Non disponible')}"
    ]

    return '\n'.join(formatted_message)

#convertit la reponse de la requete en str plus lisible pour un format message telegram compatible uniquement avec chainbase
def convertmsgchainbase(chaine_json):
    try:
        # Convertir la chaîne de caractères JSON en dictionnaire Python
        donnees = json.loads(chaine_json)

        # Extraire les informations nécessaires
        code = donnees.get("code", "")
        message = donnees.get("message", "")
        prix = donnees.get("data", {}).get("price", "")
        symbole = donnees.get("data", {}).get("symbol", "")
        date_mise_a_jour = donnees.get("data", {}).get("updated_at", "")

        # Formatter le message pour être lisible et clair
        message_final = f"Code: {code}\nMessage: {message}\nPrix de {symbole}: {prix}\nMise à jour le: {date_mise_a_jour}"

        return message_final
    except json.JSONDecodeError:
        return "Erreur de format JSON."

@bot.message_handler(commands=['mobulaprixtoken'])
def handle_mobula(message):
    try:
        _, param = message.text.split(maxsplit=1)
        resultat = prixmobula(param)
        print(resultat)
        bot.reply_to(message,convertmsgmobula(resultat))
    except ValueError:
        bot.reply_to(message, "Veuillez fournir un paramètre. Exemple:  ")

#la commande coinpaprika est définie dans la librairie coinpaprika

@bot.message_handler(commands=['cpaprikaprixtoken'])
def handle_cpaprika(message):
    try:
        _, param = message.text.split(maxsplit=1)
        resultat = prixcpaprika(param)
        bot.reply_to(message,convertmsgcpaprika(resultat))
    except ValueError:
        bot.reply_to(message, "Veuillez fournir un paramètre. Exemple: /cpaprikprixtoken bitcoin")

@bot.message_handler(commands=['cmcprixtoken'])
def handle_cmc(message):
    try:
        _, param = message.text.split(maxsplit=1)
        resultat = prixcmc(param)
        bot.reply_to(message,convertmsgcmc (resultat))
    except ValueError:
        bot.reply_to(message, "Veuillez fournir un paramètre. Exemple: /cmcprixtoken btc")

@bot.message_handler(commands=['moralisprixtoken'])
def handle_moralis(message):
    try:
        _, param1, param2 = message.text.split(maxsplit=2)
        resultat = prixmoralis(param1, param2)
        bot.reply_to(message, convertmsgmoralis(resultat))
    except ValueError:
        bot.reply_to(message, "Veuillez fournir la chaine ainsi que l'adresse. Exemple: /moralisprixtoken eth 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")

@bot.message_handler(commands=['chainbaseprixtoken'])
def handle_chainbase(message):
    try:
        _, param1, param2 = message.text.split(maxsplit=2)
        resultat = prixchainbase(param1, param2)
        bot.reply_to(message, convertmsgchainbase(resultat))
    except ValueError:
        bot.reply_to(message, "Veuillez fournir l'id de la chaine ainsi que l'adresse. Exemple: /chainbaseprixtoken 1 0x0000000000000000000000000000000000000000")

'''
#la commande pour covalent ne marche pas
@bot.message_handler(commands=['covalentprixtoken'])
def handle_chainbase(message):
    try:
        _, param1, param2 = message.text.split(maxsplit=2)
        response = prixcovalent(param1, param2)
        """
        if response:
            if not response.error:
                # Accéder aux données de prix
                token_prices = response.data
                # Traiter et formater token_prices selon vos besoins
        else:
            # Gérer l'erreur
            error_message = response.error_message
        """
        bot.reply_to(message,str(response))
    except ValueError:
        bot.reply_to(message, "Veuillez fournir la chaine ainsi que l'adresse. Exemple: /covalentprixtoken eth-mainnet 0x0000000000000000000000000000000000000000")
'''

bot.polling()