import requests
import base64
import json
import discord
import os
from dispander import dispand
from discord.ext import tasks

client = discord.Client()
TOKEN = os.environ['DISCORD_BOT_TOKEN']
str_api_key = os.environ['GCP_API']
voice_active = 'false'


@client.event
async def on_ready():
    print('ready')
    if not discord.opus.is_loaded():
        # もし未ロードだったら
        discord.opus.load_opus("heroku-buildpack-libopus")

@client.event
async def on_message(message):
    global voice_active, voich, language
    if message.author.bot:
        return
    if message.content.startswith('/connect'):
        if message.content[9:] == '日本語' or 'JP' or 'Jp' or 'jp':
            print('JP')
            language = 'ja-JP'
        elif message.content[9:] == '韓国語' or 'KR' or 'Kr' or 'kr':
            print('KR')
            language = 'ko-KR'
        elif message.content[9:] == '中国語' or 'CH' or 'Ch' or 'ch':
            print('CH')
            language = 'cmn-CN'
        elif message.content[9:] == '英語' or 'EN' or 'En' or 'en':
            print('EN')
            language = 'en-US'
        else:
            language = 'ja-JP'
        voich = await discord.VoiceChannel.connect(message.author.voice.channel)
        voice_active = 'true'
    # 切断
    if message.content.startswith('/discon'):
        await voich.disconnect()
        voice_active = 'false'

    if voice_active == 'true':
        if message.content.find('http') != -1:
            pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
            text_to_serch = message.content
            url_list = re.findall(pattern, text_to_serch)
            text_mod = message.content
            for item in url_list:
                text_mod = text_mod.remove
            str_url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize?key="
            str_headers = {'Content-Type': 'application/json; charset=utf-8'}
            url = str_url + str_api_key
            str_json_data = {
                'input': {
                    'text': text_mod
                },
                'voice': {
                    'languageCode': language,
                    'name': 'ja-JP-Wavenet-C',
                    'ssmlGender': 'MALE'
                },
                'audioConfig': {
                    'audioEncoding': 'MP3'
                }
            }
            jd = json.dumps(str_json_data)
            # print(jd)
            print("begin request")

            s = requests.Session()
            r = requests.post(url, data=jd, headers=str_headers)
            print("status code : ", r.status_code)
            print("end request")
            if r.status_code == 200:
                parsed = json.loads(r.text)
                with open('data.mp3', 'wb') as outfile:
                    outfile.write(base64.b64decode(parsed['audioContent']))
                voich.play(discord.FFmpegPCMAudio('data.mp3'), after=print('playing'))
                return

        else:
            str_url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize?key="
            str_headers = {'Content-Type': 'application/json; charset=utf-8'}
            url = str_url + str_api_key
            str_json_data = {
                'input': {
                    'text': message.content
                },
                'voice': {
                    'languageCode': 'ja-JP',
                    'name': 'ja-JP-Wavenet-C',
                    'ssmlGender': 'MALE'
                },
                'audioConfig': {
                    'audioEncoding': 'MP3'
                }
            }
            jd = json.dumps(str_json_data)
            # print(jd)
            print("begin request")

            s = requests.Session()
            r = requests.post(url, data=jd, headers=str_headers)
            print("status code : ", r.status_code)
            print("end request")
            if r.status_code == 200:
                parsed = json.loads(r.text)
                with open('data.mp3', 'wb') as outfile:
                    outfile.write(base64.b64decode(parsed['audioContent']))
                voich.play(discord.FFmpegPCMAudio('data.mp3'), after=print('playing'))
                return

    await dispand(message)

client.run(TOKEN)