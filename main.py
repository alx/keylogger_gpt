import os
import base64
import shutil
import json
from datetime import datetime
from PIL import Image
from openai import OpenAI, OpenAIError
import pyperclip

# Define paths and constants
inbox_path = '/home/alx/org/inbox/screenshots/'
outbox_path = '/home/alx/org/outbox/screenshots/'
output_file = '/home/alx/org/inbox_screenshots.org'

API_KEY='sk-...'
client = OpenAI(api_key=API_KEY)

# top status bar and bottom status bar heigh size in pixel
# it will be cropped from screenshot
status_height_top = 60
status_height_bottom = 26

# resize image to lower resolution
thumbnail_size = (800, 450)

def extract_json_from_image(image_path, prompt):
    try:
        im = Image.open(image_path)
        # Size of the image in pixels (size of original image)
        # (This is not mandatory)
        width, height = im.size

        # Setting the points for cropped image
        left = 0
        top = status_height_top
        right = width
        bottom = height - status_height_bottom

        # Cropped image of above dimension
        # (It will not change original image)
        im1 = im.crop((left, top, right, bottom))
        im1.thumbnail(thumbnail_size)
        im1.save(image_path, 'png')
 
        with open(image_path, 'rb') as image_file:
            img_b64_str = base64.b64encode(image_file.read()).decode('utf-8')
        img_type = "image/png"  # or appropriate type based on the image format

        text_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{img_type};base64,{img_b64_str}"},
                        },
                    ],
                }
            ],
            response_format={ "type": "json_object" }
        )
        result = text_response.choices[0].message.content
        return json.loads(result)
    except OpenAIError as e:
        print(f"An error occurred: {e}")
        return ''

def prepare_prompt(creation_date):

    tag_list = ['cat_1', 'cat_2']
    return ''.join((
        "[no prose]\n"
        "you are a function that only respond as json and only return 4 variables in json: url, title, description, tag_list\n"
        "you cannot say anything else, you cannot chat with user directly\n"
        "don’t say anything other that the json text requested\n"
        "\n"
        "given this screenshot:\n"
        "- what is the $URL of displayed webpage?\n"
        "- what is the title of the $URL? you can use web fetch to get html page title from $URL\n"
        "- what $TAG_LIST array could be used? get inspiration from this list: [",
        ','.join(tag_list),
        "]\n"
        "- give a good and short $DESCRIPTION of the displayed webpage\n"
        "\n"
        "make sure the json format exactly like this:\n"
        "{'url': $URL, 'title': $TITLE, 'description': $DESCRPITION, 'tag_list': $TAG_LIST}\n"
    ))

def process_images():

    for screenshot in os.listdir(inbox_path):
        if screenshot.endswith('.png'):
            # Copy image to outbox
            inbox_file_path = os.path.join(inbox_path, screenshot)
            outbox_file_path = os.path.join(outbox_path, screenshot)
            shutil.copy(inbox_file_path, outbox_file_path)

            # Extract creation date from screenshot filename
            creation_date_str = screenshot.split('.')[0]
            try:
                creation_date = datetime.strptime(creation_date_str, '%Y-%m-%d_%H-%M-%S')
            except ValueError:
                print(f"Failed to parse date from {screenshot}")
                continue
            creation_date_formatted = creation_date.strftime('%Y-%m-%d %a %H:%M')

            prompt = prepare_prompt(creation_date_formatted)

            # Use OpenAI to extract and process text from image
            extracted_json = extract_json_from_image(inbox_file_path, prompt)
            if not extracted_json:
                continue

            # copy extracted_text to clipboard
            clipboard_text = extracted_json["url"]
            pyperclip.copy(clipboard_text)

            # Format output
            formatted_output = ''.join((
                "** [[",
                extracted_json["url"],
                "][",
                extracted_json["title"],
                "]] :",
                ':'.join(extracted_json["tag_list"]),
                ":\n"
                ":PROPERTIES:\n"
                ":CREATED: [",
                creation_date_formatted,
                "]\n"
                ":END:\n"
                "\n",
                extracted_json["description"],
                "\n"
            ))

            # Append output to output file
            with open(output_file, 'a') as f:
                f.write(formatted_output + '\n')

            # Remove file from inbox
            os.remove(inbox_file_path)

if __name__ == '__main__':
    process_images()
