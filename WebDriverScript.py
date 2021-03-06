from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import argparse
import time
import json

# define a list to store all apps and sections' urls on the website
url_list= []

no_privacy_counter = 0

free_app_counter = 0

paid_app_counter = 0

def modify(text):
        
    # get rid of "\u"
    text = text.encode('ascii', errors='ignore').strip().decode('ascii')

    return text
    
# quickly scroll down to bottom of the page
def quick_scroll_to_bottom(driver):

    js = "return action=document.body.scrollHeight"

    #initilize the current height = 0
    height = 0

    #get the height of the current window
    new_height = driver.execute_script(js)

    while height < new_height:

        for i in range(height, new_height, 400):
            driver.execute_script('window.scrollTo(0, {})'.format(i))
            time.sleep(0.2)
            height = new_height
            time.sleep(0.2)
            new_height = driver.execute_script(js)

    time.sleep(2)

    
# slowly scroll down to the bottom of the page 
def slow_scroll_to_bottom(driver):
    
    temp_height=0
    
    while True:
 
        driver.execute_script("window.scrollBy(0,800)")

        time.sleep(4)

        check_height = driver.execute_script("return document.documentElement.scrollTop || window.pageYOffset || document.body.scrollTop;")

        if check_height==temp_height:
            
            break
        
        temp_height=check_height
                      
def save_as_json(dict, list):

    title = dict['App Title']
    
    # get rid of invalid characters 
    if ":" in title:
        title = title.replace(":","")

    #path may change 
    path = "./"
    filePathNameWExt = os.path.join(path, title + '.json')
    
    with open(filePathNameWExt, 'w') as fp:
      
        json_str = json.dumps(dict)
        fp.write(json_str)
        
        fp.write('\n\n\n\n')

        json_str = json.dumps(list)
        fp.write(json_str)
                                   
def extract_additional_details_reviews(driver, dict, list):

    global no_privacy_counter

    details = driver.find_element_by_class_name('app-details__header')
    driver.execute_script("arguments[0].scrollIntoView();",details)

    time.sleep(2)
            
    #store inforamtion in dictionary
    row_left = driver.find_elements_by_class_name("app-details-row__left")
    row_right = driver.find_elements_by_class_name("app-details-row__right")

    for index in range(len(row_left)):

        left_name = row_left[index].get_attribute("innerText")

        if (left_name == "Developer Privacy Policy") or (left_name == "Developer Terms of Service"):

            try:

                parent = row_right[index]

                link = parent.find_element_by_css_selector("a.app-details-row__link.link.link--clickable")

                link.click()

                # this will open a new tab.Thus, there are total two tabs: app's webpage and privacy's webpage
                app_webpage = 0
                privacy_webpage = 1
                
                windows = driver.window_handles
                driver.switch_to.window(windows[privacy_webpage])
            
                quick_scroll_to_bottom(driver)
        
                # store the text of the page in dictionary
                text = driver.find_element_by_tag_name("body").get_attribute("innerText")
                text = modify(text)
                dict[left_name] = text

                # close the new tab and switch to the previous tab
                driver.close()            
                driver.switch_to.window(windows[app_webpage])
        
                time.sleep(2)
    
            except NoSuchElementException:

                dict[left_name] = 'None'

                if left_name == "Developer Privacy Policy":

                    no_privacy_counter += 1 
                    
        else:

            dict[left_name] = row_right[index].get_attribute("innerText")
   
    # apps with reviews 
    try:

        # extract star ratings
        star_ratings = driver.find_element_by_class_name('app-ratings-histogram').get_attribute('innerText')

    # apps without reviews  
    except NoSuchElementException:

        list = ['No Reviews']

    else:
        
        list.append(modify(star_ratings))

        try:

            page_counter = 1
            
            # a list stores all page numbers showing up
            review_pages = driver.find_elements_by_css_selector("div.app-review-pager__number")
            
            # get the index of the last page in the list
            last_page_index = len(review_pages) - 1

            # get the number of the last page
            total_page_number = int(review_pages[last_page_index].get_attribute('innerText'))

            print("total_page_number: ", total_page_number)

            while True:

                try:
                    # wait until the current page number is equal to the page counter 
                    wait = WebDriverWait(driver, 10)
                    wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'div.app-review-pager__number.app-review-pager__number--current'), str(page_counter)))

                except TimeoutException:
                
                    break
  
                print("page_counter: ", page_counter, "current_page_number: ", driver.find_element_by_css_selector('div.app-review-pager__number.app-review-pager__number--current').get_attribute('innerText'))
            
                # extract users' reviews on current page 
                current_reviews = driver.find_elements_by_class_name('app-review')

                for review in current_reviews:

                    text = modify(review.get_attribute('innerText'))
                
                    list.append(text)

                # reach the max page    
                if page_counter == total_page_number:

                    break
                
                else:

                    try: 
                
                        buttons = driver.find_elements_by_css_selector("button.button.button--secondary.app-review-pager__button")
                        
                        # on the first page of the review, only right arrow button is available. Thus, only one button is in the list 
                        if len(buttons) == 1:

                            #left button is not avaiable
                            right_button = 0

                            button = buttons[right_button]
                            
                        # starting from the second page, two buttons are available in the list. The first is the left arrow button, and the second is the right arrow button. Thus, we press the second button. 
                        else:

                            left_button = 0
                            right_button = 1
                            
                            button = buttons[right_button]

                        button.click()
                
                        page_counter += 1

                    except ElementClickInterceptedException:

                        print("issue")

                        break
                                            
        # only one page review          
        except IndexError:
            
            current_reviews = driver.find_elements_by_class_name('app-review')

            for review in current_reviews:

                text = modify(review.get_attribute('innerText'))
                
                list.append(text)
                                                                                                                                   
    for term in dict.items():

        print(term, '\n')        

    for item in list:

        print (item,'\n')
                    
