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
aws transcribe start-transcription-job --region us-east-1 --cli-input-json file://cmdtestjob-3-speaker-identification.json
```

- List Transcription Cmd:

```bash
aws transcribe list-transcription-jobs --region us-east-1 --status IN_PROGRESS
```

- Get Transcription Cmd:

```bash
aws transcribe get-transcription-job --region us-east-1 --transcription-job-name "cmdtestjob-3-speaker-identification"
```

- Delete Transcription Job Cmd:

```bash
aws transcribe delete-transcription-job --region us-east-1 --transcription-job-name "cmdtestjob-3-speaker-identification"
```

## Creating Custom Vocabulary in List Format Using CLI

- Example Contents of json

```json
{
  "LanguageCode": "en-US",
  "Phrases": ["ess-three"],
  "VocabularyFileUri": "https://${bucket_name}.s3.amazonaws.com/CustomVocabTableFormat-S3.txt",
  "VocabularyName": "custom-vocab-list-format"
}
```

_Note that if you include `Phrases` in your request, you cannot use `VocabularyFileUri`; you must choose one or the other._

- Create Vocabulary Cmd Syntax:

```bash
aws transcribe create-vocabulary --region us-east-1 --cli-input-json file://custom-vocab-list-format.json
```

- List Vocabularies Syntax:

```bash
aws transcribe list-vocabularies --region us-east-1 --state-equals READY
aws transcribe list-vocabularies --region us-east-1 --state-equals PENDING
aws transcribe list-vocabularies --region us-east-1 --state-equals FAILED
aws transcribe list-vocabularies --region us-east-1 --name-contains "list"

```

- Running Transcription job Using Custom Vocabulary in list format from CLI

```bash
aws transcribe start-transcription-job --region us-east-1 --cli-input-json file://cmdtestjob-1-custom-vocab-list.json
aws transcribe list-transcription-jobs --region us-east-1 --status COMPLETED
```

- Get Transcription Cmd:

```bash
aws transcribe get-transcription-job --region us-east-1 --transcription-job-name "cmdtestjob-1-custom-vocab-list"
```

- Delete Transcription Job Cmd:

```bash
aws transcribe delete-transcription-job --region us-east-1 --transcription-job-name "cmdtestjob-1-custom-vocab-list"
```

## Running Transcription job using a python script by boto3

- requirements
  1. pip
  2. boto3

To Install boto3 the SDK Package for python using pip cmd as mentioned below

```bash
pip install boto3 --user
```

- python script requirements for Amazon Transcribe:
  1. Speech File Format: Either .WAV or .MP4 stored in S3 bucket
  2. Bucket Name
  3. MP$ File Name
  4. S3 EndPoint for our Amazon Transcribe Region: s3.amazonaws.com

#### introduction to ffmpeg

```bash
# Step1: Update and upgrade Homebrew Formulae
brew update
brew upgrade
# Step2: Install FFmpeg
brew install ffmpeg
```
