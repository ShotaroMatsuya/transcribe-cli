import os
import time
from logging import DEBUG, Formatter, StreamHandler, getLogger

import boto3
from botocore.exceptions import ClientError

logger = getLogger("S3操作+Transcribe実行")
logger.setLevel(DEBUG)

stream_handler = StreamHandler()
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

transcribe = boto3.client("transcribe", region_name="us-east-1")
s3 = boto3.resource("s3")


def check_job_name(job_name):
    """job名の重複を確認"""
    job_verification = True
    # all the transcriptions
    existed_jobs = transcribe.list_transcription_jobs()
    for job in existed_jobs["TranscriptionJobSummaries"]:
        if job_name == job["TranscriptionJobName"]:
            job_verification = False
        break
    if job_verification is False:
        command = input(
            job_name + " has existed. \nDo you want to override the existed job (Y/N): "
        )
        if command.lower() == "y" or command.lower() == "yes":
            transcribe.delete_transcription_job(TranscriptionJobName=job_name)
        elif command.lower() == "n" or command.lower() == "no":
            job_name = input("Insert new job name? ")
            check_job_name(job_name)
        else:
            print("Input can only be (Y/N)")
            command = input(
                job_name
                + " has existed. \nDo you want to override the existed job (Y/N): "
            )
    return job_name


def amazon_transcribe(audio_file_name="test.mp4"):
    """ローカルファイルを指定してtranscribeを実行"""
    assets_filepath = os.path.join(os.path.dirname(__file__), "assets")
    # 存在check
    if os.path.exists(os.path.join(assets_filepath, audio_file_name)):
        logger.info("ローカルファイル「%s」は存在します。" % (audio_file_name))
    else:
        logger.warning("ローカルファイル「%s」は存在しません。" % (audio_file_name))
        return False

    # Upload audio_file
    s3_client = get_client()
    put_object(s3_client, "smat-transcription-input", audio_file_name)

    # Get s3 list
    get_object_list(s3_client, "smat-transcription-input")

    job_uri = "s3://smat-transcription-input/{}".format(audio_file_name)
    job_name = (audio_file_name.split(".")[0]).replace(" ", "")
    file_format = audio_file_name.split(".")[1]

    # check if name is taken or not
    job_name = check_job_name(job_name)
    transcribe.start_transcription_job(
        TranscriptionJobName=job_name,
        Media={"MediaFileUri": job_uri},
        MediaFormat=file_format,
        LanguageCode="en-US",
        OutputBucketName="smat-transcription-output",
        Subtitles={"Formats": ["vtt"]},
    )

    while True:
        result = transcribe.get_transcription_job(TranscriptionJobName=job_name)
        if result["TranscriptionJob"]["TranscriptionJobStatus"] in [
            "COMPLETED",
            "FAILED",
        ]:
            break
        time.sleep(15)
        print("Not ready yet....")
    if result["TranscriptionJob"]["TranscriptionJobStatus"] == "COMPLETED":
        get_object_list(s3_client, "smat-transcription-output")
        transcript_output = result["TranscriptionJob"]["Transcript"][
            "TranscriptFileUri"
        ]
        subtitle_output = result["TranscriptionJob"]["Subtitles"]["SubtitleFileUris"][0]
        transcript_file_name = os.path.split(transcript_output)[1]  # .(mp4)
        subtitle_file_name = os.path.split(subtitle_output)[1]  # .vtt

        download_object(s3_client, "smat-transcription-output", transcript_file_name)
        download_object(s3_client, "smat-transcription-output", subtitle_file_name)
        return True
    else:
        return False


def get_client():
    """s3のclient取得"""
    return boto3.client("s3", region_name="us-east-1")


def put_object(s3_client, bucket_name, object_name):
    """
    オブジェクトをバケットに追加
    """
    src_file_path = os.path.join(os.path.dirname(__file__), "assets", object_name)
    print(src_file_path)
    try:
        with open(src_file_path, "rb") as fo:
            s3_client.put_object(Bucket=bucket_name, Body=fo, Key=object_name)
        logger.info("オブジェクト「%s」をバケット「%s」に追加しました。" % (object_name, bucket_name))
    except ClientError as e:
        logger.error(e)
        logger.warning(
            "オブジェクト「%s」をバケット「%s」に追加する処理に失敗しました。" % (object_name, bucket_name)
        )
        return False
    return True


def get_object_list(s3_client, bucket_name):
    """
    オブジェクト一覧を取得
    """

    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        logger.info("オブジェクト一覧:")
        # logger.info(response)
        if response["KeyCount"] > 0:
            for object in response["Contents"]:
                logger.info(f'  {object["Key"]}')
        else:
            logger.info("オブジェクトが存在しません。")
    except ClientError as e:
        logger.error(e)
        logger.warning("オブジェクト一覧取得エラーです。")


def download_object(s3_client, bucket_name, object_name):
    """オブジェクトをダウンロード"""
    try:
        s3_client.download_file(
            Bucket=bucket_name,
            Key=object_name,
            Filename="./results/{}".format(object_name),
        )
        logger.info("オブジェクト「%s」のダウンロードしました。" % object_name)
    except ClientError as e:
        logger.error(e)
        logger.warning("オブジェクト「%s」のダウンロードに失敗しました。" % object_name)
        return False
    return True


def delete_object(s3_client, bucket_name, object_name):
    """
    オブジェクトを削除
    """
    try:
        s3_client.delete_object(Bucket=bucket_name, Key=object_name)
        logger.info("オブジェクト「%s」を削除しました。" + bucket_name)
    except ClientError as e:
        logger.error(e)
        logger.warning("オブジェクト「%s」の削除に失敗しました。" % bucket_name)
        return False
    return True


def main():
    amazon_transcribe("Usage-of-S3-Buckets.mp4")
    s3_client = get_client()
    # get_object_list(s3_client, "smat-transcription-output")
    # download_object(s3_client, "smat-transcription-output", "test.json")
    # put_object(s3_client, "smat-transcription-input", "Usage+of+S3+Buckets.mp4")
    # get_object_list(s3_client, "smat-transcription-input")
    delete_object(s3_client, "smat-transcription-input", "test.mp4")
    get_object_list(s3_client, "smat-transcription-input")


if __name__ == "__main__":
    main()
