import aiohttp
import asyncio
import os
import re
import numpy as np
from cv2 import cv2
from dotenv import load_dotenv
from fuzzywuzzy import fuzz, process

load_dotenv()
API_KEY = '0a7f0178f488957'

choices = ['HP', 'DEF', 'SPD', 'Status ACC', 'ATK', 'CRIT DMG', 'Critical', 'Status RES']

reg = re.compile(r'\d+(?:\.\d+)?')
hp_reg = re.compile(r'\d,\d{3}')

min_mains = {'HP': 611.0, 'ATK': 125.0, 'DEF': 70, 'ATK%': 10.0, 'Status ACC%':10.0, 'Status RES%':10.0,
			 'SPD': 7.0, 'Critical%': 9.0, 'CRIT DMG%': 11.0, 
			 'HP%': 10.0, 'DEF%': 10.0, }
max_mains = {'HP': 3055, 'ATK': 625.0, 'DEF': 350, 'ATK%': 50.0, 'Status ACC%':50.0, 'Status RES%':50.0,
			 'SPD': 35.0, 'Critical%': 45.0, 'CRIT DMG%': 	55.0, 
			 'HP%': 50.0, 'DEF%': 50.0, }
max_subs = {'ATK': 232.0, 'SPD': 16.0, 'ATK%': 27.0, 'Status ACC%':27.0, 'Status RES%':27.0,
			'Critical%': 16.0, 'CRIT DMG%': 25.0, 'DEF': 171.0, 'HP': 1021.0, 'DEF%': 27.0, 'HP%': 27.0}
weights = {'HP': 0, 'ATK': 0.5, 'ATK%': 1,  'Status ACC%':0, 'Status RES%':0,
		   'SPD': 1, 'Critical%': 1, 'CRIT DMG%': 1,
		   'HP%': 0, 'DEF%': 0, 'DEF': 0, }

async def ocr(url):
	async with aiohttp.ClientSession() as session:
		async with session.get(url) as r:
			size = int(r.headers['Content-length'])
			if size > 1e6:
				img = np.asarray(bytearray(await r.read()), dtype="uint8")
				flag = cv2.IMREAD_GRAYSCALE
				if size > 2e6:
					flag = cv2.IMREAD_REDUCED_GRAYSCALE_2
				img = cv2.imdecode(img, flag)
				_, img = cv2.imencode(os.path.splitext(url)[1], img)
				data = aiohttp.FormData()
				data.add_field('apikey', API_KEY)
				data.add_field('OCREngine', '2')
				data.add_field('file', img.tobytes(), content_type='image/png', filename='image.png')
				ocr_url = 'https://api.ocr.space/parse/image'
				async with session.post(ocr_url, data=data) as r:
					json = await r.json()
			else:
				ocr_url = f'https://api.ocr.space/parse/imageurl?apikey={API_KEY}&OCREngine=2&url={url}'
				async with session.get(ocr_url) as r:
					json = await r.json()
			print(json)
			if json['OCRExitCode'] != 1:
				return False, '.'.join(json['ErrorMessage'])
			return True, json['ParsedResults'][0]['ParsedText']

def parse(text):
	# print(text)
	stat = None
	results = []
	for line in text.splitlines():
		if not line or line.lower() == 'in':
			continue
		line = line.replace(':','.').replace('-','').replace('0/0','%').replace('SPO','SPD')
		# print(line, fuzz.partial_ratio(line, 'Piece Set'))
		if fuzz.partial_ratio(line, 'Piece Set') > 80 and len(line) > 4:
			break
		value = hp_reg.search(line)
		if value:
			print(line)
			value = int(value[0].replace(',', ''))
			results += [['HP', value]]
			stat = None
			continue
		# print(line)
		extract = process.extractOne(line, choices, scorer=fuzz.partial_ratio)
		# print(process.extract(line, choices, scorer=fuzz.partial_ratio))
		if ((extract[1] > 80) and len(line) > 1) or stat:
			print(line)
			if (extract[1] > 80):
				stat = extract[0]
			line = line.replace(',','')
			value = reg.findall(line)
			if not value:
				continue
			value = max(value, key=len)
			if len(value) < 2:
				continue
			if line.find('%', line.find(value)) != -1 and '.' not in value:
				value = value[:-1] + '.' + value[-1]
			if '%' in line:
				stat += '%'
			value = float(value)
			results += [[stat, value]]
			stat = None
			if len(results) == 5:
				break
	return results

def rate(results, options={}):
	main = True
	main_score = 0.0
	sub_score = 0.0
	sub_weight = 0
	main_weight = 8
	level = 15
	if 'Level' in options:
		level = int(options['Level'])
		main_weight -= (5 - level / 3)
		del options['Level']
	# Replaces weights with options
	custom_weights = {**weights, **options}
	for result in results:
		key, value = result
		if main:
			main = False
			max_main = max_mains[key] - (max_mains[key] - min_mains[key]) * (1 - level / 15.0)
			main_score = value / max_main * custom_weights[key] * main_weight
			if key in ['ATK', 'HP', 'DEF']:
				main_weight *= custom_weights[key]
			count = 0
			for k,v in sorted(custom_weights.items(), reverse=True, key=lambda item: item[1]):
				if k == key or k not in max_subs:
					continue
				if count == 0:
					sub_weight += v * (1 + level / 4)
				else:
					sub_weight += v
				count += 1
				if count == 4:
					break
		else:
			sub_score += value / max_subs[key] * custom_weights[key]
		result[1] = value
		print(result)
	score = (main_score + sub_score) / (main_weight + sub_weight) * 100 if main_weight + sub_weight > 0 else 100
	main_score = main_score / main_weight * 100 if main_weight > 0 else 100
	main_score = 100 if main_score > 99 else main_score
	sub_score = sub_score / sub_weight * 100 if sub_weight > 0 else 100
	print(f'Artifact Score: {score:.2f}% (main {main_score:.2f}% {main_weight}, sub {sub_score:.2f}% {sub_weight})')
	return score, main_score, sub_score

if __name__ == '__main__':
	url = 'https://media.discordapp.net/attachments/550687426440462356/1034174488427892896/unknown.png'
	suc, text = asyncio.run(ocr(url))
	print(text)
	if suc:
		results = parse(text)
		rate(results, {'Level': 0})
