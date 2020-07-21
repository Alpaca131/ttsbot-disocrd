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
from googletrans import Translator

client = discord.Client()
translator = Translator()
TOKEN = os.environ['DISCORD_BOT_TOKEN']
str_api_key = os.environ['GCP_API']
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
lang = {}
spk_rate_dic = {}
voice_active = {}
word_limit = {}
name_speech = {}


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
    global spk_rate_dic, expand_off
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
        embed = discord.Embed(title="ヘルプ・コマンド一覧", description="以下がこのBotで使えるコマンド一覧です。", color=discord.Colour.blue())
        embed.add_field(name='t.con (例：t.con lang=en server limit=50)', value='(オプション：言語、文字数制限、反応する対象、名前読み上げ)'
                                                                              '\n__**言語(lang=)**__\n・指定なし(もしくはjp)･･･日本語\n・en･･･英語\n・kr･･･韓国語\n・ch･･･中国語\n・auto･･･自動検知(※遅延が増加する場合があります。)'
                                                                              '\n__**文字数制限(limit=文字数)：**__\n・反応する文字数を制限できます。'
                                                                              '\n__**反応する対象：**__\n・指定なし(もしくはchannel)･･･コマンドのチャンネルに反応\n・server･･･サーバー全体に反応'
                                                                              '\n__**名前読み上げ(name=on/off)：**__\nメッセージの前に送信者の名前を読み上げます。')
        embed.add_field(name='t.<lang>(翻訳して読み上げ)',
                        value="指定の言語に翻訳してから読み上げます。\n(※遅延が増加する場合があります。)", inline=False)
        embed.add_field(name='t.dc',
                        value="BotをVCから切断します。", inline=False)
        embed.add_field(name='t.expand',
                        value="(オプション：on/off)\nリンク展開機能のオンオフを切り替えます。", inline=False)
        embed.add_field(name='t.release note',
                        value="このBotの最新のアップデート内容を確認できます。", inline=False)
        embed.add_field(name='t.invite',
                        value="このBotの招待リンクを送ります。ご自由にお使い下さい。", inline=False)
        embed.add_field(name='t.support',
                        value="このBotのサポートサーバーの招待リンクを送ります。\nバグ報告・ご要望等あればこちらまでお願いします。", inline=False)
        await message.channel.send(embed=embed)
        return
    if message.content == 't.help en':
        await message.channel.send('Wirting now...\n・ω・')
    if message.content == 't.release note':
        embed = discord.Embed(title="◆2020/07/21(12:43)リリース◆", color=discord.Colour.red())
        embed.add_field(name='機能追加',
                        value="・翻訳機能を追加しました。ヘルプで使用方法を確認できます。\n・送信者の名前を読み上げる機能を追加しました。ヘルプで使用方法を確認できます。", inline=False)
        embed.add_field(name='バグフィックス',
                        value="・メンションのIDが読み上げられる問題を修正しました。", inline=False)
        await message.channel.send(embed=embed)
        return
    if message.content == 't.release note en':
        embed = discord.Embed(title="◆2020/07/21(12:43))リリース◆", color=discord.Colour.red())
        embed.add_field(name='Added function',
                        value="・Added translate function.", inline=False)
        embed.add_field(name='Bug fix',
                        value="・Fixed the problem that bot reads mention by ID.", inline=False)
        await message.channel.send(embed=embed)
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
        global voice_active, name
        if message.author.voice is None:
            await message.channel.send('VCに接続してからもう一度お試し下さい。')
            return
        # 名前読み上げ
        if message.content.find('name=on') != -1:
            name_speech[message.guild.id] = 'on'
            name_msg = '名前読み上げ：オン'
        elif message.content.find('name=off') != -1:
            name_speech[message.guild.id] = 'off'
            name_msg = '名前読み上げ：オフ'
        else:
            name_speech[message.guild.id] = 'off'
            name_msg = '名前読み上げ：オフ'

        # 文字数制限
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
        # チャンネルに反応
        if message.content.find('channel')!= -1:
            print('channel')
            detect = ' (チャンネルに反応)'
            voice_active[message.guild.id] = message.channel.id
        # サーバーに反応
        elif message.content.find('server')!= -1:
            print('guild')
            detect_msg = ' サーバー全体に反応'
            voice_active[message.guild.id] = message.guild.id
        # その他(チャンネルに反応)
        else:
            print('else-ch')
            detect_msg = ' チャンネルに反応'
            voice_active[message.guild.id] = message.channel.id
        # 言語
        if message.content.find('lang=jp')!= -1:
            print('JP')
            lang_msg = '日本語'
            language = 'ja-JP'
            lang[message.guild.id] = language
        elif message.content.find('lang=kr')!= -1:
            print('KR')
            lang_msg = '韓国語'
            language = 'ko-KR'
            lang[message.guild.id] = language
        elif message.content.find('lang=ch')!= -1:
            print('CH')
            lang_msg = '中国語'
            language = 'cmn-CN'
            lang[message.guild.id] = language
        elif message.content.find('lang=en')!= -1:
            print('EN')
            lang_msg = '英語'
            language = 'en-US'
            lang[message.guild.id] = language
        elif message.content.find('lang=auto')!= -1:
            print('auto')
            lang_msg = '自動検知'
            language = 'auto'
            lang[message.guild.id] = language
        else:
            print('else-JP')
            lang_msg = '日本語'
            language = 'ja-JP'
            lang[message.guild.id] = language

        embed = discord.Embed(title= message.author.voice.channel.name + "に接続しました。", description='言語：'+ lang_msg +'\n' + limit_msg + '\n' + detect_msg + '\n' + name_msg, color=0x00c707)
        await message.channel.send(embed=embed)
        await discord.VoiceChannel.connect(message.author.voice.channel)
        return


    # 切断
    if message.content == 't.dc':
        voich = message.guild.voice_client
        # アクティブ状態リセット
        if message.guild.id in voice_active:
            del lang[message.guild.id]
            del voice_active[message.guild.id]
            if message.guild.id in word_limit:
                del word_limit[message.guild.id]
            await voich.disconnect()
            return
        else:
            await message.channel.send('現在Botはどのチャンネルにも参加していません。')
            return

    if message.guild.id == voice_active.get(message.guild.id) or message.channel.id == voice_active.get(message.guild.id):
        # demojiでUnicode絵文字を除去
        message.content = demoji.replace(message.content, '')
        # 正規表現でカスタム絵文字を除去
        message.content = re.sub(r'<:\w*:\d*>', '', message.content)
        # 正規表現でメンションを除去
        message.content = re.sub(r'<@\d+>', '', message.content)
        if message.guild.id in word_limit:
        	limit = word_limit.get(message.guild.id)
        	msg_content = message.content[:int(limit)]
        else:
        	msg_content = message.content
        language = lang.get(message.guild.id)
        if language == 'auto':
            detect_lang = translator.detect(message.content).lang
            if detect_lang == 'ja':
                language = 'ja-JP'
            elif detect_lang == 'en':
                language = 'en-US'
            elif detect_lang == 'ko':
                language = 'ko-KR'
            elif detect_lang.find('CN'):
                language = 'cmn-CN'
            else:
                await message.channel.send('サポートされてない言語です。\nError:Unsopported language. (lang=' + detect_lang + ')')
                return
        # URL除去
        if msg_content.find('http') != -1:
            pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
            url_list = re.findall(pattern, msg_content)
            for item in url_list:
                msg_content = msg_content.remove(item)
        # 翻訳
        if msg_content.startswith('t.'):
            msg_content = translator.translate(msg_content[5:], dest=message.content[2:4]).text
        # 名前読み上げ
        if name_speech.get(message.guild.id) == 'on':
            if language == 'ja-JP':
                msg_content = message.author.name + '：' + msg_content
            else:
                msg_content = message.author.name + ':' + msg_content
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