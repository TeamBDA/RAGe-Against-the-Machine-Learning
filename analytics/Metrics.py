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
def total_words_num1(data_rows):
    stats = {}

    for row in data_rows:
        temp_speaker = row['speaker']
        current_rec_len = stats.setdefault(temp_speaker, 0)
        stats[temp_speaker] = len(row['transcript'].split()) + current_rec_len

    speaker = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
    return speaker

def total_words_num2(data_rows):
    stats = {}

    for row in data_rows:
        speaker = row['speaker']
        # Split once, use twice if needed
        word_count = len(row['transcript'].split())
        
        # Direct dictionary access is much faster than .update()
        stats[speaker] = stats.get(speaker, 0) + word_count

    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

def ml_speaker(data_rows, mode):
    # Leverage the function that already works perfectly
    word_totals = total_words_num1(data_rows)
    print(word_totals)
    word_totals = total_words_num2(data_rows)
    print(word_totals)
    if not word_totals:
        return {}
        
    # Since total_words_num2 is already sorted descending:
    if mode == "most":
        speaker = list(word_totals.keys())[0]
    else:  # "least"
        speaker = list(word_totals.keys())[-1]
        
    return {speaker: word_totals[speaker]}

# Returns total speaking time for each person involved in the meeting in seconds
# Not limited to 5 at the moment, as we have just 5 people in our team, but can be limited
def speakers_total_time(data_rows):
    stats = {}

    for row in data_rows:
        temp_speaker = row['speaker']
        current_rec_len = stats.setdefault(temp_speaker, 0)
        stats.update({temp_speaker: round(float(row['total_speaking_time_seconds']) + current_rec_len, 2) })

    speaker = dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
    return speaker

# Returns total meeting speaking time in seconds
def meeting_total_time(data_rows):
    time = 0.0

    for row in data_rows:
        time += float(row['total_speaking_time_seconds'])

    return round(time, 2)

# Returns average speaking(recording) time per person in seconds
def average_time_per_speaker(data_rows):
    stats = {}
    records_per_speaker = {}


    for row in data_rows:
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
def average_speech_rate(data_rows):
    stats = speakers_total_time(data_rows)
    words_per_speaker = total_words_num2(data_rows)

    average_stats = {}

    for i in stats.keys():
        average_stats[i] = round(words_per_speaker[i] / stats[i], 2)

    average_stats = dict(sorted(average_stats.items(), key=lambda x: x[1], reverse=True))

    return average_stats

# Creating metrics report using available function from this module
def generate_report_csv(input_filename, output_filename):
    output_path = f"{TRANSCRIPTIONS_DIR}/{output_filename}"
    data_rows = list(read_file(input_filename))

    most_words = ml_speaker(data_rows, "most")
    least_words = ml_speaker(data_rows, "least")
    speaking_times = speakers_total_time(data_rows)
    speech_rates = average_speech_rate(data_rows)

    most_words_speaker = list(most_words.keys())[0]
    most_words_count = list(most_words.values())[0]

    least_words_speaker = list(least_words.keys())[0]
    least_words_count = list(least_words.values())[0]

    total_time = sum(speaking_times.values())
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
if __name__ == '__main__':
    generate_report_csv("transcriptions_metrics.csv", "report.csv")