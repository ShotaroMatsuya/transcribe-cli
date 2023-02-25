import os
import subprocess
from logging import DEBUG, Formatter, StreamHandler, getLogger

# import boto3
# from botocore.exceptions import ClientError

logger = getLogger("ffmpeg：")
logger.setLevel(DEBUG)

stream_handler = StreamHandler()
formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def merge_video_with_vvt(video, vtt, output_file_name):
    video_filepath = os.path.join(os.path.dirname(__file__), "assets", video)
    # 存在check
    if os.path.exists(video_filepath):
        logger.info("ローカルファイル「%s」は存在します。" % (video))
    else:
        logger.warning("ローカルファイル「%s」は存在しません。" % (video))
        return False
    vtt_filepath = os.path.join(os.path.dirname(__file__), "results", vtt)
    # 存在check
    if os.path.exists(vtt_filepath):
        logger.info("ローカルファイル「%s」は存在します。" % (vtt))
    else:
        logger.warning("ローカルファイル「%s」は存在しません。" % (vtt))
        return False

    # cmd ; ffmpeg -i <input.mp4> -i <input.vtt> -c copy -c:s mov_text -metadata:s:s:0 language=jpn <output.mkv>
    if video.endswith(".mp4") and vtt.endswith(".vtt"):
        cmdline = (
            "ffmpeg -i "
            + video_filepath
            + " -i "
            + vtt_filepath
            + " -map 0:v -map 0:a -map 1 -metadata:s:s:0 language=eng -c:v copy -c:a copy -c:s webvtt "
            + "{}.mkv".format(output_file_name)
        )
        subprocess.call(cmdline, shell=True)


def main():
    test_audio_file = "Usage-of-S3-Buckets.mp4"
    test_vtt_file = "ja.Usage-of-S3-Buckets.vtt"
    merge_video_with_vvt(test_audio_file, test_vtt_file, "ja.Usage-of-S3-Buckets")


if __name__ == "__main__":
    main()
