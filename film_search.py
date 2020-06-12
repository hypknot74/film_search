import sys
import requests
import bs4
from slacker import Slacker
import time
import os
import pdfkit
#from selenium import webdriver
#from selenium.webdriver.chrome.options import Options

argv = sys.argv
google_search_url = "https://www.google.co.jp/search"

# slackトークンには使用するbotのトークンを入れる
slack_token = "slackトークン"
channel = "film_search"

def get_film_name(argv):
    argv.pop(0)
    film_name = ' '.join(argv)
    japanese_title = film_name
    original_title = None
    return japanese_title, original_title

def get_html(japanese_title, original_title ,review_site_name):
    if review_site_name == "filmarks":
        judge_url = "filmarks.com/movies/"
    else:
        judge_url = "imdb.com/title/"
    # 原題があれば原題で検索
    if original_title != None:
        film_name = original_title
    else:
        film_name = japanese_title

    # google検索結果のhtml取得
    try:
        req = requests.get(google_search_url, params={"q": film_name + " " + review_site_name})
        time.sleep(2)
    except:
        condition = "error"
        return condition, None
    search_result_html = req.text
    #print(req.url)

    # google検索結果HTMLをパースする
    soup = bs4.BeautifulSoup(search_result_html, "html.parser")

    # 検索結果のタイトルとurlを取得
    title_url = soup.select(".kCrYT")
    # 検索結果トップのurlを取得
    url = title_url[0].a.get("href").split("&sa=U&")[0].replace("/url?q=", "")

    # レビューサイトのhtml取得
    # 対象のレビューサイトでない場合
    if judge_url not in str(url):
        information = "no"
        html_text = None
        url = None
    # 対象のレビューサイトの場合
    else:
        information = "yes"
        try:
            req = requests.get(url)
            time.sleep(1)
            html_text = req.text
        except Exception as e:
            print(str(e))
            condition = "error"
            return condition, None, None, None, information

    condition = "success"
    return condition, html_text, information, url, film_name

def get_Filmarks_information_and_pdf(html_text, film_name):
    if html_text == None:
        pass
    else:
        # filmarksのHTMLをパースする
        soup = bs4.BeautifulSoup(html_text, "lxml")
        # 邦題
        japanese_title = soup.find(class_="p-content-detail__title").text
        # (~年制作の映画)ってのがくっついてたら消す
        if "年製作の映画" in japanese_title:
            japanese_title = japanese_title[:-12]
        # 原題
        if len(soup.find(class_="p-content-detail__original").text) == 0:
            original_title = None
        else:
            original_title = soup.find(class_="p-content-detail__original").text
        #評価
        filmarks_rate = soup.find(class_="c-rating__score").text
        if filmarks_rate == "-": #評価がない場合
            filmarks_rate = None
        else :
            filmarks_rate = float(filmarks_rate)

        # 視聴者数
        # 視聴者数も取りたいが動的に変化するのでchromedriverが必要
        # しかし、現chromeのバージョンに対応してないため断念
        # view_tag = soup.find(class_="p-movie-cassette__action p-movie-cassette__action--marks")
        # view = view_tag.find(class_="p-movie-cassette__action__body").text
        # if view == "-": #視聴者数がない場合
        #     view = 0
        # else :
        #     view = int(view)

        # 上映日
        other_info = soup.select_one("body > div.l-main > div.p-content-detail > div.p-content-detail__head > div > div.p-content-detail__body > div.p-content-detail__main > div.p-content-detail__other-info")
        try :
            other_information = other_info.text
        except:
            other_information = None
        # ジャンル
        genre_tag = soup.select_one("body > div.l-main > div.p-content-detail > div.p-content-detail__head > div > div.p-content-detail__body > div.p-content-detail__main > div.p-content-detail__genre > ul > li > a")
        if not genre_tag : # ジャンルがない場合
            genre = None
        else : # ジャンルがある場合
            genre = genre_tag.text
        # filmarksは画像が多いためpdfの生成にかなり時間がかかるため作らない
        """
        # htmlファイル作成
        html_file = "./" + str(film_name) + ".html"
        with open(html_file, mode="w") as f:
            f.write(html_text)

        # pdf作成
        filmarks_pdf_file = "./Filmarks.pdf"
        try:
            print("pdf作成")
            pdfkit.from_file(html_file, filmarks_pdf_file)
            print("pdf作成")
        except Exception as e:
            print(str(e))


        os.remove(html_file)
        """
        return japanese_title, original_title, filmarks_rate, other_information, genre

