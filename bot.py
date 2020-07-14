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
voice_active_guild = []
lang = {}
spk_rate_dic = {}
voice_active_ch = []


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
    if message.content == 't.help':
        await message.channel.send('このBotのヘルプです。\n\n「t.con (オプション:反応する対象、言語)」\n(使用例：t.con en server)\n自分が接続しているVCにBotを接続させます。\n反応する対象：\n・指定なし(もしくはchannel)･･･コマンドのチャンネルに反応\n・server･･･サーバー全体に反応\n\n言語：\n・指定なし(もしくはjp)･･･日本語\n・en･･･英語\n・kr･･･韓国語\n・ch･･･中国語\n\n「t.dc」\n**自分が接続しているVCから**このBotを切断します。\n\n「t.release note」\nこのBotの最新のアップデート内容を確認できます。\n\n「t.invite」\nこのBotの招待リンクを送ります。ご自由にお使い下さい。\n\n「t.support」\nこのBotのサポートサーバーの招待リンクを送ります。バグ報告・要望等あればこちらまでお願いします。')
    if message.content == 't.release note':
        await message.channel.send('◆2020/07/14(22:07)リリース◆\n\n機能追加\n・サポートサーバーへのリンクを追加\n\nバグフィックス\n・なし')
    if message.content == 't.invite':
        await message.channel.send('このBotの招待リンクです。導入してもらえると喜びます。\n開発者:Alpaca#8032\nhttps://discord.com/api/oauth2/authorize?client_id=727508841368911943&permissions=3153472&scope=bot')
    if message.content == 't.support':
        await message.channel.send('このBotのサポートサーバーです。バグ報告・要望等あればこちらにお願いします。お気軽にどうぞ。\nhttps://discord.gg/DbtZAcX')

    if message.content.startswith('t.con'):
        global voice_active
        if message.author.voice is None:
            await message.channel.send('VCに接続してからもう一度お試し下さい。')
            return
        # チャンネル
        if message.content.find('channel')!=-1:
            print('channel')
            detect = '(チャンネルに反応)'
            voice_active_ch.append(message.channel.id)
        # サーバー
        elif message.content.find('server')!=-1:
            print('guild')
            detect = '(サーバー全体に反応)'
            voice_active_guild.append(message.guild.id)
        # その他
        else:
            print('else-ch')
            detect = '(チャンネルに反応)'
            voice_active_ch.append(message.channel.id)

        await message.channel.send(message.author.voice.channel.name + 'に接続しました。 ' + detect)
        if message.content[6:8] == 'jp':
            print(message.content[6:8])
            print('JP')
            language = 'ja-JP'
            lang[str(message.guild.id)] = language
        elif message.content[6:8] =='kr':
            print(message.content[6:8])
            print('KR')
            language = 'ko-KR'
            lang[str(message.guild.id)] = language
        elif message.content[6:9] == 'ch':
            print(message.content[6:8])
            print('CH')
            language = 'cmn-CN'
            lang[str(message.guild.id)] = language
        elif message.content[6:8] == 'en':
            print(message.content[6:8])
            print('EN')
            language = 'en-US'
            lang[str(message.guild.id)] = language
        else:
            print('else-JP')
            print(message.content[6:8])
            language = 'ja-JP'
            lang[str(message.guild.id)] = language

        await discord.VoiceChannel.connect(message.author.voice.channel)
        return


    # 切断
    if message.content == 't.dc':
        voich = message.guild.voice_client
        if message.guild.id in voice_active_guild:
            voice_active_guild.remove(message.guild.id)
            del lang[str(message.guild.id)]
            await voich.disconnect()
        elif message.channel.id in voice_active_ch:
            voice_active_ch.remove(message.channel.id)
            del lang[str(message.guild.id)]
            await voich.disconnect()
        else:
            await message.channel.send('現在Botはどのチャンネルにも参加していません。')
        return

    if message.guild.id in voice_active_guild or message.channel.id in voice_active_ch:
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
        language = lang[str(message.guild.id)]
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

client.run(TOKEN)