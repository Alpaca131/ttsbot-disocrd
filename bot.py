import requests
import base64
import asyncio
import signal
import discord
import os
from dispander import dispand
import re
import json
import urllib.request
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import demoji
from googletrans import Translator
import time
import dill

client = discord.Client()
translator = Translator()
TOKEN = os.environ['DISCORD_BOT_TOKEN']
str_api_key = os.environ['GCP_API']
gauth = GoogleAuth()
gauth.LocalWebserverAuth()
drive = GoogleDrive(gauth)
loop = asyncio.get_event_loop()
file_name = ['voice_active', 'read_name', 'word_limit', 'speech_speed', 'lang', 'read_queue']
language_name = {'jp': ['日本語', 'ja-JP'], 'kr': ['韓国語', 'ko-KR'], 'ch': ['中国語', 'cmn-CN'],
                 'en': ['英語', 'en-US'], 'auto': ['自動検知', 'auto']}
message_dict = {'1': ['言語', '言語を入力して下さい。', 'lang'], '2': ['文字数制限', '文字数を入力して下さい。', 'word_limit'],
                '3': ['読み上げ速度', '0.25～4までの間で入力して下さい。', 'speech_speed'],
                '4': ['反応する対象', 'channel/serverのどちらかを入力して下さい。', 'target'],
                '5': ['名前読み上げ', 'on/offのどちらかを入力してください。', 'read_name'], '6': ['辞書登録', '特殊な読み方の単語を登録します\n単語を入力して下さい']}
server_dict = {}
server_data = {}
read_queue = {}
lang = {}
speech_speed = {}
word_limit = {}
read_name = {}
voice_active = {}
shutdown = False
SIGTERM = False
imported = []


def handler(signum, frame):
    global SIGTERM
    print('signal catch')
    with open('expand.json', 'w', encoding='utf-8') as f:
        json.dump(expand_off, f, ensure_ascii=False, indent=4)
    filepath = 'expand.json'
    title = 'expand.json'
    file = drive.CreateFile(
        {'id': '1zX-mbDeN_Mlx-p_62WSE5zAgsqu_jFX5', 'title': title, 'mimeType': 'application/json'})
    file.SetContentFile(filepath)
    file.Upload()
    print('upload-complete')
    SIGTERM = True


def multiple_replace(text, adict):
    """ 一度に複数のパターンを置換する関数
    - text中からディクショナリのキーに合致する文字列を探し、対応の値で置換して返す
    - キーでは、正規表現を置換前文字列とできる
    """

    rx = re.compile('|'.join(adict))

    def dedictkey(text):
        """ マッチした文字列の元であるkeyを返す
        """
        for key in adict.keys():
            if re.search(key, text):
                return key

    def one_xlat(match):
        return adict[dedictkey(match.group(0))]

    return rx.sub(one_xlat, text)


@client.event
async def on_ready():
    global expand_off, server_data, server_dict
    demoji.download_codes()
    await client.change_presence(activity=discord.Game(name="「t.help」でヘルプ", type=1))
    f = drive.CreateFile({'id': '1zX-mbDeN_Mlx-p_62WSE5zAgsqu_jFX5'})
    f.GetContentFile('expand.json')
    with open('expand.json') as f:
        expand_off = json.load(f)
    e = drive.CreateFile({'id': '15twVdWyUw7yJSD0BaGTpi-lRil5XmY6t'})
    e.GetContentFile('server_data.json')
    with open('server_data.json') as e:
        server_data = json.load(e)
    g = drive.CreateFile({'id': '1FgKvjrUdGG996d3bWkAlve_FjM5CqrOi'})
    g.GetContentFile('server_dict.json')
    with open('server_data.json') as g:
        server_dict = json.load(g)
    await client.get_channel(742064500160594050).send('ready')
    print('ready')
    if not discord.opus.is_loaded():
        # もし未ロードだったら
        discord.opus.load_opus("heroku-buildpack-libopus")


