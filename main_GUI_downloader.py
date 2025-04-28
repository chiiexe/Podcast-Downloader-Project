import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

import requests
import xml.etree.ElementTree as ET
import datetime #needed for parsing within the episode loop even if not displayed rn 
import re #needed to clean filename later
import os #needed for path operations later

root = tk.Tk()
root.title("Podcast Downloader") #give window a title
#root.geometry("600x400") #window size
root.config(bg="#E5B5DD") #bground colour pink :3

episode_details = []
download_queue = [] #list to hold the download queue

#define callback function for the button click event, this is called then the button is pressed

def handle_fetch_click():
    feed_url = url_entry.get() #get text from entry widget
    if not feed_url:
        messagebox.showwarning("Input Error", "Please enter an RSS feed URL.") #check if the URL is empty and show a warning message
        return
    
    print(f"Attempting to fetch: {feed_url}") #print to console for debugging

    #this is where we add the actual code for fetching, parsing, and the GUI update logic
    #clear previous results
    podcast_title_label.config(text="Podcast Title: Fetching...")
    episode_listbox.delete(0, tk.END) #clear the listbox before adding new data (from index 0 to the end)
    root.update_idletasks() #force GUI update to show "fetching..." message

    rss_content = None
    podcast_title = "Podcast Title Not Found" #default values 

    try: #essential to catch errors, especially when dealing with network requests
        
        response = requests.get(feed_url, timeout=10) #in case of url timeouts
        response.raise_for_status() #raise an error for bad responses but idek know how this deals with the error tbh shh 
        rss_content = response.text
        print("Feed fetched successfully.") #print to console for debug, remove later

    except requests.exceptions.RequestException as e: #for request errors like 404 or timeouts
        #handle fetching errors by showing message box, reset label, stop
        messagebox.showerror("Fetch error", f"Error fetching RSS feed:\n{e}\nPlease check the URL and try again.")
        podcast_title_label.config(text="Podcast Title: Error fetching feed")
        return #stop processing this click
    
    if rss_content: #parsing if fetch successful
        
        try:
            print("Parsing XML content...") #another print to console debug to be removed
            root_xml = ET.fromstring(rss_content) #use a different variable name than the tkinter root to avoid confusion
            title_element = root_xml.find('channel/title') #extract podcast title like in my previous code definitely not copy n paste
            if title_element is not None and title_element.text:
                podcast_title = title_element.text
            else:
                podcast_title = "Podcast Title Not Found in Feed." #more specific default

            
            items = root_xml.findall('channel/item')
            skipped_count = 0 
            date_format = "%a, %d %b %Y %H:%M:%S %z" #still need to edit this to be more flexible and accpt different formats, but this is a start

            global episode_details #ake this accessible outside the function
            episode_details = [] #reset the list of episodes for each fetch

            for item in items:
                title_el = item.find('title')
                enclosure_el = item.find('enclosure')
                pub_date_el = item.find('pubDate')

                if title_el is not None and enclosure_el is not None and pub_date_el is not None:

                    title_text = title_el.text if title_el.text else "Untitled Episode" #fill in a default if no title is found
                    
                    mp3_url = enclosure_el.get('url')
                    pub_text = pub_date_el.text

                    if not mp3_url: #skip if enclosure URL is missing cus then theres nothing to download obviously silly
                        skipped_count += 1
                        continue

                    try: #we parse the date still to keep structure and we'll use it later
                        parsed_date = datetime.datetime.strptime(pub_text, date_format)
                    except (ValueError, TypeError): #handle date errors better
                        parsed_date = None #or datetime.datetime.min maybe or .now() ? 
                        skipped_count += 1 #increment skipped count if we can't parse the date
                    
                    episode_data = {
                        'title': title_text, 
                        'url': mp3_url,
                        'date': parsed_date
                    }
                    episode_details.append(episode_data) #append the episode data to the list
                else:
                    skipped_count += 1 #count items missing tags

            print(f"Finished processing episodes. Found: {len(episode_details)}, Skipped: {skipped_count}")

        except ET.ParseError as e_xml: #handle xml parsing errors eugh why dont programs just do this themselves dummies
            messagebox.showerror("Parse error", f"Error parsing XML content:\n{e_xml}\nPlease check the feed format.")
            podcast_title_label.config(text="Podcast Title: Error parsing feed")
            return
        except Exception as e_generic: #catch any other unexpected errors
            messagebox.showerror("Error", f"An unexcpected error occurred:\n{e_generic}")
            podcast_title_label.config(text="Podcast Title: Error")
            return
        
    else: #this case shouldnt happen cus of the raise_for_status() but just in case
        messagebox.showwarning("Warning", "Feed fetched successfully, but content was empty.")
        podcast_title_label.config(text="Podcast Title: Feed content empty")
        return
    
    #we update the GUI with parsed data here
    podcast_title_label.config(text=f"Podcast Title: {podcast_title}")

    if episode_details: #if we have episodes, we can display them
        for episode in episode_details: #add episode title to listbox
            episode_listbox.insert(tk.END, episode['title'])
    
    else: #handle errors in case feed pasred okay but no valid episodes found
        episode_listbox.insert(tk.END, "(No valid episodes found.)")

