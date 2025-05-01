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
root.geometry("900x600") #window size
root.config(bg="#ffd8e7") #bground colour pink :3

##style.theme_use('default') ##can i create themes?? 
style = ttk.Style()
style.element_create("Custom.Treeheading.border", "from", "default")
style.layout("Custom.Treeview.Heading", [
    ("Custom.Treeheading.cell", {'sticky': 'nswe'}),
    ("Custom.Treeheading.border", {'sticky':'nswe', 'children': [
        ("Custom.Treeheading.padding", {'sticky':'nswe', 'children': [
            ("Custom.Treeheading.image", {'side':'right', 'sticky':''}),
            ("Custom.Treeheading.text", {'sticky':'we'})
        ]})
    ]}),
])
style.configure("Custom.Treeview.Heading",
    background="#d0a6b9", 
    foreground="white", 
    relief="raised", 
    font=("Courier", 10))
style.map("Custom.Treeview.Heading",
    relief=[('active','groove'),('pressed','sunken')])



episode_details = []
download_queue = [] #list to hold the download queue
current_download_path = ""

###START OF CALLBACK FUNCTIONS###

def update_status(message):
    """updates the text of the status bar label."""
    status_label.config(text=message)
    root.update_idletasks() #force GUI update

#define callback function for the button click event, this is called then the button is pressed
def handle_fetch_click():
    feed_url = url_entry.get() #get text from entry widget
    if not feed_url:
        messagebox.showwarning("Input Error", "Please enter an RSS feed URL.") #check if the URL is empty and show a warning message
        return
    
    update_status(f"Attempting to fetch: {feed_url}...") #update status bar

    #clear previous results
    podcast_title_label.config(text="Podcast Title: Fetching...")
    episode_treeview.delete(*episode_treeview.get_children()) #this uses *, the unpacking operator, to pass all IDs obtained from get_children to the delete() function
    root.update_idletasks() #force GUI update to show "fetching..." message

    rss_content = None
    podcast_title = "Podcast Title Not Found" #default values 

    try: #essential to catch errors, especially when dealing with network requests
        
        response = requests.get(feed_url, timeout=10) #in case of url timeouts
        response.raise_for_status() #raise an error for bad responses but idek know how this deals with the error tbh shh 
        rss_content = response.text
        update_status("Feed fetched successfully. Parsing data.") 

    except requests.exceptions.RequestException as e: #for request errors like 404 or timeouts
        #handle fetching errors by showing message box, reset label, stop
        messagebox.showerror("Fetch error", f"Error fetching RSS feed:\n{e}\nPlease check the URL and try again.")
        podcast_title_label.config(text="Podcast Title: Error fetching feed")
        update_status("An error occurred while fetching the feed.")
        return #stop processing this click
    
    if rss_content: #parsing if fetch successful
        
        try:
            
            update_status("Feed fetched successfully. Parsing data...")
            #print("Parsing XML content...") #another print to console debug to be removed
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

            update_status(f"Finished processing episodes. Found: {len(episode_details)}, Skipped: {skipped_count}")

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
        for index, episode in enumerate(episode_details): #use enumerate to get both index and episode data
            
            title_text = episode['title'] #get title
            episode_date_obj = episode['date'] #get date object

            if episode_date_obj:
                display_date_str = episode_date_obj.strftime('%d.%m.%Y') #format date object into readable D:M:Y string
            else: 
                display_date_str = "Date N/A" #or unknown incase of parsing errors
            
            episode_treeview.insert(parent='', index=tk.END, iid=index, values=(title_text, display_date_str))
    
    else: #handle errors in case feed pasred okay but no valid episodes found
        update_status("Feed parsed, but no valid episodes found.")