@client.event
async def on_message(message):
    global voice_active, lang, speech_speed, word_limit, read_name, voice_active, imported, shutdown
    if shutdown:
        return
    if message.channel.id == 742064500160594050:
        await restart_file(message=message)
    if message.author.bot:
        return
    if message.guild is None:
        await dm_command(message=message)
    if message.guild.id not in expand_off:
        await dispand(message)
    if message.content == 't.help':
        await help_message(ch=message.channel)
    if message.content == 't.release note':
        embed = discord.Embed(title="◆2020/08/23(04:28)リリース◆", color=discord.Colour.red())
        embed.add_field(name='機能追加',
                        value="・辞書機能を追加しました。", inline=False)
        embed.add_field(name='バグフィックス',
                        value="・なし", inline=False)
        await message.channel.send(embed=embed)
        return
    if message.content == 't.invite':
        await message.channel.send('このBotの招待リンクです。導入してもらえると喜びます。'
                                   '\n開発者:Alpaca#8032\nhttps://discord.com/api/oauth2/authorize?client_id'
                                   '=727508841368911943&permissions=3153472&scope=bot')
        return
    if message.content == 't.support':
        await message.channel.send('このBotのサポートサーバーです。バグ報告・要望等あればこちらにお願いします。お気軽にどうぞ。\nhttps://discord.gg/DbtZAcX')
        return
    if message.content == 't.save':
        await save_settings(message=message)
    if message.content.startswith('t.expand'):
        await message_expand(message=message)
    if message.content.startswith('t.con'):
        await connect(message=message)
    if message.content == 't.del':
        if str(message.guild.id) in server_data:
            embed = discord.Embed(title='削除中', color=discord.Colour.red())
            deleting_msg = await message.channel.send(embed=embed)
            del server_data[str(message.guild.id)]
            with open('server_data.json', 'w') as f:
                json.dump(server_data, f, indent=4)
            filepath = 'server_data.json'
            title = 'server_data.json'
            file = drive.CreateFile(
                {'id': '15twVdWyUw7yJSD0BaGTpi-lRil5XmY6t', 'title': title, 'mimeType': 'application/json'})
            file.SetContentFile(filepath)
            file.Upload()
            print('server_data upload-complete')
            embed = discord.Embed(title='削除完了')
            await deleting_msg.edit(embed=embed)
            return
        else:
            'サーバーのデフォルト設定はまだ保存されていません。'
    # 設定view
    if message.content == 't.view':
        if str(message.guild.id) in server_data:
            embed = discord.Embed(title='サーバーのデフォルト設定')
            for item in message_dict:
                if item == '6':
                    embed.add_field(name=message_dict.get(item)[0],
                                    value='`t.dict`でサーバー辞書を表示できます', inline=False)
                    continue
                name = message_dict.get(item)[0]
                val = server_data.get(str(message.guild.id)).get(message_dict.get(item)[2])
                if val == 'None':
                    val = '未設定(デフォルト)'
                embed.add_field(name=name, value=val, inline=False)
            await message.channel.send(embed=embed)
            return
        else:
            await message.channel.send('サーバーのデフォルト設定はまだ保存されていません。')
            return
    # 辞書view
    if message.content == 't.dict':
        if str(message.guild.id) in server_dict:
            embed = discord.Embed(title='サーバー辞書')
            for item in server_dict:
                embed.add_field(name='単語：' + item, value='読み方' + server_dict[str(message.guild.id)].get(item), inline=False)
            await message.channel.send(embed=embed)
            return
        else:
            await message.channel.send('辞書にはまだ何も登録されていません。')
            return
    # キュークリア
    if message.content == 't.reset':
        if message.guild.id not in read_queue or len(read_queue.get(message.guild.id)) == 0:
            await message.channel.send('キューは空です')
            return
        del read_queue[message.guild.id]
        await message.channel.send('キューをクリアしました')
    # 切断
    if message.content == 't.dc':
        if not import_check():
            return
        voich = message.guild.voice_client
        # アクティブ状態リセット
        try:
            await voich.disconnect()
        except AttributeError:
            await message.channel.send('現在Botはどのチャンネルにも接続していません。')
            return
        if message.guild.id in voice_active:
            del lang[message.guild.id]
            del voice_active[message.guild.id]
            del speech_speed[message.guild.id]
            del read_name[message.guild.id]
            del word_limit[message.guild.id]
            del read_queue[message.guild.id]
            return
    # 読み上げ
    if message.guild.id == voice_active.get(message.guild.id) \
            or message.channel.id == voice_active.get(message.guild.id):
        if not import_check():
            return
        message.content = url_remove(text=message.content)
        # 文字数制限
        limit = word_limit.get(message.guild.id)
        message.content = message.content[:int(limit)]
        # 言語判定
        language = lang.get(message.guild.id)
        if language == 'auto':
            detect_lang = translator.detect(message.content).lang
            try:
                if detect_lang == 'ja':
                    language = 'ja-JP'
                elif detect_lang == 'en':
                    language = 'en-US'
                elif detect_lang == 'ko':
                    language = 'ko-KR'
                elif detect_lang.find('CN'):
                    language = 'cmn-CN'
                else:
                    await message.channel.send('サポートされてない言語です。\nError:Unsupported language. (lang=' + detect_lang + ')')
                    return
            except NameError:
                language = 'ja-JP'
        # 読み上げ速度
        speed = float(speech_speed.get(message.guild.id))
        # 翻訳
        if message.content.startswith('t.'):
            message.content = translator.translate(message.content[5:], dest=message.content[2:4]).text
        # 辞書機能
        if str(message.guild.id) in server_dict:
            original_text = message.content
            trans_tone = server_dict[str(message.guild.id)]
            message.content = multiple_replace(original_text, trans_tone)
        # 名前読み上げ
        if read_name.get(message.guild.id) == 'on':
            message.content = message.author.name + ':' + message.content
        # 読み上げキュー＆読み上げ
        if message.guild.id not in read_queue:
            read_queue[message.guild.id] = []
        read_queue.get(message.guild.id).append(message.content)
        while len(read_queue[message.guild.id]) != 0:
            voich = message.guild.voice_client
            if voich.is_playing():
                await asyncio.sleep(0.3)
                continue
            content = read_queue.get(message.guild.id).pop(0)
            r = tts_request(text=content, language=language, speed=speed)
            if r.status_code == 200:
                parsed = json.loads(r.text)
                with open(str(message.guild.id) + '-data.mp3', 'wb') as outfile:
                    outfile.write(base64.b64decode(parsed['audioContent']))
                try:
                    voich.play(discord.FFmpegPCMAudio(str(message.guild.id) + '-data.mp3'), after=print('playing'))
                except AttributeError or discord.errors.ClientException:
                    await discord.VoiceChannel.connect(message.author.voice.channel)
                    voich.play(discord.FFmpegPCMAudio(str(message.guild.id) + '-data.mp3'), after=print('playing'))
                continue
            else:
                print('API error')
                continue


