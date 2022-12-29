# Amazon Transcribe DEMO

## Running a Transcription Job via CLI

- requirements
  1. Bucket name
  2. File Name
  3. S3 EndPoint for our Amazon Transcribe Region: s3.amazonaws.com
  4. Json file named
- Example Contents of json

```json
{
  "TranscriptionJobName": "request ID",
  "LanguageCode": "en-US",
  "MediaFormat": "wav",
  "Media": {
    "MediaFileUri": "https://${s3_endpoint}/${bucket_name}/${file:_name}.wav"
  }
}
```

- Start Transcription Cmd syntax:

```bash
aws transcribe start-transcription-job \
  --region us-east-1 \
  --cli-input-json file://test-start-command.json
```

- List Transcription Cmd Syntax:

```bash
aws transcribe list-transcription-jobs \
  --region us-east-1 \
  --status IN_PROGRESS
```

- Get Transcription Job Cmd Syntax:

```bash
aws transcribe get-transcription-job \
  --region us-east-1 \
  --transcription-job-name "cmdtestjob"
```

---

- Start Transcription Cmd:

```bash
aws transcribe start-transcription-job --region us-east-1 --cli-input-json file://cmdtestjob-2-channel-identification.json
```

- List Transcription Cmd:

```bash
aws transcribe list-transcription-jobs --region us-east-1 --status IN_PROGRESS
```

- Get Transcription Cmd:

```bash
aws transcribe get-transcription-job --region us-east-1 --transcription-job-name "cmdtestjob-2-channel-identification"
```

- Delete Transcription Job Cmd:

```bash
aws transcribe delete-transcription-job --region us-east-1 --transcription-job-name "cmdtestjob-2-channel-identification"
```