def handle_select_folder_click():
    global current_download_path

    selected_path = ask_for_download_directory_gui() #call function that shows the dialog

    if selected_path:
        current_download_path = selected_path #update global variable

        #update the entry widget with selected path
        download_folder_entry.config(state='normal') #make editable
        download_folder_entry.delete(0, tk.END) #clear current text
        download_folder_entry.insert(0, current_download_path) #insert new path
        download_folder_entry.config(state='readonly') #make read only again
    else:
        messagebox.showinfo("No Selection", "No folder selected. Using default download location.")
        

def on_episode_select(event):
    """callback when selection changes in main episode list"""
    #check if anything selected in list
    if episode_treeview.selection(): #clear selection in queue list
        queue_treeview.selection_set(())

def on_queue_select(event):
    """callback when selection changes in queue list"""
    if queue_treeview.selection(): #clear selection in episode list
        episode_treeview.selection_set(())

def clear_all_selection_on_bg_click(event):
    """clears selections in both treeviews if click is on BACKGROUND widget""" #surely theres an easier way to do this?? 
    widget_clicked = event.widget

    background_widgets = {root, list_frame, selected_frame, url_frame, download_folder_frame}

    if widget_clicked in background_widgets:
        episode_treeview.selection_set(())
        queue_treeview.selection_set(())


def add_selected_to_queue(): #function to add selected episodes to the queue
    global episode_details #make sure we can access the global variable
    global download_queue #make sure we can access the global variable
    selected_indices = episode_treeview.selection() #get indices of selected items from episode_treeview

    if not selected_indices:
        update_status("No episodes selected.")
        return
    
    added_count = 0
    newly_added_queue_iids = []

    for index_str in selected_indices: #selection() returns strings, convert to int
        try:
            index= int(index_str)
            if 0 <= index < len(episode_details): #check index is valid
                episode_data = episode_details[index]
                selected_title = episode_data['title'] #get the title of the selected episode

                is_duplicate = False #check for duplicates in download_queue (based on URL)
                for item_in_queue in download_queue: #check if the item is already in the queue
                    if item_in_queue['url'] == episode_data['url']:
                        is_duplicate = True
                        break

                if not is_duplicate: #add to download queue list
                    download_queue.append(episode_data)
                    added_count += 1
                    new_queue_index = len(download_queue) - 1 #get the index of the newly added item in download_queue

                    episode_date_obj = episode_data['date'] #get date object
                    if episode_date_obj:
                        display_date_str = episode_date_obj.strftime('%d.%m.%Y') #format date object
                    else:
                        display_date_str = "Date N/A" #or unknown incase of parsing errors
                    
                    new_iid_str = str(new_queue_index)
                    queue_treeview.insert(parent='', #insert into queue_treeview using its index in download_queue as IID
                                          index=tk.END,
                                          iid=new_iid_str, #use string queue index as IID
                                          values=(selected_title, display_date_str))
                    
                    newly_added_queue_iids.append(new_iid_str)
                    
            else: 
                update_status(f"WARNING: Invalid index {index} encountered.") #this shouldnt happen, maybe pop error box and ask to retry 
        except ValueError:
            update_status(f"WARNING: Could not convert selected IID '{index_str}' to integer.") #shouldnt happpen either idk what id do to fix this rn its on the list

    if added_count > 0:
        update_status(f"Added {added_count} episode(s) to queue.")

        #temp unbind of selection remove events
        episode_treeview.unbind('<<TreeviewSelect>>')
        queue_treeview.unbind('<<TreeviewSelect>>')
        
        queue_treeview.selection_set(newly_added_queue_iids) #set selection in queue_treeview to the new IIDs items

        if newly_added_queue_iids:
            queue_treeview.see(newly_added_queue_iids[-1]) #scroll to last added item

        episode_treeview.bind('<<TreeviewSelect>>', on_episode_select)
        queue_treeview.bind('<<TreeviewSelect>>', on_queue_select)
    
    #episode.treeview.selection_set(()) - clear episodebox after adding?? 

                    