def url_remove(text):
    # demojiでUnicode絵文字を除去
    text = demoji.replace(text, '')
    # 正規表現でカスタム絵文字を除去
    text = re.sub(r'<:\w*:\d*>', '', text)
    # 正規表現でメンションを除去
    text = discord.utils.escape_markdown(text=text)
    text = text.replace('\*', '')
    text = text.replace('\_', '')
    text = text.replace('\~', '')
    text = text.replace('\|', '')
    text = text.replace('\`', '')
    text = text.replace('> ', '')
    text = discord.utils.escape_mentions(text=text)
    text = re.sub(r'<@​!\d+>', '', text)
    text = re.sub(r'<@​&\d+>', '', text)
    # 正規表現でチャンネルメンションを除去
    text = re.sub(r'<#\d+>', '', text)
    # URL除去
    if text.find('http') != -1:
        pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
        url_list = re.findall(pattern, text)
        for item in url_list:
            text = text.remove(item)
    return text


def tts_request(text, language, speed):
    str_url = "https://texttospeech.googleapis.com/v1/text:synthesize?key="
    str_headers = {'Content-Type': 'application/json; charset=utf-8'}
    url = str_url + str_api_key
    str_json_data = {
        'input': {
            'text': text
        },
        'voice': {
            'languageCode': language,
            'name': language + '-Wavenet-C',
            'ssmlGender': 'MALE'
        },
        'audioConfig': {
            'audioEncoding': 'MP3',
            "speakingRate": speed
        }
    }
    jd = json.dumps(str_json_data)
    # print(jd)
    print("begin request")

    s = requests.Session()
    r = requests.post(url, data=jd, headers=str_headers)
    print("status code : ", r.status_code)
    print("end request")
    return r


