from __future__ import print_function

import time

import boto3

transcribe = boto3.client("transcribe", region_name="us-east-1")
job_name = "python-transcribe-test"
job_uri = "https://s3.amazonaws.com/smat-transcription-input/Usage+of+S3+Buckets.mp4"
transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={"MediaFileUri": job_uri},
    MediaFormat="mp4",
    LanguageCode="en-US",
)
while True:
    status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    if status["TranscriptionJob"]["TranscriptionJobStatus"] in ["COMPLETED", "FAILED"]:
        break
    print("Not ready yet...")
    time.sleep(5)
    print(status)