def remove_selected_from_queue():
	
    global download_queue
    
    selected_iids = queue_treeview.selection() #get selected IIDs (strings) from the queue_treeview

    ##sort string IIDs based on their integer value in reverse order (1,5,2 > 5,2,1)
    sorted_iids = sorted(selected_iids, key=int, reverse=True)

    if not selected_iids:
        update_status("No episodes selected to remove.")
        return
    
    removed_count = 0
    for iid_str in sorted_iids: #iterate through sorted (string) IIDs
        try: #convert string IID to integer index for list manipulation
            index = int(iid_str)
            
            if 0 <= index < len(download_queue): #delete from the download_queue list (using integer index)
                del download_queue[index]
                removed_count += 1
            else:
                update_status(f"WARNING: Invalid index {index} encountered. Unable to delete from queue - restart the program please.")

            queue_treeview.delete(iid_str) #delete from the queue_treeview

        except ValueError:
            update_status(f"WARNING: Could not convert selected IID '{iid_str}' to integer during removal.")
        except Exception as e:
            update_status(f"Error removing item with IID {iid_str}: {e}")

    if removed_count > 0:
        update_status(f"Removed {removed_count} episode(s) from queue.")
    else:
        update_status("Could not remove selected items from queue, unexcpected error.")
    

def clean_filename(title):
    """cleans a string into a pure lovely filename"""
    filename = title.replace(" ","_") #replace space with underscore
    filename = re.sub(r'[^a-zA-Z0-9_.-]','',filename) #removes chars not alphanumeric or underscore but keeps periods and hyphens
    return filename

def get_default_download_path():
    """determines the default download path (downloads or cwd)"""
    home_dir = os.path.expanduser('~') #get home dir
    preferred_default = os.path.join(home_dir, 'Downloads') #preferred default is the downloads folder in home dir
    if os.path.isdir(preferred_default): #check if the preferred default exists
        return preferred_default #return it if it does
    else: 
        fallback_default = os.getcwd()
        return fallback_default #otherwise return the current working directory

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
        initialdir=default_folder_to_use
    )
    #check result and return it
    if chosen_directory: #check if the user selected something (path is not empty or None)
        return chosen_directory #return selected path 
    else:
        return None #return None to indicate cancellation
    
def download_queued_episodes():

    global download_queue
    global current_download_path

    target_folder = current_download_path
    if not target_folder or not os.path.isdir(target_folder): 
        messagebox.showerror("Invalid Path", f"Download folder is not set or is invalid: \n{target_folder}")
        return #stop the function
    
    update_status(f"Starting download of {len(download_queue)} episodes to {target_folder}...")

    episodes_to_process = list(download_queue) #make a copy in case we modify queue later
    errors_occurred = False
    success_count = 0

    for episode in episodes_to_process:
        episode_url = episode['url']
        cleaned_title = clean_filename(episode['title'])
        filename = f"{cleaned_title}.mp3"
        filepath = os.path.join(target_folder, filename) #create full filepath

        update_status(f"Downloading: {filename}...") #update status for each file
        try:
            
            with requests.get(episode_url, stream=True, timeout=20) as response: #use stream=true for large files
                response.raise_for_status() #check if request was successful

                with open(filepath, 'wb') as f: #open file in binary write mode
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

            update_status(f"Downloaded: {filename}")
            success_count += 1

        
        except requests.exceptions.RequestException as e:
            update_status(f"FAILED (Network/HTTP Error): {filename} - {e}") #update on error
            errors_occurred = True
        except Exception as e:
            update_status(f"FAILED (File/Other Error): {filename} - {e}") #update on error
            errors_occurred = True

    #print("Download process finished.") #remove on debug (i did!)
    
    final_message= ""
    final_message = f"Finished. Downloaded {success_count}/{len(episodes_to_process)} episodes."
    if errors_occurred:
        final_message += " Some errors occurred."


    clear_queue_question = final_message + "\n\nWould you like to clear the download queue?" #add the question to the final_message
    should_clear = messagebox.askyesno("Download Complete", clear_queue_question) #show yes/no dialog

    if should_clear: #act based on user's choice, returns True is user clicked yes
        try:
            download_queue.clear() #clear data list#
            queue_treeview.delete(*queue_treeview.get_children()) #delete from the queue_treeview
            update_status("Queue cleared. Ready.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not clear the queue:\n{e}")
    else:
        update_status("Download finished. Ready.")
        

