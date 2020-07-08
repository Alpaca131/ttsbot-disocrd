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
voice_active = []


@client.event
async def on_ready():
    print('ready')
    if not discord.opus.is_loaded():
        # もし未ロードだったら
        discord.opus.load_opus("heroku-buildpack-libopus")

@client.event
async def on_message(message):
    global voice_active, language
    if message.author.bot:
        return
    if message.content == '/release note':
        await message.channel.send('◆2020/07/09(1:28)リリース◆\n\n機能追加\n・複数サーバーでの同時実行に対応\n\nバグフィックス\n・言語選択が機能しないバグを修正')
    if message.content.startswith('/connect'):
        if message.author.voice is None:
            await message.channel.send('VCに接続してからもう一度お試し下さい。')
            return
        voice_active.append(str(message.guild.id))
        await message.channel.send(message.author.voice.channel.name + 'に参加しました。')
        if message.content[9:] == '日本語' or 'JP' or 'Jp' or 'jp' or None:
            print('JP')
            language = 'ja-JP'
            await discord.VoiceChannel.connect(message.author.voice.channel)
            return
        if message.content[9:] == '韓国語' or 'JP' or 'Jp' or 'jp':
            print('KR')
            language = 'ko-KR'
            await discord.VoiceChannel.connect(message.author.voice.channel)
            return
        if message.content[9:] == '中国語' or 'CH' or 'Ch' or 'or':
            print('CH')
            language = 'cmn-CN'
            await discord.VoiceChannel.connect(message.author.voice.channel)
            return
        if message.content[9:] == '英語' or 'EN' or 'En' or 'en':
            print('EN')
            language = 'en-US'
            await discord.VoiceChannel.connect(message.author.voice.channel)
            return


    # 切断
    if message.content == '/discon':
        if str(message.guild.id) not in voice_active:
            await message.channel.send('現在Botはどのチャンネルにも接続していません。')
            return
        voich = message.guild.voice_client
        if voich is None:
            await message.channel.send('Botと同じVCに入ってからもう一度お試し下さい。')
            return
        await voich.disconnect()
        voice_active.remove(message.guild.id)
        return

    if str(message.guild.id) in voice_active:
        if message.content.find('http') != -1:
            pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
            text_to_serch = message.content
            url_list = re.findall(pattern, text_to_serch)
            text_mod = message.content
            for item in url_list:
                text_mod = text_mod.remove(item)
            speech_text = text_mod
        else:
            speech_text = message.content
        str_url = "https://texttospeech.googleapis.com/v1beta1/text:synthesize?key="
        str_headers = {'Content-Type': 'application/json; charset=utf-8'}
        url = str_url + str_api_key
        str_json_data = {
            'input': {
                'text': speech_text
            },
            'voice': {
                'languageCode': language,
                'name': language + '-Wavenet-C',
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
            with open(str(message.guild.id) + 'data.mp3', 'wb') as outfile:
                outfile.write(base64.b64decode(parsed['audioContent']))
            voich = message.guild.voice_client
            voich.play(discord.FFmpegPCMAudio(str(message.guild.id) + 'data.mp3'), after=print('playing'))
            return

    await dispand(message)

client.run(TOKEN)