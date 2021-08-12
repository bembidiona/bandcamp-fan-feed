import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup

username = 'varicela'


# scrap main user page in search of his user_id
page = requests.get(f"https://bandcamp.com/{username}")
soup = BeautifulSoup(page.content, 'html.parser')
soup = soup.find(type="button") #rip it from a button's id... afortunately it is the first
user_id = soup["id"].split("_")[1] #example id="follow-unfollow_2083899"
# ---------------------------------------------------------------

print(f"username: {username}")
print(f"fan_id: {user_id}");

album_collection = []
artist_collection = []

# ---------------------------------------------------------------
# grab all artits that you are following and their /music pages
with requests.Session() as s:
	# suposuslly gets some cookies
    s.get(f'https://bandcamp.com/{username}/following/artists_and_labels')
    # ask for followeers (ask clicking the see more button)
    fancollection_response = s.post('https://bandcamp.com/api/fancollection/1/following_bands',
    								#HACK: older_than_token and count, so it gives all followeers with one request
               						json = {"fan_id":str(user_id),"older_than_token":"9999999999:9999999999","count":9999})
    # convert request to json thingy so it's easies to iterate
    fancollection_response = fancollection_response.json()
    # get all artists names and construct its page url
    for artist in fancollection_response["followeers"]:
    	artist_name = artist["name"]
    	subdomain = artist["url_hints"]["subdomain"]
    	artist_page = f"https://{subdomain}.bandcamp.com"    	
    	artist_collection.append([artist_name, artist_page]) 
# ---------------------------------------------------------------


def grab_release_date(album_page):
	page = requests.get(album_page)
	soup = BeautifulSoup(page.content, 'html.parser')
	release_date = soup.find('div', attrs={'class': 'tralbum-credits'})
	release_date = release_date.text.split("\n")
	
	for line in release_date:
		if "releases" in line:
			return None
		elif "released" in line:
			line = line.split("released ")[1]
			timediff = datetime.strptime(line, '%B %d, %Y') - datetime.strptime("January 1, 0001", '%B %d, %Y')
			return timediff.days
	return None

# ---------------------------------------------------------------
# Create a list with lastest album id of every artist and its release date
for i, artist in enumerate(artist_collection):

	freshness = 0

	if(i == 10):
		break
	# elif(i < 37):
	# 	continue

	print(f"PROCESSING {i+1} / {len(artist_collection)}")

	artist_name = artist[0]
	artist_page = artist[1]
	print(artist_page + "/music")
	page = requests.get(artist_page + "/music")
	soup = BeautifulSoup(page.content, 'html.parser')
	# soup = soup.find("data-item-id") #rip it from a button's id... afortunately it is the first
	music_grid = soup.find('ol', attrs={'id': 'music-grid'})

	if music_grid != None:
		# artist has multiple albums
		soup = music_grid.find('li')
		album_id = soup["data-item-id"].split("-")[1]
		# scrap and generate link to album
		soup = music_grid.find('a')
		album_href = soup["href"]
		if album_href[0] == "/":  # "/album/neverind"
			album_page = artist_page + soup["href"]
		else: #https://sethgraham.bandcamp.com/album/the-heart-pumps-kool-aid?label=2117584517&amp;tab=music
			album_page = album_href 
		# grab freshness if albums was release
		freshness = grab_release_date(album_page)
	else:
		# weird page
		soup = soup.find('meta', attrs={'name': 'bc-page-properties'})
		if soup == None:
			# does no have nothing published yet. example: https://abathy.bandcamp.com/music
			continue
		else:
			# artist has only one album
			soup = json.loads(soup["content"])
			album_id = soup["item_id"]
			# grab freshness if albums was release
			freshness = grab_release_date(artist_page)

	if freshness == None:
		#disc, still not fully released. only a demo, so not add to the collection
		pass
	else:
		print(f"freshness: {freshness}")
		album_collection.append([freshness, int(album_id)])
# ---------------------------------------------------------------

# ---------------------------------------------------------------
# Order album list so it start with the lastest releases (biggest freshnes)
album_collection.sort(reverse=True)
print(album_collection)

# ---------------------------------------------------------------

# ---------------------------------------------------------------
# create a html page with embeded player
generated_html = ""
for i, album in enumerate(album_collection):
	# only add the newstest 30
	if(i == 30): 
		break
	album_id = album[1]
	generated_html += f'<iframe style="border: 0; width: 350px; height: 470px;" src="https://bandcamp.com/EmbeddedPlayer/album={album_id}/size=large/bgcol=ffffff/linkcol=0687f5/tracklist=false/transparent=true/" seamless></iframe>\n'

Html_file= open("index.html","w")
Html_file.write(generated_html)
Html_file.close()
# ---------------------------------------------------------------

print(f"NUMBER OF FOLLOWEERS: {len(artist_collection)}")