def import_check():
    if 'voice_active' in imported and 'read_name' in imported and 'word_limit' in imported and \
            'speech_speed' in imported and 'lang' in imported and 'read_queue' in imported:
        return True
    else:
        return False


async def help_message(ch):
    embed = discord.Embed(title="ヘルプ・コマンド一覧", description="以下がこのBotで使えるコマンド一覧です。", color=discord.Colour.blue())
    embed.add_field(name='t.con (例：t.con lang=en server limit=50 name=on speed=1.25)',
                    value='(オプション：言語、文字数制限、読み上げ速度、反応する対象、名前読み上げ)'
                          '\n__**言語(lang=)**__\n'
                          '・指定なし(もしくはjp)･･･日本語\n・en･･･英語\n・kr･･･韓国語\n・ch･･･中国語\n・auto･･･自動検知(※遅延が増加する場合があります。) '
                          '\n__**文字数制限(limit=数字)：**__\n・反応する文字数を制限できます。デフォルトは50です。'
                          '\n__**読み上げ速度(speed=数字)：**__\n・読み上げ速度を変更できます。デフォルトは1です。\n0.25～4の間で指定できます。'
                          '\n__**反応する対象：**__\n・指定なし(もしくはchannel)･･･コマンドのチャンネルに反応\n・server･･･サーバー全体に反応'
                          '\n__**名前読み上げ(name=on/off)：**__\nメッセージの前に送信者の名前を読み上げます。')
    embed.add_field(name='t.save',
                    value="サーバーごとのデフォルト設定を保存できます。", inline=False)
    embed.add_field(name='t.del',
                    value="サーバーごとのデフォルト設定を削除できます。", inline=False)
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
    await ch.send(embed=embed)
    return


async def dm_command(message):
    if message.author.id == 539910964724891719:
        if message.content == 'サーバー':
            await message.channel.send(str(len(client.guilds)))
            return
        if message.content == 'reset':
            imported.append('voice_active')
            imported.append('read_name')
            imported.append('word_limit')
            imported.append('speech_speed')
            imported.append('lang')
            await message.channel.send('リセットしました。')
            return
        if message.content == 'backup' or message.content == 'save':
            await send_file(ch=client.get_channel(742064500160594050))
            await message.channel.send('TTSデータバックアップ完了')
            with open('expand.json', 'w', encoding='utf-8') as f:
                json.dump(expand_off, f, ensure_ascii=False, indent=4)
            filepath = 'expand.json'
            title = 'expand.json'
            file = drive.CreateFile(
                {'id': '1zX-mbDeN_Mlx-p_62WSE5zAgsqu_jFX5', 'title': title, 'mimeType': 'application/json'})
            file.SetContentFile(filepath)
            file.Upload()
            await message.channel.send('expandアップロード完了')


async def restart_file(message):
    global voice_active, lang, speech_speed, word_limit, read_name, read_queue, voice_active, imported, shutdown
    if message.content == 'ready' and SIGTERM:
        await send_file(ch=message.channel)
        shutdown = True
        return
    elif message.content in file_name:
        print('file recieved')
        for attachment in message.attachments:
            imported.append(message.content)
            url = attachment.url
            save_name = message.content + ".dill"
            # ダウンロードを実行
            opener = urllib.request.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) '
                                                'Gecko/20100101 Firefox/47.0')]
            urllib.request.install_opener(opener)
            urllib.request.urlretrieve(url, save_name)
            if message.content == 'lang':
                lang = dill.load(open(save_name, 'rb'))
            elif message.content == 'speech_speed':
                speech_speed = dill.load(open(save_name, 'rb'))
            elif message.content == 'word_limit':
                word_limit = dill.load(open(save_name, 'rb'))
            elif message.content == 'read_name':
                read_name = dill.load(open(save_name, 'rb'))
            elif message.content == 'voice_active':
                voice_active = dill.load(open(save_name, 'rb'))
            elif message.content == 'read_queue':
                read_queue = dill.load(open(save_name, 'rb'))
            print('dict loaded')


