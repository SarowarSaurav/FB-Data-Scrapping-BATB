import json
import re
import time

import chromedriver_autoinstaller
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

from config import username, password, number_posts_max, number_comments_max, output_file_name

chromedriver_autoinstaller.install()
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


class Post_Scraper:
    """
    Post_Scraper class allows to scrape Facebook Posts based on search queries.
    """
    LOGIN_URL = "https://www.facebook.com"
    MBASIC_URL = "https://mbasic.facebook.com"
    REACTIONS_NAMES = ['Like', 'Angry', 'Love', 'Haha', 'Sad', 'Care', 'Wow']

    def __init__(self, posts_url) -> None:
        self.driver = webdriver.Chrome()
        self.posts_url = posts_url.replace("www", "mbasic")

    def login(self, username, password) -> None:
        """
        Login to a Facebook Account.

        Args:
            username (`str`)
                Facebook account username/email
            passward (`str`)
                Facebook account password    
        """
        self.driver.get(self.LOGIN_URL)
        time.sleep(2)
        email_ = self.driver.find_element(By.NAME, "email")
        pass_ = self.driver.find_element(By.NAME, "pass")
        email_.send_keys(username)
        time.sleep(1)
        pass_.send_keys(password)
        time.sleep(2)
        email_.submit()
        time.sleep(10)

    def get_content(self, url=None):
        """
        parsing html from a web page.

        Args:
            url (`str`)
                web page url.
        Return:
            A beautiful soup object.
        """
        if url is None:
            url = self.posts_url
        self.driver.get(url)
        page_content = self.driver.page_source
        soup = BeautifulSoup(page_content, 'html.parser')
        return soup

    def clean_url(self, posts_urls_list):
        """
        Convert posts urls to mbasic facebook format.

        Args:
            posts_urls_list (`list[str]`)
        Return:
            A list of urls after applying the cleaning formula.
        """
        clean_posts_urls_list = [
            self.MBASIC_URL + url.replace("https://m.facebook.com", '').replace(self.MBASIC_URL, '') for url in
            posts_urls_list]
        return clean_posts_urls_list

    def get_more_posts(self, soup):
        """
        get more posts by going to the next page if exist.
        
        Args:
            soup (`bs4.BeautifulSoup object`):
                post html content.
        Return:
            A url (`str`) to get the next page.
        """
        if soup.find("div", id="see_more_pager") is not None:
            more_posts_url = soup.find("div", id="see_more_pager").find('a', href=True)['href']
        else:
            more_posts_url = None
        return more_posts_url

    def get_posts_info(self, soup, posts_urls_list=None, post_date_list=None, likes_list=None):
        """
        Extract the full stoy url, the post reactions and the publishing date. 
        """
        if posts_urls_list is None:
            posts_urls_list = []
        if post_date_list is None:
            post_date_list = []
        if likes_list is None:
            likes_list = []

        while True:
            time.sleep(2)
            posts = soup.find_all("div", class_="by")
            for post in posts:
                like_span = post.find("div", id=re.compile("sentence_"))
                full_story_tag = post.find('a', href=re.compile("#footer_action_list"))
                if full_story_tag is None:
                    full_story_tag = post.find('a', href=re.compile("/story.php"))
                post_date_abbr = post.find("abbr")
                if full_story_tag:
                    full_story_href = full_story_tag["href"].replace("https://m.facebook.com", '').replace(
                        self.MBASIC_URL, '')
                    posts_urls_list.append(full_story_href)
                    if post_date_abbr:
                        post_date = post_date_abbr.get_text()
                        post_date_list.append(post_date)
                    else:
                        post_date_list.append('None')
                    if like_span:
                        if like_span.get_text():
                            likes = like_span.get_text()
                            if likes == "Like · React":
                                likes = '0'
                            else:
                                replacement = ["· Like · React", "· Like", "· Love", "· Haha", "· Care", "· Wow",
                                               "· Angry"]
                                [likes := likes.replace(item, '') for item in replacement]
                            likes_list.append(likes)
                        else:
                            likes_list.append('0')
                    else:
                        likes_list.append('0')
            more_posts_url = self.get_more_posts(soup)
            if more_posts_url:
                soup = self.get_content(more_posts_url)
            else:
                break
        posts_urls_list = self.clean_url(posts_urls_list)

        return posts_urls_list, likes_list, post_date_list

    def get_post_images(self, soup):
        """
        Extract the full stoy (post) images.
        Args:
            soup (`bs4.BeautifulSoup object`)
        Return:
            A string of multiple image urls ("url1 \n url2 \n").
        """

        img_a_tag_1 = soup.find_all('a', href=re.compile("/photo.php?fbid="))
        img_a_tag_2 = soup.find_all('a', href=re.compile("/photo"))

        if len(img_a_tag_1) > 0:
            img_url = self.LOGIN_URL + img_a_tag_1[0]['href']
        elif len(img_a_tag_2) > 0:
            img_url = self.LOGIN_URL + img_a_tag_2[0]['href']
        else:
            img_a_tag_3 = soup.find_all('a', href=re.compile("pcb"))
            if len(img_a_tag_3) > 0:
                img_url = ''
                for item in img_a_tag_3:
                    img_url += self.LOGIN_URL + item['href'] + "\n"
            else:
                img_a_tag_3 = soup.find_all('a', href=re.compile("photos"))
                if len(img_a_tag_3) > 0:
                    img_url = ''
                    for item in img_a_tag_3:
                        img_url += self.LOGIN_URL + item['href'] + "\n"
        return img_url

    def get_profile(self, soup):
        """
        Get the creator profile.
        Args:
            soup (`bs4.BeautifulSoup object`)
        Return:
            A string containing the creator name.
            A string containing the profile url.
        """
        h3 = soup.find("h3")
        if h3 is not None:
            if h3.find('a') is not None:
                profile_name = h3.a.get_text()
                if h3.a.has_attr('href'):
                    h3_a_tag = h3.a['href']
                    h3_a_tag = h3_a_tag.replace("&__tn__=C-R", '')
                    profile_url = self.LOGIN_URL + h3_a_tag
                else:
                    profile_url = "None"
        else:
            a_tag_actor = soup.find('a', class_="actor-link")
            if a_tag_actor is not None:
                profile_name = a_tag_actor.get_text()
                if a_tag_actor.has_attr('href'):
                    profile_url = self.LOGIN_URL + a_tag_actor['href']
                else:
                    profile_url = "None"
            else:
                profile_name = "None"
                profile_url = "None"

        return profile_name, profile_url

    def get_post_description(self, soup):
        """
        Extract the post descrtiption (text).
        """


        p = soup.findAll("p")
        if len(p) > 0:
            description_text = ' '
            for item in p:
                description_text += item.get_text() + ' '
        else:
            description_text = ' '
            div_tag = soup.find('div', {'data-ft': '{"tn":"*s"}'})
            if div_tag is not None:
                description_text += div_tag.get_text()
            else:
                div_tag = soup.find('div', {'data-ft': '{"tn":",g"}'})
                if div_tag is not None:
                    description_text += div_tag.get_text().split(" · in Timeline")[0].replace('· Public', '')
        return description_text

    def get_post_reactions(self, soup):
        desc_ = []
        pq = soup.find("abbr")
        if pq is not None:
            desc_.append(pq.get_text())

        return desc_


    def get_reactions(self, soup):
        reaction_list = []
        pdt = soup.find("div", class_="df")
        if pdt is not None:
            for reactions in range(1):
                reactions = pdt.get_text()
                reaction_list.append(reactions)
        pd = soup.find("div", class_="ct")
        if pd is not None:
            for reactions in range(1):
                reactions = pd.get_text()
                reaction_list.append(reactions)
        pdy = soup.find("div", class_="da")
        if pdy is not None:
            for reactions in range(1):
                reactions = pdy.get_text()
                reaction_list.append(reactions)
        pdv = soup.find("div", class_="dl")
        if pdv is not None:
            for reactions in range(1):
                reactions = pdv.get_text()
                reaction_list.append(reactions)
        pdm = soup.find("div", class_="_1g06")
        if pdm is not None:
            for reactions in range(1):
                reactions = pdm.get_text()
                reaction_list.append(reactions)

        pdh = soup.find("div", class_="dh")
        if pdh is not None:
            for reactions in range(1):
                reactions = pdh.get_text()
                reaction_list.append(reactions)

        return reaction_list


    def more_comments(self, soup):

        if soup.find('div', id=re.compile("see_next_")) is not None:
            more_comments_url = soup.find('div', id=re.compile("see_next_")).find('a', href=True)['href'].replace(
                'https://m.facebook.com', '')
        else:
            more_comments_url = None
        return more_comments_url

    def get_post_comments(self, soup, comments_dict={}, who_commented_dict={}, comments_max=1):

        count = 0
        while count <= comments_max:
            who_commented_profiles, who_commented_names = [], []
            comments_tag = soup.find_all('h3')
            if len(comments_tag) > 0:
                for i in comments_tag:
                    a_tag = i.find('a')
                    if a_tag is not None:
                        if a_tag.has_attr('href'):
                            a_href = a_tag['href']
                            if ("refid=52&__tn__=R" in a_href) or ('refid=18&__tn__=R' in a_href) or (
                                    "?rc=p&__tn__=R" in a_href):
                                a_href = a_href.replace("&refid=52&__tn__=R", '')
                                a_href = a_href.replace("refid=52&__tn__=R", '')
                                a_href = a_href.replace("&refid=18&__tn__=R", '')
                                a_href = a_href.replace("?refid=18&__tn__=R", '')
                                a_href_url = self.LOGIN_URL + a_href
                                who_commented_profiles.append(a_href_url)
                                who_commented_names.append(a_tag.get_text())
                                # Comments Extraction:
            div = soup.find_all('div')
            div_text = [i.get_text() for i in div]

            aa, aa1 = [], []
            for i in div_text:
                if i not in aa:
                    aa.append(i)
            for j in aa:
                if 'Like · React · Reply · More ·' in j and 'View more comments…' not in j:
                    aa1.append(j)

            ll = [' ' for i in range(len(who_commented_names))]
            if len(who_commented_names) > 0:
                for i in range(len(who_commented_names)):
                    for j in aa1:
                        if who_commented_names[i] in j:
                            com = j.split(who_commented_names[i])[1]
                            ll[i] = com.split("Like")[0].replace('"', '')
                            if 'Edited ·' in ll[i]:
                                ll[i] = com.split("Edited ·")[0]

                    for i in range(len(who_commented_names)):
                        comments_dict[who_commented_names[i]] = ll[i]
                        who_commented_dict[who_commented_names[i]] = who_commented_profiles[i]
            count = len(comments_dict.keys())

            more_comments = self.more_comments(soup)
            if more_comments is not None:
                more_comments_url = self.MBASIC_URL + more_comments.replace(self.MBASIC_URL, '')
                self.driver.get(more_comments_url)
                page_content = self.driver.page_source
                soup = BeautifulSoup(page_content, 'html.parser')

            else:
                break

        comments_dict = json.dumps(comments_dict, ensure_ascii=False).encode('utf8').decode()
        who_commented_dict = json.dumps(who_commented_dict, ensure_ascii=False).encode('utf8').decode()
        return comments_dict


