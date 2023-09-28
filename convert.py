from argparse import ArgumentParser
import functions

parser = ArgumentParser()
parser.add_argument("-u", "--url", default=None)
user_url = parser.parse_args().url

if user_url is None:
    print("Please specify an URL of the book using --url=")
    quit()

chapters = {}
response_html = functions.download_page_or_quit(user_url)

title, book_id, last_page_num, table_of_contents = functions.parse_book_info(
    response_html
)

for current_page_num in range(1, last_page_num + 1):
    current_chapter_title = None

    for chapter_title in list(table_of_contents.keys()):
        if current_page_num >= table_of_contents[chapter_title]["start_page"]:
            if table_of_contents[chapter_title]["end_page"] is None or current_page_num <= table_of_contents[chapter_title]["end_page"]:
                current_chapter_title = chapter_title

    if current_chapter_title is None:
        current_chapter_title = "Предисловие"

    if current_chapter_title not in chapters:
        chapters[current_chapter_title] = ""

    page_url = functions.generate_url(user_url, current_page_num)
    response_html = functions.download_page_or_quit(page_url)
    chapters[current_chapter_title] += functions.parse_page(response_html)

filename = title.replace(" ", "_")

functions.generate_e_book(
    id=book_id,
    title=title,
    language="ru",
    author="КБК",
    chapters_dict=chapters,
    output_file_without_ext=filename
)

print("Done: " + filename)