async def message_expand(message):
    if message.content[9:11] == 'on':
        if message.guild.id in expand_off:
            expand_off.remove(message.guild.id)
            await message.channel.send('メッセージ展開をオンにしました。')
            return
        else:
            await message.channel.send('メッセージ展開は既にオンです。')
            return
    if message.content[9:12] == 'off':
        if message.guild.id not in expand_off:
            expand_off.append(message.guild.id)
            await message.channel.send('メッセージ展開をオフにしました。')
            return
        else:
            await message.channel.send('メッセージ展開は既にオフです。')
            return


async def send_file(ch):
    # lang
    dill.dump(lang, open('lang.dill', 'wb'))
    file = discord.File('lang.dill')
    # speech_speed
    dill.dump(speech_speed, open('speech_speed.dill', 'wb'))
    file2 = discord.File('speech_speed.dill')
    # word_limit
    dill.dump(word_limit, open('word_limit.dill', 'wb'))
    file3 = discord.File('word_limit.dill')
    # read_name
    dill.dump(read_name, open('read_name.dill', 'wb'))
    file4 = discord.File('read_name.dill')
    # voice_active
    dill.dump(voice_active, open('voice_active.dill', 'wb'))
    file5 = discord.File('voice_active.dill')
    # read_queue
    dill.dump(read_queue, open('read_queue.dill', 'wb'))
    file6 = discord.File('read_queue.dill')
    await ch.send('lang', file=file)
    await ch.send('speech_speed', file=file2)
    await ch.send('word_limit', file=file3)
    await ch.send('read_name', file=file4)
    await ch.send('read_queue', file=file6)
    await ch.send('voice_active', file=file5)
    return


