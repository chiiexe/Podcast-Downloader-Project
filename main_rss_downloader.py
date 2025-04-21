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

def clear_screen():
     """Clears the terminal screen. """
     if os.name == 'nt': #windows
          os.system('cls')
     else: #macOS and linux (os.name is 'posix')
          os.system('clear')

def select_download_folder():

     home_dir = os.path.expanduser('~')
     preferred_default = os.path.join(home_dir, 'Downloads')
     fallback_default = os.getcwd() #current directory

     default_folder_to_use = "" #variable to hold the actual default path
     default_display_message ="" #variable for the message shown in the prompt

     if os.path.isdir(preferred_default): #preferred path exists so use it
          default_folder_to_use = preferred_default
          abs_default_path = os.path.abspath(default_folder_to_use)
          default_display_message = f"{abs_default_path}"
     else:
          default_folder_to_use = fallback_default
          abs_default_path = os.path.abspath(default_folder_to_use)
          default_display_message = f"the current directory ({abs_default_path}) \n (Standard 'Downloads' folder not found)"

     while True:
          folder_prompt = (
               f"Enter the folder path where episodes should be saved. \n"
               f"Leave blank to use default: {default_display_message}\n"
               f"(Enter '0' to return to menu): "
          )

          download_folder_input = input(folder_prompt)

          if download_folder_input == '0':
               return None

          elif not download_folder_input:
               print(f"Using default folder: {os.path.abspath(default_folder_to_use)}")
               return os.path.abspath(default_folder_to_use)

          elif os.path.isdir(download_folder_input):
               print(f"Using specified folder: {os.path.abspath(download_folder_input)}")
               return os.path.abspath(download_folder_input)

          else:
               print(f"\nError: '{download_folder_input}' is not a valid directory path or command. Please try again. \n")

def download_episodes(episodes_to_download, target_folder):

     print("Starting download...")


     for episode in episodes_to_download:
          cleaned_title = clean_filename(episode['title'])  # clean title for filename
          filename = f"{cleaned_title}.mp3"  # create a filename with .mp3 extension

          filepath = os.path.join(target_folder, filename)  # create full file path

          print(f"Downloading: {filename} from {episode['url']}")  # Print download info
          try:
               urllib.request.urlretrieve(episode['url'], filepath)
               print(f"Downloaded: {filename}")
          except Exception as e:
               print(f"Error downloading {filename} from {episode['url']}: {e}")

     print("\nDownload complete!") #completion message

def process_single_feed():
     while True:

          rss_feed_url = input("Please enter the RSS feed URL (or type 'quit' to exit): ")

          if rss_feed_url.lower() == 'quit':
               print("Exiting program.")
               return False

          if not rss_feed_url:
               print("Error: URL cannot be empty. Please try again.")
          else:
               print(f"Fetching feed from: {rss_feed_url}")
               break

     rss_content = None
     try:

          response = requests.get(rss_feed_url, timeout=10) #in case of url timeouts
          response.raise_for_status()
          rss_content = response.text
          print("Feed fetched successfully.")

     except requests.exceptions.RequestException as e:
          print(f"Error fetching RSS feed: {e}")
          print("Unable to retrieve RSS feed. Please check the URL or try another.")
          input("Press enter to continue...")
          return True

     if rss_content:
          print("Parsing XML content...")

          try: #this is for parsing errors

               root = ET.fromstring(rss_content)
               podcast_title_element = root.find('channel/title')
               if podcast_title_element is not None:
                    podcast_title = podcast_title_element.text
               else:
                    podcast_title = "Podcast Title Not Found"

               items = root.findall('channel/item')

               episode_details = []
               skipped_count = 0
               date_format = "%a, %d %b %Y %H:%M:%S %z" #i think ill edit this later so its more flexible

               print(f"Found {len(items)} items. Processing episodes...")
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
                              skipped_count += 1


               print("Finished processing episodes.")
          except ET.ParseError as e_xml:
          #to handle errors from malformed XML
               print(f"Error parsing XML: {e_xml}")
               print("The RSS feed content might be invalid or not well-formed XML. Check the URL or try another.")
               input("Press enter to continue...")
               return True 

     else:
          print("No RSS content found. Cannot parse.")
          input("Press Enter to continue...")
          return True

     print(f"Podcast: {podcast_title}")
     print(f"Found {len(episode_details)} valid episodes.")



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

     if min_date and max_date:

          display_format = "%d-%m-%Y"

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
     3. List all episodes. (15 per page)
     4. Choose a different RSS feed.
     5. Exit.
     Enter your choice (1-5): """

     while True: #loops forever until break out
          clear_screen()
          print(f"Podcast: {podcast_title}")
          print(f"Total episodes: {len(episode_details)}")

          if 'start_date_str' in locals() and 'end_date_str' in locals() and start_date_str and end_date_str: # Check if defined and not None
               print(f"Date range: {start_date_str} to {end_date_str}")
          print("---") #separator

          choice = input(prompt) #choice inside loop

          if choice not in ['1', '2', '3', '4', '5']:
               print("Invalid input. Please choose a number between 1-5.")
               continue #loops if no correct input

          if choice == '1':
               print("Okay, preparing to download all episodes.")

               chosen_folder_path = select_download_folder()

               if chosen_folder_path is None:
                    print(f"Folder selection cancelled. Returning to main menu.")
                    continue

               confirm_all_download = input(f"Start download of {len(episode_details)} episodes to {chosen_folder_path}? (yes/no): ") #get confirm

               if confirm_all_download not in ["yes", "y", "Y", "YES"]: #check answer
                    print("Download cancelled by user.")
                    continue

               download_episodes(episode_details, chosen_folder_path)

               post_download_choice = input("Download complete. Enter 0 to Quit, or press Enter to return to the main menu: ")

               if post_download_choice == '0':
                    print("Exiting program.")
                    return False #exit the main while loop
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

               chosen_folder_path = select_download_folder()

               if chosen_folder_path is None:
                    print(f"Folder selection cancelled. Returning to main menu.")
                    continue

               range_confirmation = input(f"Found {len(episodes_in_range)} episodes between these dates. Choose these episodes? (yes/no): ")

               if range_confirmation not in ["yes", "y", "Y", "YES"]: #checking answer
                    print("Download cancelled by user.")
                    continue

               confirm_download = input(f"Start download of {len(episodes_in_range)} episodes to {chosen_folder_path}? (yes/no):") #confirming

               if confirm_download not in ["yes", "y", "Y", "YES"]: #check answer
                    print("Download cancelled by user.")
                    continue

               download_episodes(episodes_in_range, chosen_folder_path)

               post_download_choice = input("Download complete. Enter 0 to Quit, or press Enter to return to the main menu: ")

               if post_download_choice == '0':
                    print("Exiting program.")
                    return False #exit the main while loop
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

                    clear_screen()
                    print(f"Podcast: {podcast_title}")
                    print(f"Total episodes: {total_episodes} ({start_date_str} to {end_date_str})")
                    print("---") #separator

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

          elif choice == '4':
               # Break the inner menu loop to go back to the URL prompt loop
               break
          elif choice == '5':
               print("Exiting program.")
               return False
     
     return True


if __name__ == "__main__":
     while True:
          should_continue = process_single_feed()

          if not should_continue:
               break
          print("\n----------------------------------\n")

print("\nProgram finished.")


