import requests
import os
import random
from openai import OpenAI
#import sounddevice as sd
#import soundfile as sf
import gspread
from pydub import AudioSegment
from pydub.playback import play

def get_sheet():
    """ 
    スプレッドシートを取得する関数 
    
    """
    # 認証してGoogleスプレッドシートにアクセス
    gc = gspread.service_account(filename="./.config/airadio.json")
    # スプレッドシートを開く (スプレッドシートのURLの最後にあるIDを使用)
    sh = gc.open_by_key(os.getenv("SPREADSHEET_URL"))
    #シートを取得
    ws = sh.worksheet("data")
    return ws

def make_ngwords_list():
    """ 
    NGリストを作成 
    
    """
    ng_words = ['事故','死亡','骨折','重傷','殺害','傷害','暴力','被害者','放送事故',\
            'ポルノ','アダルト','セックス','バイブレーター','マスターベーション','オナニー','スケベ','羞恥','セクロス',\
            'エッチ','SEX','風俗','童貞','ペニス','巨乳','ロリ','触手','羞恥','ノーブラ',\
            '大麻','麻薬',\
            '基地外','糞','死ね','殺す','しね','ころす',\
            'shit','piss','fuck','cunt','cocksucker','motherfucker','tits',\
            'R18','R-18','例のアレ','真夏の夜の淫夢','アヘ顔','亀頭','へんたい','ヘンタイ','変態','パンチラ',\
            '♂','アッー','アナル','アヘ顔','イマラ','淫','運営のお気に入り','エッチ','MKT','おっぱい','オッパイ','オナシャス','ガチムチ',\
            '姦','元祖羞恥心','亀頭','KMR','糞','クルルァ','グロ','ゲイ','ケツ','殺','シコ','自分を売る',\
            '18禁','春画','処女','ショタ','パイパン','フェラ','ふたなり','ペニス','へんたい','ヘンタイ','変態','ホモ',\
            'マラ','まんこ','マンコ','野獣','幼女','ょぅ','レイプ','レズ','ろり','ロリ','セックス','せっくす',\
            'レスリングシリーズ','来いよアグネス','紳士','運営仕事しろ','例のプール',\
        ]
    return ng_words

def check_ngwords(words_list, ng_words):
    """
    リストからNGリストに載ってる単語を取り除く。

    """
    filtered_array = [
    row for row in words_list if not any(
        any(ng_word in item for item in row) for ng_word in ng_words
    )
]
    return filtered_array

def pick_up_mail(ws,pick_up_num,words_list):
    """ 
    リストからランダムにpick_up_um個要素を抽出し、
    何を抽出したかスプレッドシートに記録する。
    
    """
    not_used_list=[x for x in words_list if str(x[4])=="0"]

    if len(not_used_list) >= pick_up_num:
        choices = random.sample(not_used_list,pick_up_num)
    else:
        return []

    #スプレッドシート更新
    for c in choices:
        row_num = int(c[0])+1
        ws.update_acell(f'E{row_num}',"1")

    return choices

def get_reply(client,content):
    """
    contentの中身をChatGPTに質問する。

    """
    res= client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role":"user",
            "content":(content)
        }]
    )
    reply = res.choices[0].message.content
    return reply

def input_to_male(content):
    """
    田中に投げかける質問文を生成する。

    """
    content = str(content)
    text = "あなたは田中という男の芸人だ。\
        友達の中田と、簡単な会話をしている。\
        次の中田の言葉に対して、文脈に即した上で、短文でできる限り馬鹿馬鹿しい返事をして。また冒頭に挨拶をする必要はありません。\n"
    return text + content

def input_to_female(content):
    """
    中田に投げかける質問文を生成する。
    
    """
    content = str(content)
    text = "あなたは中村という、常に冷静な女性だ。\
        友達の田村と、簡単な会話をしています。\
        次の田村の言葉に対して、文脈に即した上で、短文でできる限り現実的な返事をして。また冒頭に挨拶をする必要はありません。\n"
    return text + content

