import json
import re
import time
import requests
import gdshortener
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from bs4 import BeautifulSoup
from selenium import webdriver
from io import BytesIO
from PIL import Image
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import os


path_file_json_config = 'config.json'


#config.json
def load_configs():
    global time_sleep, token, id_grupo, id_canal, id_test, id_magazineluiza, link_grupo, link_canal
    try:
        if os.path.exists(path_file_json_config):
            with open(path_file_json_config, 'r') as file:
                config = json.load(file)
                time_sleep = int(config['timesleep'])
                token = config['token_bot']
                id_grupo = config['id_grupo']
                id_canal = config['id_canal']
                id_test = config['id_test']
                id_magazineluiza = config['id_magazineluiza']
                link_grupo = config['link_grupo']
                link_canal = config['link_canal']
        else:
            with open(path_file_json_config, 'w') as file:
                configs = {'timesleep': 0,
                           'token_bot': '',
                           'id_grupo': '',
                           'id_canal': '',
                           'id_test': '',
                           'id_magazineluiza': '',
                           'link_grupo': '',
                           'link_canal': ''}
                json.dump(configs, file, indent=2)
    except Exception as e:
        print(f'Erro: {e}')


load_configs()


class MarketPlace:
    def __init__(self, link, time_sleep=1):
        chrome_op = Options()
        chrome_op.add_argument('--headless')
        self.url = link
        standard_plataform = re.compile("(aliexpress|mercadolivre|magalu|amzn|shope|magazinevoce|bit|tid)")
        find_plataform = str(standard_plataform.findall(self.url))
        platform = self._formata_texto(find_plataform)
        navigator = webdriver.Chrome(options=chrome_op)
        navigator.get(self.url)
        self._site_html = BeautifulSoup(navigator.page_source, 'html.parser')
        if platform == 'aliexpress':
            self._scrapingAliexpress()
        elif platform == 'mercadolivre':
            self._scrapingMercadoLivre()
        elif platform == 'amzn':
            self._scrapingAmazon()
        elif platform == 'magalu' or 'magazinevoce' or 'bit' or 'tid':
            request_link = requests.get(self.url).url
            new_link = request_link.split('/', 4)
            new_link[3] = id_magazineluiza
            new = '/'.join(new_link)
            self.url = self.shorten_link(new)
            self._scrapingMagazine()
        time.sleep(time_sleep)

    def shorten_link(self, link):
        s = gdshortener.ISGDShortener()
        short_link = s.shorten(link)
        return str(short_link[0])

    def _formata_texto(self, mensagem: str):
        padrao = r"[\[''\]]"
        new_text = re.sub(padrao, "", mensagem)
        return new_text

    def _scrapingAmazon(self):
        try:
            self.product_name = self._site_html.find('span', id='productTitle').get_text().strip()
            price = self._site_html.find('span', class_='a-offscreen')
            div_image = self._site_html.find('div', id='imgTagWrapperId')
            product_image = div_image.find('img')
            self.src_image = product_image['src']
            image_request = requests.get(self.src_image)
            img = Image.open(BytesIO(image_request.content))
            img.save('img.png')
            self.money_amount = ''
            for p in price:
                self.money_amount += p.text
        except Exception as e:
            print(f'Erro: {e}')

    def _scrapingAliexpress(self):
        try:
            self.product_name = self._site_html.find('h1', {'data-pl': 'product-title'}).get_text().strip()
            price = self._site_html.find('div', class_='es--wrap--erdmPRe notranslate')
            div_image = self._site_html.find('div', 'magnifier--wrap--hQvf3up')
            product_image = div_image.find('img')
            self.src_image = product_image['src']
            image_request = requests.get(self.src_image)
            img = Image.open(BytesIO(image_request.content))
            img.save('img.png')
            self.money_amount = ''
            for p in price:
                self.money_amount += p.text
        except Exception as e:
            print(f'Erro: {e}')

    def _scrapingMagazine(self):
        try:
            self.product_name = self._site_html.find('h1', {'data-testid': 'heading-product-title'}).get_text().strip()
            price = self._site_html.find('p', {'data-testid': 'price-value'}).get_text().strip()
            div_image = self._site_html.find('div', class_='sc-iGgWBj depLym')
            product_image = div_image.find('img')
            self.src_image = product_image['src']
            image_request = requests.get(self.src_image)
            img = Image.open(BytesIO(image_request.content))
            img.save('img.png')
            self.money_amount = ''
            for p in price:
                self.money_amount += p
        except Exception as e:
            print(f'Erro: {e}')

    def _scrapingMercadoLivre(self):
        try:
            self.product_name = self._site_html.find('h3', class_='ui-eshop-item__title').get_text().strip()
            price = self._site_html.find('span', class_='andes-money-amount__fraction').get_text().strip()
            div_image = self._site_html.find('div', class_='ui-eshop-item__image-link')
            product_image = div_image.find('img')
            self.src_image = product_image['src']
            image_request = requests.get(self.src_image)
            img = Image.open(BytesIO(image_request.content))
            img.save('img.png')
            self.money_amount = 'R$'
            for p in price:
                self.money_amount += p
        except Exception as e:
            print(f'Erro: {e}')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello friend!')


