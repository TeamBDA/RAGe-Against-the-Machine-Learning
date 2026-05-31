import csv
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
TRANSCRIPTIONS_DIR = os.path.join(BASE_DIR, "data")

#Returns total amount of words per person
#Not limited to 5 at the moment, as we have just 5 people in our team, but can be limited
def total_words_num(filename):
    stats = {}
    with open(f"{TRANSCRIPTIONS_DIR}/{filename}", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            temp_speaker = row['speaker']
            current_rec_len = stats.setdefault(temp_speaker, 0)
            stats.update({temp_speaker: len(row['transcript'].split()) + current_rec_len})

    speaker = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
    return speaker

#Returns TOP speaker name and amount of words
def top_speaker(filename):
    stats = {}
    temp_speaker = ""
    temp_rec_len = 0
    with open(f"{TRANSCRIPTIONS_DIR}/{filename}", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if temp_rec_len == 0 or temp_rec_len < len(row['transcript'].split()):
                temp_rec_len = len(row['transcript'].split())
                temp_speaker = row['speaker']

        if temp_speaker:
            stats[temp_speaker] = temp_rec_len

    return stats

#Returns BOTTOM speaker name and amount of words in meeting
def bot_speaker(filename):
    stats = {}
    temp_speaker = ""
    temp_rec_len = 0
    with open(f"{TRANSCRIPTIONS_DIR}/{filename}", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if temp_rec_len == 0 or temp_rec_len > len(row['transcript'].split()):
                temp_rec_len = len(row['transcript'].split())
                temp_speaker = row['speaker']

        if temp_speaker:
            stats[temp_speaker] = temp_rec_len

    return stats

#Returns total speaking time for each person involved in the meeting in seconds
#Not limited to 5 at the moment, as we have just 5 people in our team, but can be limited
def speakers_total_time(filename):
    stats = {}
    with open(f"{TRANSCRIPTIONS_DIR}/{filename}", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            temp_speaker = row['speaker']
            current_rec_len = stats.setdefault(temp_speaker, 0)
            stats.update({temp_speaker: round(float(row['total_speaking_time_seconds']) + current_rec_len, 2) })

    speaker = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
    return speaker

#Returns total meeting speaking time in seconds
def meeting_total_time(filename):
    time = 0.0
    with open(f"{TRANSCRIPTIONS_DIR}/{filename}", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            time += float(row['total_speaking_time_seconds'])

    return round(time, 2)

#Returns average speaking(recording) time per person in seconds
def average_time_per_speaker(filename):
    stats = {}
    records_per_speaker = {}
    with open(f"{TRANSCRIPTIONS_DIR}/{filename}", newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            temp_speaker = row['speaker']

            if temp_speaker not in records_per_speaker:
                records_per_speaker[temp_speaker] = stats.setdefault(temp_speaker, 0)

            records_per_speaker[temp_speaker] += 1
            current_rec_len = stats.setdefault(temp_speaker, 0)
            stats.update({temp_speaker: float(row['total_speaking_time_seconds']) + current_rec_len})

    average_stats = {}

    for i in stats.keys():
        average_stats[i] = round(stats[i] / records_per_speaker[i], 2)

    average_stats = dict(sorted(average_stats.items(), key=lambda x: x[1], reverse=True))

    return average_stats

#Return average speech rate per person in seconds
def average_speech_rate(filename):
    stats = speakers_total_time(filename)
    words_per_speaker = total_words_num(filename)

    average_stats = {}

    for i in stats.keys():
        average_stats[i] = round(words_per_speaker[i] / stats[i], 2)

    average_stats = dict(sorted(average_stats.items(), key=lambda x: x[1], reverse=True))

    return average_stats


### TEST PART
### CAN CHECK ANY METHOD IN THIS FILE JUST USING CODE BELOW AND A NAME OF CSV FILE
#if __name__ == '__main__':
#    test = average_speech_rate("transcriptions.csv")
#    print(test)