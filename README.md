My mom asked me to make offline versions (for her e-book device) of Christian books from MinistryBooks.ru website (are available for online reading only).

```
pip install bs4 requests EbookLib
python convert.py --url=https://ministrybooks.ru/?mb=208
```

You will find an EPUB file in the directory where you run the script.
Feel free to take my code as a base and add changes to convert other online books to EPUB using Python.

You can use this code as an example of using the [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) and [EbookLib](https://github.com/aerkalov/ebooklib) libraries.
