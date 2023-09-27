from ebooklib import epub
from requests.exceptions import RequestException
import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import ParseResult, urlparse, parse_qs


def parse_url_book_id_page_num(url: str):
    parsed_url = urlparse(url)  # type: ParseResult
    parsed_query = parse_qs(parsed_url.query)  # type: dict

    return (int(parsed_query['mb'][0]), int(parsed_query['part'][0]))


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


def parse_book_info(html):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", id="toc")

    div = content.find("div", {"class": "ngg-navigation"})
    navigation_a_tags = div.find_all("a", href=True)

    last_page_num = 0

    for a in navigation_a_tags:
        book_id, current_page_num = parse_url_book_id_page_num(a['href'])

        if current_page_num > last_page_num:
            last_page_num = current_page_num

    title_h1 = content.find("h1", {"class": "series"})

    if not title_h1:
        title_h1 = soup.find("h1", {"class": "title"})

    table_of_contents_ol = content.find("ol")
    table_of_contents_li = table_of_contents_ol.find_all("li", recursive=False)
    table_of_contents = {}

    for li in table_of_contents_li:
        a = li.find("a", recursive=False)
        book_id, page_num = parse_url_book_id_page_num(a['href'])
        table_of_contents[a.text] = page_num

    return (title_h1.text, book_id, last_page_num, table_of_contents)


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
    book.set_identifier(str(id))
    book.set_title(str(title))
    book.set_language(str(language))
    book.add_author(str(author))

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
