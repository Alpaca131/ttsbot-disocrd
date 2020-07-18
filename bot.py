import requests
import base64
import json
import discord
import os
from dispander import dispand
from discord.ext import tasks
import re
import json
from urllib.request import *
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import demoji

client = discord.Client()
TOKEN = os.environ['DISCORD_BOT_TOKEN']
str_api_key = os.environ['GCP_API']
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
voice_active_guild = []
lang = {}
spk_rate_dic = {}
voice_active_ch = []
word_limit = {}


@client.event
async def on_ready():
    global expand_off
    demoji.download_codes()
    print('ready')
    await client.change_presence(activity=discord.Game(name="「t.help」でヘルプ", type=1))
    f = drive.CreateFile({'id': '1zX-mbDeN_Mlx-p_62WSE5zAgsqu_jFX5'})
    f.GetContentFile('expand.json')
    with open('expand.json') as f:
        expand_off = json.load(f)
    if not discord.opus.is_loaded():
        # もし未ロードだったら
        discord.opus.load_opus("heroku-buildpack-libopus")

@client.event
async def on_message(message):
    global voice_active, dispand, spk_rate_dic, expand_off
    if message.author.bot:
        return
    if message.guild is None:
        if message.author.id == 539910964724891719:
            if message.content == 'サーバー':
                await message.channel.send(str(len(client.guilds)))
                return
    if message.guild.id not in expand_off:
        await dispand(message)
    if message.content == 't.help':
        await message.channel.send('このBotのヘルプです。\n\n**「t.con (オプション：反応する対象、言語、文字数制限)」**\n(使用例：t.con en server limit=50)\n自分が接続しているVCにBotを接続させます。\n\n反応する対象：\n・指定なし(もしくはchannel)･･･コマンドのチャンネルに反応\n・server･･･サーバー全体に反応\n\n文字数制限：\n・反応する文字数を制限できます。(limit=文字数)\n\n言語：\n・指定なし(もしくはjp)･･･日本語\n・en･･･英語\n・kr･･･韓国語\n・ch･･･中国語\n\n**「t.dc」**\n自分が接続しているVCからこのBotを切断します。\n\n**「t.expand (オプション：on/off)」**\nリンク展開機能のオンオフを切り替えます。\n\n**「t.release note」**\nこのBotの最新のアップデート内容を確認できます。\n\n**「t.invite」**\nこのBotの招待リンクを送ります。ご自由にお使い下さい。\n\n**「t.support」**\nこのBotのサポートサーバーの招待リンクを送ります。バグ報告・要望等あればこちらまでお願いします。')
        return
    if message.content == 't.release note':
        await message.channel.send('◆2020/07/16(0:55)リリース◆\n\n機能追加\n・なし\n\nバグフィックス\n・デフォルト絵文字、カスタム絵文字のIDが読み上げられていた不具合を修正。')
        return
    if message.content == 't.invite':
        await message.channel.send('このBotの招待リンクです。導入してもらえると喜びます。\n開発者:Alpaca#8032\nhttps://discord.com/api/oauth2/authorize?client_id=727508841368911943&permissions=3153472&scope=bot')
        return
    if message.content == 't.support':
        await message.channel.send('このBotのサポートサーバーです。バグ報告・要望等あればこちらにお願いします。お気軽にどうぞ。\nhttps://discord.gg/DbtZAcX')
        return
    if message.content.startswith('t.expand'):
        if message.content[9:11] == 'on':
            if message.guild.id in expand_off:
                expand_off.remove(message.guild.id)
                with open('expand.json', 'w', encoding='utf-8') as f:
                    json.dump(expand_off, f, ensure_ascii=False, indent=4)
                filepath = 'expand.json'
                title = 'expand.json'
                file = drive.CreateFile(
                    {'id': '1zX-mbDeN_Mlx-p_62WSE5zAgsqu_jFX5', 'title': title, 'mimeType': 'application/json'})
                file.SetContentFile(filepath)
                file.Upload()
                print('upload-complete')
                await message.channel.send('メッセージ展開をオンにしました。')
                return
            else:
                await message.channel.send('メッセージ展開は既にオンです。')
                return

        if message.content[9:12] == 'off':
            if message.guild.id not in expand_off:
                expand_off.append(message.guild.id)
                with open('expand.json', 'w', encoding='utf-8') as f:
                    json.dump(expand_off, f, ensure_ascii=False, indent=4)
                filepath = 'expand.json'
                title = 'expand.json'
                file = drive.CreateFile(
                    {'id': '1zX-mbDeN_Mlx-p_62WSE5zAgsqu_jFX5', 'title': title, 'mimeType': 'application/json'})
                file.SetContentFile(filepath)
                file.Upload()
                print('upload-complete')
                await message.channel.send('メッセージ展開をオフにしました。')
                return
            else:
                await message.channel.send('メッセージ展開は既にオフです。')
                return

    if message.content.startswith('t.con'):
        global voice_active
        if message.author.voice is None:
            await message.channel.send('VCに接続してからもう一度お試し下さい。')
            return
        if message.content.find('limit=')!= -1:
            m = re.search('limit=\d+', message.content)
            if m is None:
                await message.channel.send('「limit=」オプションが間違っています。「t.help」でヘルプを確認できます。')
                return
            limit_num = m.group()[6:]
            word_limit[message.guild.id] = limit_num
            limit_msg = '文字数制限：' + limit_num
        else:
            limit_msg =  '文字数制限：なし'
            
        # チャンネル
        if message.content.find('channel')!=-1:
            print('channel')
            detect = '(チャンネルに反応)'
            voice_active_ch.append(message.channel.id)
            if message.guild.id in voice_active_guild:
                voice_active_guild.remove(message.guild.id)
        # サーバー
        elif message.content.find('server')!=-1:
            print('guild')
            detect = '(サーバー全体に反応)'
            voice_active_guild.append(message.guild.id)
            if message.channel.id in voice_active_ch:
                voice_active_ch.remove(message.channel.id)
        # その他
        else:
            print('else-ch')
            detect = '(チャンネルに反応)'
            voice_active_ch.append(message.channel.id)
            if message.guild.id in voice_active_guild:
                voice_active_guild.remove(message.guild.id)

        await message.channel.send(message.author.voice.channel.name + 'に接続しました。 ' + detect + ' (' +limit_msg + ')')
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
        # アクティブ状態リセット
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
        # 文字数制限リセット
        if message.guild.id in word_limit:
        	del word_limit[message.guild.id]
        return

    if message.guild.id in voice_active_guild or message.channel.id in voice_active_ch:
        message.content = demoji.replace(message.content, '')
        message.content = re.sub(r'<:\w*:\d*>', '', message.content)
        if message.guild.id in word_limit:
        	limit = word_limit.get(message.guild.id)
        	msg_content = message.content[:int(limit)]
        else:
        	msg_content = message.content
        if msg_content.find('http') != -1:
            pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
            url_list = re.findall(pattern, msg_content)
            for item in url_list:
                msg_content = msg_content.remove(item)
        language = lang[str(message.guild.id)]
        str_url = "https://texttospeech.googleapis.com/v1/text:synthesize?key="
        str_headers = {'Content-Type': 'application/json; charset=utf-8'}
        url = str_url + str_api_key
        str_json_data = {
            'input': {
                'text': msg_content
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