async def connect(message):
    if message.author.voice is None:
        await message.channel.send('VCに接続してからもう一度お試し下さい。')
        return
    # 名前読み上げ
    if message.content.find('name=on') != -1:
        read_name[message.guild.id] = 'on'
        name_msg = '名前読み上げ：オン'
    elif message.content.find('name=off') != -1:
        read_name[message.guild.id] = 'off'
        name_msg = '名前読み上げ：オフ'
    else:
        if str(message.guild.id) in server_data:
            read_name_server_data = server_data.get(str(message.guild.id)).get('read_name')
            if read_name_server_data != 'None':
                read_name[message.guild.id] = read_name_server_data
                if read_name_server_data == 'on':
                    name_msg = '名前読み上げ：オン'
                else:
                    name_msg = '名前読み上げ：オフ'
            else:
                read_name[message.guild.id] = 'off'
                name_msg = '名前読み上げ：オフ　(デフォルト)'
        else:
            read_name[message.guild.id] = 'off'
            name_msg = '名前読み上げ：オフ　(デフォルト)'

    # 文字数制限
    if message.content.find('limit=') != -1:
        m = re.search('limit=\d+', message.content)
        if m is None:
            await message.channel.send('「limit=」オプションが間違っています。「t.help」でヘルプを確認できます。')
            return
        limit_num = m.group()[6:]
        word_limit[message.guild.id] = limit_num
        limit_msg = '文字数制限：' + limit_num
    else:
        if str(message.guild.id) in server_data:
            word_limit_server_data = server_data.get(str(message.guild.id)).get('word_limit')
            if word_limit_server_data != 'None':
                word_limit[message.guild.id] = str(word_limit_server_data)
                limit_msg = '文字数制限：' + str(word_limit_server_data)
            else:
                word_limit[message.guild.id] = 50
                limit_msg = '文字数制限：50　(デフォルト)'
        else:
            word_limit[message.guild.id] = 50
            limit_msg = '文字数制限：50　(デフォルト)'
    # 読み上げ速度
    if message.content.find('speed=') != -1:
        m = re.search('speed=\d+(?:.\d+)?', message.content)
        if m is None:
            await message.channel.send('「speed=」オプションが間違っています。「t.help」でヘルプを確認できます。')
            return
        speed_num = m.group()[6:]
        speech_speed[message.guild.id] = speed_num
        speed_msg = '読み上げ速度：' + speed_num
    else:
        if str(message.guild.id) in server_data:
            speech_speed_server_data = server_data.get(str(message.guild.id)).get('speech_speed')
            if speech_speed_server_data != 'None':
                speech_speed[message.guild.id] = str(speech_speed_server_data)
                speed_msg = '読み上げ速度：' + str(speech_speed_server_data)
            else:
                speech_speed[message.guild.id] = '1'
                speed_msg = '読み上げ速度：1　(デフォルト)'
        else:
            speech_speed[message.guild.id] = '1'
            speed_msg = '読み上げ速度：1　(デフォルト)'

    # チャンネルに反応
    if message.content.find('channel') != -1:
        print('channel')
        detect_msg = 'チャンネルに反応'
        voice_active[message.guild.id] = message.channel.id
    # サーバーに反応
    elif message.content.find('server') != -1:
        print('guild')
        detect_msg = 'サーバー全体に反応'
        voice_active[message.guild.id] = message.guild.id
    # その他(チャンネルに反応)
    else:
        if str(message.guild.id) in server_data:
            target_server_data = server_data.get(str(message.guild.id)).get('target')
            if target_server_data == 'server':
                print('guild')
                detect_msg = 'サーバー全体に反応'
                voice_active[message.guild.id] = message.guild.id
            elif target_server_data == 'channel':
                print('channel')
                detect_msg = 'チャンネルに反応'
                voice_active[message.guild.id] = message.channel.id
            else:
                print('channel')
                detect_msg = 'チャンネルに反応　(デフォルト)'
                voice_active[message.guild.id] = message.channel.id
        else:
            print('channel')
            detect_msg = 'チャンネルに反応　(デフォルト)'
            voice_active[message.guild.id] = message.channel.id
    # 言語
    if 'lang=' in message.content:
        lang_position = message.content.find('lang=')
        lang_msg = message.content[lang_position+5:lang_position+7]
        if lang_msg in language_name:
            lang_name = language_name.get(lang_msg)[0]
            language = language_name.get(lang_msg)[1]
            lang[message.guild.id] = language
        elif message.content[lang_position+5:lang_position+9] in language_name:
            lang_name = language_name.get(message.content[lang_position+5:lang_position+9])[0]
            language = language_name.get(message.content[lang_position+5:lang_position+9])[1]
            lang[message.guild.id] = language
        else:
            await message.channel.send('「lang=」オプションが間違っています。「t.help」でヘルプを確認できます。')
            return
    else:
        if str(message.guild.id) in server_data:
            lang_server_data = server_data.get(str(message.guild.id)).get('lang')
            if lang_server_data != 'None':
                lang_name = language_name.get(lang_server_data)[0]
                language = language_name.get(lang_server_data)[1]
                lang[message.guild.id] = language
            else:
                print('else-jp')
                lang_name = '日本語'
                language = 'ja-JP'
                lang[message.guild.id] = language
        else:
            print('else-jp')
            lang_name = '日本語'
            language = 'ja-JP'
            lang[message.guild.id] = language

    embed = discord.Embed(title=message.author.voice.channel.name + "に接続しました。",
                          description='言語：' + lang_name + '\n' + limit_msg + '\n' + detect_msg + '\n' + name_msg +
                                      '\n' + speed_msg,
                          color=0x00c707)
    await message.channel.send(embed=embed)
    try:
        await discord.VoiceChannel.connect(message.author.voice.channel)
    except Exception as e:
        print(str(e))
        return


