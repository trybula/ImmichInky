import requests
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
from inky.auto import auto
import random
import json
import sys
import os

def calculate_brightness(image, box):
    region = image.crop(box)
    grayscale = region.convert('L')
    histogram = grayscale.histogram()
    pixels = sum(histogram)
    brightness = scale = len(histogram)
    
    for index in range(scale):
        ratio = histogram[index] / pixels
        brightness += ratio * (index - brightness)

    return brightness


api_key = ''
base_url = 'https://'
person_ids = [""]
photos_ids = set([])

for person in person_ids:
    url = base_url + "/api/search/metadata"
    payload = {}
    headers = {
    'Content-Type': 'application/json',
    'x-api-key': api_key,
    'Accept': 'application/json'
    }
    payload = json.dumps({
    "personIds": [person]
    })

    response = requests.request("POST", url, headers=headers, data=payload)

    data = response.json()
    #pprint.pprint(data)
    items = data['assets']['items']
    for item in items:
        try:
            tmp = (item['id'],item['exifInfo']['city'],item['exifInfo']['country'])
        except (TypeError, KeyError) as e:
            tmp = (item['id'],"Somewhere Beautiful","")
            photos_ids.add(tmp)


selected_asset = random.choice(list(photos_ids))
selected_id = selected_asset[0]

url = base_url + "/api/assets/"+ selected_id +"/thumbnail?size=preview"
payload = {}
headers = {
  'Accept': 'application/octet-stream',
  'x-api-key': api_key
}
response = requests.request("GET", url, headers=headers, data=payload)


# Convert the byte stream to a BytesIO object
image_data = BytesIO(response.content)

# Open the image using Pillow
image = Image.open(image_data)

inky = auto(ask_user=True, verbose=True)
saturation = 0.5

rotated = False
if image.size[0] < image.size[1]: #rotate vertical
    image = image.transpose(Image.ROTATE_90)
    rotated = True
wpercent = (800 / float(image.size[0]))
hsize = int((float(image.size[1]) * float(wpercent))) 
image = image.resize((800, hsize), Image.Resampling.LANCZOS) #resize
if image.size[1] > 480: #crop
    croptop = (image.size[1]-480)/2
    image = image.crop((0, croptop, image.size[0], image.size[1]-croptop))
curr_path = os.path.dirname(os.path.abspath(__file__))
font = ImageFont.truetype(f"{curr_path}/FreeSans.ttf", 16)

text = " "+ selected_asset[1] + ", " + selected_asset[2] + " "

box = [font.getbbox(text, anchor = "la")[0] + font.getbbox(text, anchor = "la")[2], font.getbbox(text, anchor = "la")[1] + font.getbbox(text, anchor = "la")[3]]
img_txt = Image.new('L', box)
draw = ImageDraw.Draw(img_txt)
draw.text((0, 0),text,(255),font=font)
if rotated:
    rotated_text=img_txt.rotate(90,  expand=1)
    text_position = (image.size[0]-box[1], 0)
    text_box = (text_position[0], text_position[1], text_position[0] + box[1], text_position[1] + box[0])
else:
    rotated_text = img_txt
    text_position = (0, image.size[1]-box[1])
    text_box = (text_position[0], text_position[1], text_position[0] + box[0], text_position[1] + box[1])


brightness = calculate_brightness(image, text_box)
#print(text_box)
#print(brightness)
if brightness < 128:
    text_color = (255, 255, 255)  
else:
    text_color = (0, 0, 0)  
colored_text = ImageOps.colorize(rotated_text, (0, 0, 0), text_color)
image.paste(colored_text, text_position, rotated_text)
#image.show()
inky.set_image(image, saturation=saturation)
inky.show()
