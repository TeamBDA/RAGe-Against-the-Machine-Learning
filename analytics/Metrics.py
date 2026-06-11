import csv
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
TRANSCRIPTIONS_DIR = os.path.join(BASE_DIR, "data")

# Reading file and returning row by row, not everything together
# Especially important for big CSV files
def read_file(filename):
    filepath = f"{TRANSCRIPTIONS_DIR}/{filename}"

    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            yield row

# Returns total amount of words per person
# Not limited to 5 at the moment, as we have just 5 people in our team, but can be limited
def total_words_num(filename):
    stats = {}

    for row in read_file(filename):
        temp_speaker = row['speaker']
        current_rec_len = stats.setdefault(temp_speaker, 0)
        stats.update({temp_speaker: len(row['transcript'].split()) + current_rec_len})

    speaker = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
    return speaker

# Returns speaker with the most/least words spoken
def ml_speaker(filename, mode):
    stats = {}
    temp_speaker = ""
    temp_rec_len = 0

    for row in read_file(filename):

        # Temporary length(temp_rec_len) == 0 -> in case when just function starting first time and temporary length == 0, so we save first value
        if temp_rec_len == 0:
            temp_rec_len = len(row['transcript'].split())
            temp_speaker = row['speaker']

        # If temp_rec_len < len(row['transcript'].split()) -> checking if temporary length which was saved in the previous step < than current one
        # If it's true -> we have a speaker with new highest amount of words per recording, so we need to save it in our stats dictionary
        if mode == "most" and temp_rec_len < len(row['transcript'].split()):
            temp_rec_len = len(row['transcript'].split())
            temp_speaker = row['speaker']

        # If temp_rec_len > len(row['transcript'].split()) -> checking if temporary length which was saved in the previous step > than current one
        # If it's true -> we have a speaker with new lowest amount of words per recording, so we need to save it in our stats dictionary
        elif mode == "least" and temp_rec_len > len(row['transcript'].split()):
            temp_rec_len = len(row['transcript'].split())
            temp_speaker = row['speaker']

    # If temp_speaker not empty -> populate stats from temporary variables(name and amount of words)
    if temp_speaker:
        stats[temp_speaker] = temp_rec_len

    return stats

# Returns total speaking time for each person involved in the meeting in seconds
# Not limited to 5 at the moment, as we have just 5 people in our team, but can be limited
def speakers_total_time(filename):
    stats = {}

    for row in read_file(filename):
        temp_speaker = row['speaker']
        current_rec_len = stats.setdefault(temp_speaker, 0)
        stats.update({temp_speaker: round(float(row['total_speaking_time_seconds']) + current_rec_len, 2) })

    speaker = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
    return speaker

# Returns total meeting speaking time in seconds
def meeting_total_time(filename):
    time = 0.0

    for row in read_file(filename):
        time += float(row['total_speaking_time_seconds'])

    return round(time, 2)

# Returns average speaking(recording) time per person in seconds
def average_time_per_speaker(filename):
    stats = {}
    records_per_speaker = {}


    for row in read_file(filename):
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

# Return average speech rate per person in seconds
def average_speech_rate(filename):
    stats = speakers_total_time(filename)
    words_per_speaker = total_words_num(filename)

    average_stats = {}

    for i in stats.keys():
        average_stats[i] = round(words_per_speaker[i] / stats[i], 2)

    average_stats = dict(sorted(average_stats.items(), key=lambda x: x[1], reverse=True))

    return average_stats

# Creating metrics report using available function from this module
def generate_report_csv(input_filename, output_filename):
    output_path = f"{TRANSCRIPTIONS_DIR}/{output_filename}"

    most_words = ml_speaker(input_filename, "most")
    least_words = ml_speaker(input_filename, "least")
    speaking_times = speakers_total_time(input_filename)
    speech_rates = average_speech_rate(input_filename)

    most_words_speaker = list(most_words.keys())[0]
    most_words_count = list(most_words.values())[0]

    least_words_speaker = list(least_words.keys())[0]
    least_words_count = list(least_words.values())[0]

    total_time = meeting_total_time(input_filename)
    average_time = round(total_time / len(speaking_times), 2)

    report = [
        ["Metric", "Result"],
        ["Most words", f"{most_words_speaker}, {most_words_count} words"],
        ["Least words", f"{least_words_speaker}, {least_words_count} words"],
        ["Total speaking time", f"{total_time} seconds"],
        ["Average speaking time per speaker", f"{average_time} seconds"],
    ]

    for index, speaker in enumerate(speaking_times, start=1):
        report.append([
            f"{index} speaker by time",
            f"{speaker}, {speaking_times[speaker]} seconds"
        ])

    for speaker in speech_rates:
        report.append([
            f"{speaker} average speech rate",
            f"{speech_rates[speaker]} words/second"
        ])

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(report)


### TEST PART
### CAN CHECK ANY METHOD IN THIS FILE JUST USING CODE BELOW AND A NAME OF CSV FILE
# if __name__ == '__main__':
    # generate_report_csv("transcriptions_metrics.csv", "report.csv")
    # test = average_speech_rate("transcriptions_metrics.csv")
    # print(test)