async def set_time_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE, ):
    command = ' '.join(context.args)
    if command == '':
        with open(path_file_json_config, 'r') as file:
            dados = json.load(file)
        await update.message.reply_text('💤 Time Sleep atual: ' + str(dados['timesleep']) + ' segundos')
    else:
        try:
            with open(path_file_json_config, 'r') as file:
                dados = json.load(file)
            with open(path_file_json_config, 'w') as file:
                dados['timesleep'] = int(command)
                json.dump(dados, file, indent=2)
            await update.message.reply_text(f'💤 Time Sleep definido para: {command} segundos')
        except Exception as e:
            await update.message.reply_text(f'Erro: {e}')


def loadConfig():
    try:
        with open(path_file_json_config, 'r') as file:
            dados = json.load(file)
            time_sleep = int(dados['timesleep'])
            return time_sleep
    except Exception as e:
        print(f'Falha: {e}')


async def send_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = ' '.join(context.args)
    chat_id = id_grupo
    tempo = time_sleep
    count_number = 0
    await update.message.reply_text(f'⚙️ Preparando link(s)...\n⏱️ Time sleep: {tempo} segundos')
    link = url.split(' ')
    tempo_inicial = time.time()
    try:
        for ln in link:
            count_number += 1
            try:
                ti = time.time()
                dados = MarketPlace(ln, time_sleep=tempo)
                img_response = requests.get(dados.src_image)
                imagem = Image.open(BytesIO(img_response.content))
                imagem.save('img.png')
                path_img = 'img.png'
                text = (f'📢 {dados.product_name}\n\n💶 {dados.money_amount}\n🎟 CUPOM: \n✅ {dados.url}\n\n▶️Grupos de ofertas:\n'
                        f'{link_grupo}')
                await context.bot.send_photo(chat_id=chat_id, photo=open(path_img, 'rb'), caption=text)
                tf = time.time()
                await update.message.reply_text(f'☑️ Link {count_number} enviado! ⏱️ Tempo: {(tf - ti):.2f} segundos')
                print(f'Tarefa executada... CHAT_ID: {update.message.chat.id} CHAT_TYPE: {update.message.chat.type}')
            except Exception as e:
                await update.message.reply_text(f'❌ Link {count_number} falhou!')
                print(f'Erro: {e}')
                continue
    except Exception as e:
        await update.message.reply_text(f'❌Erro: {e}')
        print(f'Erro: {e}')
    finally:
        await update.message.reply_text('✅ Tarefa conluida!')
    tempo_final = time.time()
    print(f'Tempo de execução: {(tempo_final - tempo_inicial):.2f} segundos')


