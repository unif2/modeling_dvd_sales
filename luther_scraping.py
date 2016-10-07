from __future__ import print_function, division
import pandas as pd
import numpy as np
import requests
import matplotlib.pyplot as plt
from datetime import datetime
from bs4 import BeautifulSoup
from time import sleep
import pickle
import html5lib
import re
import sys

sys.setrecursionlimit(100000)

def get_genre_links(url='http://www.the-numbers.com/market/genres'):
    """ Returns a dictionary of Genre, Links of Movies pairs """
    base_url = 'http://www.the-numbers.com'
    soup = BeautifulSoup(requests.get(url).text, 'html5lib')
    table=soup.find('table')
    movies_by_genre_dict={}
    for link in table.find_all('a'):
        movies_by_genre_dict[link.text] = base_url + link.get('href').replace('market','movies')
    return movies_by_genre_dict

def get_movie_value(soup, field_name):
    '''Grab a value from the-numbers HTML
    
    Takes a string attribute of a movie on the page and
    returns the string in the next sibling object
    (the value for that attribute)
    or None if nothing is found.
    '''
    obj = soup.find(text=re.compile(field_name))
    if not obj: 
        return None
    # this works for most of the values
    next = obj.findNext()
    if next:
        return next.text 
    else:
        return None


def get_opening_weekend(url):
	"""
	Scrapes the Opening Weekend Data for each movie
	"""
	soup = BeautifulSoup(requests.get(url).text, 'html5lib')
	movie_list = soup.findAll('table')
	for table in movie_list:
		for row in table.findAll("tr"):
			x = row.find('a', href=re.compile('/box-office-chart/weekend/'))
			if x:
				y = x.findNext()
				if y:
					z = y.findNext()
					if z:
						return z.text
					else:
						return None
				else:
					return None


def get_more_movie_info(url):
	''' Extract the running time, production budget
	international box office, domestic DVD sales, and
	domestic Blu-ray sales from each movie in the list.
	Each movie has its own site which contains this info.'''
	soup = BeautifulSoup(requests.get(url).text, 'html5lib')
	x = soup.find('td', {"class" : "data sum"})
	if x:
		y = x.text
	else:
		y = None
	return get_movie_value(soup,'Running Time:'), get_movie_value(soup,'Production.Budget'), y, get_movie_value(soup,'Domestic DVD Sales'), get_movie_value(soup,'Domestic Blu-ray Sales')


def movie_scrape(genre,url,base_url = 'http://www.the-numbers.com'):
	""" We are going to scrape from a site that has a list of movies from a
	particular genre.  The information is in taburlar form.  You can click on each
	movie from this list to go to another site that has the Running Time, Budget, DVD Sales info
	etc.  We will scrape all this.
	"""
	base_url = 'http://www.the-numbers.com'
	movie_data=[]
	soup = BeautifulSoup(requests.get(url).text, 'html5lib')
	movie_list = soup.find('table')
	header = ['Movie', 'Release Date', 'Distributor', 'MPAA Rating', 'Domestic Gross', 'Inflation-Adjusted Gross']
    
    # The following for loop will extract the link URL for each movie in the list, where the other info is located
	movie_url_list = []
	movie_url_list2 = []
	for row in movie_list.findAll("tr"):
		all_td = row.findAll('td')
		if len(all_td)>0:
			cell = all_td[0]
			x = cell.find('a')
			if x: #movie_url = 
				movie_url_list.append(base_url + x['href'])
				t = x['href']
				y = t.replace('summary','box-office')
				movie_url_list2.append(base_url + y)
	i = 0
	for row in movie_list.findAll("tr"):
		row_dict={}  # Now we will loop through each row of the table to extract some info
		for j,cell in enumerate(row.findAll("td")):
			row_dict[header[j]]=cell.find(text=True)
		row_dict['Genre'] = genre
		sleep(0.1)
        # The following code scrapes the Running Time, Production Budget, International Box Office, DVD and Blu-ray sales info from each movie's own URL ('movie' as above)
		if i < len(movie_list.findAll("tr"))-1:
			row_dict['Running Time'], row_dict['Production Budget'], row_dict['International Box Office'], row_dict['Domestic DVD Sales'], row_dict['Domestic Blu-ray Sales'] = get_more_movie_info(movie_url_list[i-1])
			row_dict['Opening'] = get_opening_weekend(movie_url_list2[i-1])
		movie_data.append(row_dict)
		
		i += 1

	movies_df = pd.DataFrame(movie_data)
	movies_df.dropna()
	movies_df.drop(movies_df.index[[-1]], inplace=True)
	movies_df['Release Date'] = movies_df['Release Date'].astype('unicode')
	movies_df = movies_df[movies_df['Release Date'] != 'nan']

	movies_df['Release Date'] = movies_df['Release Date'].apply(lambda x: x.encode('ascii', 'ignore'))
	movies_df['Release Date'] = pd.to_datetime(movies_df['Release Date'], format = '%b%d,%Y')
	movies_df['Domestic Gross'] = movies_df['Domestic Gross'].apply(lambda x: int(x.replace('$', '').replace(',', '')))
	movies_df['Inflation-Adjusted Gross'] = movies_df['Inflation-Adjusted Gross'].apply(lambda x: int(x.replace('$', '').replace(',', '')))
	movies_df.to_pickle('results'+genre[:3]+'Opening2.pkl')
	sleep(0.1)


d = get_genre_links()

for k,v in d.iteritems():
	print("Scraping the " + k + " movies...")
	movie_scrape(k,v)