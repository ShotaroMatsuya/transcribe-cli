import os
import time
from logging import DEBUG, Formatter, StreamHandler, getLogger
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.exceptions import ClientError

from helper.captions_helper import Captions
from helper.helper import AwsHelper, FileHelper, S3Helper

logger = getLogger("S3操作+Translate")
logger.setLevel(DEBUG)

stream_handler = StreamHandler()
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def s3_event_handler(src_lng, target_lng):
    request = {}
    request["bucketName"] = "smat-translate-test"  # bucket名
    request["sourceLanguage"] = src_lng  # 英語：en、日本語：ja
    request["targetlanguage"] = target_lng
    request["trigger_file"] = "triggerfile"

    logger.info("request: {}".format(request))
    try:
        captions = Captions()
        # filter only the VTT for processing in the input folder
        objs = S3Helper().getFilteredFileNames(request["bucketName"], "input/", ["vtt"])
        for obj in objs:
            print(obj)  # ファイル名
            try:
                vttObject = {}
                vttObject["Bucket"] = request["bucketName"]
                vttObject["Key"] = obj
                captions_list = []
                # based on the file type call the method that converts them into pyth9on list object
                if obj.endswith("vtt"):
                    captions_list = captions.vttToCaptions(vttObject)
                print(captions_list)
                # convert the text captions in the list object to a delimited file
                delimitedFile = captions.ConvertToDemilitedFiles(captions_list)
                fileName = obj.split("/")[-1]
                newObjectKey = "captions-in/{}.delimited".format(fileName)
                S3Helper().writeToS3(
                    str(delimitedFile), request["bucketName"], newObjectKey
                )
                output = "Output Object: {}/{}".format(
                    request["bucketName"], newObjectKey
                )
                logger.debug(output)
                S3Helper().renameObject(
                    request["bucketName"], obj, "{}.processed".format(obj)
                )

            except ClientError as e:
                logger.error(
                    "An error occured starting the Translate Batch Job: %s" % e
                )
        translateContext = {}
        translateContext["sourceLang"] = request["sourceLanguage"]
        translateContext["targetLangList"] = [request["targetlanguage"]]
        translateContext[
            "roleArn"
        ] = "arn:aws:iam::528163014577:role/TranslateCaptionServiceRole"
        translateContext["bucket"] = request["bucketName"]
        translateContext["inputLocation"] = "captions-in/"
        translateContext["outputLocation"] = "captions-out/"
        translateContext["jobPrefix"] = "TranslateJob-captions"
        # Call Amazon Translate to translte the delimited files in the captions-in folder
        jobinfo = captions.TranslateCaptions(translateContext)

        S3Helper().deleteObject(
            request["bucketName"], "input/{}".format(request["trigger_file"])
        )
        logger.error(jobinfo)
        return (jobinfo["JobId"], jobinfo["JobName"])
    except ClientError as e:
        logger.error("An error occured with S3 Bucket Operation: %s" % e)
        return None


def checkStatusOfJob(job_name):
    translate_client = AwsHelper().getClient("translate")
    while True:
        result = translate_client.list_text_translation_jobs(
            Filter={"JobName": job_name}
        )
        if result["TextTranslationJobPropertiesList"][0]["JobStatus"] in [
            "COMPLETED",
            "COMPLETED_WITH_ERROR",
            "FAILED",
        ]:
            break
        time.sleep(15)
        print("Not ready yet....")
    if result["TextTranslationJobPropertiesList"][0]["JobStatus"] == "COMPLETED":
        return True
    else:
        logger.warn(
            "Job Name {} failed or completed with errors, exiting".format(job_name)
        )
        return False