async def send_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = ' '.join(context.args)
    chat_id = id_canal
    tempo = time_sleep
    count_number = 0
    await update.message.reply_text(f'⚙️ Preparando link(s)...\n⏱️ Time sleep: {tempo} segundos')
    link = url.split(' ')
    tempo_inicial = time.time()
    try:
        for ln in link:
            count_number += 1
            try:
                ti = time.time()
                dados = MarketPlace(ln, time_sleep=tempo)
                img_response = requests.get(dados.src_image)
                imagem = Image.open(BytesIO(img_response.content))
                imagem.save('img.png')
                path_img = 'img.png'
                text = (f'📢 {dados.product_name}\n\n💶 {dados.money_amount}\n🎟 CUPOM: \n✅ {dados.url}\n\n▶️Grupos de ofertas:\n'
                        f'{link_canal}')
                await context.bot.send_photo(chat_id=chat_id, photo=open(path_img, 'rb'), caption=text)
                tf = time.time()
                await update.message.reply_text(f'☑️ Link {count_number} enviado! ⏱️ Tempo: {(tf - ti):.2f} segundos')
                print(f'Tarefa executada... CHAT_ID: {update.message.chat.id} CHAT_TYPE: {update.message.chat.type}')
            except Exception as e:
                await update.message.reply_text(f'❌ Link {count_number} falhou!')
                print(f'Erro: {e}')
                continue
    except Exception as e:
        await update.message.reply_text(f'❌Erro: {e}')
        print(f'Erro: {e}')
    finally:
        await update.message.reply_text('✅ Tarefa conluida!')
    tempo_final = time.time()
    print(f'Tempo de execução: {(tempo_final - tempo_inicial):.2f} segundos')


async def send_to_testChanel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = ' '.join(context.args)
    chat_id = id_test
    tempo = time_sleep
    count_number = 0
    await update.message.reply_text(f'⚙️ Preparando link(s)...\n⏱️ Time sleep: {tempo} segundos')
    link = url.split(' ')
    tempo_inicial = time.time()
    try:
        for ln in link:
            count_number += 1
            try:
                ti = time.time()
                dados = MarketPlace(ln, time_sleep=tempo)
                img_response = requests.get(dados.src_image)
                imagem = Image.open(BytesIO(img_response.content))
                imagem.save('img.png')
                path_img = 'img.png'
                text = (f'📢 {dados.product_name}\n\n💶 {dados.money_amount}\n🎟 CUPOM: \n✅ {dados.url}\n\n▶️Grupos de ofertas:\n'
                        f'{link_grupo}')
                await context.bot.send_photo(chat_id=chat_id, photo=open(path_img, 'rb'), caption=text)
                tf = time.time()
                await update.message.reply_text(f'☑️ Link {count_number} enviado! ⏱️ Tempo: {(tf - ti):.2f} segundos')
                print(f'Tarefa executada... CHAT_ID: {update.message.chat.id} CHAT_TYPE: {update.message.chat.type}')
            except Exception as e:
                await update.message.reply_text(f'❌ Link {count_number} falhou!')
                print(f'Erro: {e}')
                continue
    except Exception as e:
        await update.message.reply_text(f'❌Erro: {e}')
        print(f'Erro: {e}')
    finally:
        await update.message.reply_text('✅ Tarefa conluida!')
    tempo_final = time.time()
    print(f'Tempo de execução: {(tempo_final - tempo_inicial):.2f} segundos')


if __name__ == '__main__':
    try:
        application = ApplicationBuilder().token(token).build()
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('test', send_to_testChanel))
        application.add_handler(CommandHandler('grupo', send_to_group))
        application.add_handler(CommandHandler('canal', send_to_channel))
        application.add_handler(CommandHandler('time', set_time_sleep))
        print('bot iniciado...')
        application.run_polling()
    except:
        print(f'Adicione a API TOKEN no arquivo \"{path_file_json_config}\" para o bot funcionar\n'
              f'OBS.: Adicione tabém as configurações de do ID do Canal ou Grupo, '
              f'ID da Magazine Luiza e o Link do seu grupo ou canal')