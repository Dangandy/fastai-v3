# fastai libraries
from fastai import *
from fastai.vision import *
from fastai.callbacks.hooks import *

# Recommendation
import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine

# Web stuff
import aiohttp
import asyncio
import uvicorn
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

export_file_url = (
    "https://drive.google.com/uc?export=download&id=1-1qWJ8qX_eRZfap2tC4RDVbuijB39oDS"
)
export_file_name = "export.pkl"

classes = ["bracelet", "earring", "necklace", "ring"]
path = Path(__file__).parent

app = Starlette()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["X-Requested-With", "Content-Type"],
)
app.mount("/static", StaticFiles(directory="app/static"))


class SaveFeatures:
    features = None

    def __init__(self, m):
        self.hook = m.register_forward_hook(self.hook_fn)
        self.features = None

    def hook_fn(self, module, input, output):
        out = output.detach().cpu().numpy()
        if isinstance(self.features, type(None)):
            self.features = out
        else:
            self.features = np.row_stack((self.features, out))
        # self.features = out

    def remove(self):
        self.hook.remove()


async def download_file(url, dest):
    if dest.exists():
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, "wb") as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and "CPU-only machine" in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
df = pd.read_csv("app/cosine.csv")
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
sf = SaveFeatures(learn.model[1][4])
loop.close()


@app.route("/")
async def homepage(request):
    html_file = path / "view" / "index.html"
    return HTMLResponse(html_file.open().read())


@app.route("/analyze", methods=["POST"])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data["file"].read())
    img = open_image(BytesIO(img_bytes))
    prediction = learn.predict(img)
    print(f"prediction complete: {prediction}")

    # recommendation code
    array = np.array(sf.features)
    x = array.tolist()
    base_vector = x[-1]
    print(f"base vector: {base_vector}")
    cosine_similarity = 1 - df["img_repr"].apply(lambda x: cosine(x, base_vector))
    similar_img_ids = np.argsort(cosine_similarity)[-1]

    print(f"found df: {df.iloc[similar_img_ids]}")
    image = df.iloc[similar_img_ids].image
    title = df.iloc[similar_img_ids].title
    price = df.iloc[similar_img_ids].price
    link = df.iloc[similar_img_ids].link

    return JSONResponse(
        {
            "image": str(image),
            "title": str(title),
            "price": str(price),
            "link": str(link),
        }
    )


if __name__ == "__main__":
    if "serve" in sys.argv:
        uvicorn.run(app=app, host="0.0.0.0", port=5000, log_level="info")
