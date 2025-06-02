import os
import requests
from urllib.parse import urlsplit

# List of media URLs
media_urls = [
    "https://media.hhomesltd.com/images/87283/218-M_orig.jpg",
    "https://media.hhomesltd.com/images/specs/floorplans/553-007.jpg",
    "https://media.hhomesltd.com/images/106810/HOU-Elyson-218M09_orig.jpg",
    "https://media.hhomesltd.com/images/106811/HOU-Elyson-218M03_orig.jpg",
    "https://media.hhomesltd.com/images/106812/HOU-Elyson-218M02_orig.jpg",
    "https://media.hhomesltd.com/images/106813/HOU-Elyson-218M04_orig.jpg",
    "https://media.hhomesltd.com/images/106814/HOU-Elyson-218M05_orig.jpg",
    "https://media.hhomesltd.com/images/106815/HOU-Elyson-218M06_orig.jpg",
    "https://media.hhomesltd.com/images/106816/HOU-Elyson-218M07_orig.jpg",
    "https://media.hhomesltd.com/images/106817/HOU-Elyson-218M08_orig.jpg",
    "https://media.hhomesltd.com/images/106818/HOU-Elyson-218M10_orig.jpg",
    "https://media.hhomesltd.com/images/106819/HOU-Elyson-218M11_orig.jpg",
    "https://media.hhomesltd.com/images/106820/HOU-Elyson-218M12_orig.jpg",
    "https://media.hhomesltd.com/images/106821/HOU-Elyson-218M13_orig.jpg",
    "https://media.hhomesltd.com/images/106822/HOU-Elyson-218M14_orig.jpg",
    "https://media.hhomesltd.com/images/106823/HOU-Elyson-218M15_orig.jpg",
    "https://media.hhomesltd.com/images/106824/HOU-Elyson-218M16_orig.jpg",
    "https://media.hhomesltd.com/images/106825/HOU-Elyson-218M17_orig.jpg",
    "https://media.hhomesltd.com/images/106826/HOU-Elyson-218M18_orig.jpg",
    "https://media.hhomesltd.com/images/106827/HOU-Elyson-218M19_orig.jpg",
    "https://media.hhomesltd.com/images/106828/HOU-Elyson-218M20_orig.jpg",
    "https://media.hhomesltd.com/images/106829/HOU-Elyson-218M21_orig.jpg",
    "https://media.hhomesltd.com/images/106830/HOU-Elyson-218M22_orig.jpg",
    "https://media.hhomesltd.com/images/106831/HOU-Elyson-218M23_orig.jpg",
    "https://media.hhomesltd.com/images/106832/HOU-Elyson-218M24_orig.jpg",
    "https://media.hhomesltd.com/images/106833/HOU-Elyson-218M25_orig.jpg",
    "https://media.hhomesltd.com/images/106834/HOU-Elyson-218M26_orig.jpg",
    "https://media.hhomesltd.com/images/106835/HOU-Elyson-218M27_orig.jpg",
    "https://media.hhomesltd.com/images/106836/HOU-Elyson-218M28_orig.jpg",
    "https://media.hhomesltd.com/images/106837/HOU-Elyson-218M29_orig.jpg",
    "https://media.hhomesltd.com/images/106838/HOU-Elyson-218M30_orig.jpg",
    "https://media.hhomesltd.com/images/106839/HOU-Elyson-218M31_orig.jpg",
    "https://media.hhomesltd.com/images/106840/HOU-Elyson-218M32_orig.jpg",
    "https://media.hhomesltd.com/images/106841/HOU-Elyson-218M33_orig.jpg",
    "https://media.hhomesltd.com/images/106842/HOU-Elyson-218M34_orig.jpg",
    "https://media.hhomesltd.com/images/106843/HOU-Elyson-218M35_orig.jpg",
    "https://media.hhomesltd.com/images/106844/HOU-Elyson-218M36_orig.jpg",
    "https://media.hhomesltd.com/images/106845/HOU-Elyson-218M37_orig.jpg",
    "https://media.hhomesltd.com/images/106846/HOU-Elyson-218M38_orig.jpg",
    "https://media.hhomesltd.com/images/106847/HOU-Elyson-218M39_orig.jpg",
    "https://media.hhomesltd.com/images/106848/HOU-Elyson-218M40_orig.jpg",
    "https://media.hhomesltd.com/images/106849/HOU-Elyson-218M41_orig.jpg",
    "https://media.hhomesltd.com/images/106850/HOU-Elyson-218M42_orig.jpg",
    "https://media.hhomesltd.com/images/106851/HOU-Elyson-218M43_orig.jpg",
    "https://media.hhomesltd.com/images/106852/HOU-Elyson-218M44_orig.jpg",
    "https://media.hhomesltd.com/images/106853/HOU-Elyson-218M45_orig.jpg",
    "https://media.hhomesltd.com/images/106854/HOU-Elyson-218M46_orig.jpg",
    "https://media.hhomesltd.com/images/106855/HOU-Elyson-218M47_orig.jpg",
    "https://media.hhomesltd.com/images/106856/HOU-Elyson-218M48_orig.jpg",
    "https://media.hhomesltd.com/images/106857/HOU-Elyson-218M49_orig.jpg",
    "https://media.hhomesltd.com/images/106858/HOU-Elyson-218M50_orig.jpg",
    "https://media.hhomesltd.com/images/106859/HOU-Elyson-218M51_orig.jpg",
    "https://media.hhomesltd.com/images/106860/HOU-Elyson-218M52_orig.jpg",
    "https://media.hhomesltd.com/images/106861/HOU-Elyson-218M53_orig.jpg",
    "https://media.hhomesltd.com/images/106862/HOU-Elyson-218M54_orig.jpg",
    "https://media.hhomesltd.com/images/106863/HOU-Elyson-218M55_orig.jpg",
    "https://media.hhomesltd.com/images/106864/HOU-Elyson-218M56_orig.jpg",
    "https://media.hhomesltd.com/images/106865/HOU-Elyson-218M57_orig.jpg",
    "https://media.hhomesltd.com/images/106866/HOU-Elyson-218M58_orig.jpg"
]


# Destination folder
download_folder = r"C:\409 Prarie"
os.makedirs(download_folder, exist_ok=True)

# Download each image
for url in media_urls:
    try:
        filename = os.path.basename(urlsplit(url).path)
        file_path = os.path.join(download_folder, filename)

        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise error for bad status

        with open(file_path, 'wb') as out_file:
            for chunk in response.iter_content(chunk_size=8192):
                out_file.write(chunk)

        print(f"Downloaded: {filename}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")
