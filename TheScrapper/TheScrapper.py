
import json
from argparse import ArgumentParser
import csv
import re

import requests
from requests.exceptions import MissingSchema

from modules.info_reader import InfoReader
from modules.scrapper import Scrapper


def clean_url(url):
    # Remove leading/trailing whitespace and non-printable characters
    cleaned_url = url.strip()
    cleaned_url = re.sub(r'[^\x20-\x7E]', '', cleaned_url)
    return cleaned_url

def read_urls_from_csv(file_path):
    urls = []
    with open(file_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)
        for row in csv_reader:
            if row:
                url = clean_url(row[0])
                urls.append(url)
    return urls

# Replace 'input.csv' with your file path
urls = read_urls_from_csv('filename.csv')
print(urls)

def save_output_to_csv(output_data, file_name):
    csv_file_name = f"output/{file_name}.csv"
    with open(csv_file_name, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["Target", "E-Mails", "Numbers", "SocialMedia"])
        for item in output_data:
            target = item["Target"]
            emails = ", ".join(item["E-Mails"])
            numbers = ", ".join(item["Numbers"])
            social_media = ", ".join(item["SocialMedia"])
            csv_writer.writerow([target, emails, numbers, social_media])

if __name__ == "__main__":
    parser = ArgumentParser(description="TheScrapper - Contact finder")
    parser.add_argument("-u", "--url", required=False,
                        help="The URL of the target.")
    parser.add_argument("-us", "--urls", required=False,
                        help="The URL of the target.")
    parser.add_argument("-c", "--crawl", default=False, required=False, action="store_true",
                        help="Use every URL found on the site and hunt it down for information.")
    parser.add_argument("-b", "--banner", default=False, required=False, action="store_true",
                        help="Use every URL found on the site and hunt it down for information.")
    parser.add_argument("-s", "--sm", default=False, required=False, action="store_true",
                        help="Extract info from the SocialMedia accounts.")
    parser.add_argument("-o", "--output", default=False, required=False, action="store_true",
                        help="Save the output in JSON and CSV files.")
    parser.add_argument("-v", "--verbose", default=False, required=False, action="store_true",
                        help="Verbose output mode.")
    args = parser.parse_args()

    def verbPrint(content: str):
        if args.verbose:
            print(content)
        pass

    target_type = ""
    if not args.url and not args.urls:
        exit("Please add --url or --urls")
    else:
        if args.url:
            target_type = "URL"
        else:
            target_type = "FILE"


    if target_type == "URL":
        if not (args.url.startswith("https://") or args.url.startswith("http://")):
            args.url = "http://" + args.url

        print("*" * 50 + "\n" + f"Target: {args.url}" + "\n" + "*" * 50 + "\n")

        requests.get(args.url)

        url = args.url
        verbPrint("Scraping (and crawling) started")
        scrap = Scrapper(url=url, crawl=args.crawl)
        verbPrint("Scraping (and crawling) done\nReading and sorting information")
        IR = InfoReader(content=scrap.getText())
        emails = IR.getEmails()
        numbers = IR.getPhoneNumber()
        sm = IR.getSocials()
        verbPrint("Reading and sorting information done")

        print("\n")
        print("E-Mails: " + "\n - ".join(emails))
        print("Numbers:" + "\n - ".join(numbers))
        if args.sm:
            print("SocialMedia: ")
            sm_info = IR.getSocialsInfo()
            for x in sm_info:
                url = x["url"]
                info = x["info"]
                if info:
                    print(f" - {url}:")
                    for y in info:
                        print(f"     - {y}: {info[y]}")
                else:
                    print(f" - {url}")
        else:
            print("SocialMedia: " + ", ".join(sm))
        if args.output:
            out = {
                "E-Mails": emails,
                "SocialMedia": sm,
                "Numbers": numbers
            }
            file_name = url.lower().replace("http://", "").replace("https://", "").replace("/", "")
            json.dump(out, open(f"output/{file_name}.json", "w+"), indent=4)

    elif target_type == "FILE":
        out = []
        urls_from_csv = read_urls_from_csv(args.urls)
        for url in urls_from_csv:
            url = url.strip()  # Remove any leading/trailing whitespace
            if not url.startswith("https://") and not url.startswith("http://"):
                url = "http://" + url

            print("*" * 50 + "\n" + f"Target: {url}" + "\n" + "*" * 50 + "\n")

            requests.get(url)
            verbPrint("Scraping (and crawling) started")
            scrap = Scrapper(url=url, crawl=args.crawl)
            verbPrint("Scraping (and crawling) done\nReading and sorting information")
            IR = InfoReader(content=scrap.getText())
            emails = IR.getEmails()
            numbers = IR.getPhoneNumber()
            sm = IR.getSocials()
            out.append({
                "Target": url,
                "E-Mails": emails,
                "SocialMedia": sm,
                "Numbers": numbers
            })
            verbPrint("Reading and sorting information done")
            print("E-Mails:\n" + "\n - ".join(emails))
            print("Numbers:\n" + "\n - ".join(numbers))
            if args.sm:
                print("SocialMedia: ")
                sm_info = IR.getSocialsInfo()
                for x in sm_info:
                    url = x["url"]
                    info = x["info"]
                    if info:
                        print(f" - {url}:")
                        for y in info:
                            print(f"     - {y}: {info[y]}")
                    else:
                        print(f" - {url}")
            else:
                print("SocialMedia: " + ", ".join(sm))

        if args.output:
            file_name = args.urls.replace("/", "_").replace(".csv", "")
            json.dump(out, open(f"output/{file_name}.json", "w+"), indent=4)
            save_output_to_csv(out, file_name)