def man_talks(client,content):
    """
    田中に質問文を投げかけて、回答を生成する。
    
    """
    txt = input_to_male(content)
    reply = get_reply(client,txt)
    return reply

def female_talks(client,content):
    """
    中田に質問文を投げかけて、回答を生成する。
    
    """
    txt = input_to_female(content)
    reply = get_reply(client,txt)
    return reply


def talk_with_each_other(client,first_content,repeat_time=2):
    """
    田中と中田の会話のやりとりをrepeat_time分、生成する。
    
    """
    conv_list = []
    content = first_content
    i = 0
    while i < repeat_time:
        content = man_talks(client,content)
        conv_list.append(content)
        content = female_talks(client,content)
        conv_list.append(content)
        i += 1
    return conv_list

def is_charactor_num(num):
    """
    voicevoxに渡すキャラクター番号を、入力に応じて返す。
    """
    if num%2: #もし2で割り切れるなら、女性の声を当てる。
        return 9
    else: #もし2で割り切れないなら、男性の声を当てる。
        return 39



    
def get_audio_filepath(reply, charactor_num):
    """
    textをvoicevoxに読み上げてもらう。音声ファイルをwavで保存。
    
    """
    params = {"text":reply, "speaker":charactor_num}
    res = requests.post(
        f'http://localhost:50021/audio_query',
        params=params
    )
    res = requests.post(
        f'http://localhost:50021/synthesis',
        params=params,
        json = res.json()
    )
    voice = res.content
    file_path = f'audio/airadio-voice.wav'
    with open(file_path, "wb") as f:
        f.write(voice)
    return file_path

    #音声ファイルを再生
    #data,fs = sf.read(file_path)
    #sd.play(data,fs)
    #sd.wait()

def get_audio_file(file_path):
    """
    wavファイルを呼び出して、AudioSegmentに変換。
    
    """
    #音声ファイルをAudioSegmentで出力
    audio_file = AudioSegment.from_file(file_path)
    return audio_file

def get_audio_reply(reply, charactor_num):
    """
    voicevoxに読み上げてもらう音声をAudioSegmentに変換。
    
    """
    filepath = get_audio_filepath(reply, charactor_num)
    audio_reply = get_audio_file(filepath)
    return audio_reply

def make_them_speak(client,conv_list):
    """
    二人の会話のやりとりを交互に読み上げてもらう。
    
    """
    combined_audio_file = AudioSegment.empty()
    for i, conv in enumerate(conv_list):
        combined_audio_file += get_audio_reply(conv,is_charactor_num(i))
    return combined_audio_file

def get_mail_content(content_list):   
    """
    メールの内容を取得する。
    
    """
    radio_names = list(map(lambda x:x[5], content_list))
    for i in range(len(radio_names)):
        if radio_names[i].strip(" ") == "":
            radio_names[i] = "なし"
        else:
            radio_names[i] += "さん"
    odais = list(map(lambda x:x[6], content_list))
    return radio_names,odais
    
def oogiri(client,ws,oogiri_list):
    """
    大喜利のコーナーの文章を生成する。
    
    """
    pick_up_list = pick_up_mail(ws,2,oogiri_list)

    if len(pick_up_list) < 2:
        return []

    radio_names, odais = get_mail_content(pick_up_list)
    answers = []
    for odai in odais:
        answer = get_reply(client,f'あなたは芸人です。次のお題に対して大喜利してください。\n{odai}')
        answers.append(answer) 

    contents1 = ["大喜利ー！","えーと、このコーナーは、リスナーから募集したお題で大喜利をしていくコーナーです。",\
                "今週のお題はこちら！",\
                f'ラジオネーム{radio_names[0]}からいただきました。{odais[0]}', f'{answers[0]}']
    reply10 = female_talks(client,answer[0])
    reply11 = talk_with_each_other(client,reply10,repeat_time=2)
    contents2 = ["",f'えー続いて、ラジオネーム{radio_names[1]}からいただきました。{odais[1]}',\
                f'{answers[1]}']
    reply20 = female_talks(client,answer[1])
    reply21 = talk_with_each_other(client,reply20,repeat_time=2)

    return contents1 + [reply10] + reply11 + contents2 + [reply20] + reply21 