###END OF CALLBACK FUNCTIONS###
##https://feeds.megaphone.fm/thedavidfrumshow

#create button to clear queue under rigth listbox/frame + add all to queue button for the episode_treeview
#add URL fixing so it affixes https or http to the link if not provided?
#start working on multi processes so it can download multiple at once? 

###START OF WIDGETS N SHIT###
#url input area
url_frame = tk.Frame(root, bg="#ffd8e7") #use frame to group URL label and entry. we use frames to group widgets together, which helps with layout when using .pack() or .grid()
url_label = tk.Label(url_frame, text = "Enter RSS URL:", font=("Courier", 10), bg="#FFFFFF")
url_entry = tk.Entry(url_frame, width=50, relief=tk.SUNKEN, bg="#d0a6b9", fg="white", font=("Courier", 10))
fetch_button = tk.Button(url_frame, text="Fetch Feed", bg="#d0a6b9", fg="white", font=("Courier", 8), command=handle_fetch_click) #command set now to handlefetch

url_label.grid(row=0, column=0, padx=5, pady=5) #start of our switch to .grid() 
url_entry.grid(row=0, column=1, padx=5, pady=5)
fetch_button.grid(row=0, column=2, padx=5, pady=5)
url_frame.grid(row=0, column=0, columnspan=2, sticky="ew") #grid

#podcast title display
podcast_title_label = tk.Label(root, text="Podcast Title: ---", font=("Courier", 12, "bold"), bg="#FFFFFF") ##shows title and default until feed fetched
podcast_title_label.grid(row=1, column=0, columnspan=2, sticky="ew")

##CREATE list_frame and episode_treeview##
list_frame = tk.Frame(root) #frame to hold treeview and scrollbar
scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL) #standard scrollbar going vertical
episode_treeview = ttk.Treeview(list_frame,
                                style="Custom.Treeview",
                                columns=('title', 'date'), 
                                yscrollcommand=scrollbar.set,
                                selectmode='extended',
                                )
episode_treeview.focus_set()
addqueue_button = tk.Button(list_frame, text="Add to Queue", font=("Courier", 8), command=add_selected_to_queue) 

episode_treeview.column('#0', width=0, stretch=tk.NO) #treeview columns
episode_treeview.heading('#0', text='')

episode_treeview.column('title', anchor=tk.W, width=250) #left aligned
episode_treeview.heading('title', text='Episode Title', anchor=tk.W)

episode_treeview.column('date', anchor=tk.W, width=150) #left aligned
episode_treeview.heading('date', text='Published Date', anchor=tk.W)

scrollbar.config(command=episode_treeview.yview) #tells the scrollbar to scroll the treeview when moved

##PLACE list_frame and episode_treeview##
list_frame.grid(row=3, column=0, sticky="nsew", padx=5, pady=5)
episode_treeview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
scrollbar.grid(row=0, column=1, sticky="ns") 
addqueue_button.grid(row=1, column=0, columnspan=2, pady=(5, 5), padx=5) #grid the button below the listbox

episode_treeview.bind('<<TreeviewSelect>>', on_episode_select) ##remove selection event


##CREATE selected_frame and queue_treeview##

selected_frame=tk.Frame(root)
selected_scrollbar=tk.Scrollbar(selected_frame, orient=tk.VERTICAL)
queue_treeview = ttk.Treeview(selected_frame,
                                style="Custom.Treeview",
                                columns=('title', 'date'), 
                                yscrollcommand=selected_scrollbar.set,
                                selectmode='extended',
                                )