async def save_settings(message):
    if str(message.guild.id) in server_data:
        onetime_server_data = server_data.get(str(message.guild.id))
    else:
        onetime_server_data = {'lang': 'None', 'word_limit': 'None', 'speech_speed': 'None', 'target': 'None',
                               'read_name': 'None'}
    if str(message.guild.id) in server_dict:
        onetime_server_dict = server_dict.get(str(message.guild.id))
    else:
        onetime_server_dict = {}
    embed = discord.Embed(title='サーバーごとに設定を保存できます',
                          description='選択肢の数字をチャットに入力して下さい。\n「quit」でキャンセルできます。', color=discord.Color.green())
    embed.add_field(name='1️⃣言語', value='・指定なし(もしくはjp)･･･日本語\n'
                                        '・en･･･英語\n・kr･･･韓国語\n'
                                        '・ch･･･中国語\n'
                                        '・auto･･･自動検知(※遅延が増加する場合があります。) ', inline=False)
    embed.add_field(name='2️⃣文字数制限',
                    value='・反応する文字数を制限できます。\n・デフォルトは50です。', inline=False)
    embed.add_field(name='3️⃣読み上げ速度',
                    value='・読み上げ速度を変更できます。デフォルトは1です。\n・0.25～4の間で指定できます。', inline=False)
    embed.add_field(name='4️⃣反応する対象(channel/server)',
                    value='・指定なし(もしくはchannel)･･･コマンドのチャンネルに反応\n・server･･･サーバー全体に反応', inline=False)
    embed.add_field(name='5️⃣名前読み上げ(on/off)',
                    value='・メッセージの前に送信者の名前を読み上げます。', inline=False)
    embed.add_field(name='~~6️⃣辞書登録~~(実装中。まだ使えません。)',
                    value='・特殊な読み方の単語を辞書に登録します。', inline=False)
    await message.channel.send(embed=embed)
    embed = discord.Embed(title='設定ウィザード',
                          description='選択肢の番号を半角数字で入力して下さい。',
                          color=discord.Color.red())
    wizzard = await message.channel.send(embed=embed)
    guide_msg = '\n`追加で設定するには、選択肢の数字を入力します。`\n`終了し保存するには、「save」と入力します。`\n`キャンセルするには「quit」と入力します。`'
    save = False
    while not save:
        def check_bot(m):
            if not m.author.bot:
                if m.channel == message.channel:
                    return True
            return False

        answer_msg = await client.wait_for('message', check=check_bot)
        if answer_msg.content == 'save':
            save = True
            embed = discord.Embed(title='保存中...',
                                  description='保存中...',
                                  color=discord.Color.red())
            await wizzard.edit(embed=embed)
            server_data[str(message.guild.id)] = onetime_server_data
            with open('server_data.json', 'w') as f:
                json.dump(server_data, f, indent=4)
            filepath = 'server_data.json'
            title = 'server_data.json'
            file = drive.CreateFile(
                {'id': '15twVdWyUw7yJSD0BaGTpi-lRil5XmY6t', 'title': title, 'mimeType': 'application/json'})
            file.SetContentFile(filepath)
            file.Upload()
            print('server_data upload-complete')
            if str(message.guild.id) in server_dict:
                del server_dict[str(message.guild.id)]
            server_dict[str(message.guild.id)] = onetime_server_dict
            with open('server_dict.json', 'w') as f:
                json.dump(server_dict, f, indent=4)
            filepath = 'server_dict.json'
            title = 'server_dict.json'
            file = drive.CreateFile(
                {'id': '1FgKvjrUdGG996d3bWkAlve_FjM5CqrOi', 'title': title, 'mimeType': 'application/json'})
            file.SetContentFile(filepath)
            file.Upload()
            print('server_dict upload-complete')
            embed = discord.Embed(title='保存完了',
                                  description='保存が完了しました。',
                                  color=discord.Color.red())
            await wizzard.edit(embed=embed)
            return
        elif answer_msg.content == 'quit':
            save = True
            embed = discord.Embed(title='終了',
                                  description='キャンセルしました。',
                                  color=discord.Color.red())
            await wizzard.edit(embed=embed)
            return
        elif answer_msg.content not in message_dict:
            embed = discord.Embed(title='エラー：メッセージが正しくありません',
                                  description='指定のメッセージ以外が送られたため、操作をキャンセルしました',
                                  color=discord.Color.red())
            await wizzard.edit(embed=embed)
            return
        embed = discord.Embed(title=message_dict.get(answer_msg.content)[0],
                              description=message_dict.get(answer_msg.content)[1],
                              color=discord.Color.red())
        await wizzard.edit(embed=embed)
        # 言語オプション
        if answer_msg.content == '1':
            lang_answer = await client.wait_for('message', check=check_bot)
            if lang_answer.content in language_name:
                lang_name = language_name.get(lang_answer.content)[0]
                onetime_server_data['lang'] = lang_answer.content
                embed = discord.Embed(title='デフォルトの言語を設定しました',
                                      description='言語：' + lang_name + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue
            else:
                embed = discord.Embed(title='エラー：サポートしていない言語を指定しています',
                                      description='autoオプションをお試し下さい。もしかしたら検知できるかもしれません。' + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue

        elif answer_msg.content == '2':
            word_limit_answer = await client.wait_for('message', check=check_bot)
            if not str.isdigit(word_limit_answer.content):
                embed = discord.Embed(title='エラー：数字以外が入力されました',
                                      description='半角数字を入力して下さい。' + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue
            onetime_server_data['word_limit'] = int(word_limit_answer.content)
            embed = discord.Embed(title='デフォルトの文字数制限を設定しました',
                                  description='文字数制限：' + word_limit_answer.content + guide_msg,
                                  color=discord.Color.red())
            await wizzard.edit(embed=embed)
            continue

        elif answer_msg.content == '3':
            speech_speed_answer = await client.wait_for('message', check=check_bot)
            try:
                onetime_server_data['speech_speed'] = float(speech_speed_answer.content)
                embed = discord.Embed(title='デフォルトの読み上げ速度を設定しました',
                                      description='読み上げ速度：' + speech_speed_answer.content + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue
            except ValueError:
                embed = discord.Embed(title='エラー：数字以外が入力されました',
                                      description='半角数字を入力して下さい。' + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue

        elif answer_msg.content == '4':
            target_answer = await client.wait_for('message', check=check_bot)
            if target_answer.content == 'channel' or target_answer.content == 'server':
                onetime_server_data['target'] = target_answer.content
                embed = discord.Embed(title='デフォルトの反応する対象を設定しました',
                                      description='反応する対象：' + target_answer.content
                                                  + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue
            else:
                embed = discord.Embed(title='エラー：channel/server以外が入力されました',
                                      description='channel/serverのどちらかを入力して下さい。' + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue

        elif answer_msg.content == '5':
            read_name_answer = await client.wait_for('message', check=check_bot)
            if read_name_answer.content == 'on' or read_name_answer.content == 'off':
                onetime_server_data['read_name'] = read_name_answer.content
                embed = discord.Embed(title='デフォルトの名前読み上げを設定しました',
                                      description='名前読み上げ：' + read_name_answer.content
                                                  + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue
            else:
                embed = discord.Embed(title='エラー：on/off以外が入力されました',
                                      description='on/offのどちらかを入力して下さい。' + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue
        elif answer_msg.content == '6':
            dict_word_answer = await client.wait_for('message', check=check_bot)
            embed = discord.Embed(title='読み方を入力して下さい',
                                  description='単語：' + dict_word_answer.content,
                                  color=discord.Color.red())
            await wizzard.edit(embed=embed)
            dict_read_answer = await client.wait_for('message', check=check_bot)
            p = re.compile('[\u3041-\u309F]+')
            if not p.fullmatch(dict_read_answer.content):
                embed = discord.Embed(title='エラー：ひらがな以外が入力されました',
                                      description='ひらがなで入力して下さい。' + guide_msg,
                                      color=discord.Color.red())
                await wizzard.edit(embed=embed)
                continue
            embed = discord.Embed(title='辞書を設定しました',
                                  description='**※注意 まだ保存されていません**\nもう1つ設定する場合は、6を入力して下さい' + guide_msg,
                                  color=discord.Color.red())
            embed.add_field(name='単語', value=dict_word_answer.content, inline=False)
            embed.add_field(name='読み方', value=dict_read_answer.content, inline=False)
            await wizzard.edit(embed=embed)
            onetime_server_dict[dict_word_answer.content] = dict_read_answer.content
            continue
    return


signal.signal(signal.SIGTERM, handler)
loop.run_until_complete(client.start(TOKEN))