def iwasetaikoto(client,ws,iwasetaikoto_list):
    """
    AIに言わせたいことのコーナーの文章を生成する。
    
    """
    pick_up_list = pick_up_mail(ws,2,iwasetaikoto_list)

    if len(pick_up_list) < 2:
        return []
    
    radio_names, odais = get_mail_content(pick_up_list)

    contents1 = ["AIに言わせたいこと！","えーと、このコーナーは、我々AIパーソナリティーに読み上げてほしい文章を募集するコーナーです。",\
                "今週のお題はこちら！",\
                f'ラジオネーム{radio_names[0]}からいただきました。', f'{odais[0]}']
    reply10 = female_talks(client,odais[0])
    reply11 = talk_with_each_other(client,reply10,repeat_time=2)
    contents2 = ["",f'えーと、続いて、ラジオネーム{radio_names[1]}からいただきました。',\
                f'{odais[1]}']
    reply20 = female_talks(client,odais[1])
    reply21 = talk_with_each_other(client,reply20,repeat_time=1)

    return contents1 + [reply10] + reply11 + contents2 + [reply20] + reply21


def hutsuota(ws,hutsuota_list):
    """
    ふつおたのコーナーの文章を生成する。
    
    """
    pick_up_list = pick_up_mail(ws,1,hutsuota_list)
    if len(pick_up_list) == 0:
        return ""
    radio_name, odai = get_mail_content(pick_up_list)
    content = f'ふつおたが届いています。ラジオネーム、{radio_name[0]}からいただきました。\n{odai[0]}'
    return content

def get_title(client,content):
    """
    タイトルと要約を取得。
    
    """
    text = f'次の文章を要約して、人を惹きつけるタイトルをつけてください。\n{content}'
    return get_reply(client,text)

