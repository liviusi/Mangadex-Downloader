#!/usr/bin/env python3

import os, json, time, shutil, requests, argparse
from fpdf import FPDF
from PIL import Image

URL = "https://api.mangadex.org/"

def floatify(elem):
	x = 0
	try:
		x = float(elem[0])
	finally:
		return x

# ID is Manga ID
def get_title(ID, lang):
	r = requests.get(URL + "manga/{}".format(ID))
	json_r = r.json()
	try:
		title = json_r["data"]["attributes"]["title"][lang]
		return title
	except KeyError:
		print("ID {} is not valid.".format(ID))
		exit(1)

# ID is Manga ID
def get_chapters(ID, lang):
	BASE = URL + "manga/{}/feed?".format(ID)
	chapter_list = []
	r = requests.get(BASE, { 'limit': '0', 'translatedLanguage[]': lang })
	try:
		total = r.json()["total"]
	except KeyError:
		print("Could not get chapters for {}.".format(ID))
		exit(1)
	if (total == 0):
		print("No chapters are available for {}.".format(ID))
		return chapter_list
	# no more than 500 chapters can be loaded at a time
	offset = 0
	at_most = 500
	while offset < total:
		r = requests.get(BASE, { 'order[chapter]': 'asc', 'order[volume]': 'asc', 'limit': str(at_most), 'translatedLanguage[]': lang, 'offset': str(offset) })
		chapters = r.json()["results"]
		for chapter in chapters:
			chapter_number = chapter["data"]["attributes"]["chapter"] # chapter number
			chapter_id = chapter["data"]["id"] # chapter unique id
			chapter_title = chapter["data"]["attributes"]["title"] # chapter title
			if chapter_number == None:
				chapter_list.append(("ONESHOT", chapter_title, chapter_id))
			else:
				chapter_list.append((chapter_number, chapter_title, chapter_id))
		offset += 500
	return chapter_list

# ID is Chapter ID
def get_chapnum(ID):
	r = requests.get(URL + "chapter/{}".format(ID))
	chapter = json.loads(r.text) # chapter data
	return chapter["data"]["attributes"]["chapter"]

# ID is Chapter ID
def get_images(ID, mode):
	r = requests.get(URL + "chapter/{}".format(ID))
	chapter = json.loads(r.text) # chapter data
	r = requests.get(URL + "at-home/server/{}".format(ID))
	try:
		base = r.json()["baseUrl"] # used to retrieve pages
	except KeyError:
		print("Server could not be found for chapter {}.".format(ID))
		exit(1)
	# now urls can be computed
	images = []
	hash = chapter["data"]["attributes"]["hash"]
	for p in chapter["data"]["attributes"][mode]: # pages' filename
			images.append("{}/{}/{}/{}".format(base, mode, hash, p))
	return images

def download_chapter(ID, mode="data", lang="en"):
	images = get_images(ID, mode)
	num = get_chapnum(ID)
	dest_directory = os.path.join(os.getcwd(), num)
	if not os.path.exists(dest_directory):
		os.makedirs(dest_directory)
	for page_number, image in enumerate(images, 1):
		name = str(page_number) + ".png"
		dest_filename = os.path.join(dest_directory, name)
		r = requests.get(image)
		success = False
		while not success:
			if r.status_code != 200:
				time.sleep(2)
				print("Failure downloading page no.{}.".format(page_number))
			else:
				success = True
				with open(dest_filename, 'wb') as f:
					f.write(r.content)
					print("Page no.{} downloaded successfully.".format(page_number))
					f.close()
		time.sleep(0.5)
	print("Chapter downloaded successfully.")

def download_manga(ID, mode="data", lang="en"):
	title = get_title(ID, lang)
	chapters = get_chapters(ID, lang)
	for c in chapters:
		num = c[0]
		manga_ID = c[2]
		images = get_images(manga_ID, mode)
		dest_directory = os.path.join(os.getcwd(), title, num)
		if not os.path.exists(dest_directory):
			os.makedirs(dest_directory)
		elif os.listdir(dest_directory): # chapter has already been downloaded
			continue
		for page_number, image in enumerate(images, 1):
			name = str(page_number) + ".png"
			dest_filename = os.path.join(dest_directory, name)
			r = requests.get(image)
			success = False
			while not success:
				if r.status_code != 200:
					time.sleep(2)
					print("[CHAPTER {}] Failure downloading page no.{}.".format(num, page_number))
				else:
					success = True
					with open(dest_filename, 'wb') as f:
						f.write(r.content)
						print("[CHAPTER {}] Page no.{} downloaded successfully.".format(num, page_number))
						f.close()
			tmp = Image.open(dest_filename)
			tmp.save(dest_filename, "PNG")
			time.sleep(0.5)
		print("Chapter {} downloaded successfully.".format(num))
		pdf = FPDF()
		for image in sorted(os.listdir("{}".format(dest_directory, num))):
			pdf.add_page()
			pdf.image("{}/{}".format(dest_directory, image), 0, 0, 210, 297) # A4 format
		pdf.output("{}.pdf".format(dest_directory))
		print("Chapter {} assembled successfully. Cleaning up...".format(num))
		shutil.rmtree(dest_directory)
	print("Manga downloaded successfully.")

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-l", dest="lang", required=False, action="store",
						help="download in specified language code (default: en)", default="en")
	parser.add_argument("-d", dest="datasaver", required=False, action="store_true",
						help="downloads images in lower quality")
	args = parser.parse_args()

	lang = "en" if args.lang is None else str(args.lang)
	mode = args.datasaver if args.datasaver == "datasaver" else "data"

	ID = ""
	while True:
		req = input("Enter m to download a whole manga, c for a single chapter, q to quit. ")
		if req == "q":
			break
		elif req == "m" or "q":
			ID = input("Enter the ID. ")
			if req == "m":
				print("Title: {}".format(get_title(ID, lang)))
				download_manga(ID, mode, lang)
			else:
				download_chapter(ID, mode, lang)
		else:
			print("Not a valid command has been passed. Now quitting.")
			break

if __name__ == "__main__":
	main()
