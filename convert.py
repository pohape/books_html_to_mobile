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

title, book_id, last_page_num, table_of_ctnts = functions.parse_book_info(
    response_html
)

for current_pg_num in range(1, last_page_num + 1):
    current_chapter_title = None

    for chapter_ttl in list(table_of_ctnts.keys()):
        if current_pg_num >= table_of_ctnts[chapter_ttl]["start_page"]:
            if table_of_ctnts[chapter_ttl]["end_page"] is None or\
                    current_pg_num <= table_of_ctnts[chapter_ttl]["end_page"]:
                current_chapter_title = chapter_ttl

    if current_chapter_title is None:
        current_chapter_title = "Предисловие"

    if current_chapter_title not in chapters:
        chapters[current_chapter_title] = ""

    page_url = functions.generate_url(user_url, current_pg_num)
    print("Downloading {}/{}: {}".format(
        current_pg_num,
        last_page_num,
        page_url
    ))

    response_html = functions.download_page_or_quit(page_url)
    current_parsed_page = functions.parse_page(response_html)
    chapters[current_chapter_title] += current_parsed_page

    print("Added {:.2f} KB to the book, total \
size of the book is {:.2f} KB\n".format(
        len(current_parsed_page) / 1024,
        sum([len(parsed_page) for parsed_page in chapters.values()]) / 1024
    ))

filename = title.replace(" ", "_")

functions.generate_e_book(
    id=book_id,
    title=title,
    language="ru",
    author="КБК",
    chapters_dict={k: v for (k, v) in chapters.items() if len(v) > 0},
    output_file_without_ext=filename
)

print("Done: " + filename)
