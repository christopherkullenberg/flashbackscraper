# Flashbackscraper
A simple python script for scraping Flasback forum threads.

![Terminal demo](https://digitalametoder.science/files/render1544006868267.gif)


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

If you want to map the network created as an effect of the "quote" function in the Flashback forum, there is a script, ``sqlite2gexf.py`` that converts the scraped data to a .gexf file, which can be opened in for instance [Gephi](https://gephi.org). The script requires the module [networkx](https://networkx.github.io/), then you can simply run:

    python sqlite2gexf <name of sqlite3 file>

See the file ``t2977018.gexf`` for an example in the example_outputs folder. 