def _draw_as_table(df, pagesize):
    alternating_colors = [['white'] * len(df.columns), ['lightgray'] * len(df.columns)] * len(df)
    alternating_colors = alternating_colors[:len(df)]
    fig, ax = plt.subplots(figsize=pagesize)
    ax.axis('tight')
    ax.axis('off')
    the_table = ax.table(cellText=df.values,
                         rowLabels=df.index,
                         colLabels=df.columns,
                         rowColours=['lightblue'] * len(df),
                         colColours=['lightblue'] * len(df.columns),
                         cellColours=alternating_colors,
                         loc='center')
    return fig


def dataframe_to_pdf(df, filename, numpages=(1, 1), pagesize=(11, 8.5)):
    with PdfPages(filename) as pdf:
        nh, nv = numpages
        rows_per_page = len(df) // nh
        cols_per_page = len(df.columns) // nv
        for i in range(0, nh):
            for j in range(0, nv):
                page = df.iloc[(i * rows_per_page):min((i + 1) * rows_per_page, len(df)),
                       (j * cols_per_page):min((j + 1) * cols_per_page, len(df.columns))]
                fig = _draw_as_table(page, pagesize)
                if nh > 1 or nv > 1:
                    # Add a part/page number at bottom-center of page
                    fig.text(0.5, 0.5 / pagesize[0],
                             "Part-{}x{}: Page-{}".format(i + 1, j + 1, i * nv + j + 1),
                             ha='center', fontsize=8)
                pdf.savefig(fig, bbox_inches='tight')

                plt.close()


