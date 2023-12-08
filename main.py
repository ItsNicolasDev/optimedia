from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from PIL import Image
import os
from urllib.request import urlretrieve
from pydantic import BaseModel
import tempfile
import shutil
import uuid
from moviepy.editor import VideoFileClip
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/web", StaticFiles(directory="web", html=True), name="web")


class CompressionInput(BaseModel):
    url: str
    max_size: int


def download_file(url: str, dest: str):
    urlretrieve(url, dest)


def compress_image(input_path, output_path, quality=85):
    with Image.open(input_path) as image:
        original_width, original_height = image.size
        new_width = original_width // 2
        new_height = original_height // 2

        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        resized_image.save(output_path, "webp", quality=quality)


def compress_video(input_path, output_path, resize=True):
    clip = VideoFileClip(input_path)
    size = clip.size

    if resize:
        clip = clip.resize(0.5)

    clip.write_videofile(output_path, codec="libx265", audio_codec="aac", fps=15, audio_bitrate="64k")
    return size


def save_to_static_folder(temp_dir, output_format):
    static_folder = "static"
    os.makedirs(static_folder, exist_ok=True)

    compressed_file_name = os.listdir(temp_dir)[0]
    compressed_file_path_temp = os.path.join(temp_dir, compressed_file_name)

    compressed_file_name_new = f"compressed_{uuid.uuid4()}.{output_format}"
    compressed_file_path_new = os.path.join(static_folder, compressed_file_name_new)

    shutil.copy(compressed_file_path_temp, compressed_file_path_new)

    return compressed_file_path_new


@app.post("/compress")
async def compress_resource(input_data: CompressionInput):
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, "input")
            download_file(input_data.url, input_path)

            compressed_path = os.path.join(temp_dir, f"compressed_{uuid.uuid4()}")

            if input_data.url.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                compress_image(input_path, f"{compressed_path}.webp", quality=85)
                output_format = "webp"
            elif input_data.url.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                size = compress_video(input_path, f"{compressed_path}.mp4")
                output_format = "mp4"
            else:
                return JSONResponse(content={"error": "Format not supported"})

            output_size = os.path.getsize(f"{compressed_path}.{output_format}") / 1024
            if output_size > input_data.max_size:
                return JSONResponse(content={"error": "Output file too big"})

            compressed_file_path = save_to_static_folder(temp_dir, output_format)
            result = {
                "input_resource_size": f"{round(os.path.getsize(input_path) / 1024, 2)} Ko",
                "output_resource_size": f"{round(output_size, 2)} Ko",
                "compression_ratio": f"{round((1 - output_size / (os.path.getsize(input_path) / 1024)) * 100, 2)} %",
                "input_dimensions": size if input_data.url.lower().endswith(
                    ('.mp4', '.avi', '.mov', '.mkv')) else Image.open(input_path).size,
                "output_dimensions": VideoFileClip(compressed_file_path).size if output_format == "mp4" else Image.open(
                    compressed_file_path).size,
                "input_format": input_data.url.split('.')[-1].lower(),
                "output_format": output_format,
                "compressed_file_url": f"/download/{os.path.basename(compressed_file_path)}",
            }

            return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{filename}")
async def download_compressed_file(filename: str):
    static_folder = "static"
    compressed_file_path = os.path.join(static_folder, filename)

    if not os.path.exists(compressed_file_path):
        raise HTTPException(status_code=404, detail="Compressed file not found")

    return FileResponse(compressed_file_path)