def processRequest(request):
    output = ""
    logger.info("request: {}".format(request))
    up = urlparse(request["s3uri"], allow_fragments=False)
    accountid = request["accountId"]
    jobid = request["jobId"]
    bucketName = up.netloc
    basePrefixPath = "captions-out/" + accountid + "-TranslateText-" + jobid + "/"
    languageCode = request["langCode"]
    logger.debug("Base Prefix Path:{}".format(basePrefixPath))
    captions = Captions()
    # filter only the delimited files with .delimited suffix
    objs = S3Helper().getFilteredFileNames(bucketName, basePrefixPath, ["delimited"])
    logger.debug(objs)
    for obj in objs:
        try:
            # Read the Delimited file contents
            content = S3Helper().readFromS3(bucketName, obj)
            fileName = FileHelper().getFileName(obj)
            sourceFileName = FileHelper().getFileName(
                obj.replace("{}.".format(languageCode), "")
            )
            logger.debug("SourceFileKey:{}.processed".format(sourceFileName))
            soureFileKey = "input/{}.processed".format(sourceFileName)
            vttObject = {}
            vttObject["Bucket"] = bucketName
            vttObject["Key"] = soureFileKey
            captions_list = []
            # Based on the file format, call the right method to load the file as python object
            if fileName.endswith("vtt"):
                captions_list = captions.vttToCaptions(vttObject)
            elif fileName.endswith("srt"):
                captions_list = captions.srtToCaptions(vttObject)
            # Replace the text captions with the translated content
            translatedCaptionsList = captions.DelimitedToWebCaptions(
                captions_list, content, "<span>", 15
            )
            translatedText = ""
            # Recreate the Caption files in VTT or SRT format
            if fileName.endswith("vtt"):
                translatedText = captions.captionsToVTT(translatedCaptionsList)

            logger.debug(translatedText)
            logger.debug(content)
            newObjectKey = "output/{}".format(fileName)
            # Write the VTT or SRT file into the output S3 folder
            S3Helper().writeToS3(str(translatedText), bucketName, newObjectKey)
            output = "Output Object: {}/{}".format(bucketName, newObjectKey)
            logger.debug(output)
        except ClientError as e:
            logger.error("An error occured with S3 bucket operations: %s" % e)

    objs = S3Helper().getFilteredFileNames(bucketName, "captions-in/", ["delimited"])
    if request["delete_captionsin"] and request["delete_captionsin"] is True:
        for obj in objs:
            try:
                logger.debug("Deleting temp delimited caption files {}".format(obj))
                S3Helper().deleteObject(bucketName, obj)
            except ClientError as e:
                logger.error("An error occured with S3 bucket operations: %s" % e)


def translate_job_event_handler(job_id):
    request = {}
    request["delete_captionsin"] = True
    try:
        request["jobId"] = job_id
        request["accountId"] = "528163014577"
        translate_client = AwsHelper().getClient("translate")
        response = translate_client.describe_text_translation_job(JobId=job_id)
        request["jobName"] = response["TextTranslationJobProperties"]["JobName"]
        request["s3uri"] = response["TextTranslationJobProperties"]["InputDataConfig"][
            "S3Uri"
        ]
        request["langCode"] = response["TextTranslationJobProperties"][
            "TargetLanguageCodes"
        ][0]
        return request
    except ClientError as e:
        logger.error("An error occured with Amazon Translate Operation: %s" % e)


def get_client():
    """s3のclient取得"""
    return boto3.client("s3", region_name="us-east-1")


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
            return response["Contents"]
        else:
            logger.info("オブジェクトが存在しません。")
    except ClientError as e:
        logger.error(e)
        logger.warning("オブジェクト一覧取得エラーです。")


def download_object(s3_client, bucket_name, object_key, file_name):
    """オブジェクトをダウンロード"""
    try:
        s3_client.download_file(
            Bucket=bucket_name,
            Key=object_key,
            Filename="./results/{}".format(file_name),
        )
        logger.info("オブジェクト「%s」のダウンロードしました。" % object_key)
    except ClientError as e:
        logger.error(e)
        logger.warning("オブジェクト「%s」のダウンロードに失敗しました。" % object_key)
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
    bucket_name = "smat-translate-test"
    # upload ".vtt" and "triggerfile" to "input/"
    src_vtt = "Usage-of-S3-Buckets.vtt"
    with Path("./assets/{}".format(src_vtt)).open("rb") as fo:
        S3Helper.writeToS3(fo, bucket_name, "input/{}".format(src_vtt))
        S3Helper.writeToS3("", bucket_name, "input/triggerfile")
    source_lng = "en"
    target_lng = "ja"
    job_id, job_name = s3_event_handler(source_lng, target_lng)
    if job_name is not None:
        if checkStatusOfJob(job_name):
            req = translate_job_event_handler(job_id)
            processRequest(req)
        else:
            logger.warn(
                "Job ID {} failed or completed with errors, exiting".format(
                    req["jobId"]
                )
            )
    # download "ja.*.vtt"
    obj_key = S3Helper().getFilteredFileNames(
        bucket_name, "output/{}.{}".format(target_lng, src_vtt), ["vtt"]
    )[0]
    s3_client = get_client()
    download_object(
        s3_client, bucket_name, obj_key, "{}.{}".format(target_lng, src_vtt)
    )
    delete_object(s3_client, bucket_name, obj_key)


if __name__ == "__main__":
    main()