def get_IMDb_information_and_pdf(html_text):
    if html_text == None:
        pass
    else:
        # imdbのHTMLをパースする
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        """
        try:
            imdb_rate = soup.select_one("#titleOverview > div.media.overview-top > div > p > time")
            print(imdb_rate)
            imdb_rate = float(imdb_rate)
        except Exception as e:
            print(str(e))
            imdb_rate = None
        """
        # htmlファイル作成
        html_file = "./" + str(film_name) + ".html"
        with open(html_file, mode="w") as f:
            f.write(html_text)

        # pdf作成
        # slackerでアップロード時にマルチバイト文字のファイルを開けないため
        # 適当に英語で名前をつける
        imdb_pdf_file = "./IMDb.pdf"
        try:
            pdfkit.from_file(html_file, imdb_pdf_file)
        except:
            pass

        os.remove(html_file)

        return imdb_pdf_file

def make_comment_list(japanese_title, original_title, filmarks_rate, other_information, genre, filmarks_url, imdb_url):
    comment_list = []
    # imdbの情報が取得できなかった場合
    if imdb_information == "no":
        comment_list.append("*IMDbの情報は取得できませんでした!*")

    comment_list.append("邦題：" + japanese_title)

    if original_title != None:
        comment_list.append("原題：" + original_title)

    if filmarks_rate != None:
        comment_list.append("Filmarksの評価：" + str(filmarks_rate) + "/5")
    else:
        comment_list.append("Filmarksの評価：" + "なし")
    if imdb_information != "no":
        """
        if imdb_rate != None:
            comment_list.append("IMDbの評価：" + str(imdb_rate) + "/10")
        else:
            comment_list.append("IMDbの評価：" + "なし")
        """
    # comment_list.append("Filmarks視聴者数：" + view)

    if other_information != None:
        comment_list.append(other_information)

    if genre != None:
        comment_list.append("ジャンル：" + genre)

    if filmarks_url != None:
        comment_list.append("FilmarksのURL：" + filmarks_url)

    if imdb_url != None:
        comment_list.append("IMDbのURL：" + imdb_url)

    return comment_list

def slack_upload(imdb_pdf_file, comment_list):
    # filmarksの情報が取得できなかった場合
    if filmarks_information == "no":
        slacker = Slacker(slack_token)
        slacker.chat.post_message(channel, "お探しの作品に関する情報を取得できません。")
    else:
        if imdb_information == "no":
            comment = "\n".join(comment_list)
            slacker = Slacker(slack_token)
            slacker.chat.post_message(channel, comment)
        else:
            comment = "\n".join(comment_list)
            slacker = Slacker(slack_token)
            slacker.files.upload(file_=imdb_pdf_file, filename=str(film_name) + "_IMDb.pdf", channels=channel, initial_comment=comment)
            os.remove(imdb_pdf_file)


if __name__ == "__main__":
    japanese_title, original_title = get_film_name(argv)
    condition, html_text, information, url, film_name = get_html(japanese_title, original_title, "filmarks")
    filmarks_url = url
    # filmarksで情報を取得できなければコメントを出して終了
    if information == "no":
        filmarks_information = "no"
        filmarks_pdf_file, imdb_pdf_file, comment_list = None, None, None
        slacker = Slacker(slack_token)
        slacker.chat.post_message(channel, "お探しの作品に関する情報を取得できません。")
    else:
        filmarks_information = "yes"
        if condition == "error":
            quit()
        japanese_title, original_title, filmarks_rate, other_information, genre = get_Filmarks_information_and_pdf(html_text, film_name)
        condition, html_text, information, url, film_name = get_html(japanese_title, original_title, "imdb")
        imdb_url = url
        if information == "no":
            imdb_information = "no"
        else:
            imdb_information = "yes"
        if condition == "error":
            quit()
        imdb_pdf_file = get_IMDb_information_and_pdf(html_text)
        time.sleep(1)
        comment_list = make_comment_list(japanese_title, original_title, filmarks_rate, other_information, genre, filmarks_url, imdb_url)
        slack_upload(imdb_pdf_file, comment_list)