def test_extraction_python_org(driver):

    global free_app_counter

    global paid_app_counter
    
    # scroll to the bottom of the page to obtain all elements
    slow_scroll_to_bottom(driver)    
     
    # a list of items on the webpage
    items = driver.find_elements_by_css_selector('a.store-section-item-tile')

    for item in items:

        url = item.get_attribute("href")

        url_list.append(url)

    print("number of items: ", len(url_list), "\n")
        
    # access urls on the current webpage 
    for url in url_list:
           
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.app-description__title')))

        driver.execute_script("window.scrollBy(0,200)")

        # define a dictionary to store an app's information           
        dict = {}

        # define a list to store all reviews             
        review_list = []    

        #extract the title   
        dict['App Title'] = driver.find_element_by_class_name("app-description__title").get_attribute("innerText")
        
        #extract the description
        text = driver.find_element_by_class_name('store-item-detail-page-description__content').get_attribute("innerText")
        text = modify(text)
        dict['App description'] = text
        
        #extract from the purchase section
        text = driver.find_element_by_class_name('app-purchase').get_attribute("innerText")

        if "Free" in text:
            free_app_counter += 1

        else:
            paid_app_counter += 1 
            
        text = modify(text)  
        dict['Purchase section'] = text

        quick_scroll_to_bottom(driver)
        
        #scroll up to find "Additional Details & Reviews" section
        extract_additional_details_reviews(driver, dict, review_list)
           
        # save data as a json file
        save_as_json(dict, review_list)
                                                                                                                                                                           
        # go back to the main website           
        driver.back()
                
        time.sleep(2)
                    
    print('\n')
    print("Number of apps: ", len(url_list), '\n')
    print("Total apps without privacy information: ", no_privacy_counter, '\n')
    print("Total paid apps for Quest: ", paid_app_counter, '\n')
    print("Total free apps for Quest: ", free_app_counter)

if __name__ == '__main__':

    
    #parser = argparse.ArgumentParser("configure the driver & pass the URL of the oculus app store")
    #parser.add_argument("path", help = "your driver's path", type = str)
    #parser.add_argument("url", help = "the app store url you are going to explore (default: 'https://www.oculus.com/experiences/quest/section/1888816384764129/')", type = str)
    #args = parser.parse_args()

    # set English as chromdriver's defult language
    options = webdriver.ChromeOptions()
    options.add_argument('--lang=en')

    # executable_path = "C:\Program Files\Google\Chrome\Application\chromedriver.exe"
    driver = webdriver.Chrome(executable_path = r"C:\Program Files\Google\Chrome\Application\chromedriver.exe", options=options)

    # access the Oculus App website: "https://www.oculus.com/experiences/quest/section/554169918379884/#/?_k=yep7ow"
    driver.get("https://www.oculus.com/experiences/quest/section/554169918379884/#/?_k=yep7ow")
    driver.maximize_window()

    time.sleep(4)

    # extract data from the website 
    test_extraction_python_org(driver)

    driver.quit()