if __name__ == "__main__":

    posts_url = input(str("Enter Posts Url: "))
    scraper = Post_Scraper(posts_url)
    scraper.login(username, password)
    soup = scraper.get_content()
    posts_urls_list, post_date_list, likes_list = scraper.get_posts_info(soup)
    print(f">>> Number of Posts Availible: {len(posts_urls_list)}")

    profile_names_list, post_date_list_, descriptions_list, who_commented_list, comments_list, reaction_list = [], [], [], [], [], []
    if number_posts_max > len(posts_urls_list):
        number_posts_max = len(posts_urls_list)

    for i in range(number_posts_max):
        post_url = posts_urls_list[i]
        post_soup = scraper.get_content(post_url)
        time.sleep(30)
        profile_name, profile_url = scraper.get_profile(post_soup)
        post_date_list = scraper.get_posts_info(soup)
        profile_names_list.append(profile_name)
        descriptions_list.append(scraper.get_post_description(post_soup))
        post_date_list_.append(scraper.get_post_reactions(post_soup))
        reaction_list.append(scraper.get_reactions(post_soup))

        comments_list.append(scraper.get_post_comments(post_soup, comments_max=number_comments_max))
        print("----------------------------------")
        print(f"post {i + 1} successfully scraped")

    print(len(profile_names_list), len(descriptions_list), len(comments_list), len(who_commented_list))
    data = {"profile_name": profile_names_list[:number_posts_max],
            "post_description": descriptions_list[:number_posts_max],"Reaction Count": reaction_list[:number_posts_max],
            "Posting Date": post_date_list_[:number_posts_max],"comments": comments_list[:number_posts_max]}
    df = pd.DataFrame(data)
    df.to_(output_file_name)
    scraper.driver.close()
