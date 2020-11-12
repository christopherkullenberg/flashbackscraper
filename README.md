# Flashbackscraper
A simple python script for scraping [flashback.org](https://flashback.org) forum threads. It uses BeautifulSoup to parse the html responses from the forum, this way avoiding any (known) limitations in how much data can be fetched. Features include:

* Scraping of entire threads.
* Scraping of multiple threads from a file list.
* Scraping a subforum for thread urls, which then can be scraped as multiple threads.
* Running the scraper through the Tor socks5 proxy (experimental feature, do not use for opsec).

![Terminal demo](https://digitalametoder.science/files/render1544006868267.gif)

*Note*: Use responsibly with regards to network usage and potential privacy aspects.


## Requirements

* Python3
* Beautiful Soup 4

Install with:

    easy_install beautifulsoup4

or...

    pip install beautifulsoup4

## Usage, single thread mode

    python flashbackscraper.py -u <URL to flashback thread>


### Example

    python flashbackscraper.py -u https://www.flashback.org/t2977018

See the example_output folder for  sqlite3/csv files.

## Usage, multiple threads from file mode

    python flashbackscraper -f <file with newline separated urls>


### Example

    python flashbackscraper.py -f filewithurls.txt

## Usage, scrape subforum for thread urls and write to file

    python flashbackscraper.py -s <URL to subforum>


### Example

    python3 flashbackscraper.py -s https://www.flashback.org/f328

Then you can run the ``-f`` option, as above, to get all the posts of all the trhreads in a subforum. For example, the above command will produce a text file called ``f328.txt`` which then can be scraped with

    python flashbackscraper.py -f f328.txt

**Warning:** This will create a lot of requests and network traffic. **Use responsibly!**.



## Extras

### Example data analysis

In the folder ``flashback_data_analysis`` you will find a Jupyter notebook called ``filosofer.ipynb``, which contains some example analysis approaches. It also shows how you can read a Pandas dataframe from the .sqlite3 database and how to parse date and time correctly.


### Run scraper through Tor darknet

By adding the ``-t`` flag, you may run the https requests through the Tor socks5 proxy on port 9050. This requires that you have [Tor installed](https://torproject.org) on your system and that there is a functioning proxy on the standard Tor port. This feature is still a bit experimental, so **do not rely on it for anonymity**.



### Network analysis file

If you want to map the network created as an effect of the "quote" function in the Flashback forum, there is a script, ``sqlite2gexf.py`` that converts the scraped data to a .gexf file, which can be opened in for instance [Gephi](https://gephi.org). The script requires the module [networkx](https://networkx.github.io/), then you can simply run:

    python sqlite2gexf <name of sqlite3 file>

See the file ``t2977018.gexf`` in the example_outputs folder as an example.