queue_treeview.focus_set()
removequeue_button = tk.Button(selected_frame, text="Remove from Queue", font=("Courier", 8), command=remove_selected_from_queue) #button to remove episodes from queue

queue_treeview.column('#0', width=0, stretch=tk.NO) #treeview columns
queue_treeview.heading('#0', text='')

queue_treeview.column('title', anchor=tk.W, width=250) #left aligned
queue_treeview.heading('title', text='Episode Title', anchor=tk.W)

queue_treeview.column('date', anchor=tk.W, width=150) #left aligned
queue_treeview.heading('date', text='Published Date', anchor=tk.W)

selected_scrollbar.config(command=queue_treeview.yview) #tells the scrollbar to scroll the treeview when moved

##PLACE selected_frame and queue_treeview##

selected_frame.grid(row=3, column=1, sticky="nsew", padx=5, pady=5) 
queue_treeview.grid(row=0, column=0, sticky="nsew", padx=5, pady=5) #grid the listbox in the selected frame
selected_scrollbar.grid(row=0, column=1, sticky="ns")
removequeue_button.grid(row=1, column=0, columnspan=2, pady=(5, 5), padx=5) 

queue_treeview.bind('<<TreeviewSelect>>', on_queue_select) ##remove selection event


#using the function to get the default download path
current_download_path = get_default_download_path() #get the default download path

#make a frame for the download folder and button widgets
download_folder_frame = tk.Frame(root, bg="#ffd8e7") #main frame
download_folder_label = tk.Label(download_folder_frame, text="Download Folder:", font=("Courier", 10), bg="#FFFFFF") #label for the folder path

#create entry widget
download_folder_entry = tk.Entry(download_folder_frame, width=50, relief=tk.SUNKEN) #may need to adjust width 
download_folder_entry.insert(0, current_download_path) #insert the path we just got into entry box
download_folder_entry.config(state='readonly') #make it readonly so the user can't edit it 

#create button
select_folder_button = tk.Button(download_folder_frame, text ="Select Folder", command=handle_select_folder_click, font=("Courier", 8)) 

#layout for widgets INSIDE download folder frame
download_folder_label.grid(row=0, column=0, padx=5, pady=5, sticky='w') #label on left
download_folder_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew') #entry expands
select_folder_button.grid(row=0, column=2, padx=5, pady=5) #button on right

download_folder_frame.grid_columnconfigure(1, weight=1) #allows the entry to expand with the window

download_folder_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 5)) #place the frame in the main window

#creating the download button
download_button = tk.Button(root, text="Download Queued Episodes", command=download_queued_episodes, font=("Courier", 8)) #command set later
download_button.grid(row=5, column=0, columnspan=2, pady=(5, 10)) #place the button in root grid

#creating status widget
status_label = tk.Label(root, text="Ready.", bd=1, relief=tk.SUNKEN, font=("Courier", 8), bg="#FFFFFF", anchor=tk.E) 
status_label.grid(row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 5))

list_frame.grid_rowconfigure(0, weight=1) #allows the listbox to expand with the window
list_frame.grid_columnconfigure(0, weight=1) #allows the scrollbar to expand with the window
selected_frame.grid_rowconfigure(0, weight=1)
selected_frame.grid_columnconfigure(0, weight=1) 

root.grid_rowconfigure(3, weight=1) #allows the list frame to expand with the window
root.grid_columnconfigure(0, weight=1) #allows the URL frame to expand with the window
root.grid_columnconfigure(1, weight=1) #allows selected_frame to expand with the window

        
#assign the callback function to the button click event
#addqueue_button.config(command=add_selected_to_queue) 
#download_button.config(command=download_queued_episodes)

root.bind('<Button-1>', clear_all_selection_on_bg_click)


#start GUI event loop
root.mainloop()
