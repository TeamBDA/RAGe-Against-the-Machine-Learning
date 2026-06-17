import csv
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
TRANSCRIPTIONS_DIR = os.path.join(BASE_DIR, "data/results")


def read_file(filename):
    """
        Reading file and returning row by row, not everything together
        Especially important for big CSV files
    """
    filepath = os.path.join(TRANSCRIPTIONS_DIR, filename)

    with open(filepath, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        return list(reader)


def get_rows(data):
    """
        1. Check if data is the name of transcription file, then read file and pass rows from it.
        2. If data already contains raw raws, just return them for processing
    """
    if isinstance(data, str):
        return read_file(data)
    return data


def total_words_num(data):
    """
        Returns total amount of words per person
        Not limited to 5 at the moment, as we have just 5 people in our team, but can be limited
    """
    rows = get_rows(data)

    stats = {}

    for row in rows:
        speaker = row['speaker']

        # Split once
        word_count = len(row['transcript'].split())

        # Directly access dictionary
        stats[speaker] = stats.get(speaker, 0) + word_count

    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

def ml_speaker_rec(data, mode):
    """
        Returns speaker with the most/least words spoken per recording
    """
    rows = get_rows(data)

    stats = {}
    temp_speaker = ""
    temp_rec_len = 0

    for row in rows:

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

def ml_speaker_t(data, mode):
    """
        Returns speaker with the most/least words spoken per in total per meeting
    """
    rows = get_rows(data)

    # Get word totals
    word_totals = total_words_num(rows)
    if not word_totals:
        return {}

    # Since total_words_num is already sorted descending:
    if mode == "most":
        speaker = list(word_totals.keys())[0]
    else:  # "least"
        speaker = list(word_totals.keys())[-1]

    return {speaker: word_totals[speaker]}


def speakers_total_time(data):
    """
        Returns total speaking time for each person involved in the meeting in seconds
        Not limited to 5 at the moment, as we have just 5 people in our team, but can be limited
    """
    rows = get_rows(data)

    stats = {}

    for row in rows:
        temp_speaker = row['speaker']
        stats[temp_speaker] = stats.get(temp_speaker, 0.0) + float(row['total_speaking_time_seconds'])

    # Round to 2 decimal places and sort by value in descending order
    final_stats = {k: round(v, 2) for k, v in stats.items()}
    return dict(sorted(final_stats.items(), key=lambda x: x[1], reverse=True))


def meeting_total_time(data):
    """
        Returns total meeting speaking time in seconds
    """
    rows = get_rows(data)

    time = 0.0

    for row in rows:
        time += float(row['total_speaking_time_seconds'])

    return round(time, 2)


def average_time_per_speaker(data):
    """
        Returns average speaking(recording) time per person in seconds
    """
    rows = get_rows(data)

    stats = {}
    records_per_speaker = {}


    for row in rows:
        temp_speaker = row['speaker']
        seconds = float(row['total_speaking_time_seconds'])
        
        # Track how many times this speaker turned up
        records_per_speaker[temp_speaker] = records_per_speaker.get(temp_speaker, 0) + 1
        
        # Track their cumulative seconds
        stats[temp_speaker] = stats.get(temp_speaker, 0.0) + seconds

    average_stats = {}

    for i in stats.keys():
        # Total speaking time for that person / records which were created by that speaker
        average_stats[i] = round(stats[i] / records_per_speaker[i], 2)

    average_stats = dict(sorted(average_stats.items(), key=lambda x: x[1], reverse=True))

    return average_stats

def average_time_per_meeting(data):
    """
        Returns average speaking time per meeting
    """
    rows = get_rows(data)

    stats = average_time_per_speaker(rows)

    return sum(stats.values()) / len(stats)

def average_speech_rate(data):
    """
        Return average speech rate per person in seconds
    """
    rows = get_rows(data)

    stats = speakers_total_time(rows)
    words_per_speaker = total_words_num(rows)

    average_stats = {}

    for i in stats.keys():
        # Total words per speaker / total speaking time for that person
        average_stats[i] = round(words_per_speaker[i] / stats[i], 2)

    average_stats = dict(sorted(average_stats.items(), key=lambda x: x[1], reverse=True))

    return average_stats

def questions_per_speaker(data):
    """
        Returns amount of questions per speaker using question field.
        If no questions found, returns message that no one answered any questions.
    """
    rows = get_rows(data)

    stats = {}

    for row in rows:
        speaker = row["speaker"]

        if row["question_flag"]:
            stats[speaker] = stats.get(speaker, 0) + 1

    return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))

def generate_report_csv(data, output_filename):
    """
        Creating metrics report using available function from this module
    """
    rows = get_rows(data)

    output_path = f"{TRANSCRIPTIONS_DIR}/{output_filename}"

    most_words = ml_speaker_t(rows, "most")
    least_words = ml_speaker_t(rows, "least")
    speaking_times = speakers_total_time(rows)
    speech_rates = average_speech_rate(rows)
    questions = questions_per_speaker(rows)

    most_words_speaker = list(most_words.keys())[0]
    most_words_count = list(most_words.values())[0]

    least_words_speaker = list(least_words.keys())[0]
    least_words_count = list(least_words.values())[0]

    total_time = sum(speaking_times.values())
    average_time = round(average_time_per_meeting(rows))

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

    if questions:
        top_speaker = list(questions.keys())[0]
        top_count = list(questions.values())[0]

        report.append([
            "Most questions",
            f"{top_speaker}, {top_count} questions"
        ])
    else:
        report.append([
            "Most questions",
            "No questions detected"
        ])

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(report)


### TEST PART
### CAN CHECK ANY METHOD IN THIS FILE JUST USING CODE BELOW AND A NAME OF CSV FILE
if __name__ == '__main__':
    generate_report_csv("enriched_transcripts.csv", "report.csv")
    print("Report generated successfully as report.csv in the data/results directory.")