def add_selected_to_queue(): #function to add selected episodes to the queue
    global episode_details #make sure we can access the global variable
    global download_queue #make sure we can access the global variable
    selected_indices = episode_listbox.curselection() #get indices of selected items from episode_listbox


    for index in selected_indices: #loop through selected indices cus it could be multiple
        episode_data = episode_details[index]
        selected_title = episode_data['title'] #get the title of the selected episode

        is_duplicate = False

        for item_in_queue in download_queue: #check if the item is already in the queue
            if item_in_queue['url'] == episode_data['url']:
                is_duplicate = True
                break

        if not is_duplicate:
                download_queue.append(episode_data)
                queue_listbox.insert(tk.END, selected_title) #add title to other listbox

def remove_selected_from_queue():
    
	global download_queue
	
	selected_indices = queue_listbox.curselection()
	sorted_indices = sorted(selected_indices, reverse=True) #sort in reverse order to avoid index issues when deleting

	for index in sorted_indices: #loop in reverse 
		del download_queue[index] #remove from queue list
		queue_listbox.delete(index) #remove from listbox
        
def clean_filename(title):
    """cleans a string into a pure lovely filename"""
    filename = title.replace(" ","_") #replace space with underscore
    filename = re.sub(r'[^a-zA-Z0-9_.-]','',filename) #removes chars not alphanumeric or underscore but keeps periods and hyphens
    return filename

def ask_for_download_directory_gui():
    """opens a file dialog to select download directory"""
    home_dir = os.path.expanduser('~') #get home directory
    preferred_default = os.path.join(home_dir, 'Downloads')
    fallback_default = os.getcwd() #get current working directory as fallback

    default_folder_to_use = "" #variable to hold actual default path

    if os.path.isdir(preferred_default): 
        default_folder_to_use = preferred_default
    else:
        default_folder_to_use = fallback_default 
    
    chosen_directory = filedialog.askdirectory(
        title="Select Download Folder", #title for dialog window
        intialdir=default_folder_to_use
    )
    #check result and return it
    if chosen_directory: #check if the user selected something (path is not empty or None)
        return chosen_directory #return selected path 
    else:
        return None #return None to indicate cancellation


#url input area
url_frame = tk.Frame(root, bg="#E5B5DD") #use frame to group URL label and entry. we use frames to group widgets together, which helps with layout when using .pack() or .grid()
url_label = tk.Label(url_frame, text = "Enter RSS URL:", font=("Courier", 10), bg="#FFFFFF")
url_entry = tk.Entry(url_frame, width=50)
fetch_button = tk.Button(url_frame, text="Fetch Feed", font=("Courier, 8"), command=None) #command set later

url_label.grid(row=0, column=0, padx=5, pady=5) #start of our switch to .grid() 
url_entry.grid(row=0, column=1, padx=5, pady=5)
fetch_button.grid(row=0, column=2, padx=5, pady=5)
url_frame.grid(row=0, column=0, sticky="ew") #grid

#podcast title display
podcast_title_label = tk.Label(root, text="Podcast Title: ---", font=("Courier", 12), bg="#FFFFFF") ##shows title and default until feed fetched
podcast_title_label.grid(row=1, column=0, columnspan=2, sticky="ew")

#episode list area

list_frame = tk.Frame(root) #frame to hold listbox and scrollbar
scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL) #standard scrollbar, vertical makes it go well, vertically
episode_listbox = tk.Listbox(list_frame, height=15, width=70, selectmode='EXTENDED', #main list display, heigh suggests how many lines to show initially, width is the number of characters per line
yscrollcommand=scrollbar.set)
addqueue_button = tk.Button(list_frame, text="Add to Queue", command=add_selected_to_queue) #command needs to be set later

#configure scrollbar to scroll listbox
scrollbar.config(command=episode_listbox.yview) #tells the scrollbar to scroll the listbox when moved

scrollbar.grid(row=0, column=1, sticky="ns") 
episode_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
list_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
addqueue_button.grid(row=1, column=0, columnspan=2, pady=(5, 5), padx=5) #grid the button below the listbox

##trying to create a frame to the right of the listbox to show selected episodes in the queue

selected_frame = tk.Frame(root) #frame to hold selected episode info
selected_scrollbar = tk.Scrollbar(selected_frame, orient=tk.VERTICAL) #scrollbar for the selected episodes listbox
queue_listbox = tk.Listbox(selected_frame, height=15, width=70, selectmode='EXTENDED',
yscrollcommand=selected_scrollbar.set) #listbox to show downloaded episodes
removequeue_button = tk.Button(selected_frame, text="Remove from Queue", command=remove_selected_from_queue) #button to remove episodes from queue

selected_frame.grid(row=2, column=1, sticky="nsew", padx=5, pady=5) 
queue_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5) #grid the listbox in the selected frame
removequeue_button.grid(row=1, column=0, columnspan=2, pady=(5, 5), padx=5) 

selected_scrollbar.config(command=queue_listbox.yview) #stuff for the selected scrollbar scroll to work hehe
selected_scrollbar.grid(row=0, column=1, sticky="ns")



list_frame.grid_rowconfigure(0, weight=1) #allows the listbox to expand with the window
list_frame.grid_columnconfigure(0, weight=1) #allows the scrollbar to expand with the window
selected_frame.grid_rowconfigure(0, weight=1)
selected_frame.grid_columnconfigure(0, weight=1) 

root.grid_rowconfigure(2, weight=1) #allows the list frame to expand with the window
root.grid_columnconfigure(0, weight=1) #allows the URL frame to expand with the window
root.grid_columnconfigure(1, weight=1) #allows selected_frame to expand with the window

        
#assign the callback function to the button click event
fetch_button.config(command=handle_fetch_click)
addqueue_button.config(command=add_selected_to_queue) 

#start GUI event loop
root.mainloop()
