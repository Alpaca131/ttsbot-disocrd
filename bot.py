import requests
import base64
import json
import discord
import os
from dispander import dispand
from discord.ext import tasks
import re

client = discord.Client()
TOKEN = os.environ['DISCORD_BOT_TOKEN']
str_api_key = os.environ['GCP_API']
voice_active = {}
spk_rate_dic = {}


@client.event
async def on_ready():
    print('ready')
    if not discord.opus.is_loaded():
        # もし未ロードだったら
        discord.opus.load_opus("heroku-buildpack-libopus")

@client.event
async def on_message(message):
    global voice_active, dispand, spk_rate_dic
    if message.author.bot:
        return
    if message.content == '!help':
        await message.channel.send('このBotのヘルプです。\n\n「!con 言語」\n(使用例：!con en)\n自分が接続しているVCにBotを接続させます。\n言語：\n・指定なし(もしくはjp)･･･日本語\n・en･･･英語\n・kr･･･韓国語\n・ch･･･中国語\n\n「!discon」\n**自分が接続しているVCから**このBotを切断します。\n\n「!release note」\nこのBotの最新のアップデート内容を確認できます。\n\n「!invite」\nこのBotの招待リンクを送ります。ご自由にお使い下さい。')
    if message.content == '!release note':
        await message.channel.send('◆2020/07/09(19:11)リリース◆\n\n機能追加\n・プレフィックスを「//」から「!」へ変更\n・ヘルプを更新\n\nバグフィックス\n・複数サーバーで同時に使用している際、言語選択が正常に機能しない事があるバグを修正')
    if message.content == '!invite':
        await message.channel.send('このBotの招待リンクです。導入してもらえると喜びます。\n開発者:Alpaca#8032\nhttps://discord.com/api/oauth2/authorize?client_id=727508841368911943&permissions=3153472&scope=bot')

    if message.content.startswith('!con '):
        if message.author.voice is None:
            await message.channel.send('VCに接続してからもう一度お試し下さい。')
            return
        await message.channel.send(message.author.voice.channel.name + 'に接続しました。')
        if message.content[9:] == 'jp':
            print(message.content[9:])
            print('JP')
            language = 'ja-JP'
            voice_active[str(message.guild.id)] = language
        if message.content[9:] =='kr':
            print(message.content[9:])
            print('KR')
            language = 'ko-KR'
            voice_active[str(message.guild.id)] = language
        if message.content[9:] == 'ch':
            print(message.content[9:])
            print('CH')
            language = 'cmn-CN'
            voice_active[str(message.guild.id)] = language
        if message.content[9:] == 'en':
            print(message.content[9:])
            print('EN')
            language = 'en-US'
            voice_active[str(message.guild.id)] = language
        else:
            print('else-JP')
            print(message.content[9:])
            language = 'ja-JP'
            voice_active[str(message.guild.id)] = language

        await discord.VoiceChannel.connect(message.author.voice.channel)
        return


    # 切断
    if message.content == '!discon':
        if str(message.guild.id) not in voice_active:
            await message.channel.send('現在Botはどのチャンネルにも接続していません。')
            return
        voich = message.guild.voice_client
        if voich is None:
            await message.channel.send('Botと同じVCに入ってからもう一度お試し下さい。')
            return
        await voich.disconnect()
        del voice_active[str(message.guild.id)]
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
        language = voice_active[str(message.guild.id)]
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