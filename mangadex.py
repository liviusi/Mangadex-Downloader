# -------------------------------- 
# --------- Requirements ---------
# --------------------------------
import os.path
from tqdm import tqdm # It just makes things look good
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC

# next_chapter = driver.find_element_by_class_name("chapter-link-right").get_attribute("href")

def chapterValid(URL):
    if 'http' in URL and '://mangadex.org/chapter' in URL:
        return True
    else:
        return False

# Loads page, driver has already gotten URL
def loadPage(driver):
    DELAY = 2
    try:
        sleep(DELAY)
        alert = driver.find_element_by_class_name("message") # needed
        ActionChains(driver).move_to_element(alert).click().perform() # needed
        WebDriverWait(driver, DELAY).until(expected_conditions.presence_of_element_located(
            (By.XPATH, "html/body/div[1]/div[2]/div[2]/div/img"))) # Loaded
    except Exception:
        sleep(DELAY)

# download picture given its direct link and directory to save it in
def downloadPic(picURL, directory, pageNUM):
    import requests
    AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'
    req = requests.get(picURL, headers={'User-Agent':AGENT})
    with open(directory + '/' + str(pageNUM) + '.png', 'wb') as f:
        f.write(req.content)

# download page given driver, title, URL and delay
def downloadPage(driver, directory, chapTITLE, chapURL, pageNUM):
    driver.get(chapURL + '/' + str(pageNUM))
    loadPage(driver)
    picURL = driver.find_element_by_xpath("html/body/div[1]/div[2]/div[2]/div/img").get_attribute("src")
    downloadPic(picURL, directory, pageNUM)

# download chapter given driver, title, URL and delay
def downloadChapter(driver, chapTITLE, chapURL):    
    firstPAGE = chapURL + '/1'
    driver.get(firstPAGE)
    loadPage(driver)

    # Fetch data
    title = driver.find_element_by_class_name('manga-link').text
    pages = int(driver.find_element_by_class_name('total-pages').text)

    if not os.path.exists(title):
        os.mkdir(title)

    if not os.path.exists(title + '/' + chapTITLE):
        os.mkdir(title + '/' + chapTITLE)
    
    for page in tqdm(range(1, pages + 1)): # from the first one till the last
        downloadPage(driver, title + '/' + chapTITLE, chapTITLE, chapURL, page)


# Fetch every chaptr given titleURL
def fetchALLChapters(driver, titleURL):
    # Additional imports
    import requests
    from bs4 import BeautifulSoup

    page = requests.get(titleURL)
    soup = BeautifulSoup(page.content, 'html.parser')
    items = soup.findAll('item')
    if not items:
        print('Error occurred. Is the ID valid?')
    else:
        for item in tqdm(items):
            strings = item.text.split('\n')
            chapTITLE = strings[1]
            chapURL = strings[2]
            downloadChapter(driver, chapTITLE, chapURL)

def startDriver():
    # Get chromedriver, it needs to be in the same directory as I was too lazy to bother adding it to PATH
    dir_path = os.path.dirname(os.path.realpath(__file__))
    DRIVERPATH = dir_path + '/chromedriver.exe'

    # Define stuff for Chrome webdriver
    WINDOWSIZE = "1920,1080"
    chrome_options = Options()  
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--window-size=%s" % WINDOWSIZE)
    driver = webdriver.Chrome(executable_path=DRIVERPATH, options=chrome_options)
    return driver



def main():
    URL = 'https://mangadex.org/'
    RSS = 'rss/FDW2GXwUf79AqzS5y4mKkCN8rpZnBeuc/manga_id/'
    print('What do you want to download?\n')
    i = str(input('c for a single chapter, m for whole manga: '))
    while True:
        if i == 'c':
            j = str(input('\nWrite the whole URL: '))
            if not chapterValid(j):
                print('URL is not valid. Try again.')
                continue
            else:
                driver = startDriver()
                downloadChapter(driver, '', j)
                driver.close()
                break
        elif i == 'm':
            id = str(input('\nWrite the manga id: '))
            driver = startDriver()
            fetchALLChapters(driver, URL + RSS + id)
            driver.close()
            break
            

if __name__ == '__main__':
    main()
