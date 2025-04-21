import requests
import xml.etree.ElementTree as ET
import urllib.request
import re #regular expression library
import os # 'os' module
import datetime


def clean_filename(title):
    """cleans a string into a pure lovely filename"""
    filename = title.replace(" ","_") #replace space with underscore
    filename = re.sub(r'[^a-zA-Z0-9_.-]','',filename) #removes chars not alphanumeric or underscore but keeps periods and hyphens
    return filename


rss_feed_url = input("Please enter the RSS feed URL: ") #get url from user input

response = requests.get(rss_feed_url)
rss_content = response.text

root = ET.fromstring(rss_content)

podcast_title_element = root.find('channel/title')
if podcast_title_element is not None:
    podcast_title = podcast_title_element.text
else:
    podcast_title = "Podcast Title Not Found"

items = root.findall('channel/item')

episode_details = []
skipped_count = 0
date_format = "%a, %d %b %Y %H:%M:%S %z"


for item in items:
    title_element = item.find('title') #find title tag
    enclosure = item.find('enclosure') #find mp3 url enclosure
    publish_date = item.find('pubDate') #find item publish date

    if enclosure is not None and title_element is not None and publish_date is not None: #check all are found
        title_text = title_element.text #get text content of title tag
        mp3_url = enclosure.get('url')
        pub_text = publish_date.text

        try:
            parsed_date = datetime.datetime.strptime(pub_text, date_format) #attempt to parse date
        
            episode_data = { #store data on success
                'title': title_text,
                'url': mp3_url,
                'date': parsed_date
            }
            episode_details.append(episode_data) #add dictionary to the list

        except ValueError:
            skipped_count += 1 #count failures silently
            #optional: handle other formats here?

min_date = None
max_date = None

if episode_details: #check list not empty
     min_date = episode_details[0]['date']
     max_date = episode_details[0]['date'] #start with using first episode date

     for episode in episode_details:
          current_episode_date = episode['date']

          if current_episode_date < min_date:
               min_date = current_episode_date

          if current_episode_date > max_date:
               max_date = current_episode_date


print(f"Podcast: {podcast_title}")
print(f"Found {len(episode_details)} valid episodes.")

if min_date and max_date:
     
     display_format = "%Y-%m-%d"

     start_date_str = min_date.strftime(display_format)
     end_date_str = max_date.strftime(display_format)

     print(f"Date range found: {start_date_str} to {end_date_str}")
else:
     print("Could not determine date range. (No valid episodes?)")

if skipped_count > 0:
        print(f"Skipped {skipped_count} episodes due to unparseable dates.")

prompt = """Please choose an option: 
1. Download all episodes.
2. Download episodes from a selected date range.
3. List all episodes. (Warning - if there are a lot of episodes, this will be a VERY long list.)
4. Choose a different RSS feed.
5. Exit.
Enter your choice (1-5): """