def main():
    print("処理を開始します。")
    client = OpenAI()
    ws = get_sheet()
    mail_data = ws.get_all_values()
    ng_words = make_ngwords_list()

    #ふつおたがあれば最初に読む。最初のトークの内容を生成。
    hutsuota_list=[x for x in mail_data if "ふつおた" in x[2]]
    hutsuota_list = check_ngwords(hutsuota_list, ng_words)
    first_content = ""

    if len(hutsuota_list) != 0:
        first_content = hutsuota(ws,hutsuota_list)

    if first_content == "":
        topic_list = ["何か面白い話してよ。","最近どう？",
                      "最近見た夢あれば教えて。","最近ハマってるものある？","最近どこか行った？",
                      "最近何か食べた？","最近欲しいものある？"]
        first_content = random.sample(topic_list,1)
        
    print("ふつおたの処理完了")

    #大喜利コーナー
    oogiri_list=[x for x in mail_data if "大喜利" in x[2]]
    oogiri_list = check_ngwords(oogiri_list,ng_words)
    oogiri_conv = []
    if len(oogiri_list) >= 2: #大喜利のメールが二件以上あれば大喜利のコーナー実施。
        oogiri_conv = oogiri(client,ws,oogiri_list)
    print("大喜利の処理完了")

    #AIに言わせたいことのコーナー
    iwasetaikoto_list=[x for x in mail_data if ("言わせたい" in x[2])or("いわせたい" in x[2])]
    iwasetaikoto_list = check_ngwords(iwasetaikoto_list, ng_words)
    iwasetaikoto_conv = []
    if len(iwasetaikoto_list) >= 2: #AIに言わせたいことのメールが二件以上あれば大喜利のコーナー実施。
        iwasetaikoto_conv = iwasetaikoto(client,ws,iwasetaikoto_list)
    print("言わせたいことの処理完了")

    #オープニングのコーナーを生成。
    opening = ["こんにちは！AIの田中です。","こんにちはAIの中田です。",\
                "この番組はAIパーソナリティの田中と中田でお送りいたします。",\
                "内容はすべてリスナーの皆様とAIによって作られています。",\
                "よろしくお願いします。オープニング行きます、AIラジオ"]
    
    #エンディングのコーナーを生成。
    ending  =  ["AIラジオ、そろそろお別れのお時間です。","大喜利のお題やAIに言わせたいこと、ふつおたのメールお待ちしております。",\
               "件名にコーナー名を書いて送ってください。","宛先はTANAKATA、ドット、AIRADIO、アット、GMAIL、ドット、COM",
               "たなかた、ドット、AIラジオアットジーメールコムとお覚えください。","感想は、ハッシュタグ田中と中田のAIラジオをつけてポストしてください。"\
               "お願いしますー。","以上、ここまでのお相手は中田と","田中でした！今週も聞いてくれてありがとう！","来週もお楽しみに！","さよならー！"]
    
    #フリートーク（ふつおた）のコーナーを生成。
    conv_list = talk_with_each_other(client,first_content,repeat_time=6) 
    #conv_list = ['「うん、ウサギの耳を持つスパゲッティマシーンが欲しいんだ！」', '「それはユニークなアイデアね。どんな用途を考えているの？」', '「うん、カメラの代わりにスイカを使って、スイカの中から風景を撮ろうと思ってるんだ！」', '「面白いアイデアね、その発想でどんな風景が撮れるか楽しみ。」']
    print("フリートークの内容生成完了")

    #要約文・タイトルを生成。
    subtitle = opening + [first_content] + conv_list + oogiri_conv + iwasetaikoto_conv + ending 
    title = get_title(client,subtitle)
    text = title + "\n-----以下本文-----\n" + str(subtitle)
    print("----------------------")
    print(text)
    print("----------------------")
    print("全テキストの生成完了")

    #BGMの収録
    audio1 = get_audio_file("airadio-bgm.mp3").fade_out(1000)
    audio2 = get_audio_file("airadio-corner-bgm.mp3").fade_out(1000) - 10
    print("BGMの処理完了")


    #オープニングの収録
    opening_audio = make_them_speak(client,opening) + audio1
    print("オープニングの収録終了")

    #フリートークの収録
    free_talk_audio1 = get_audio_reply(first_content, 9)
    free_talk_audio2 = make_them_speak(client,conv_list)
    free_talk_audio = free_talk_audio1 + free_talk_audio2
    play(free_talk_audio)
    print("フリートークの収録終了")

    #大喜利の収録
    if len(oogiri_conv) >= 2:
        oogiri_audio = audio2 + make_them_speak(client,oogiri_conv).fade_out(1000)
    else:
        oogiri_audio = AudioSegment.empty()
    print("大喜利の収録終了")

    #我々に言わせたいことの収録
    if len(iwasetaikoto_conv) >= 2:
        iwasetaikoto_audio = audio2 + make_them_speak(client,iwasetaikoto_conv).fade_out(1000)
    else:
        iwasetaikoto_audio = AudioSegment.empty()
    print("言わせたいことの収録終了")

    #エンディングの収録
    ending_audio = audio1 + make_them_speak(client,ending)
    print("エンディングの収録終了")

    #音声ファイル処理
    body = opening_audio + free_talk_audio + oogiri_audio + iwasetaikoto_audio + ending_audio
    play(body)
    body.export("output.wav", format="wav")

    #テキストファイルの処理
    with open("cointent.txt", "wb") as f:
        f.write(text.encode("utf-8"))
    print("全処理の完了。output.wav, content.txtを確認してください。")
   
if __name__=="__main__":
    main()