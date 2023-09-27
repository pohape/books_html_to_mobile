from ebooklib import epub
from requests.exceptions import RequestException
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import ParseResult, urlparse, parse_qs


def generate_url(user_url: str, page_num: int):
    parsed_url = urlparse(user_url)  # type: ParseResult
    current_page_url = "{}://{}{}?".format(
        parsed_url.scheme,
        parsed_url.netloc,
        parsed_url.path
    )

    parsed_query = parse_qs(parsed_url.query)  # type: dict
    parsed_query['part'] = [page_num]

    for key in parsed_query:
        current_page_url += "{}={}&".format(
            key,
            str(parsed_query[key][0])
        )

    return current_page_url[:-1]


def find_last_page_num(html):
    soup = BeautifulSoup(html, "html.parser")

    div = soup.find("div", {"class": "ngg-navigation"})
    a_tags = div.find_all("a", href=True)

    last_page_num = 0

    for a in a_tags:
        parsed_url = urlparse(a['href'])
        parsed_query = parse_qs(parsed_url.query)
        current_page_num = int(parsed_query['part'][0])

        if current_page_num > last_page_num:
            last_page_num = current_page_num

    return last_page_num


def download_page_or_quit(url):
    try:
        response = requests.get(url)
    except RequestException as e:
        print("Could not download the web page: " + str(e))
        quit()

    if response.status_code != 200:
        print("Something went wrong, got status code " +
              str(response.status_code))
        quit()

    return response.text


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", id="toc")

    clean_content = ""

    for tag in content.find_all(recursive=False):
        tag = tag  # type: Tag

        if tag.has_attr("class") and tag.get("class")[0] == "ngg-navigation":
            continue
        elif tag.name == "br":
            continue
        else:
            clean_content += str(tag)

    return clean_content


def generate_e_book(
        id,
        author,
        title,
        language,
        html_content,
        output_file_without_ext
):
    book = epub.EpubBook()

    # set metadata
    book.set_identifier(id)
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    # create chapter
    chapter = epub.EpubHtml(title=title, file_name="book.xhtml", lang=language)
    chapter.content = html_content

    # add chapter
    book.add_item(chapter)

    # define Table Of Contents
    book.toc = (
        epub.Link("book.xhtml", title, title),
        (epub.Section(title), (chapter,)),
    )

    # basic spine
    book.spine = ["nav", chapter]

    # write to the file
    epub.write_epub(output_file_without_ext + ".epub", book, {})