while True: #loops forever until break out
     choice = input(prompt) #choice inside loop

     if choice not in ['1', '2', '3', '4', '5']:
          print("Invalid input. Please choose a number between 1-5.")
          continue #loops if no correct input
     
     if choice == '1':
          print("Okay, preparing to download all episodes.")

          while True:
                         folder_prompt = "Enter the full folder path to download episodes to, or leave blank for current directory. (0 - return to menu): "

                         download_folder_input = input(folder_prompt)

                         if download_folder_input == '0': #check if user wants to return home
                              download_folder = None #use None as special assign

                              break #exit folder loop
                         
                         elif not download_folder_input: #check if user left directory blank to use current
                              download_folder = ""
                              confirmed_folder = os.path.abspath(os.getcwd()) #find current directory
                              print(f"Using current directory: {confirmed_folder}")
                              break #exit folder loop
                        
                         elif os.path.isdir(download_folder_input): #valid directory entered
                              download_folder = download_folder_input #store path
                              confirmed_folder = os.path.abspath(download_folder)
                              print(f"Downloading to folder: {confirmed_folder}")
                              break #exit this folder loop
                         
                         else: #input wasnt 0 or a valid directory
                              print(f"Error: '{download_folder_input}' is not a valid directory path.")
                              #loop repeats until valid path or 0

          if download_folder is None:
               print(f"Returning to main menu.")
               continue
          
          if download_folder: 
               display_path = os.path.abspath(download_folder) #if specific folder was chosen
          else: 
               display_path = os.path.abspath(os.getcwd()) #if using current directory
          
          confirm_all_download = input(f"Start download of {len(episode_details)} episodes to {display_path}? (yes/no): ") #get confirm
          
          if confirm_all_download not in ["yes", "y", "Y", "YES"]: #check answer
               print("Download cancelled by user.")
               continue
          
          print("Starting download...")
          

          for episode in episode_details:
               cleaned_title = clean_filename(episode['title'])  # clean title for filename
               filename = f"{cleaned_title}.mp3"  # create a filename with .mp3 extension

               filepath = os.path.join(download_folder, filename)  # create full file path

               print(f"Downloading: {filename} from {episode['url']}")  # Print download info
               try:
                    urllib.request.urlretrieve(episode['url'], filepath)
                    print(f"Downloaded: {filename}")
               except Exception as e:
                    print(f"Error downloading {filename} from {episode['url']}: {e}")

          print("\nDownload complete!") #completion message
          post_download_choice = input("Download complete. Enter 0 to Quit, or press Enter to return to the main menu: ")

          if post_download_choice == '0':
                print("Exiting program.")
                break #exit the main while loop 
          else: 
               print("Returning to main menu.")
               continue #return to start of main while loop
     
     elif choice == '2':
          print("Okay, preparing to download episodes from a selected date range.")

          while True: 
               min_date_user_str = input("Enter the earliest date you want to download (YYYY-MM-DD): ")
               try:
                    min_date_user = datetime.datetime.strptime(min_date_user_str, "%Y-%m-%d")
                    break #exit loop if date is valid
               except ValueError:
                    print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
          
          while True: 
               max_date_user_str = input("Enter the latest date you want to download (YYYY-MM-DD): ")
               try:
                    max_date_user = datetime.datetime.strptime(max_date_user_str, "%Y-%m-%d")
                    break #exit loop if date is valid
               except ValueError:
                    print("Invalid date format. Please enter the date in YYYY-MM-DD format.")

          end_date_boundary = max_date_user + datetime.timedelta(days=1) #this fixes an error because of stripping the timezone data
          episodes_in_range = [] #empty list to store date matches

          for episode in episode_details: #loop through parsed episodes
               episode_date = episode['date'] #gets the datetime object for this episode

               episode_date_naive = episode_date.replace(tzinfo=None) #to fix a TypeError cus of naive and aware datetimes

               #check if episode date is within user selected range with this cool chain comparison thing 
               if min_date_user <= episode_date_naive < end_date_boundary:
                    episodes_in_range.append(episode) #add it to the episodes in range list

          if not episodes_in_range:
               print("No episodes found within specified range.")
               continue

          range_confirmation = input(f"Found {len(episodes_in_range)} episodes between these dates. Download episodes? (yes/no): ")  

          if range_confirmation not in ["yes", "y", "Y", "YES"]: #checking answer
               print("Download cancelled by user.")
               continue

          while True:
               folder_prompt = "Enter the full folder path to download episodes to, or leave blank for current directory: "

               download_folder_input = input(folder_prompt) #ive learnt i can reuse variable names if theyre in different code blocks is okay oof

               if not download_folder_input:
                    download_folder = ""
                    confirmed_folder = os.path.abspath(os.getcwd()) #finds current directory
                    print(f"Using current directory: {confirmed_folder}")
                    break
               
               elif os.path.isdir(download_folder_input): #valid directory entered babyyyy
                    download_folder = download_folder_input #store path
                    confirmed_folder = os.path.abspath(download_folder)
                    print(f"Downloading to folder: {confirmed_folder}")
                    break #exit outta here

               else: #input if neither are valid
                    print(f"Error: '{download_folder_input}' is not a valid directory path.")
                    #loop repeats until either default or valid directory
          
          if download_folder:
               display_path = os.path.abspath(download_folder) #if specific folder was chosen
          else:
               display_path = os.path.abspath(os.getcwd()) #if using current directory
          
          confirm_download = input(f"Start download of {len(episodes_in_range)} episodes to {display_path}? (yes/no):") #confirming

          if confirm_download not in ["yes", "y", "Y", "YES"]: #check answer
               print("Download cancelled by user.")
               continue

          print("Starting download...")

          for episode in episodes_in_range:
               cleaned_title = clean_filename(episode['title'])  # clean title for filename
               filename = f"{cleaned_title}.mp3"  # create a filename with .mp3 extension

               filepath = os.path.join(download_folder, filename)  # create full file path

               print(f"Downloading: {filename} from {episode['url']}")  # Print download info
               try:
                    urllib.request.urlretrieve(episode['url'], filepath)
                    print(f"Downloaded: {filename}")
               except Exception as e:
                    print(f"Error downloading {filename} from {episode['url']}: {e}")

          print("\nDownload complete!") #completion message
          post_download_choice = input("Download complete. Enter 0 to Quit, or press Enter to return to the main menu: ")

          if post_download_choice == '0':
                print("Exiting program.")
                break #exit the main while loop 
          else: 
               print("Returning to main menu.")
               continue #return to start of main while loop
          
     elif choice == '3':

          if not episode_details:
               print("No episodes to list.")
               continue

          print(f"Okay, listing {len(episode_details)} episodes.")

          page_size = 15

          total_episodes = len(episode_details)
          total_pages = (total_episodes + page_size - 1) // page_size

          current_page = 0

          #display episodes for current page
          #show user what page theyre on
          #ask user what they want to do next (next page, previous page, choose select episodes to download, return to menu)

          #slice indices fun
          while True: 
               start_index = current_page * page_size #so first index is at p * page_size, cus p is current_page variable starting at 0
               end_index = start_index + page_size #the index after the last episode on the page is (p + 1) * page_size #end_index = min(start_index + page_size, total_episodes)

               episodes_on_page = episode_details[start_index:end_index]

               print("\n--- Episodes on this page ---")
               if not episodes_on_page: #should be redudant check
                    print(" (No episodes on this page - this shouldn't happen.)")
               else: #loop through the episodes for the current page

                    for index, episode in enumerate(episodes_on_page, start=start_index): #use enumerate starting from the overall index of the first item on this page

                         display_date = episode['date'].strftime("%Y-%m-%d") #format date for display

                         print(f"{index + 1}. {episode['title']} ({display_date})") #print the episode number (+1 cus we start from 1) plus title and date (maybe reformat to show day first?)
               
               print("-----------------\n")
               print(f"Page {current_page + 1} of {total_pages}")

               prompt_message = "Enter 'n' for next, 'p' for previous, 'q' to quit listing:"

               user_command = input(prompt_message).lower() #get input n convert to lower

               if user_command == 'q':
                    print("Returning to menu.")
                    break
               
               elif user_command == 'n':
                    if current_page < total_pages - 1: #if we are NOT on the last page, we increase page number
                         #change current page
                         current_page += 1
                    else: #if check was false, we ARE on last page
                         print("\nAlready on the last page.")

               elif user_command == 'p':
                    if current_page > 0: #check we're not on the first page, index 0
                         current_page -= 1 #if check is good, safe to decrease by 1
                    else:
                         print("\nAlready on first page.")

               else:
                    print("Not a valid command. Please use 'n' for next page, 'p' for previous page, or 'q' to quit to menu.")
