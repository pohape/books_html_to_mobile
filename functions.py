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


def parse_book_info(html: str):
    soup = BeautifulSoup(html.replace("<br>", "<br />"), "html.parser")
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
    table_of_contents_last_element_title = None

    for li in table_of_contents_li:
        a = li.find("a", recursive=False)
        book_id, page_num = parse_url_book_id_page_num(a['href'])

        if table_of_contents_last_element_title is not None:
            table_of_contents[table_of_contents_last_element_title]["end_page"] = page_num - 1

        table_of_contents[a.text] = {"start_page": page_num, "end_page": None}
        table_of_contents_last_element_title = a.text

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


def parse_page(html: str):
    soup = BeautifulSoup(html.replace("<br>", "<br />"), "html.parser")
    content = soup.find("div", id="toc")

    # remove all <ol> <li> <a> tags
    for ol in content.find_all("ol"):
        li = ol.find("li", recursive=False)

        if li is not None:
            a = li.find("a", recursive=False)

            if a is not None:
                ol.decompose()

    for tag_name in ("h1", "h2"):
        for tag in content.find_all(tag_name):
            if tag.has_attr("class") and tag.get("class")[0] == "series":
                tag.decompose()
            elif tag.get_text() == 'СОДЕРЖАНИЕ':
                tag.decompose()
            else:
                b = soup.new_tag("b")
                b.string = tag.get_text()

                p = soup.new_tag("p", align="center")
                p.append(b)

                tag.replace_with(p)

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
        id: int,
        author: str,
        title: str,
        language: str,
        chapters_dict: dict,
        output_file_without_ext: str,
        table_of_contents_needed=True
):
    book = epub.EpubBook()

    # set metadata
    book.set_identifier(str(id))
    book.set_title(str(title))
    book.set_language(str(language))
    book.add_author(str(author))

    if table_of_contents_needed:
        book.spine = ["nav"]
        i = 0

        for chapter_title in list(chapters_dict.keys()):
            i += 1

            # create chapter
            chapter = epub.EpubHtml(
                title=chapter_title,
                file_name=str(i) + ".xhtml",
                lang=language,
                content=chapters_dict[chapter_title],
            )

            # add chapter
            book.add_item(chapter)
            book.spine.append(chapter)
            book.toc.append(epub.Link(
                href=str(i) + ".xhtml",
                title=chapter_title,
                uid=str(i)
            ))
    else:
        full_content_as_chapter = epub.EpubHtml(
            title=title,
            file_name="book.xhtml",
            lang=language,
            content="\n".join(chapters_dict.values()),
        )
        book.spine = [full_content_as_chapter]
        book.add_item(full_content_as_chapter)

    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # write to the file
    epub.write_epub(output_file_without_ext + ".epub", book, {})
